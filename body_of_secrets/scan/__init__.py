"""Document-ingest security primitives.

Scanning is not enabled by this package yet. The current release only defines
the immutable provenance record used by the forthcoming ingest gate.
"""

from .models import ScanRecord

__all__ = ["ScanRecord"]
