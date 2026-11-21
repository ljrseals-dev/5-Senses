"""Network isolation test for the local MusicNN inference path."""
from __future__ import annotations

import socket

import numpy as np
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("librosa")
pytest.importorskip("soundfile")

from body_of_secrets.sensory.musicnn_adapters import predict_msd_tags  # noqa: E402
from body_of_secrets.sensory.musicnn_frontend import make_patches, waveform_to_logmel  # noqa: E402
from body_of_secrets.sensory.musicnn_msd import MusicnnMSD, load_msd_musicnn  # noqa: E402


def test_musicnn_frontend_loader_and_inference_need_no_network(tmp_path, monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("network socket use is forbidden in offline inference")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)

    checkpoint = tmp_path / "local-only.pt"
    torch.save(MusicnnMSD().state_dict(), checkpoint)
    model = load_msd_musicnn(checkpoint)

    time = np.arange(4096, dtype=np.float64) / 16000
    waveform = 0.1 * np.sin(2.0 * np.pi * 440.0 * time)
    logmel = waveform_to_logmel(waveform, 16000)
    patches = make_patches(logmel)
    result = predict_msd_tags(model, patches)

    assert result.patch_count == 1
    assert len(result.mean_probabilities) == 50
