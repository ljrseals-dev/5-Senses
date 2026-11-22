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
    """Immutable record of a scan decision for one exact document byte stream.

    sig_age_hours and engine/signature versions may be None when the scanner
    could not provide trustworthy metadata. Such a record must not be
    interpreted as clean; callers should use verdict="degraded".
    """

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
        if not re.fullmatch(r"[0-9a-fA-F]{64}", self.sha256):
            raise ValueError("sha256 must be exactly 64 hexadecimal characters")
        if not self.scanner.strip():
            raise ValueError("scanner must not be empty")
        if self.verdict not in ("clean", "malware", "degraded"):
            raise ValueError("verdict must be clean, malware, or degraded")
        if self.sig_age_hours is not None and (
            not math.isfinite(self.sig_age_hours) or self.sig_age_hours < 0
        ):
            raise ValueError("sig_age_hours must be finite and non-negative")
        if not self.magic_type.strip():
            raise ValueError("magic_type must not be empty")
        if not self.scanned_at.strip():
            raise ValueError("scanned_at must be an ISO-8601 timestamp")
        try:
            datetime.fromisoformat(self.scanned_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("scanned_at must be an ISO-8601 timestamp") from exc
