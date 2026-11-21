"""Command-line interface for BODY OF SECRETS."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from body_of_secrets import __version__
from body_of_secrets.archive import Archive
from body_of_secrets.brain import Engine
from body_of_secrets.cpp_debug import analyze_cpp_file, report_json
from body_of_secrets.cpp_corpus import import_manifest, load_manifest
from body_of_secrets.expert import build_default_expert
from body_of_secrets.language import NGramModel
from body_of_secrets.memory import Memory
from body_of_secrets.neural import demo_hopfield, demo_xor


def _cmd_ask(args: argparse.Namespace) -> int:
    archive = Archive(args.db) if args.db else Archive()
    engine = Engine(archive=archive, expert=build_default_expert())

    answer = engine.ask(
        args.question,
        mode=args.mode,
        subject=args.subject,
        use_archive=not args.no_archive,
    )

    if args.json:
        print(json.dumps({
            "question": answer.question,
            "mode": answer.mode,
            "answer": answer.answer,
            "subject": answer.subject,
            "truth_status": answer.truth_status,
            "evidence": [{"tag": e.tag, "count": e.count} for e in answer.evidence],
            "sources": answer.sources,
            "classical": answer.classical,
            "version": answer.version,
        }, indent=2))
    else:
        print(f"Mode: {answer.mode}  |  Classical: {answer.classical}")
        if answer.subject:
            print(f"Subject: {answer.subject}")
        print(f"Truth status: {answer.truth_status}")
        if answer.sources:
            print("Sources:", "; ".join(answer.sources))
        print()
        print(answer.answer)
        if answer.evidence:
            print()
            print("Evidence tags:", ", ".join(f"{e.tag}×{e.count}" for e in answer.evidence))
    archive.close()
    return 0


def _cmd_import(args: argparse.Namespace) -> int:
    archive = Archive(args.db)
    path = Path(args.path)
    if path.is_file():
        doc_id = archive.import_text_file(path, source=args.source or str(path))
        print(f"Imported file → {doc_id}")
    elif path.is_dir():
        count = 0
        for f in sorted(path.rglob("*")):
            if f.is_file() and f.suffix.lower() in {".txt", ".md", ".rst", ".text"}:
                doc_id = archive.import_text_file(f, source=args.source or str(f))
                print(f"  {f.name} → {doc_id}")
                count += 1
        print(f"Imported {count} documents.")
    else:
        print(f"Path not found: {path}", file=sys.stderr)
        archive.close()
        return 1
    print(f"Archive now contains {archive.count()} document(s).")
    archive.close()
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    archive = Archive(args.db)
    hits = archive.search(args.query, limit=args.limit)
    if not hits:
        print("No hits.")
    for h in hits:
        print(f"[{h.score:.3f}] {h.title}  ({h.source})")
        print(f"         {h.snippet}")
        print()
    archive.close()
    return 0


def _cmd_memory(args: argparse.Namespace) -> int:
    mem = Memory()
    if args.action == "put":
        mem.put(args.key, args.value, source="cli")
        print(f"Stored: {args.key}")
    elif args.action == "get":
        entry = mem.get(args.key)
        if entry:
            print(json.dumps({"key": entry.key, "value": entry.value, "source": entry.source}, indent=2))
        else:
            print("Not found.")
            mem.close()
            return 1
    elif args.action == "list":
        for k in mem.list_keys():
            print(k)
    elif args.action == "search":
        for e in mem.search(args.key):
            print(f"{e.key}: {e.value}")
    mem.close()
    return 0


def _cmd_ngram(args: argparse.Namespace) -> int:
    model = NGramModel(n=args.n, level=args.level)
    if args.train:
        path = Path(args.train)
        if path.is_file():
            model.train_file(path)
        else:
            model.train([args.train])
        print(f"Trained {args.n}-gram ({args.level}) model. Vocab size: {len(model.vocab)}")
    if args.generate:
        print(model.generate(length=args.length, seed=args.seed))
    if args.prefix:
        conts = model.most_likely_continuations(args.prefix, k=5)
        for tok, p in conts:
            print(f"  {tok!r:20s}  p={p:.4f}")
    return 0


def _cmd_neural(args: argparse.Namespace) -> int:
    if args.demo == "hopfield":
        print(demo_hopfield())
    elif args.demo == "mlp":
        print(demo_xor())
    else:
        print("Unknown demo. Choose: hopfield | mlp")
        return 1
    return 0



def _cmd_debug_cpp(args: argparse.Namespace) -> int:
    """Run static C++ triage; never launches a compiler or executes source."""
    try:
        report = analyze_cpp_file(args.source, standard=args.std, input_text=args.description or "")
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"C++ triage failed: {exc}", file=sys.stderr)
        return 2

    archive = Archive(args.db)
    record_json = report_json(report)
    doc_id = archive.import_document(
        title=f"C++ debug triage {report.record_id}",
        content=record_json,
        source=f"cpp-debug:{report.source_path}",
        tags=["cpp-debug", "static-triage", args.std],
        metadata={"record_id": report.record_id, "source_sha256": report.source_sha256,
                  "verification": "NOT_RUN"},
    )
    archive.close()
    payload = json.loads(record_json)
    payload["archive_document_id"] = doc_id
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Record: {report.record_id}")
        print(f"Source SHA-256: {report.source_sha256}")
        print(f"Observations: {len(report.observations)}")
        for item in report.observations:
            print(f"  {item.rule} at line {item.line}: {item.excerpt}")
        print(f"Hypotheses: {len(report.hypotheses)}")
        for item in report.hypotheses:
            print(f"  {item.id} [{item.status}] {item.category}: {item.statement}")
            for test in item.discriminating_tests:
                print(f"    Discriminate with: {test}")
        print("Verification: NOT RUN (static triage only; no compiler or sanitizer launched)")
        print(f"Archived as: {doc_id}")
    return 0



def _cmd_cpp_corpus(args: argparse.Namespace) -> int:
    """Import metadata-only C++ corpus records; never fetch or copy source code."""
    try:
        manifest = load_manifest(args.manifest)
        if args.dry_run:
            print(f"Validated {len(manifest['records'])} metadata records from {len(manifest['sources'])} repositories.")
            print("No Archive writes performed.")
            return 0
        with Archive(args.db) as archive:
            imported = import_manifest(archive, args.manifest)
            print(f"Imported or refreshed {len(imported)} metadata-only C++ reference records.")
            print("Source code copied: no")
            print("Rights status: UNVERIFIED_HOLD (all records)")
            for doc_id in imported:
                print(f"  {doc_id}")
        return 0
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(f"C++ corpus import failed: {exc}", file=sys.stderr)
        return 2



def _cmd_status(args: argparse.Namespace) -> int:
    archive = Archive(args.db)
    print(f"BODY OF SECRETS v{__version__}")
    print(f"Archive documents : {archive.count()}")
    print(f"Archive DB        : {archive.db_path}")
    mem = Memory()
    print(f"Memory keys       : {len(mem.list_keys())}")
    mem.close()
    archive.close()
    print("Classical components: Archive, Memory, Expert, NGram, Hopfield, MLP — available")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="body-of-secrets",
        description="BODY OF SECRETS — Classical Intelligence & Language Architecture",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--db", default="data/archive.db", help="Path to archive SQLite DB")

    sub = parser.add_subparsers(dest="command")

    p_ask = sub.add_parser("ask", help="Ask a question (classical-first)")
    p_ask.add_argument("question", help="The question to ask")
    p_ask.add_argument("-m", "--mode", default="CLASSICAL",
                       choices=["AUTO", "CLASSICAL", "RESEARCH", "ARCHIVE", "AUDIT", "HYBRID"])
    p_ask.add_argument("-s", "--subject", default=None)
    p_ask.add_argument("--no-archive", action="store_true")
    p_ask.add_argument("--json", action="store_true")
    p_ask.set_defaults(func=_cmd_ask)

    p_imp = sub.add_parser("import", help="Import documents into the Archive")
    p_imp.add_argument("path", help="File or directory to import")
    p_imp.add_argument("--source", default=None)
    p_imp.set_defaults(func=_cmd_import)

    p_search = sub.add_parser("search", help="BM25 search over the Archive")
    p_search.add_argument("query")
    p_search.add_argument("-n", "--limit", type=int, default=5)
    p_search.set_defaults(func=_cmd_search)

    p_mem = sub.add_parser("memory", help="Key-value associative memory")
    p_mem.add_argument("action", choices=["put", "get", "list", "search"])
    p_mem.add_argument("key", nargs="?", default="")
    p_mem.add_argument("value", nargs="?", default="")
    p_mem.set_defaults(func=_cmd_memory)

    p_ng = sub.add_parser("ngram", help="Classical n-gram language model")
    p_ng.add_argument("--train", help="File path or raw text to train on")
    p_ng.add_argument("--n", type=int, default=3)
    p_ng.add_argument("--level", choices=["word", "char"], default="word")
    p_ng.add_argument("--generate", action="store_true")
    p_ng.add_argument("--length", type=int, default=40)
    p_ng.add_argument("--seed", default=None)
    p_ng.add_argument("--prefix", default=None)
    p_ng.set_defaults(func=_cmd_ngram)

    p_nn = sub.add_parser("neural", help="Run classical neural demos")
    p_nn.add_argument("demo", choices=["hopfield", "mlp"])
    p_nn.set_defaults(func=_cmd_neural)


    p_cpp = sub.add_parser("debug-cpp", help="Evidence-preserving, non-executing C++ source triage")
    p_cpp.add_argument("--source", required=True, help="C++ source file to inspect (read-only)")
    p_cpp.add_argument("--std", default="c++20", choices=["c++17", "c++20"])
    p_cpp.add_argument("--description", default=None, help="Observed failure or diagnostic (not executed)")
    p_cpp.add_argument("--json", action="store_true")
    p_cpp.set_defaults(func=_cmd_debug_cpp)

    p_corpus = sub.add_parser("cpp-corpus", help="Import metadata-only C++ reference corpus records")
    p_corpus.add_argument("--manifest", default="data/cpp_reference_corpora.json")
    p_corpus.add_argument("--dry-run", action="store_true", help="Validate and preview without Archive writes")
    p_corpus.set_defaults(func=_cmd_cpp_corpus)

    p_st = sub.add_parser("status", help="Show system status")
    p_st.set_defaults(func=_cmd_status)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
