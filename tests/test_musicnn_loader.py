"""Tests for the optional MSD MusicNN loader."""
from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from body_of_secrets.sensory.musicnn_msd import MusicnnMSD, load_msd_musicnn  # noqa: E402


def make_checkpoint(path):
    state = MusicnnMSD().state_dict()
    for name, tensor in list(state.items()):
        if name.endswith(("running_mean", "running_var")):
            state[name] = tensor.float()
        elif name.endswith("num_batches_tracked"):
            state[name] = tensor.to(torch.int64)
        elif tensor.is_floating_point():
            state[name] = tensor.half()
    torch.save(state, path)


def assert_batch_norm_fp32(model):
    modules = [
        m for m in model.modules()
        if isinstance(m, (torch.nn.BatchNorm1d, torch.nn.BatchNorm2d))
    ]
    assert modules
    for module in modules:
        assert module.running_mean.dtype == torch.float32
        assert module.running_var.dtype == torch.float32
        assert module.weight.dtype == torch.float32
        assert module.bias.dtype == torch.float32
        assert module.num_batches_tracked.dtype == torch.int64


def test_fp32_loader_preserves_batch_norm_checkpoint_state(tmp_path):
    checkpoint = tmp_path / "synthetic.pt"
    make_checkpoint(checkpoint)
    model = load_msd_musicnn(checkpoint)
    assert_batch_norm_fp32(model)


def test_half_loader_keeps_batch_norm_fp32_and_is_deterministic(tmp_path):
    checkpoint = tmp_path / "synthetic.pt"
    make_checkpoint(checkpoint)
    model = load_msd_musicnn(checkpoint, half=True)
    assert_batch_norm_fp32(model)

    sample = torch.zeros((1, 187, 96), dtype=torch.float16)
    with torch.inference_mode():
        first = model(sample)
        second = model(sample)
    assert first.shape == (1, 50)
    assert first.dtype == torch.float16
    assert torch.equal(first, second)


def test_loader_requires_state_dict(tmp_path):
    checkpoint = tmp_path / "invalid.pt"
    torch.save(["not", "a state dict"], checkpoint)
    with pytest.raises(TypeError, match="state-dict"):
        load_msd_musicnn(checkpoint)


def test_loader_requires_existing_checkpoint(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_msd_musicnn(tmp_path / "missing.pt")


def test_model_rejects_wrong_mel_dimension():
    with pytest.raises(ValueError, match="96"):
        MusicnnMSD()(torch.zeros((1, 187, 80)))
