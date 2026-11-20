# Boy Scout: corpus and historical text discovery

This scout catalogs datasets and digital-library records without silently downloading
large archives. It supports Hugging Face Datasets metadata and Internet Archive text
records. Results are discovery leads, not assertions that the material is complete,
public domain, or licensed for model training.

Search Hugging Face with search_huggingface_datasets(query) and historical Internet
Archive texts with search_internet_archive(query), both in
body_of_secrets.scouting.corpora. Combine results and write them with
write_corpus_inventory(candidates, destination). Store inventories under data/inventory
and keep acquired source material outside Git.

For each candidate, manually record the exact item/revision, creator, source URL,
license/rights statement, retrieval date, file list, expected size, and checksum.
Separate public-domain, openly licensed, research-only, unknown-rights, and restricted
material. Unknown rights must remain on hold; availability online is not permission
for redistribution or training.

Suggested search families: encyclopedias and dictionaries; classical AI and 1980s
computer science; mathematics and sciences; engineering; history and literature;
programming manuals; multilingual texts; speech/transcripts; and carefully licensed
instruction/reasoning datasets.


## Priority reference-work catalog

The first acquisition wave should favor complete historical reference works whose
specific editions can be verified as public domain or otherwise openly licensed.
These are search targets, not pre-approved downloads:

| Work | Target edition / period | Scout notes |
|---|---|---|
| Encyclopaedia Britannica | 11th edition (1911) | Seek complete volume set and OCR/text companions; verify volume coverage. |
| The Century Dictionary and Cyclopedia | 1889–1911 | Multi-volume dictionary/reference collection; track supplements separately. |
| Catholic Encyclopedia | 1907–1912 | Specialized reference work; check each host's reuse terms. |
| Jewish Encyclopedia | 1901–1906 | Specialized reference work; preserve article and volume provenance. |
| Encyclopedia Americana | Early editions | Verify the exact edition and publication history; do not assume every edition is public domain. |
| U.S. government reference works | Edition-specific | Check the issuing agency, contractor contributions, and any third-party material. |
| Wikisource | Collection-specific | Prefer proofread transcriptions and retain page/edition references. |
| Project Gutenberg | Book/volume-specific | Prefer its plain-text editions where available; preserve Gutenberg identifiers and headers. |
| Wikimedia dumps | Dated dump snapshot | Treat as a distinct modern collaborative corpus, not as a historical encyclopedia. Record the applicable license and attribution obligations. |

### Copyright and rights gate

Do not use a single year such as 1931 as an automatic legal determination. Copyright
depends on the work's jurisdiction, publication date, authorship, publication history,
renewal/formalities where applicable, later revisions, and the terms attached to the
specific digital edition. A public-domain underlying work can still be accompanied by
separately protected editorial material, images, annotations, or a database layer.

Every candidate must receive one explicit rights state before acquisition:

- `PUBLIC_DOMAIN_VERIFIED` — documented basis for the specific edition and jurisdiction.
- `OPEN_LICENSE_VERIFIED` — exact license and required attribution/share-alike terms recorded.
- `RESEARCH_ONLY` — access permitted for limited research, but reuse/training not cleared.
- `UNKNOWN_HOLD` — rights not established; do not bulk-download or ingest.
- `RESTRICTED` — do not acquire unless a separate lawful authorization exists.

Record the evidence URL, date checked, edition, rights statement, and reviewer decision.
Do not infer permission from a download button, Internet Archive availability, or a
search result. Keep copyrighted modern reference sets out of the acquisition queue
unless a lawful license or explicit authorization covers the intended use.


## Curated first-wave catalog

The initial edition-specific catalog is committed at
`data/inventory/historical_reference_works.json`. It contains seven targets:
Britannica 11th, 7th, and 9th editions; the Century Dictionary and Cyclopedia;
the Catholic Encyclopedia; the Jewish Encyclopedia; and dated Wikimedia dumps.

The catalog deliberately distinguishes:
- **Scan availability** from clean machine-readable text.
- A work's historical copyright status from a host site's HTML/database terms.
- A reported open license from an independently checked release's exact license.
- A complete print edition from verified digital volume coverage.

### Current research findings

- Britannica 11th is a 29-volume edition. Wikisource lists the scan-backed volume indexes,
  but its transcription project labels the work incomplete. Do not mark it as complete
  plain text until every volume and index has been checked.
- Machine-readable Britannica 7th and 9th edition TXT/TEI releases are reported by the
  Tu-Plogan historical Britannica project under CC BY 4.0. Pin the exact release and
  preserve attribution before reuse.
- The Century Dictionary bibliography exposes volume-level scans and OCR formats.
  The catalog records a 24-part target, but the scout still needs to enumerate every
  part and check missing/duplicate coverage.
- The Catholic Encyclopedia's first edition and later special edition/supplements are
  separate targets. New Advent's online transcription carries site-specific notices;
  do not bulk-copy that site's HTML on the assumption that the underlying 1907-1912
  print work is public domain.
- The Jewish Encyclopedia's 12-volume historical work and a modern site's complete-text
  claim do not, by themselves, establish permission to scrape that site's database.
  Prefer independently rights-reviewed scans or transcriptions.

### Catalog state

Every entry currently says `NOT_DOWNLOADED`. This is an intentional, accurate state:
the catalog is a verified research lead list, not a record of acquired files. Update
the acquisition state only after recording the actual downloaded file list, byte sizes,
SHA-256 hashes, edition/volume identifiers, retrieval date, and applicable license evidence.
