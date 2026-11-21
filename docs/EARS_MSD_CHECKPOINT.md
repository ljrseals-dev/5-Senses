# Ears / MSD MusicNN checkpoint record

## Integration boundary

MusicNN is an optional sensory feature extractor. It emits 50 independent MSD
tag logits; callers apply sigmoid when probabilities are required. It does not
replace or train the existing MLP, Hopfield, Expert, Archive, or n-gram
subsystems.

The model loader is local-file-only. It does not download weights or contact a
model hub. The checkpoint is not vendored in this repository.

## Supplied checkpoint inventory

| Item | Observed value |
|---|---|
| Filename | MSD_musicnn_optimized_fp16.pt |
| Bytes | 1,617,541 |
| SHA-256 | 17f79e34e075c2b9b94d394b5f1d82819db28e8887a7e2a6d0618e33540d81db |
| State-dict entries | 75 |
| Structural check | 75 expected / 75 found / 0 mismatches |
| Learnable parameter storage | FP16 |
| BatchNorm affine parameters | FP16 |
| BatchNorm running_mean / running_var | FP32 |
| num_batches_tracked | int64 (11 tensors) |

The supplied check_keys.py structural check completed successfully. The
checkpoint was separately loaded with torch.load(weights_only=True) to inspect
the dtype of every BatchNorm running-statistics and tracking tensor. All 22
running-statistics tensors (11 means and 11 variances) are FP32; all 11
tracking tensors are int64.

## Loader correction

The previous half=True implementation called model.half() on the entire
module. That operation also downcast BatchNorm affine parameters and running
statistics. The new loader restores every BatchNorm1d/BatchNorm2d module to
FP32 after converting the model to half precision. The default path keeps the
whole model in FP32 and promotes stored FP16 parameters during state-dict load.

## Provenance and licensing

The uploaded archive's LICENSE is an MIT license for the supplied code, with
copyright attributed to Lewis James Seals Jr. Its README explicitly says that
upstream terms for the original MusicNN weights and code apply and does not
grant or assert a weight license. The public MusicNN PyTorch model repository
labels its repository Apache-2.0, but that label alone does not establish the
redistribution rights for this separately exported checkpoint or the
underlying MSD-derived training artifacts.

Therefore the .pt file is intentionally not committed here. Keep it as a
user-supplied local artifact until the exact checkpoint provenance and
redistribution terms are documented. Record and verify its SHA-256 before use.

## Verification status — incomplete

- [x] Structural keys/shapes: 75/75, zero mismatches.
- [x] Checkpoint BatchNorm dtype inspection: all running statistics FP32.
- [x] Loader preserves FP32 BatchNorm state in FP32 and mixed-precision modes.
- [x] Same-process deterministic inference test on a fixed synthetic input.
- [ ] FP32 source checkpoint acquired and provenance verified.
- [ ] Fixed-input FP32-source versus supplied-checkpoint logits comparison.
- [ ] Maximum absolute logit difference recorded.
- [ ] Upstream reference implementation parity test passed.

No numerical-equivalence claim is made. The supplied artifact contains FP16
learnable parameters, so those values cannot be reconstructed exactly from
the optimized file. A valid drift measurement requires the corresponding
original FP32 source checkpoint and the reference implementation. Neither was
included in the supplied archive. The current checkpoint README's structural
check is not a numerical reference fixture.

## Preprocessing is a separate gate

The supplied documentation specifies a 16 kHz mono target, 512-point STFT,
256-sample hop, 96 mel bins, and log10(10000 * mel + 1). It does not
sufficiently establish all frontend details (including exact mel filterbank
implementation/normalization, window convention, centering/padding, and
resampling implementation) against the original training pipeline. These
values must not be treated as a verified preprocessing contract until checked
against the reference implementation and a known input/output fixture.

## Tag quality is separate

Numerical parity does not establish musical usefulness. No Expert rule may
treat an MSD tag as a verified fact. A held-out, provenance-recorded track set
with expected tag behavior and per-tag evaluation is required before making
tag-quality claims or authoring authoritative Expert rules.
