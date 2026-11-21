# EM-assisted corpus cleaning

The Boy Scout cleaner is a conservative, local, evidence-preserving pipeline. It
does not download data, call a hosted LLM, execute hidden remote agents, or claim
to train a pretrained neural model.

## Processing stages

1. **Intake gate** — accept only regular, non-symlink UTF-8 text files with
   `.txt`, `.md`, `.rst`, or `.text` extensions. Raw source files are never
   edited.
2. **Integrity baseline** — compute SHA-256 for the exact raw bytes.
3. **Deterministic cleanup** — NFC Unicode normalization, line-ending
   normalization, removal of NUL/control/format characters, horizontal
   whitespace cleanup, and collapse of excessive blank lines. It does not
   modernize spelling, remove hyphenation, rewrite punctuation, or change dates.
4. **Corpus-local EM profile** — fit an unsupervised noisy-channel profile over
   the observed corpus vocabulary using a small, directional OCR-confusion seed
   list (observed OCR form -> candidate printed form). The latent word distribution and confusion probabilities are iteratively
   re-estimated. Candidate words must already occur in the corpus.
5. **Conservative correction gate** — EM proposals are **review-only by default**.
   To apply the opt-in correction gate, the caller must explicitly enable
   `apply_em_corrections` / `--apply-em-corrections`. Even then, only lowercase
   tokens with posterior probability at least 0.995 and margin over the runner-up
   at least 0.20 can be changed. Capitalized tokens remain review-only. Unknown
   names, dates, numerals, quotations, and historical spellings are not
   normalized by a modern dictionary.
6. **Review queue** — uncertain proposals are written to JSONL with observed
   token, candidate, posterior, margin, action, and reason. Review proposals do
   not alter the cleaned text.
7. **Provenance manifest** — record source/output paths, raw and cleaned SHA-256,
   accepted correction counts, and review counts.

## Run

```python
from body_of_secrets.scouting.cleaning import clean_directory

results = clean_directory(
    "data/incoming/britannica",
    "data/processed/britannica",
    review_dir="data/review/britannica",
)
print(f"Processed {len(results)} text files")
```

CLI equivalent:

```bash
body-of-secrets clean data/incoming/britannica data/processed/britannica \\
  --review-dir data/review/britannica --iterations 12
# Optional, higher-risk step after inspecting the review policy:
body-of-secrets clean data/incoming/britannica data/processed/britannica-em \\
  --review-dir data/review/britannica-em --apply-em-corrections
```

The default per-file limit is 25 MiB and can be raised with
`--max-file-bytes` when a legitimate OCR text volume is larger. The destination
tree is separate from the source tree. Existing output files are not overwritten.
The cleaner refuses symlink source files and invalid UTF-8 rather than silently
replacing undecodable bytes.

## Important model boundary

This is **unsupervised EM adaptation**, not supervised training and not a
pretrained correction model. EM estimates latent word probabilities and
confusion-channel probabilities from the corpus itself. It can rank only
candidates supported by its observed vocabulary and seeded OCR confusions.
It cannot verify the original page image or guarantee semantic correctness.
For historical works, low-confidence proposals must remain unresolved until
checked against the scan or a trusted transcription.

Do not mix different languages, centuries, typefaces, OCR engines, or unrelated
domains into one EM profile. Fit one profile per coherent volume/edition or
well-defined OCR batch. Evaluate on manually checked pages held out by volume,
not randomly split lines, to avoid leakage from repeated content and print
artifacts.

## Agentic orchestration boundary

The stages above are separate, deterministic roles (intake, integrity, cleanup,
EM ranking, review, provenance), but currently run locally in one process.
There are no autonomous agents with credentials or unrestricted filesystem
access. If a later orchestrator is added, it must receive scoped input/output
paths, no network access by default, and must never modify raw sources or
approve its own uncertain corrections.

## Research basis

- Noisy-channel OCR correction and language-model priors:
  https://aclanthology.org/W14-0608/
- EM-based estimation for OCR correction:
  https://boston.lti.cs.cmu.edu/callan/Workshops/IR-OCR-02/rong.pdf
- Unsupervised correction using repeated text variants:
  https://aclanthology.org/2018.acl-long.58/
- Deduplication and OCR correction for large digitized book corpora:
  https://aclanthology.org/2021.findings-emnlp.356/

Research results are methodological references, not proof that this implementation
has achieved any particular error-rate improvement. Benchmark this cleaner on
edition-specific ground truth before promoting a cleaned corpus to training data.
