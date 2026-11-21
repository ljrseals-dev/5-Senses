"""Manifest-bound C++ compile/link/sanitizer verification harness.

Only checked-in fixture IDs may be executed. This module is separate from
cpp_debug.py, whose static analysis remains strictly non-executing.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_MANIFEST = Path("tests/fixtures/cpp/manifest.json")
ALLOWED_STANDARDS = {"c++98", "c++11", "c++14", "c++17", "c++20"}
ALLOWED_EXPECTED = {"COMPILE_FAIL", "LINK_FAIL", "ASAN_FINDING", "UBSAN_FINDING", "CLEAN"}
ALLOWED_SANITIZERS = {"address", "undefined", "thread"}
OUTPUT_LIMIT = 24_000


def _bounded(value: str | None) -> str:
    value = value or ""
    if len(value) <= OUTPUT_LIMIT:
        return value
    return value[:OUTPUT_LIMIT] + "\n[output truncated by cpp_harness]"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65_536), b""):
            digest.update(block)
    return digest.hexdigest()


def load_fixture_manifest(path: str | Path = DEFAULT_MANIFEST) -> tuple[Path, dict[str, Any]]:
    manifest_path = Path(path).resolve()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported C++ fixture manifest schema_version")
    if payload.get("external_source_code_included") is not False:
        raise ValueError("fixture manifest must explicitly exclude external source code")
    fixtures = payload.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise ValueError("fixture manifest requires a non-empty fixtures array")

    seen: set[str] = set()
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            raise ValueError("each fixture entry must be an object")
        fixture_id = fixture.get("id")
        relative = fixture.get("path")
        if not isinstance(fixture_id, str) or not fixture_id or fixture_id in seen:
            raise ValueError("fixture IDs must be non-empty and unique")
        seen.add(fixture_id)
        if not isinstance(relative, str) or not relative:
            raise ValueError(f"{fixture_id}: path must be a non-empty string")
        rel_path = Path(relative)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            raise ValueError(f"{fixture_id}: fixture path must stay within the fixture root")
        if fixture.get("standard") not in ALLOWED_STANDARDS:
            raise ValueError(f"{fixture_id}: unsupported C++ standard")
        if fixture.get("expected") not in ALLOWED_EXPECTED:
            raise ValueError(f"{fixture_id}: unsupported expected outcome")
        sanitizers = fixture.get("sanitizers")
        if not isinstance(sanitizers, list) or any(s not in ALLOWED_SANITIZERS for s in sanitizers):
            raise ValueError(f"{fixture_id}: invalid sanitizer list")
        timeout = fixture.get("timeout_seconds", 10)
        if not isinstance(timeout, int) or not 1 <= timeout <= 60:
            raise ValueError(f"{fixture_id}: timeout_seconds must be between 1 and 60")
        if fixture["expected"] in {"COMPILE_FAIL", "LINK_FAIL"} and sanitizers:
            raise ValueError(f"{fixture_id}: compile/link failure fixtures cannot request sanitizers")
        if fixture["expected"] == "ASAN_FINDING" and sanitizers != ["address"]:
            raise ValueError(f"{fixture_id}: ASAN fixture must request only address sanitizer")
        if fixture["expected"] == "UBSAN_FINDING" and sanitizers != ["undefined"]:
            raise ValueError(f"{fixture_id}: UBSAN fixture must request only undefined sanitizer")
        if fixture["expected"] == "CLEAN" and not sanitizers:
            raise ValueError(f"{fixture_id}: clean controls must run under at least one sanitizer")

    return manifest_path.parent.resolve(), payload


def _environment() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "LC_ALL": "C",
        "LANG": "C",
        "ASAN_OPTIONS": "abort_on_error=1:detect_leaks=0",
        "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1",
        "TSAN_OPTIONS": "halt_on_error=1",
    }


def _run(argv: list[str], *, cwd: Path, timeout: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd),
            env=_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
            close_fds=True,
        )
        return {
            "returncode": completed.returncode,
            "stdout": _bounded(completed.stdout),
            "stderr": _bounded(completed.stderr),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout
        err = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else exc.stderr
        return {
            "returncode": None,
            "stdout": _bounded(out),
            "stderr": _bounded(err),
            "timed_out": True,
        }


def _sanitizer_flags(name: str) -> list[str]:
    return [f"-fsanitize={name}", "-fno-omit-frame-pointer", "-g"]


def _sanitizer_available(compiler: str, sanitizer: str, standard: str,
                         timeout: int, work: Path) -> tuple[bool, str]:
    source = work / f"probe_{sanitizer}.cpp"
    obj = work / f"probe_{sanitizer}.o"
    exe = work / f"probe_{sanitizer}"
    source.write_text("int main() { return 0; }\n", encoding="utf-8")
    flags = _sanitizer_flags(sanitizer)
    compile_result = _run(
        [compiler, f"-std={standard}", *flags, "-c", str(source), "-o", str(obj)],
        cwd=work, timeout=timeout,
    )
    if compile_result["timed_out"] or compile_result["returncode"] != 0:
        return False, "sanitizer compile probe failed: " + compile_result["stderr"]
    link_result = _run(
        [compiler, *flags, str(obj), "-o", str(exe)],
        cwd=work, timeout=timeout,
    )
    if link_result["timed_out"] or link_result["returncode"] != 0:
        return False, "sanitizer link probe failed: " + link_result["stderr"]
    execute_result = _run([str(exe)], cwd=work, timeout=timeout)
    if execute_result["timed_out"] or execute_result["returncode"] != 0:
        return False, "sanitizer runtime probe failed: " + execute_result["stderr"]
    return True, ""


def _finding(stderr: str, sanitizer: str) -> bool:
    signatures = {
        "address": ("ERROR: AddressSanitizer:", "AddressSanitizer: heap-use-after-free"),
        "undefined": ("runtime error:", "UndefinedBehaviorSanitizer"),
        "thread": ("WARNING: ThreadSanitizer:", "ThreadSanitizer: data race"),
    }
    return any(token in stderr for token in signatures[sanitizer])


def _run_one(source: Path, compiler: str, standard: str, sanitizer: str | None,
             timeout: int, work: Path) -> dict[str, Any]:
    flags = ["-Wall", "-Wextra", "-Wpedantic", "-O0"]
    if sanitizer:
        flags.extend(_sanitizer_flags(sanitizer))
    obj = work / "fixture.o"
    exe = work / "fixture"
    compile_result = _run(
        [compiler, f"-std={standard}", *flags, "-c", str(source), "-o", str(obj)],
        cwd=work, timeout=timeout,
    )
    if compile_result["timed_out"]:
        return {"outcome": "TIMEOUT", "phase": "compile", "flags": flags, **compile_result}
    if compile_result["returncode"] != 0:
        diagnostic = compile_result["stderr"] + compile_result["stdout"]
        deleted_copy = any(token in diagnostic.lower() for token in (
            "use of deleted function", "deleted function", "is deleted",
            "call to deleted constructor",
        ))
        outcome = "COMPILE_FAIL" if deleted_copy else "UNEXPECTED_COMPILE_FAIL"
        return {"outcome": outcome, "phase": "compile", "flags": flags,
                "failure_signature_matched": deleted_copy, **compile_result}

    link_result = _run(
        [compiler, *flags, str(obj), "-o", str(exe)],
        cwd=work, timeout=timeout,
    )
    if link_result["timed_out"]:
        return {"outcome": "TIMEOUT", "phase": "link", "flags": flags, **link_result}
    if link_result["returncode"] != 0:
        diagnostic = link_result["stderr"] + link_result["stdout"]
        unresolved = any(token in diagnostic.lower() for token in (
            "undefined reference", "undefined symbol", "unresolved external",
        ))
        destructor_symbol = "interface::~interface" in diagnostic.lower()
        matched = unresolved and destructor_symbol
        outcome = "LINK_FAIL" if matched else "UNEXPECTED_LINK_FAIL"
        return {"outcome": outcome, "phase": "link", "flags": flags,
                "failure_signature_matched": matched, **link_result}

    execute_result = _run([str(exe)], cwd=work, timeout=timeout)
    if execute_result["timed_out"]:
        outcome = "TIMEOUT"
    elif sanitizer and _finding(execute_result["stderr"], sanitizer):
        outcome = {"address": "ASAN_FINDING", "undefined": "UBSAN_FINDING",
                   "thread": "TSAN_FINDING"}[sanitizer]
    elif execute_result["returncode"] == 0:
        outcome = "CLEAN"
    else:
        outcome = "EXECUTION_FAIL"
    return {
        "outcome": outcome,
        "phase": "execute",
        "flags": flags,
        "compile_returncode": compile_result["returncode"],
        "link_returncode": link_result["returncode"],
        **execute_result,
    }


def run_fixture(fixture_id: str, *, compiler_name: str = "g++",
                manifest_path: str | Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    """Run one allow-listed fixture and return provenance plus observed outcomes."""
    if compiler_name not in {"g++", "clang++"}:
        raise ValueError("compiler must be one of: g++, clang++")
    compiler = shutil.which(compiler_name)
    if compiler is None:
        raise FileNotFoundError(f"compiler not found on PATH: {compiler_name}")
    compiler = str(Path(compiler).resolve())

    fixture_root, manifest = load_fixture_manifest(manifest_path)
    entries = {item["id"]: item for item in manifest["fixtures"]}
    if fixture_id not in entries:
        raise ValueError(f"unknown fixture ID: {fixture_id}")
    fixture = entries[fixture_id]
    source = (fixture_root / fixture["path"]).resolve()
    if fixture_root not in source.parents or not source.is_file():
        raise ValueError(f"{fixture_id}: source path is missing or escapes fixture root")

    version_result = _run([compiler, "--version"], cwd=fixture_root,
                          timeout=min(fixture["timeout_seconds"], 10))
    if version_result["timed_out"] or version_result["returncode"] != 0:
        raise RuntimeError("compiler version probe failed")
    version = (version_result["stdout"] or version_result["stderr"]).splitlines()[0]
    source_hash = sha256_file(source)
    sanitizer_names: list[str | None] = fixture["sanitizers"] or [None]
    runs: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="body-of-secrets-cpp-") as temp:
        work = Path(temp).resolve()
        for index, sanitizer in enumerate(sanitizer_names):
            if sanitizer:
                available, reason = _sanitizer_available(
                    compiler, sanitizer, fixture["standard"],
                    fixture["timeout_seconds"], work,
                )
                if not available:
                    runs.append({
                        "sanitizer": sanitizer,
                        "outcome": "SANITIZER_UNAVAILABLE",
                        "reason": _bounded(reason),
                    })
                    continue
            run = _run_one(
                source, compiler, fixture["standard"], sanitizer,
                fixture["timeout_seconds"], work,
            )
            run["sanitizer"] = sanitizer
            runs.append(run)

    expected = fixture["expected"]
    expected_for_run = expected
    if expected == "CLEAN":
        expected_for_run = "CLEAN"
    passed = bool(runs) and all(run["outcome"] == expected_for_run for run in runs)
    if expected in {"ASAN_FINDING", "UBSAN_FINDING"}:
        passed = len(runs) == 1 and runs[0]["outcome"] == expected
    return {
        "schema_version": 1,
        "fixture_id": fixture_id,
        "fixture_path": fixture["path"],
        "source_sha256": source_hash,
        "expected": expected,
        "passed": passed,
        "compiler": compiler_name,
        "compiler_path": compiler,
        "compiler_version": version,
        "platform": platform.platform(),
        "standard": fixture["standard"],
        "tags": fixture.get("tags", []),
        "execution_performed": any(run.get("phase") == "execute" for run in runs),
        "runs": runs,
        "external_source_code_included": False,
    }


def run_all(*, compiler_name: str = "g++",
            manifest_path: str | Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    _, manifest = load_fixture_manifest(manifest_path)
    results = [
        run_fixture(item["id"], compiler_name=compiler_name, manifest_path=manifest_path)
        for item in manifest["fixtures"]
    ]
    return {
        "schema_version": 1,
        "compiler": compiler_name,
        "passed": all(item["passed"] for item in results),
        "fixture_count": len(results),
        "results": results,
    }
