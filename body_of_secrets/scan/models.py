"""Typed provenance for a document security scan.

This module deliberately contains no scanner invocation or file-ingest logic.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


ScanVerdict = Literal["clean", "malware", "degraded"]


@dataclass(frozen=True)
class ScanRecord:
    """Immutable record of a scan decision for one exact document byte stream."""

    sha256: str
    scanner: str
    engine_version: str | None
    sig_version: str | None
    sig_age_hours: float | None
    verdict: ScanVerdict
    detail: str | None
    magic_type: str
    declared_extension: str
    scanned_at: str

    def __post_init__(self) -> None:
        if not isinstance(self.sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", self.sha256):
            raise ValueError("sha256 must be exactly 64 hexadecimal characters")
        for name, value in (
            ("scanner", self.scanner),
            ("magic_type", self.magic_type),
            ("declared_extension", self.declared_extension),
            ("scanned_at", self.scanned_at),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.engine_version is not None and not isinstance(self.engine_version, str):
            raise ValueError("engine_version must be a string or None")
        if self.sig_version is not None and not isinstance(self.sig_version, str):
            raise ValueError("sig_version must be a string or None")
        if self.detail is not None and not isinstance(self.detail, str):
            raise ValueError("detail must be a string or None")
        if self.verdict not in ("clean", "malware", "degraded"):
            raise ValueError("verdict must be clean, malware, or degraded")
        if self.sig_age_hours is not None and (
            isinstance(self.sig_age_hours, bool)
            or not isinstance(self.sig_age_hours, (int, float))
            or not math.isfinite(self.sig_age_hours)
            or self.sig_age_hours < 0
        ):
            raise ValueError("sig_age_hours must be finite and non-negative")
        try:
            timestamp = datetime.fromisoformat(self.scanned_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("scanned_at must be an ISO-8601 timestamp") from exc
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("scanned_at must include a timezone")
