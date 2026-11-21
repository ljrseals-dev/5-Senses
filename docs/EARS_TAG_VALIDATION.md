# Ears tag-quality validation protocol

This protocol is separate from checkpoint loading and numerical parity. A
bit-exact model does not establish that its MSD labels are meaningful for the
music, genres, or users being evaluated.

## Dataset status

No human-reviewed track set is included yet. Do not report tag-quality
performance, tune production thresholds, or add authoritative MusicNN-derived
Expert rules until a licensed, provenance-tracked evaluation set exists.

## Required record per track

- SHA-256 of the exact decoded source file.
- Source URI or acquisition record and applicable license/permission.
- Split assignment: train, validation, or held-out test.
- Reviewer identity or stable reviewer ID and review date.
- Positive tags, explicitly negative tags, and unknown/not-reviewed tags as
  separate sets. Absence from the positive set is not automatically negative.
- Optional reviewer notes explaining ambiguous or subjective labels.

The vocabulary and index order must match the canonical 50-label list in
body_of_secrets/sensory/msd_tags.py. Preserve its spelling and capitalization.

## Evaluation rules

1. Keep the held-out test split untouched during threshold selection.
2. Report per-tag and macro-averaged precision, recall, F1, ROC-AUC, and PR-AUC
   where the split has sufficient positive and negative examples.
3. Report support counts for positive, negative, and unknown labels. Do not
   compute binary metrics by silently treating unknown labels as negatives.
4. Record the model checkpoint SHA-256, preprocessing configuration hash,
   tag-vocabulary hash, integration commit SHA, and evaluation code revision.
5. Compare results by relevant domain slices (for example, genre or recording
   conditions) only when those annotations have their own provenance.
6. Keep subjective or disputed labels as reviewer disagreement/unknown; do not
   collapse them into ground truth without a documented adjudication process.

## Promotion gate

A tag can be used as a supervised target only through the explicit
human-confirmed adapter API. A model prediction alone never satisfies this
gate. Numerical equivalence, preprocessing parity, and tag quality remain
three independent verification statuses.
