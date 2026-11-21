# Local Ears and Classical-First Debugging Contract

Status: **Architecture contract / implementation not yet complete**

## Goals and hard boundaries

BODY OF SECRETS remains classical-first, local-first, offline-capable, and provenance-aware. C++17/C++20 are the primary proving ground; Python is deferred until the classical C++ metrics stabilize.

- Speech recognition is an input adapter only. It cannot become a privileged execution or write channel.
- Network access is not required for transcription, debugging, archive retrieval, or verification.
- LLM providers remain optional and must be disabled for classical-only evaluation.
- Claims are separated into observed evidence, hypotheses, and verified conclusions.
- A hypothesis is not promoted to verified knowledge solely because the system or a provider generated it.

## Ears: local transcription

Foundation: **whisper.cpp**, invoked through a thin C++ adapter or local CLI.

Pipeline:
1. Accept a local microphone stream or local audio file path.
2. Convert/resample to **16 kHz mono WAV** (Whisper input requirement).
3. Transcribe locally using a selected model, with quantized models supported where available.
4. Emit a structured speech-input record with text, source type, model identity, model confidence/score when exposed by the backend, capture/transcription timestamp, and audio provenance.
5. Inject the transcript as ordinary input into the same Brain/Expert/Archive workflow as typed input.

Suggested model tiers: start with `base.en` or `small.en`; evaluate larger models (e.g. medium or turbo variants) against a technical-vocabulary accuracy benchmark before enabling them as an option. Do not assume model confidence is factual confidence.

**Ears must not** execute shell commands, write project files, launch compilers, alter Expert rules, or apply fixes. Transcribed requests remain untrusted input and are subject to the same authorization and verification gates as typed requests.

## Evidence and provenance contract

For every debugging session, record what is available and preserve unknowns explicitly:

- input source (typed or speech); transcript and model metadata if speech
- source files and relevant excerpts/hash where practical
- compiler name/version, dialect (C++17/C++20), build flags
- sanitizer set and exact observed output
- test commands and outcomes
- timestamp, corpus/source provenance, and record identifier
- competing hypotheses with supporting and contradicting evidence
- proposed discriminating tests and results
- verified root cause (or UNKNOWN / PLAUSIBLE if not confirmed)
- minimal fix, if any, plus regression results
- confidence updates with reasons

Never fabricate compiler/sanitizer output, citations, timestamps, confidence values, or verification outcomes. Store model transcription scores separately from debugging hypothesis confidence.

## Debug loop

1. Ingest typed or speech input as an ordinary report.
2. Preserve initial report and observed diagnostics in the Archive with provenance.
3. Brain decomposes failure into relevant categories: lifetime, ownership, memory/UB, concurrency, templates, concepts/ranges, ABI/ODR, build, real-time safety, and logic.
4. Expert rules produce competing, ranked hypotheses with explicit confidence/truth tags and evidence links.
5. Memory (Hopfield/dense associative recall) retrieves similar cases; retrieval is advisory and linked to source records.
6. Propose minimal distinguishing tests and compiler/sanitizer runs.
7. Execute only in an explicitly configured sandbox, with execution permission and resource limits; report the actual results.
8. Update hypothesis status only based on observed test results. If unresolved, preserve UNKNOWN/PLAUSIBLE.
9. Propose a minimal patch only after evidence supports the cause.
10. Run regression tests; archive the entire outcome and provenance.

## First command milestone: `debug-cpp`

A proposed deterministic command shape:

```text
body-of-secrets debug-cpp --source failing.cpp --compiler clang++ --std c++20 --sanitizers address,undefined
```

Expected stages: classification; ranked hypotheses; evidence for/against; distinguishing tests; sandbox verification; minimal-fix recommendation only when verified; regression tests; archival of a structured session record.

The command must refuse to claim verification when compiler/sanitizer execution is unavailable, skipped, inconclusive, or failed.

## Bug-record schema (initial proposal)

```json
{
  "record_id": "cpp-debug-000001",
  "language": "cpp",
  "standard": "c++20",
  "category": ["lifetime"],
  "source_type": "typed",
  "input_text": "...",
  "transcription": null,
  "environment": {
    "compiler": "clang++",
    "compiler_version": "unknown",
    "flags": [],
    "sanitizers": ["address", "undefined"]
  },
  "observations": [],
  "hypotheses": [
    {
      "id": "H1",
      "statement": "...",
      "status": "PLAUSIBLE",
      "confidence": null,
      "supporting_evidence": [],
      "contradicting_evidence": [],
      "discriminating_tests": [],
      "verification_results": []
    }
  ],
  "verified_cause": null,
  "minimal_fix": null,
  "regression_results": [],
  "provenance": [],
  "created_at": null
}
```

Schema details (especially confidence calibration, evidence references, and timestamp source) require implementation-time validation. Null/unknown values are intentional; they must not be replaced by invented values.

## Corpus strategy

Initial sources, prioritized:
1. User-owned audio/DSP code repositories, using reproducible bugs or carefully verified cases. Candidate projects include Eyesore, hush-processor, Sogitech Cmajor components, and Aura-G-Adapter; verify repository availability and license before ingestion.
2. Carefully curated C++ Core Guidelines and official compiler/documentation examples.
3. Public compilable bug datasets and crash/fix pairs only after license, provenance, reproducibility, and data quality checks.

Seed high-signal classes: use-after-move, dangling references, iterator invalidation, races/atomics, concepts/ranges constraints, ODR/linkage, ABI mismatches, real-time allocation/locking, and sanitizer findings.

Every imported record must distinguish original observed output from editorial interpretation and preserve source URL/commit, license, compiler/toolchain, dialect, and reproducibility status. Do not bulk-import unverified examples.

## Learning and evaluation

Measure on a held-out, reproducible C++ test set:
- Top-1 and Top-3 root-cause ranking accuracy
- Discrimination rate: whether suggested tests separate competing hypotheses
- False-confirmation rate
- Fix regression rate
- Provenance completeness
- Classical-only accuracy with all LLM providers disabled

Report sample size, class distribution, test conditions, and failures alongside metrics. Do not claim intelligence improvements from prose quality.

## Python expansion gate

Python is a second language using the same evidence/hypothesis/verification record and workflow. Do not prioritize its corpus or claim C++ readiness until baseline and regression metrics are established and repeatable.

## Integration testbeds

Aura-G-Adapter and Sogitech repositories are candidate testbeds for cross-language, real-time, parameter-control, audio, and recorded narration scenarios. Inspect and confirm repository structure and current behavior before making integration claims. Keep their integration optional and isolated; speech narration does not bypass the same verification pipeline.

## Implementation sequence

1. Inspect current package architecture, CLI, Archive, Expert, Memory, tests, and dependency policy.
2. Add schema and provenance validation tests.
3. Add offline Ears adapter boundary and audio normalization tests.
4. Add speech-input integration tests proving no privileged execution/write path.
5. Add C++ corpus ingestion and provenance validation.
6. Implement `debug-cpp` stages, test/sandbox gates, and archive records.
7. Add controlled end-to-end fixtures and held-out evaluation.
8. Publish results and known limitations before expanding to Python.

This document specifies the contract only; it does not assert that these features are implemented or tested.
