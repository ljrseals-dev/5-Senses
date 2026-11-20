"""Minimal multilayer perceptron (classical feed-forward network).

Pure-Python implementation for transparency and educational use.
Not intended for large-scale training.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


def sigmoid(x: float) -> float:
    # Stable sigmoid
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    ex = math.exp(x)
    return ex / (1.0 + ex)


def sigmoid_deriv(y: float) -> float:
    """Derivative given the *activation* y = sigmoid(x)."""
    return y * (1.0 - y)


@dataclass
class MLP:
    """Small fully-connected MLP with one hidden layer."""

    n_input: int
    n_hidden: int
    n_output: int
    learning_rate: float = 0.3
    # weights[i][j] = weight from unit j in previous layer to unit i
    w_ih: list[list[float]] = field(default_factory=list)
    w_ho: list[list[float]] = field(default_factory=list)
    bias_h: list[float] = field(default_factory=list)
    bias_o: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.w_ih:
            self.w_ih = [
                [random.uniform(-0.3, 0.3) for _ in range(self.n_input)]
                for _ in range(self.n_hidden)
            ]
        if not self.w_ho:
            self.w_ho = [
                [random.uniform(-0.3, 0.3) for _ in range(self.n_hidden)]
                for _ in range(self.n_output)
            ]
        if not self.bias_h:
            self.bias_h = [random.uniform(-0.1, 0.1) for _ in range(self.n_hidden)]
        if not self.bias_o:
            self.bias_o = [random.uniform(-0.1, 0.1) for _ in range(self.n_output)]

    def forward(self, inputs: list[float]) -> tuple[list[float], list[float]]:
        if len(inputs) != self.n_input:
            raise ValueError("Input size mismatch")
        hidden = []
        for i in range(self.n_hidden):
            z = self.bias_h[i] + sum(self.w_ih[i][j] * inputs[j] for j in range(self.n_input))
            hidden.append(sigmoid(z))
        output = []
        for i in range(self.n_output):
            z = self.bias_o[i] + sum(self.w_ho[i][j] * hidden[j] for j in range(self.n_hidden))
            output.append(sigmoid(z))
        return hidden, output

    def train_step(self, inputs: list[float], targets: list[float]) -> float:
        """One online back-prop step. Returns squared error."""
        hidden, output = self.forward(inputs)

        # Output deltas
        delta_o = []
        err = 0.0
        for i in range(self.n_output):
            e = targets[i] - output[i]
            err += e * e
            delta_o.append(e * sigmoid_deriv(output[i]))

        # Hidden deltas
        delta_h = []
        for j in range(self.n_hidden):
            e = sum(delta_o[i] * self.w_ho[i][j] for i in range(self.n_output))
            delta_h.append(e * sigmoid_deriv(hidden[j]))

        # Update output weights
        for i in range(self.n_output):
            for j in range(self.n_hidden):
                self.w_ho[i][j] += self.learning_rate * delta_o[i] * hidden[j]
            self.bias_o[i] += self.learning_rate * delta_o[i]

        # Update hidden weights
        for j in range(self.n_hidden):
            for k in range(self.n_input):
                self.w_ih[j][k] += self.learning_rate * delta_h[j] * inputs[k]
            self.bias_h[j] += self.learning_rate * delta_h[j]

        return err

    def train(self, dataset: list[tuple[list[float], list[float]]], epochs: int = 1000) -> list[float]:
        history = []
        for _ in range(epochs):
            total = 0.0
            for x, y in dataset:
                total += self.train_step(x, y)
            history.append(total / max(len(dataset), 1))
        return history

    def predict(self, inputs: list[float]) -> list[float]:
        _, output = self.forward(inputs)
        return output


def demo_xor() -> str:
    """Train a tiny MLP on XOR and report final error."""
    mlp = MLP(n_input=2, n_hidden=4, n_output=1, learning_rate=0.5)
    data = [
        ([0.0, 0.0], [0.0]),
        ([0.0, 1.0], [1.0]),
        ([1.0, 0.0], [1.0]),
        ([1.0, 1.0], [0.0]),
    ]
    history = mlp.train(data, epochs=2000)
    results = []
    for x, y in data:
        pred = mlp.predict(x)[0]
        results.append(f"{x} → {pred:.3f} (target {y[0]})")
    return (
        f"MLP XOR demo (2-4-1). Final avg SE = {history[-1]:.4f}. "
        + " | ".join(results)
    )
