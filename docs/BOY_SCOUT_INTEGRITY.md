# Verification and compact storage

Integrity is recorded before and after any transfer or transformation. Build a
manifest with SHA-256 and byte size, store it beside (not inside) the source collection,
then verify after copying or downloading. A mismatch is a hold condition, not a cue
to silently replace the source.

The integrity module provides build_manifest, write_manifest, verify_manifest, and
compress_zstd. Zstandard is optional (pip install zstandard). Compression creates a
separate output and refuses to overwrite either source or existing destination. Keep
the original archive and its checksum; compression is not deduplication and does not
establish licensing or completeness.

Manifest paths are constrained to the declared root. Treat manifests received from
outside as untrusted input and review every verification result.
