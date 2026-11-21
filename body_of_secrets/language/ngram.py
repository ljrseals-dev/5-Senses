"""Simple n-gram statistical language model (classical component)."""

from __future__ import annotations

import math
import random
import re
from collections import defaultdict
from pathlib import Path

_TOKEN_RE = re.compile(r"[a-z0-9']+", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


class NGramModel:
    """Character-, word-, or exact-token n-gram model with Laplace smoothing."""

    def __init__(self, n: int = 3, level: str = "word"):
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise ValueError("n must be a positive integer")
        if level not in ("word", "char", "token"):
            raise ValueError("level must be 'word', 'char', or 'token'")
        self.n = n
        self.level = level
        self.counts: dict[tuple[str, ...], dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.context_totals: dict[tuple[str, ...], int] = defaultdict(int)
        self.vocab: set[str] = set()
        self._trained = False

    def _tokens(self, text: str) -> list[str]:
        if self.level == "char":
            return list(text.lower())
        if self.level == "token":
            return text.split()
        return tokenize(text)

    def train(self, texts: list[str]) -> None:
        for text in texts:
            tokens = self._tokens(text)
            if len(tokens) < self.n:
                continue
            for i in range(len(tokens) - self.n + 1):
                context = tuple(tokens[i : i + self.n - 1])
                target = tokens[i + self.n - 1]
                self.counts[context][target] += 1
                self.context_totals[context] += 1
                self.vocab.add(target)
            # also collect unigram vocab
            for t in tokens:
                self.vocab.add(t)
        self._trained = True

    def train_file(self, path: str | Path) -> None:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        self.train([text])

    def probability(self, context: tuple[str, ...], token: str) -> float:
        """Laplace-smoothed probability P(token | context)."""
        V = max(len(self.vocab), 1)
        count = self.counts[context].get(token, 0)
        total = self.context_totals[context]
        return (count + 1) / (total + V)

    def log_probability(self, tokens: list[str]) -> float:
        if len(tokens) < self.n:
            return 0.0
        logp = 0.0
        for i in range(len(tokens) - self.n + 1):
            context = tuple(tokens[i : i + self.n - 1])
            target = tokens[i + self.n - 1]
            p = self.probability(context, target)
            logp += math.log(p)
        return logp

    def perplexity(self, text: str) -> float:
        tokens = self._tokens(text)
        if len(tokens) < self.n:
            return float("inf")
        logp = self.log_probability(tokens)
        N = len(tokens) - self.n + 1
        return math.exp(-logp / N)

    def generate(self, length: int = 50, seed: str | None = None) -> str:
        if not isinstance(length, int) or isinstance(length, bool) or length < 0:
            raise ValueError("length must be a non-negative integer")
        if not self._trained or not self.vocab:
            return ""

        # Start from a random observed context or the provided seed
        if seed:
            tokens = self._tokens(seed)
            if self.n == 1:
                context = ()
            elif len(tokens) >= self.n - 1:
                context = tuple(tokens[-(self.n - 1) :])
            else:
                context = tuple(tokens) + ("",) * (self.n - 1 - len(tokens))
                context = context[-(self.n - 1) :]
        else:
            context = random.choice(list(self.counts.keys()))

        output = list(context)
        for _ in range(length):
            candidates = self.counts.get(context)
            if not candidates:
                # Fall back to random vocab token
                next_tok = random.choice(list(self.vocab))
            else:
                # Sample proportional to counts (with a little smoothing)
                items = list(candidates.items())
                weights = [c + 0.1 for _, c in items]
                next_tok = random.choices([t for t, _ in items], weights=weights, k=1)[0]
            output.append(next_tok)
            context = () if self.n == 1 else tuple(output[-(self.n - 1) :])

        if self.level == "char":
            return "".join(output)
        return " ".join(output)

    def most_likely_continuations(self, prefix: str, k: int = 5) -> list[tuple[str, float]]:
        if not isinstance(k, int) or isinstance(k, bool) or k < 0:
            raise ValueError("k must be a non-negative integer")
        tokens = self._tokens(prefix)
        if self.n == 1:
            context = ()
        elif len(tokens) < self.n - 1:
            context = tuple(tokens)
        else:
            context = tuple(tokens[-(self.n - 1) :])

        candidates = self.counts.get(context, {})
        if not candidates:
            return []
        scored = [(tok, self.probability(context, tok)) for tok in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]
