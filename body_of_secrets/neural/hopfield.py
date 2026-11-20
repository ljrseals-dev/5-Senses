"""Classical Hopfield network (associative memory).

Implements the original discrete Hopfield model (1982):
- Binary / bipolar states
- Symmetric weight matrix with zero diagonal
- Hebbian storage
- Asynchronous or synchronous update
- Energy function for monitoring convergence
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class HopfieldNetwork:
    """Discrete Hopfield associative memory."""

    n_units: int
    weights: list[list[float]] = field(default_factory=list)
    state: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.weights:
            self.weights = [[0.0] * self.n_units for _ in range(self.n_units)]
        if not self.state:
            self.state = [1] * self.n_units

    # ------------------------------------------------------------------
    # Storage (Hebbian)
    # ------------------------------------------------------------------

    def store(self, patterns: list[list[int]]) -> None:
        """Store bipolar patterns (+1 / -1) via Hebbian learning."""
        N = self.n_units
        # Reset weights
        self.weights = [[0.0] * N for _ in range(N)]
        for p in patterns:
            if len(p) != N:
                raise ValueError(f"Pattern length {len(p)} != n_units {N}")
            for i in range(N):
                for j in range(N):
                    if i != j:
                        self.weights[i][j] += p[i] * p[j]
        # Normalize by N (common practice)
        for i in range(N):
            for j in range(N):
                self.weights[i][j] /= N

    def store_binary(self, patterns: list[list[int]]) -> None:
        """Convenience: accept 0/1 patterns and convert to bipolar."""
        bipolar = [[1 if x else -1 for x in p] for p in patterns]
        self.store(bipolar)

    # ------------------------------------------------------------------
    # Dynamics
    # ------------------------------------------------------------------

    def energy(self, state: list[int] | None = None) -> float:
        s = state if state is not None else self.state
        E = 0.0
        N = self.n_units
        for i in range(N):
            for j in range(i + 1, N):
                E -= self.weights[i][j] * s[i] * s[j]
        return E

    def update_async(self, max_steps: int = 100) -> int:
        """Asynchronous random-order update until convergence or max_steps."""
        N = self.n_units
        steps = 0
        for _ in range(max_steps):
            order = list(range(N))
            random.shuffle(order)
            changed = False
            for i in order:
                h = sum(self.weights[i][j] * self.state[j] for j in range(N))
                new = 1 if h >= 0 else -1
                if new != self.state[i]:
                    self.state[i] = new
                    changed = True
                steps += 1
            if not changed:
                break
        return steps

    def update_sync(self, max_steps: int = 50) -> int:
        """Synchronous update (all units at once)."""
        steps = 0
        for _ in range(max_steps):
            new_state = []
            for i in range(self.n_units):
                h = sum(self.weights[i][j] * self.state[j] for j in range(self.n_units))
                new_state.append(1 if h >= 0 else -1)
            steps += 1
            if new_state == self.state:
                break
            self.state = new_state
        return steps

    def set_state(self, pattern: list[int]) -> None:
        if len(pattern) != self.n_units:
            raise ValueError("Pattern length mismatch")
        # Accept 0/1 or ±1
        self.state = [1 if x > 0 else -1 for x in pattern]

    def recall(self, cue: list[int], *, async_update: bool = True, max_steps: int = 100) -> list[int]:
        """Present a cue and let the network settle; return final state."""
        self.set_state(cue)
        if async_update:
            self.update_async(max_steps=max_steps)
        else:
            self.update_sync(max_steps=max_steps)
        return list(self.state)

    def overlap(self, a: list[int], b: list[int]) -> float:
        """Normalized overlap (cosine-like) between two bipolar vectors."""
        return sum(x * y for x, y in zip(a, b)) / self.n_units


def demo_hopfield() -> str:
    """Small self-contained demonstration."""
    # Three simple orthogonal-ish patterns of length 8
    patterns = [
        [1, 1, 1, 1, -1, -1, -1, -1],
        [1, -1, 1, -1, 1, -1, 1, -1],
        [1, 1, -1, -1, 1, 1, -1, -1],
    ]
    net = HopfieldNetwork(n_units=8)
    net.store(patterns)

    # Corrupt first pattern
    cue = patterns[0][:]
    cue[0] = -cue[0]
    cue[3] = -cue[3]

    recalled = net.recall(cue)
    ov = net.overlap(recalled, patterns[0])
    return (
        f"Hopfield demo: stored 3 patterns (N=8). "
        f"Cue with 2 bit flips → overlap with original = {ov:.2f}. "
        f"Energy = {net.energy():.3f}."
    )
