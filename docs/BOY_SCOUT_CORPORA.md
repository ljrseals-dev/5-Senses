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
