#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
ZIP="$ROOT/vendor/refactored-spoon/refactored-spoon-audited.zip"
PATCH="$ROOT/vendor/refactored-spoon/0001-Audit-fixes-safe-FTS-search-idempotent-indexing-hone.patch"

# Pin Git's canonical blob IDs. This detects accidental replacement or corruption
# without relying on a network checksum service or downloading the archive again.
EXPECTED_ZIP_BLOB="995a41f01af8e27d5c4da8a71c0a9d4eb9941ddb"
EXPECTED_PATCH_BLOB="d9a4a8e452a093ddf8017e99fca0ff5b62f3ad12"

for file in "$ZIP" "$PATCH"; do
  test -s "$file" || { echo "Missing or empty artifact: $file" >&2; exit 1; }
done

actual_zip_blob="$(git hash-object "$ZIP")"
actual_patch_blob="$(git hash-object "$PATCH")"
test "$actual_zip_blob" = "$EXPECTED_ZIP_BLOB" || {
  echo "Audited ZIP Git-blob hash mismatch: $actual_zip_blob" >&2; exit 1;
}
test "$actual_patch_blob" = "$EXPECTED_PATCH_BLOB" || {
  echo "Audit patch Git-blob hash mismatch: $actual_patch_blob" >&2; exit 1;
}

command -v unzip >/dev/null || { echo "unzip is required" >&2; exit 1; }
unzip -t "$ZIP" >/dev/null

# Parse the patch and require the audited fix areas to remain represented.
git apply --numstat "$PATCH" >/dev/null
grep -q 'safe FTS search' "$PATCH"
grep -q 'idempotent indexing' "$PATCH"
grep -q 'escaped HTML' "$PATCH"

echo "Audited offline-doc-mcp ZIP and patch integrity checks passed."
