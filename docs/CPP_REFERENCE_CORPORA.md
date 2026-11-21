# C++ reference corpora: metadata-first integration

The C++ layer uses two complementary external repositories as reference corpora,
not as model weights:

- [BartVandewoestyne/Cpp](https://github.com/BartVandewoestyne/Cpp): historical
  examples and cross-standard context.
- [BartVandewoestyne/Effective-Modern-Cpp](https://github.com/BartVandewoestyne/Effective-Modern-Cpp):
  modern C++ semantics and compilable example material.

## Current integration boundary

`data/cpp_reference_corpora.json` is a metadata-only seed manifest. It contains
stable local record IDs, source repository URLs, concept tags, candidate
language standards, explanations, hypotheses, and discriminating tests. It
pins each repository snapshot to a commit SHA, but does not claim that an
individual example path has been located: source paths remain null until the
file-level inventory is complete.

All records are marked `UNVERIFIED_HOLD`. The pinned repository snapshots are
`BartVandewoestyne/Cpp` at `376ae463ee95ee5723e74322b7fa25a59e972ac9` and
`BartVandewoestyne/Effective-Modern-Cpp` at
`a1d8f84ee679a92fade7b4ca3fa46f9f48886539`. Neither repository tree contains
LICENSE, COPYING, NOTICE, or COPYRIGHT files, and GitHub reports no detected
repository license for either. This is an unresolved rights status, not proof
that every file has identical rights. The integration does not fetch,
copy, redistribute, compile, or execute third-party source. The
Effective-Modern-Cpp README describes the repository as the author's personal
implementation and says it is not officially linked to the book; that statement
is not a reuse license. The Cpp repository's applicable license also remains
unverified. Do not bulk-import source until the exact license and file-level
notices have been reviewed.

## Import

Preview and validate without writing:

```sh
body-of-secrets cpp-corpus --dry-run
```

Import metadata records into the local SQLite Archive:

```sh
body-of-secrets cpp-corpus
```

The importer is repeatable: deterministic document IDs refresh the same
records instead of creating duplicates. It stores source repository, path,
revision, standards, concepts, Item number where known, rights status, and
explicit `source_code_included: false` metadata.

## Expert behavior

The default Expert now registers C++ semantic rules for:

- pure virtual destructors and required definitions;
- unique, shared, and weak ownership;
- the distinction between `std::move` and an actual move operation;
- forwarding references and reference collapsing;
- `auto` / `decltype` deduction;
- shared ownership versus thread safety;
- raw allocation and concurrency primitives.

Each match emits a `[PLAUSIBLE]` hypothesis plus a distinguishing test and
`[NOT_VERIFIED]`. A textual match is not a diagnosis. Compiler output,
sanitizer output, and reproducible test results must be separately recorded
before a cause can become verified.

## Remaining acquisition work

1. Inventory each source repository at a pinned commit.
2. Locate repository-wide and file-local license notices; review book-derived
   material separately from repository-authored code.
3. Populate exact source paths and revisions only after that audit.
4. Import only files whose license permits the intended storage and reuse.
5. Compile examples with their declared `-std=` mode and preserve the exact
   compiler, flags, output, and test evidence.
