# Boy Scout: integrate verified knowledge into BODY OF SECRETS

The integration helper connects acquired text collections to the existing SQLite/BM25
Archive. It accepts only plain text extensions (.txt, .md, .rst, .text), imposes a
default 25 MiB per-file limit, and reports imports, already-known sources, oversized
files, and failures separately.

Use import_text_collection(directory, archive) from
body_of_secrets.scouting.integration. Pass an already-open Archive instance and close
it using its context manager or close method. The helper does not extract ZIP/TAR files,
run OCR, execute downloaded code, or ingest binary model weights.

Run integrity checks and rights review before indexing. Keep source archives intact;
the Archive is a retrieval index, not a replacement for the original source. Track
source URL, item identifier, revision, rights, and checksum in your acquisition
inventory so retrieved passages retain provenance.
