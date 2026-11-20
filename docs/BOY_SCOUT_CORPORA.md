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
