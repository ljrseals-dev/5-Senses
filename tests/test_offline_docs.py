from body_of_secrets.archive import Archive
from body_of_secrets.offline_docs import ingest_directory, search_archive

def test_ingest_is_idempotent_and_searchable(tmp_path):
    corpus=tmp_path/"corpus"; corpus.mkdir()
    (corpus/"one.md").write_text("# Stellar navigation\n\nA sextant measures angles.",encoding="utf-8")
    with Archive(tmp_path/"archive.db") as archive:
        first=ingest_directory(archive,corpus,"fixture")
        second=ingest_directory(archive,corpus,"fixture")
        assert first["imported"]==1 and second["imported"]==1
        assert archive.count()==1
        results=search_archive(archive,"sextant navigation")
        assert results and results[0]["source"]=="fixture/one.md"
        assert results[0]["metadata"]["sha256"]

def test_ingest_enforces_size_and_extension(tmp_path):
    corpus=tmp_path/"corpus"; corpus.mkdir()
    (corpus/"ok.txt").write_text("small searchable document content",encoding="utf-8")
    (corpus/"large.txt").write_text("x"*100,encoding="utf-8")
    (corpus/"ignored.pdf").write_bytes(b"%PDF")
    with Archive(tmp_path/"archive.db") as archive:
        result=ingest_directory(archive,corpus,max_file_bytes=50)
        assert result["imported"]==1 and archive.count()==1
