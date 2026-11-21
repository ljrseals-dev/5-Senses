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
grant or assert a weight license. The original jordipons/musicnn source publishes an ISC license for its code.
The public oriyonay/musicnn-pytorch repository labels its model repository
Apache-2.0. The MSD dataset's own terms distinguish Echo Nest API data from
Last.fm tag data (CC BY-NC-SA 2.0). These are separate provenance layers; none
of those repository-level labels by itself resolves the exact redistribution
rights for this separately exported checkpoint and all of its learned
parameters. References: https://github.com/jordipons/musicnn/blob/master/LICENSE.md
and https://github.com/tbertinmahieux/MSongsDB/blob/master/LICENSE.

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
the optimized file. A public FP32 candidate was identified at
https://huggingface.co/oriyonay/musicnn-pytorch/tree/main/weights as
MSD_musicnn.pt (3.19 MB; published SHA-256
6db4c22908da50888d6a259d41980988d3b9cecc5f96fd725ede09166996dd00). It was
not acquired into this environment: the file-host download endpoint failed.
Its relationship to the supplied optimized checkpoint has not been proven.

There is also a concrete source-version discrepancy to resolve before a
reference comparison. The supplied checkpoint's structural manifest expects
keys such as timbral_1.conv.conv.weight and temp_1.conv.conv.weight. The
currently published public PyTorch port defines TimbralBlock/TemporalBlock
using conv_block, producing conv_block.conv.* key paths instead. Shapes may
still correspond, but the key-name difference means the 75/75 local structural
check is not an independent upstream compatibility check. Preserve the exact
mapping and reference source revision in the provenance record before any
key remapping or numerical comparison.

## Preprocessing is a separate gate

The original MusicNN FAQ documents 16 kHz audio, a 512-sample Hanning
window, 50% overlap, 96 mel bands, and log10(10000 * mel + 1). The public
PyTorch port specifies n_fft=512, hop_length=256, n_mels=96 and calls
librosa.feature.melspectrogram without overriding its other defaults. It also
calls librosa.resample without pinning res_type. References:
https://github.com/jordipons/musicnn/blob/master/FAQs.md and
https://huggingface.co/oriyonay/musicnn-pytorch/blob/main/musicnn_torch.py.

The new frontend makes every setting explicit: 16 kHz, n_fft/win_length 512,
hop 256, Hann window, centered constant padding, power 2, 96 Slaney-normalized
HTK-disabled mel bins from 0 to 8 kHz, log10(10000 * mel + 1), and soxr_hq
resampling. librosa is pinned to 0.11.0 in the optional audio extra. This is a
reproducible pinned interpretation of the public port, not proof of the
historical training frontend: the source port did not pin its librosa version
or resampling default. The fixed-waveform regression test is a local
implementation regression fixture, not an upstream-provided reference pair.
Preprocessing parity remains unverified until compared against an independent
reference output generated under the original dependency versions.

## Classical subsystem adapters

The ordered 50-label vocabulary is preserved exactly as published by the
MusicNN PyTorch port. Inference returns sigmoid probabilities (not softmax),
keeps per-patch scores, and averages probabilities across patches as the
reference inference utility does.

The adapters expose the 50 probabilities as MLP input features. MLP updates,
Hopfield patterns, and n-gram training require an explicit human-confirmed
tag list and a non-empty confirmation source. A registered Expert rule marks
MusicNN outputs as [UNKNOWN]; it does not turn predicted tags into facts.
Archive records include all 50 scores, the audio SHA-256, checkpoint SHA-256,
resolved preprocessing configuration and its hash, tag-vocabulary hash,
checkpoint dtype inventory, and integration commit SHA.

The model loader and adapters do not download weights or call a model hub.
The offline test blocks socket creation while loading a local checkpoint,
preprocessing a local waveform, and running inference.

## Tag quality is separate

Numerical parity does not establish musical usefulness. No Expert rule may
treat an MSD tag as a verified fact. A held-out, provenance-recorded track set
with expected tag behavior and per-tag evaluation is required before making
tag-quality claims or authoring authoritative Expert rules. The provenance
record hard-codes numerical-equivalence, preprocessing-parity, and tag-quality
verification flags to false; those flags cannot be promoted by inference.
