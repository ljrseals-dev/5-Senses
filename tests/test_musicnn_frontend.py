"""Regression tests for the explicitly configured MusicNN frontend."""
from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("librosa")
pytest.importorskip("soundfile")

from body_of_secrets.sensory.musicnn_frontend import (  # noqa: E402
    DEFAULT_PREPROCESS_CONFIG,
    make_patches,
    preprocessing_record,
    waveform_to_logmel,
)


def test_frontend_fixed_waveform_golden_values():
    sample_rate = 16000
    time = np.arange(4096, dtype=np.float64) / sample_rate
    waveform = (
        0.2 * np.sin(2.0 * np.pi * 440.0 * time)
        + 0.05 * np.sin(2.0 * np.pi * 880.0 * time)
    )
    features = waveform_to_logmel(waveform, sample_rate)

    assert features.shape == (17, 96)
    expected = np.array(
        [2.73649883, 3.49317431, 2.63581252, 0.74135810, 0.05300273, 0.02307472],
        dtype=np.float32,
    )
    np.testing.assert_allclose(
        features[0, [0, 10, 30, 50, 80, 95]], expected, rtol=1e-5, atol=1e-6
    )


def test_frontend_is_deterministic_and_stereo_downmixes():
    time = np.arange(4096, dtype=np.float64) / 16000
    mono = 0.1 * np.sin(2.0 * np.pi * 330.0 * time)
    stereo = np.column_stack([mono, mono])
    first = waveform_to_logmel(stereo, 16000)
    second = waveform_to_logmel(mono, 16000)
    np.testing.assert_array_equal(first, second)


def test_short_clip_is_zero_padded_to_reference_patch_length():
    time = np.arange(4096, dtype=np.float64) / 16000
    waveform = 0.1 * np.sin(2.0 * np.pi * 220.0 * time)
    features = waveform_to_logmel(waveform, 16000)
    patches = make_patches(features)

    assert patches.shape == (1, 187, 96)
    np.testing.assert_array_equal(patches[0, : len(features)], features)
    assert np.count_nonzero(patches[0, len(features) :]) == 0


def test_frontend_rejects_invalid_waveforms_and_rates():
    with pytest.raises(ValueError, match="empty"):
        waveform_to_logmel(np.array([], dtype=np.float32), 16000)
    with pytest.raises(ValueError, match="positive"):
        waveform_to_logmel(np.ones(32, dtype=np.float32), 0)
    with pytest.raises(TypeError, match="floating-point"):
        waveform_to_logmel(np.ones(32, dtype=np.int16), 16000)


def test_preprocessing_contract_is_explicit():
    record = preprocessing_record()
    assert record["sample_rate"] == 16000
    assert record["n_fft"] == 512
    assert record["hop_length"] == 256
    assert record["win_length"] == 512
    assert record["window"] == "hann"
    assert record["center"] is True
    assert record["pad_mode"] == "constant"
    assert record["n_mels"] == 96
    assert record["fmin"] == 0.0
    assert record["fmax"] == 8000.0
    assert record["htk"] is False
    assert record["mel_norm"] == "slaney"
    assert record["power"] == 2.0
    assert record["resample_type"] == "soxr_hq"
    assert DEFAULT_PREPROCESS_CONFIG.patch_seconds == 3.0


def test_patch_overlap_must_produce_at_least_one_hop():
    features = np.ones((200, 96), dtype=np.float32)
    with pytest.raises(ValueError, match="shorter than one hop"):
        make_patches(features, overlap_seconds=0.001)
