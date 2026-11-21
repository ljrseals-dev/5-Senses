"""Tests for symbolic music learning."""
import json,struct
import pytest
from body_of_secrets.music.corpus import CorpusWriter
from body_of_secrets.music.encoder import encode_file
from body_of_secrets.music.hopfield import MotifMemory,project_motif
from body_of_secrets.music.ngram import MusicNGramModel
from body_of_secrets.music.snapshots import SnapshotStore
from body_of_secrets.music.tokens import validate_tokens
from body_of_secrets.music.validator import evaluate_uncertainty

def _vlq(n):
    out=[n&127]; n>>=7
    while n: out.insert(0,(n&127)|128); n>>=7
    return bytes(out)

def _midi(path):
    track=b"\x00\x90\x3c\x64"+_vlq(480)+b"\x80\x3c\x00"+b"\x00\x90\x40\x64"+_vlq(480)+b"\x80\x40\x00"+b"\x00\xff\x2f\x00"
    path.write_bytes(b"MThd"+struct.pack(">IHHH",6,0,1,480)+b"MTrk"+struct.pack(">I",len(track))+track)

def test_token_validation_and_leap():
    assert validate_tokens("P060 D004 P064 D008").valid
    assert not validate_tokens("P060 D004 P080 D004").valid
    assert "invalid_token" in validate_tokens("P60 D004 P064 D004").violations

def test_midi_encoding_is_stable(tmp_path):
    path=tmp_path/"scale.mid"; _midi(path)
    assert encode_file(path)==encode_file(path)
    assert encode_file(path).startswith("P060 D004 P064 D004")

def test_abc_encoding(tmp_path):
    path=tmp_path/"scale.abc"; path.write_text("X:1\nT:Scale\nL:1/4\nK:C\nC D E F G A B c |\n")
    encoded=encode_file(path)
    assert encoded.startswith("P060 D004 P062 D004") and "P072" in encoded

def test_ngram_case_and_snapshot_roundtrip(tmp_path):
    model=MusicNGramModel(3); model.train_lines(["P060 D004 P062 D004 P064 D004"])
    assert model.continuations("P060 D004")[0][0]=="P062"
    path=tmp_path/"model.json"; model.save(path)
    assert MusicNGramModel.load(path).to_dict()==model.to_dict()

def test_motif_projection_and_capacity():
    assert project_motif(("P060","D004"))==project_motif(("P060","D004"))
    memory=MotifMemory(2); memory.build(["P060 D004 P062 D004 P064 D004 P065 D004"]*4)
    assert len(memory.patterns)<=2 and all(len(p["vector"])==128 for p in memory.patterns)

def test_corpus_dedupe_and_manifest(tmp_path):
    writer=CorpusWriter(tmp_path/"corpus.txt")
    assert writer.append("P060 D004 P062 D004",source="test")
    assert not writer.append("P060 D004 P062 D004 # ignored",source="duplicate")
    record=json.loads((tmp_path/"provenance.jsonl").read_text().splitlines()[0])
    assert record["source"]=="test" and record["sha256"]

def test_snapshot_integrity_and_rollback(tmp_path):
    corpus=tmp_path/"corpus.txt"; corpus.write_text("P060 D004 P062 D004\n")
    model=MusicNGramModel.from_file(corpus,3); memory=MotifMemory()
    store=SnapshotStore(tmp_path/"snapshots"); version=store.commit(model,memory,corpus)
    assert version=="v001"; store.verify(version)
    corpus.write_text("P060 D004 P064 D004\n"); store.rollback(version,corpus)
    assert corpus.read_text()=="P060 D004 P062 D004\n"
    assert store.load(version)[0].to_dict()==model.to_dict()

def test_uncertainty_flags_unseen_context():
    model=MusicNGramModel(3); model.train_lines(["P060 D004 P062 D004 P064 D004"])
    verdict=evaluate_uncertainty(model,MotifMemory(),"P099 D001","P060 D004")
    assert verdict.is_uncertain and verdict.reason=="unseen_context"
