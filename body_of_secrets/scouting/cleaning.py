"""Evidence-preserving OCR cleanup with a corpus-adapted EM candidate ranker.

The EM stage ranks observed token variants; it never invents a correction outside
the corpus vocabulary and never rewrites raw inputs. Conservative defaults send
ambiguous proposals to review rather than silently changing historical text.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

_TOKEN_RE = re.compile(r"[^\W_]+(?:['’][^\W_]+)?", re.UNICODE)
_CONFUSIONS = (
    # Direction is OCR-observation -> likely printed form; do not reverse it.
    ("rn", "m"), ("cl", "d"), ("vv", "w"), ("0", "o"),
    ("1", "l"), ("5", "s"), ("8", "b"), ("ﬁ", "fi"), ("ﬂ", "fl"),
)
_SPACE_RE = re.compile(r"[ \t\f\v]+")


@dataclass(frozen=True)
class CorrectionProposal:
    observed: str
    candidate: str
    posterior: float
    margin: float
    action: str
    reason: str


@dataclass(frozen=True)
class CleanResult:
    source: str
    output: str
    raw_sha256: str
    cleaned_sha256: str
    edits: tuple[dict[str, object], ...]
    proposals: tuple[CorrectionProposal, ...]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_layout(text: str) -> str:
    """Apply reversible, content-neutral Unicode and whitespace cleanup only."""
    text = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    text = text.replace("\x00", "")
    text = "".join(
        ch for ch in text
        if ch in "\n\t" or unicodedata.category(ch) not in {"Cc", "Cf"}
    )
    lines = [_SPACE_RE.sub(" ", line).rstrip() for line in text.split("\n")]
    # Collapse runs of blank lines but preserve paragraph boundaries.
    output: list[str] = []
    blank = False
    for line in lines:
        if not line.strip():
            if output and not blank:
                output.append("")
            blank = True
        else:
            output.append(line)
            blank = False
    return "\n".join(output).strip() + ("\n" if text.endswith("\n") else "")


def _token_candidates(token: str, vocabulary: set[str]) -> set[str]:
    lower = token.casefold()
    candidates: set[str] = set()
    for source, target in _CONFUSIONS:
        start = 0
        while True:
            index = lower.find(source, start)
            if index < 0:
                break
            candidate = lower[:index] + target + lower[index + len(source):]
            if candidate in vocabulary and candidate != lower:
                candidates.add(candidate)
            start = index + 1
    return candidates


class EMOCRRanker:
    """Corpus-local noisy-channel EM ranker over observed vocabulary.

    This is unsupervised adaptation, not a pretrained model. The seeded
    confusion channel is deliberately small and all output remains auditable.
    """

    def __init__(self, *, iterations: int = 12, smoothing: float = 0.1):
        if iterations < 1 or iterations > 100:
            raise ValueError("iterations must be between 1 and 100")
        if smoothing <= 0:
            raise ValueError("smoothing must be positive")
        self.iterations = iterations
        self.smoothing = smoothing
        self.priors: dict[str, float] = {}
        self.channel: dict[tuple[str, str], float] = {}

    def fit(self, texts: Iterable[str]) -> "EMOCRRanker":
        counts: Counter[str] = Counter()
        for text in texts:
            counts.update(token.casefold() for token in _TOKEN_RE.findall(text))
        total = sum(counts.values())
        if not total:
            self.priors = {}
            self.channel = {}
            return self

        vocab = set(counts)
        priors = {word: (count + self.smoothing) /
                  (total + self.smoothing * len(vocab))
                  for word, count in counts.items()}
        observations: dict[str, list[str]] = {}
        for observed in vocab:
            candidates = sorted(_token_candidates(observed, vocab))
            if candidates:
                observations[observed] = candidates

        # Initialize a directional OCR-observation channel. EM re-estimates latent
        # source frequencies and per-observation correction probabilities.
        channel = {(obs, cand): 1.0 / len(cands)
                   for obs, cands in observations.items() for cand in cands}
        for _ in range(self.iterations):
            expected_true: Counter[str] = Counter(counts)
            expected_channel: Counter[tuple[str, str]] = Counter()
            for observed, candidates in observations.items():
                mass = float(counts[observed])
                weights = {
                    cand: max(channel[(observed, cand)], 1e-12) * priors[cand]
                    for cand in candidates
                }
                denom = sum(weights.values())
                if denom <= 0:
                    continue
                for candidate, weight in weights.items():
                    responsibility = mass * weight / denom
                    expected_true[observed] -= responsibility
                    expected_true[candidate] += responsibility
                    expected_channel[(observed, candidate)] += responsibility
            expected_total = sum(expected_true.values())
            priors = {
                word: (expected_true[word] + self.smoothing) /
                (expected_total + self.smoothing * len(vocab))
                for word in vocab
            }
            for observed, candidates in observations.items():
                denom = sum(expected_channel[(observed, c)] for c in candidates)
                for candidate in candidates:
                    channel[(observed, candidate)] = (
                        expected_channel[(observed, candidate)] + self.smoothing
                    ) / (denom + self.smoothing * len(candidates))

        self.priors = priors
        self.channel = channel
        return self

    def propose(self, text: str, *, accept_posterior: float = 0.995,
                accept_margin: float = 0.20) -> list[CorrectionProposal]:
        if not 0.5 < accept_posterior <= 1.0:
            raise ValueError("accept_posterior must be in (0.5, 1]")
        if not 0 < accept_margin < 1:
            raise ValueError("accept_margin must be in (0, 1)")
        vocabulary = set(self.priors)
        proposals: list[CorrectionProposal] = []
        seen: set[str] = set()
        for token in _TOKEN_RE.findall(text):
            observed = token.casefold()
            if observed in seen:
                continue
            seen.add(observed)
            candidates = {
                candidate for candidate in _token_candidates(observed, vocabulary)
                if self.priors.get(candidate, 0.0) >= 3.0 * self.priors.get(observed, 0.0)
            }
            if not candidates:
                continue
            # Do not auto-correct capitalized tokens: likely names, headings,
            # and sentence-initial words need review.
            weights = {
                candidate: self.channel.get((observed, candidate), 1e-12)
                * self.priors.get(candidate, 0.0)
                for candidate in candidates
            }
            denom = sum(weights.values())
            if denom <= 0:
                continue
            ranked = sorted(
                ((candidate, weight / denom) for candidate, weight in weights.items()),
                key=lambda item: item[1], reverse=True,
            )
            best, posterior = ranked[0]
            second = ranked[1][1] if len(ranked) > 1 else 0.0
            margin = posterior - second
            auto = token == token.lower() and posterior >= accept_posterior and margin >= accept_margin
            proposals.append(CorrectionProposal(
                observed=token, candidate=best, posterior=round(posterior, 6),
                margin=round(margin, 6),
                action="AUTO_ACCEPT" if auto else "REVIEW",
                reason=("EM posterior and margin exceed conservative thresholds"
                        if auto else "uncertain or protected token; human review required"),
            ))
        return proposals


def clean_directory(source_dir: str | Path, destination_dir: str | Path, *,
                    review_dir: str | Path | None = None,
                    iterations: int = 12,
                    max_file_bytes: int = 25 * 1024 * 1024) -> list[CleanResult]:
    """Fit one corpus-local EM profile, then clean supported text files to a new tree."""
    raw_source = Path(source_dir)
    if raw_source.is_symlink():
        raise ValueError("source_dir must not be a symlink")
    source = raw_source.resolve()
    destination = Path(destination_dir).resolve()
    if not source.is_dir():
        raise ValueError("source_dir must be a regular directory")
    if destination == source or source in destination.parents:
        raise ValueError("destination_dir must not be inside source_dir")
    if destination.exists():
        raise FileExistsError(destination)
    review_root = None
    if review_dir is not None:
        raw_review = Path(review_dir)
        if raw_review.is_symlink():
            raise ValueError("review_dir must not be a symlink")
        review_root = raw_review.resolve()
        if review_root == source or source in review_root.parents:
            raise ValueError("review_dir must not be inside source_dir")
        if (review_root == destination or review_root in destination.parents
                or destination in review_root.parents):
            raise ValueError("review_dir and output_dir must be separate trees")
        if review_root.exists():
            raise FileExistsError(review_root)
    files = sorted(
        path for path in source.rglob("*")
        if path.is_file() and not path.is_symlink()
        and path.suffix.lower() in {".txt", ".md", ".rst", ".text"}
    )
    if max_file_bytes < 1:
        raise ValueError("max_file_bytes must be positive")
    oversized = [path for path in files if path.stat().st_size > max_file_bytes]
    if oversized:
        raise ValueError(f"input exceeds max_file_bytes: {oversized[0]}")
    ranker = EMOCRRanker(iterations=iterations).fit(
        path.read_text(encoding="utf-8", errors="strict") for path in files
    )
    # Preflight all output paths before writing any files.
    planned_outputs = [destination / path.relative_to(source) for path in files]
    if any(path.exists() for path in planned_outputs):
        raise FileExistsError("one or more cleaned output files already exist")
    manifest_path = destination / "cleaning_manifest.json"
    if manifest_path.exists() or manifest_path in planned_outputs:
        raise FileExistsError(manifest_path)

    results: list[CleanResult] = []
    for path in files:
        relative = path.relative_to(source)
        output = destination / relative
        review = review_root / (str(relative) + ".review.jsonl") if review_root else None
        results.append(clean_file(path, output, ranker=ranker, review_path=review))
    manifest = {
        "schema_version": 1,
        "method": "corpus-local EM noisy-channel ranking plus conservative Unicode/layout normalization",
        "model_training": "unsupervised corpus-local profile; not a pretrained model",
        "source_root": str(source),
        "files": [
            {
                "source": item.source, "output": item.output,
                "raw_sha256": item.raw_sha256, "cleaned_sha256": item.cleaned_sha256,
                "accepted_corrections": sum(1 for edit in item.edits
                                            if edit.get("kind") == "em_ocr_correction"),
                "review_proposals": sum(1 for proposal in item.proposals
                                        if proposal.action == "REVIEW"),
            }
            for item in results
        ],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, ensure_ascii=False)
        stream.write("\\n")
    return results


def clean_file(source: str | Path, destination: str | Path, *,
               ranker: EMOCRRanker | None = None,
               review_path: str | Path | None = None) -> CleanResult:
    """Clean one UTF-8 text file into a new path; refuse overwrite and preserve raw."""
    src, dst = Path(source), Path(destination)
    if not src.is_file() or src.is_symlink():
        raise ValueError("source must be a regular, non-symlink file")
    review = Path(review_path) if review_path is not None else None
    if dst.exists():
        raise FileExistsError(dst)
    if review is not None and review.exists():
        raise FileExistsError(review)
    raw_bytes = src.read_bytes()
    raw_text = raw_bytes.decode("utf-8", errors="strict")
    cleaned = normalize_layout(raw_text)
    edits: list[dict[str, object]] = []
    if cleaned != raw_text:
        edits.append({
            "kind": "layout_normalization",
            "before_sha256": _sha256(raw_text.encode("utf-8")),
            "after_sha256": _sha256(cleaned.encode("utf-8")),
            "reason": "NFC, control-character removal, whitespace normalization",
        })
    proposals = tuple(ranker.propose(cleaned)) if ranker else ()
    # Apply only explicitly high-confidence lowercase proposals. Each accepted
    # token is recorded; REVIEW proposals remain untouched in the text.
    accepted = {p.observed: p.candidate for p in proposals if p.action == "AUTO_ACCEPT"}
    if accepted:
        def replace_token(match: re.Match[str]) -> str:
            original = match.group(0)
            replacement = accepted.get(original.casefold())
            if original != original.lower():
                return original
            return replacement if replacement is not None else original
        corrected = _TOKEN_RE.sub(replace_token, cleaned)
        for observed, candidate in accepted.items():
            edits.append({"kind": "em_ocr_correction", "before": observed,
                          "after": candidate, "reason": "high-confidence EM proposal"})
        cleaned = corrected
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(cleaned, encoding="utf-8", newline="")
    if review is not None:
        review.parent.mkdir(parents=True, exist_ok=True)
        review.write_text(
            "".join(json.dumps(asdict(p), ensure_ascii=False) + "\n" for p in proposals),
            encoding="utf-8",
        )
    return CleanResult(
        source=str(src), output=str(dst), raw_sha256=_sha256(raw_bytes),
        cleaned_sha256=_sha256(cleaned.encode("utf-8")),
        edits=tuple(edits), proposals=proposals,
    )
