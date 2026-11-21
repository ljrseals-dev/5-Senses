"""Pinned MusicNN log-mel frontend.

The parameters mirror the public MusicNN PyTorch port's explicit settings and
its documented defaults. Resampling is pinned to soxr_hq for reproducibility.
This frontend is not yet declared numerically equivalent to the original
training pipeline; see docs/EARS_MSD_CHECKPOINT.md.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf


@dataclass(frozen=True)
class MusicNNPreprocessConfig:
    sample_rate: int = 16000
    n_fft: int = 512
    hop_length: int = 256
    win_length: int = 512
    window: str = "hann"
    center: bool = True
    pad_mode: str = "constant"
    n_mels: int = 96
    fmin: float = 0.0
    fmax: float = 8000.0
    htk: bool = False
    mel_norm: str = "slaney"
    power: float = 2.0
    log_multiplier: float = 10000.0
    log_offset: float = 1.0
    resample_type: str = "soxr_hq"
    patch_seconds: float = 3.0

    def __post_init__(self) -> None:
        if self.sample_rate <= 0 or self.n_fft <= 0 or self.hop_length <= 0:
            raise ValueError("sample_rate, n_fft, and hop_length must be positive")
        if self.win_length <= 0 or self.win_length > self.n_fft:
            raise ValueError("win_length must be in [1, n_fft]")
        if self.n_mels != 96:
            raise ValueError("MSD MusicNN requires exactly 96 mel bins")
        if not 0 <= self.fmin < self.fmax <= self.sample_rate / 2:
            raise ValueError("mel frequency bounds must fit within Nyquist")
        if self.power <= 0 or self.log_multiplier <= 0 or self.log_offset <= 0:
            raise ValueError("power and log-compression constants must be positive")
        if self.patch_seconds <= 0:
            raise ValueError("patch_seconds must be positive")


DEFAULT_PREPROCESS_CONFIG = MusicNNPreprocessConfig()


def preprocessing_record(
    config: MusicNNPreprocessConfig = DEFAULT_PREPROCESS_CONFIG,
) -> dict[str, object]:
    """Return JSON-serializable, fully resolved frontend parameters."""
    return asdict(config)


def waveform_to_logmel(
    waveform: np.ndarray,
    source_sample_rate: int,
    config: MusicNNPreprocessConfig = DEFAULT_PREPROCESS_CONFIG,
) -> np.ndarray:
    """Convert mono/stereo floating PCM to time-major float32 log-mel frames."""
    if isinstance(source_sample_rate, bool) or not isinstance(source_sample_rate, int):
        raise TypeError("source_sample_rate must be an integer")
    if source_sample_rate <= 0:
        raise ValueError("source_sample_rate must be positive")

    audio = np.asarray(waveform)
    if audio.ndim not in (1, 2):
        raise ValueError("waveform must be mono or samples-by-channels")
    if audio.size == 0 or audio.shape[0] == 0:
        raise ValueError("audio waveform is empty")
    if not np.issubdtype(audio.dtype, np.floating):
        raise TypeError("waveform must contain floating-point PCM samples")

    audio = audio.astype(np.float64, copy=False)
    if audio.ndim == 2:
        if audio.shape[1] == 0:
            raise ValueError("audio has no channels")
        audio = np.mean(audio, axis=1)
    if not np.isfinite(audio).all():
        raise ValueError("waveform contains NaN or infinite samples")

    if source_sample_rate != config.sample_rate:
        audio = librosa.resample(
            audio,
            orig_sr=source_sample_rate,
            target_sr=config.sample_rate,
            res_type=config.resample_type,
        )

    mel = librosa.feature.melspectrogram(
        y=audio,
        sr=config.sample_rate,
        n_fft=config.n_fft,
        hop_length=config.hop_length,
        win_length=config.win_length,
        window=config.window,
        center=config.center,
        pad_mode=config.pad_mode,
        power=config.power,
        n_mels=config.n_mels,
        fmin=config.fmin,
        fmax=config.fmax,
        htk=config.htk,
        norm=config.mel_norm,
        dtype=np.float32,
    )
    logmel = np.log10(config.log_multiplier * mel + config.log_offset)
    result = np.asarray(logmel.T, dtype=np.float32)
    if result.ndim != 2 or result.shape[1] != config.n_mels:
        raise RuntimeError("frontend produced an invalid mel feature shape")
    if not np.isfinite(result).all():
        raise ValueError("log-mel frontend produced non-finite values")
    return result


def make_patches(
    logmel: np.ndarray,
    *,
    overlap_seconds: float | None = None,
    config: MusicNNPreprocessConfig = DEFAULT_PREPROCESS_CONFIG,
) -> np.ndarray:
    """Tile log-mel frames into the reference port's fixed-length patches."""
    features = np.asarray(logmel, dtype=np.float32)
    if features.ndim != 2 or features.shape[1] != config.n_mels:
        raise ValueError("logmel must have shape (frames, 96)")
    if features.shape[0] == 0:
        raise ValueError("logmel contains no frames")

    frames = (
        librosa.time_to_frames(
            config.patch_seconds,
            sr=config.sample_rate,
            n_fft=config.n_fft,
            hop_length=config.hop_length,
        )
        + 1
    )
    if overlap_seconds is None:
        overlap_frames = frames
    else:
        if overlap_seconds <= 0:
            raise ValueError("overlap_seconds must be positive")
        overlap_frames = librosa.time_to_frames(
            overlap_seconds,
            sr=config.sample_rate,
            n_fft=config.n_fft,
            hop_length=config.hop_length,
        )
        if overlap_frames <= 0:
            raise ValueError("overlap_seconds is shorter than one hop")

    last_frame = features.shape[0] - frames + 1
    if last_frame <= 0:
        patch = np.zeros((frames, config.n_mels), dtype=np.float32)
        patch[: features.shape[0]] = features
        return patch[np.newaxis, ...]

    return np.stack(
        [
            features[start : start + frames]
            for start in range(0, last_frame, overlap_frames)
        ]
    ).astype(np.float32, copy=False)


def audio_file_to_patches(
    path: str | Path,
    *,
    overlap_seconds: float | None = None,
    config: MusicNNPreprocessConfig = DEFAULT_PREPROCESS_CONFIG,
) -> tuple[np.ndarray, np.ndarray]:
    """Decode a local audio file and return (patches, complete_logmel)."""
    audio, sample_rate = sf.read(Path(path), dtype="float64", always_2d=False)
    logmel = waveform_to_logmel(audio, int(sample_rate), config)
    return make_patches(logmel, overlap_seconds=overlap_seconds, config=config), logmel
