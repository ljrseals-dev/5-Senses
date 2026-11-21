"""Optional MSD MusicNN sensory model.

This auxiliary feature extractor does not replace the classical 5-Senses
subsystems. Numerical equivalence to upstream musicnn remains unverified.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "MSD MusicNN requires the optional extra: pip install body-of-secrets[musicnn]"
    ) from exc

N_MELS = 96
N_TAGS = 50
BN_KW = {"eps": 0.001, "momentum": 0.01}


class ConvReLUBN(nn.Module):
    def __init__(self, out_ch: int, kernel: tuple[int, int]) -> None:
        super().__init__()
        self.conv = nn.Conv2d(1, out_ch, kernel)
        self.bn = nn.BatchNorm2d(out_ch, **BN_KW)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.bn(F.relu(self.conv(x)))


class _Wrap(nn.Module):
    def __init__(self, out_ch: int, kernel: tuple[int, int]) -> None:
        super().__init__()
        self.conv = ConvReLUBN(out_ch, kernel)


class TimbralBlock(_Wrap):
    def __init__(self, mel_bins: int, out_ch: int) -> None:
        super().__init__(out_ch, (7, mel_bins))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(F.pad(x, (0, 0, 3, 3))).max(dim=3).values


class TemporalBlock(_Wrap):
    def __init__(self, kernel_size: int, out_ch: int) -> None:
        super().__init__(out_ch, (kernel_size, 1))
        self.kernel_size = kernel_size

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        total = self.kernel_size - 1
        x = F.pad(x, (0, 0, total // 2, total - total // 2))
        return self.conv(x).max(dim=3).values


class MidEnd(nn.Module):
    def __init__(self, in_ch: int = 561, filters: int = 64) -> None:
        super().__init__()
        for i, width in ((1, in_ch), (2, filters), (3, filters)):
            setattr(self, f"c{i}_conv", nn.Conv2d(1, filters, (7, width)))
            setattr(self, f"c{i}_bn", nn.BatchNorm2d(filters, **BN_KW))

    @staticmethod
    def _step(x: torch.Tensor, conv: nn.Conv2d, bn: nn.BatchNorm2d) -> torch.Tensor:
        x = F.pad(x.unsqueeze(1), (0, 0, 3, 3))
        return bn(F.relu(conv(x))).squeeze(3).transpose(1, 2)

    def forward(self, front: torch.Tensor) -> torch.Tensor:
        x1 = self._step(front, self.c1_conv, self.c1_bn)
        res2 = self._step(x1, self.c2_conv, self.c2_bn) + x1
        res3 = self._step(res2, self.c3_conv, self.c3_bn) + res2
        return torch.cat([front, x1, res2, res3], dim=2)


class Backend(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.bn_in = nn.BatchNorm1d(1506, **BN_KW)
        self.fc1 = nn.Linear(1506, 200)
        self.bn_fc1 = nn.BatchNorm1d(200, **BN_KW)
        self.fc2 = nn.Linear(200, N_TAGS)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        mx, mean = x.max(dim=1).values, x.mean(dim=1)
        x = torch.stack([mx, mean], dim=2).flatten(1)
        x = self.bn_in(x)
        x = self.bn_fc1(F.relu(self.fc1(x)))
        return self.fc2(x)


class MusicnnMSD(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.bn_input = nn.BatchNorm2d(1, **BN_KW)
        self.timbral_1 = TimbralBlock(38, 204)
        self.timbral_2 = TimbralBlock(67, 204)
        self.temp_1 = TemporalBlock(128, 51)
        self.temp_2 = TemporalBlock(64, 51)
        self.temp_3 = TemporalBlock(32, 51)
        self.midend = MidEnd()
        self.backend = Backend()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim != 3 or x.shape[1] < 1 or x.shape[2] != N_MELS:
            raise ValueError("expected non-empty input shaped (batch, frames, 96)")
        if not x.is_floating_point():
            raise TypeError("log-mel input must be floating point")
        x = self.bn_input(x.unsqueeze(1))
        branches = [
            self.timbral_1(x), self.timbral_2(x), self.temp_1(x),
            self.temp_2(x), self.temp_3(x),
        ]
        front = torch.cat(branches, dim=1).transpose(1, 2)
        return self.backend(self.midend(front))


def load_msd_musicnn(
    checkpoint: str | Path, *, half: bool = False,
    device: str | torch.device = "cpu",
) -> MusicnnMSD:
    """Load a local state dict; no network access is performed."""
    if not isinstance(half, bool):
        raise TypeError("half must be bool")
    path = Path(checkpoint)
    if not path.is_file():
        raise FileNotFoundError(path)
    try:
        state: Any = torch.load(path, map_location="cpu", weights_only=True)
    except TypeError as exc:
        raise RuntimeError("PyTorch with weights_only=True support is required") from exc
    if not isinstance(state, Mapping):
        raise TypeError("checkpoint must contain a state-dict mapping")

    model = MusicnnMSD()
    model.load_state_dict(state, strict=True)
    if half:
        model.half()
        for module in model.modules():
            if isinstance(module, (nn.BatchNorm1d, nn.BatchNorm2d)):
                module.float()
    model.eval()
    return model.to(device)
