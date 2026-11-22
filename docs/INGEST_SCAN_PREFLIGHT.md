# 5-Senses document-ingest scan preflight

**Status:** source inspection only; no scanner or ingest gate is implemented by
this commit.

**Inspected main:** 3cf72d5879d46166a31ff2668d82013693008953

**Related MCP integration:** open draft PR #25, branch
integrate-offline-doc-mcp, head
f699ff0a483ad56d5013ae7623beb851827c9a5c. This is not part of main and is
not a merged or production-enabled integration.

## Findings from source

### 1. Local archive ingest entry points

- body_of_secrets/archive/store.py::Archive.import_document is the central
  text-level write path. It accepts caller-provided title, content, source,
  tags, metadata, and optional doc_id, then writes the document and term index
  in one SQLite workflow.
- Archive.import_text_file reads a path with UTF-8 decoding and
  errors="replace", then calls import_document. There is no content signature,
  scanner, MIME check, or quarantine step.
- body_of_secrets/interface/cli.py::_cmd_import is the user-facing file
  import path. A single file is passed directly to import_text_file. A
  directory is recursively traversed, but only .txt, .md, .rst, and .text
  suffixes are selected. This suffix allowlist is not MIME validation.
- Consequently, a future local gate must protect both the file-based path and
  any public text-level import API that can persist untrusted content. A check
  only in the CLI would be bypassable by direct Python callers.

### 2. Idempotency and re-ingest

- If no doc_id is supplied, import_document derives a deterministic ID
  from source, title, and full content.
- The SQL write uses INSERT OR REPLACE; re-importing the same identity
  replaces the row and rebuilds its term rows. Supplying an explicit doc_id
  also replaces the existing row.
- There is no scan-state column or prior clean-record lookup today. The
  forthcoming gate must run against the exact bytes/content being persisted on
  every import attempt. It must not accept a prior clean record solely because
  the path or derived document ID matches.
- The current archive stores decoded text, not the original uploaded byte
  stream. A future implementation must explicitly decide whether the scan
  record hashes original bytes and retains that digest in metadata, and must
  avoid treating lossy UTF-8 replacement decoding as byte-preserving evidence.

### 3. Search result / MCP boundary

- On inspected main, there is no MCP adapter or remote SearchResult model.
  The main branch's Brain retrieves only from the local Archive.
- Draft PR #25 adds body_of_secrets/adapters/mcp_archive.py. Its client
  returns dictionaries from MCP JSON results after checking only that title,
  source/path, and content/snippet are strings. It does not require or validate
  an acquisition_scan field, scanner identity, signature freshness, verdict,
  or scan timestamp.
- The PR's Engine._retrieve consumes those dictionaries directly and
  includes their content in the Brain context. There is no typed SearchResult
  deserialization boundary and no missing-provenance-to-degraded behavior.
- The draft PR remains open and unmerged. The scan-provenance contract must be
  designed against the actual upstream refactored-spoon producer contract
  before changing the adapter. Missing provenance must be explicit and
  degraded during migration; it must not be silently represented as clean.

### 4. Brain prompt assembly and trust boundary

- body_of_secrets/brain/prompts.py::build_user_message is the central
  provider prompt builder. It currently prefixes retrieved text with
  "Retrieved context / documents:", but does not explicitly state that the
  material is untrusted data, delimit it with an unambiguous data boundary, or
  instruct the model not to follow instructions found inside it.
- body_of_secrets/brain/engine.py also assembles retrieval-bearing answer
  strings directly for ARCHIVE mode and the no-provider fallback. Those paths
  return text to the caller rather than passing it to an LLM. ARCHIVE mode is
  document-only and does not invoke an LLM provider.
- In the draft MCP PR, Engine._retrieve also constructs external/local context
  sections, then the provider path passes context through build_user_message.
  The prompt builder is therefore the right central place for provider-context
  delimiting, but retrieval-bearing answer formatting remains a separate output
  path.
- No tool-execution interface is present in the inspected Brain provider
  contract; the provider interface exposes text completion. Do not claim
  retrieved content can currently invoke tools based only on this repository
  source. If tools are added later, their authorization and argument validation
  require a separate trust-boundary review.

### 5. CI and dependency constraints

- pyproject.toml declares Python >=3.10; classifiers list Python 3.10,
  3.11, and 3.12.
- Both .github/workflows/python-ci.yml and
  .github/workflows/tests.yml test Python 3.10, 3.11, and 3.12.
- Runtime dependencies currently include only python-dotenv>=1.0.0.
  Neither python-magic nor a ClamAV client binding is declared.
- No scanner package should become a mandatory import for the existing package
  until its supported platforms and dependency behavior are established.
  Scanner absence must produce a degraded/refused local-ingest decision, not
  an import-time failure that breaks unrelated CLI commands.

## Design decisions for the next implementation step

1. Keep scanning opt-in only through an explicit ingest service until all
   archive write paths can be gated. Do not add a decorative scanner status.
2. Scan original bytes before decoding or indexing. Bind the SHA-256 in
   ScanRecord to those exact bytes. A text-only import API needs an explicit
   policy: either scan its UTF-8 encoding as the exact submitted payload or
   reject it when the caller cannot provide byte provenance.
3. A local verdict other than clean, including unavailable scanner,
   unavailable MIME identification, or stale/unverifiable signatures, must
   refuse indexing and leave the item eligible for a later rescan. Do not
   persist a clean result from an earlier attempt as a bypass.
4. Treat a declared-extension / libmagic mismatch as a separate blocking
   validation result. Do not label it a ClamAV malware detection.
5. Store the immutable scan record with archive provenance and ensure updates
   to a document's content invalidate any previous scan record.
6. For remote MCP results, verify upstream scan provenance rather than
   rescanning the same bytes in 5-Senses. Missing or non-clean provenance is
   degraded and must never be presented as verified clean. This requires a
   producer-side contract in refactored-spoon; the current draft consumer does
   not establish it.
7. Delimit retrieved content as untrusted data in the single provider prompt
   builder. Do not describe heuristic injection matching as a security
   boundary. No current tool-calling surface was found in the inspected
   provider API.
8. Keep the scanner invocation out of this preflight commit. The next change
   should add the local gate and its negative tests before enabling it on the
   CLI or remote adapter.

## Evidence boundary

This document reports repository source only. It does not establish that
ClamAV, clamd, libmagic, or a MIME database is installed or operational on any
host. No EICAR, MIME-mismatch, quarantine, scanner-unavailable, or live MCP
provenance acceptance test has been run by this commit. The ScanRecord model
records provenance; it does not perform scanning or protect the Archive yet.
