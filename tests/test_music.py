"""Tests for symbolic music learning."""
import json
import struct

import pytest

from body_of_secrets.language import NGramModel
from body_of_secrets.music.corpus import CorpusWriter
from body_of_secrets.music.encoder import encode_file
from body_of_secrets.music.hopfield import MotifMemory, project_motif
from body_of_secrets.music.ngram import MusicNGramModel
from body_of_secrets.music.snapshots import SnapshotStore
from body_of_secrets.music.teacher import LoggedTeacher
from body_of_secrets.music.tokens import validate_tokens
from body_of_secrets.music.training import train_music
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
def test_chord_group_does_not_absorb_next_melody_note():
    assert validate_tokens("CHD P060 D004 CHD P067 D004 P069 D004").valid
    assert not validate_tokens("CHD P067 D004 CHD P060 D004 P069 D004").valid
def test_midi_encoder_marks_simultaneous_notes_as_a_chord(tmp_path):
    path=tmp_path/"chord.mid"
    track=bytes([0,0x90,60,100,0,0x90,67,100])+_vlq(480)+bytes([0x80,60,0,0,0x80,67,0,0,0xff,0x2f,0])
    path.write_bytes(b"MThd"+struct.pack(">IHHH",6,0,1,480)+b"MTrk"+struct.pack(">I",len(track))+track)
    assert encode_file(path)=="CHD P060 D004 CHD P067 D004"

def test_midi_running_status_preserves_event_status(tmp_path):
    path=tmp_path/"running.mid"
    track=bytes([0,0x90,60,100,0,67,100])+_vlq(480)+bytes([0x80,60,0,0,67,0,0,0xff,0x2f,0])
    path.write_bytes(b"MThd"+struct.pack(">IHHH",6,0,1,480)+b"MTrk"+struct.pack(">I",len(track))+track)
    assert encode_file(path)=="CHD P060 D004 CHD P067 D004"

def test_midi_encoding_is_stable(tmp_path):
    path=tmp_path/"scale.mid"; _midi(path)
    assert encode_file(path)==encode_file(path)
    assert encode_file(path).startswith("P060 D004 P064 D004")
def test_abc_encoding(tmp_path):
    path=tmp_path/"scale.abc"
    path.write_text("X:1\nT:Scale\nL:1/4\nK:C\nC D E F G A B c |\n")
    encoded=encode_file(path)
    assert encoded.startswith("P060 D004 P062 D004") and "P072" in encoded

def test_abc_rest_is_preserved(tmp_path):
    path=tmp_path/"rest.abc"
    path.write_text("X:1\nL:1/4\nK:C\nC z2 D |\n")
    assert encode_file(path)=="P060 D004 DRST P062 D004"

def test_abc_bracket_chord_is_grouped_polyphonically(tmp_path):
    path=tmp_path/"chord.abc"
    path.write_text("X:1\nL:1/4\nK:C\n[CEG]2 D |\n")
    assert encode_file(path)=="CHD P060 D002 CHD P064 D002 CHD P067 D002 P062 D004"

def test_existing_ngram_supports_exact_symbolic_tokens():
    model=NGramModel(n=2,level="token"); model.train(["P060 D004 P064 D004"])
    assert "P060" in model.vocab and "D004" in model.vocab

def test_existing_unigram_ngram_uses_empty_context():
    model=NGramModel(n=1,level="token"); model.train(["P060 D004 P060"])
    assert model.most_likely_continuations("P060",k=1)[0][0]=="P060"
    assert len(model.generate(length=2,seed="P060").split())==2

def test_ngram_order_one_uses_empty_context():
    model=MusicNGramModel(1); model.train_lines(["P060 D004 P060"])
    distribution=model.distribution("")
    assert distribution["P060"] > distribution["D004"]
    assert abs(sum(distribution.values())-1.0)<1e-9

def test_ngram_case_entropy_and_snapshot_roundtrip(tmp_path):
    model=MusicNGramModel(3); model.train_lines(["P060 D004 P062 D004 P064 D004"])
    assert model.continuations("P060 D004")[0][0]=="P062"
    assert model.perplexity(["P060 D004 P062 D004"]) > 0
    assert abs(sum(model.distribution("P060 D004").values())-1.)<1e-9
    path=tmp_path/"model.json"; model.save(path)
    assert MusicNGramModel.load(path).to_dict()==model.to_dict()
def test_motif_projection_and_capacity():
    assert project_motif(("P060","D004"))==project_motif(("P060","D004"))
    memory=MotifMemory(2); memory.build(["P060 D004 P062 D004 P064 D004 P065 D004"]*4)
    assert len(memory.patterns)<=2 and all(len(p["vector"])==128 for p in memory.patterns)
def test_corpus_source_idempotency_and_duplicate_sources(tmp_path):
    writer=CorpusWriter(tmp_path/"corpus.txt")
    sample="P060 D004 P062 D004"
    assert writer.append(sample,source="file:a.mid")
    assert not writer.append(sample,source="file:a.mid")
    assert writer.append(sample,source="file:b.mid")
    assert not writer.append(sample,source="llm")

def test_corpus_writer_refreshes_indexes_across_instances(tmp_path):
    path=tmp_path/"corpus.txt"; first=CorpusWriter(path); second=CorpusWriter(path)
    assert first.append("P060 D004 P062 D004",source="seed")
    assert not second.append("P060 D004 P062 D004",source="llm")

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
    manifest=tmp_path/"provenance.jsonl"; manifest.write_text('{"source":"changed"}\n')
    corpus.write_text("P060 D004 P064 D004\n"); store.rollback(version,corpus)
    assert corpus.read_text()=="P060 D004 P062 D004\n"
    assert manifest.read_text()==""
    assert store.load(version)[0].to_dict()==model.to_dict()
class _Teacher:
    def __init__(self): self.calls=0
    def complete(self,prompt):
        self.calls+=1
        assert "P072 D004 P074 D004" in prompt
        return "P064 D004 P065 D004"

def test_teacher_response_is_logged_with_prompt_hash(tmp_path):
    class Teacher:
        def complete(self,prompt): return "P060 D004 P062 D004"
    log=tmp_path/"llm_responses.log"
    assert LoggedTeacher(Teacher(),log).complete("teacher prompt")=="P060 D004 P062 D004"
    record=json.loads(log.read_text().splitlines()[0])
    assert record["response"]=="P060 D004 P062 D004" and len(record["prompt_hash"])==64

def test_active_teacher_sample_is_conditioned_on_context(tmp_path):
    seed=tmp_path/"seed"; seed.mkdir()
    (seed/"scale.abc").write_text("X:1\nT:Scale\nL:1/4\nK:C\nC D E F G A B c d e |\n")
    teacher=_Teacher()
    version=train_music(seed,work_dir=tmp_path/"work",order=5,max_iterations=1,teacher=teacher)
    assert version=="v002" and teacher.calls==1
    corpus=(tmp_path/"work"/"corpus"/"symbolic_music.txt").read_text()
    assert "P072 D004 P074 D004 P064 D004 P065 D004" in corpus
    metric=json.loads((tmp_path/"work"/"metrics.jsonl").read_text().splitlines()[0])
    assert metric["status"]=="accepted" and metric["llm_query_rate"]==1.0

def test_uncertainty_flags_unseen_context():
    model=MusicNGramModel(3); model.train_lines(["P060 D004 P062 D004 P064 D004"])
    verdict=evaluate_uncertainty(model,MotifMemory(),"P099 D001","P060 D004")
    assert verdict.is_uncertain and verdict.reason=="unseen_context"

def test_corpus_recovers_source_deduplication_after_manifest_loss(tmp_path):
    path=tmp_path/"corpus.txt"
    writer=CorpusWriter(path)
    sample="P060 D004 P062 D004"
    assert writer.append(sample,source="file:my score.mid")
    (tmp_path/"provenance.jsonl").unlink()
    recovered=CorpusWriter(path)
    assert not recovered.append(sample,source="file:my score.mid")
    assert len(path.read_text().splitlines())==1

def test_motif_snapshot_rejects_mismatched_vector():
    memory=MotifMemory()
    memory.build(["P060 D004 P062 D004 P064 D004"]*3)
    data=memory.to_dict()
    data["patterns"][0]["vector"][0] *= -1
    with pytest.raises(ValueError,match="invalid motif pattern"):
        MotifMemory.from_dict(data)

def test_ngram_rejects_non_integer_order():
    with pytest.raises(ValueError,match="positive integer"):
        NGramModel(n=1.5)
    with pytest.raises(ValueError,match="positive integer"):
        NGramModel(n=True)

def test_abc_zero_duration_denominator_is_rejected(tmp_path):
    path=tmp_path/"invalid-duration.abc"
    path.write_text("X:1\nL:1/4\nK:C\nC1/0 D |\n")
    with pytest.raises(ValueError,match="denominator must be non-zero"):
        encode_file(path)

def test_public_bounds_reject_invalid_numeric_types(tmp_path):
    with pytest.raises(ValueError,match="non-negative integer"):
        NGramModel(2).generate(-1)
    with pytest.raises(ValueError,match="non-negative integer"):
        NGramModel(2).most_likely_continuations("P060",k=1.5)
    with pytest.raises(ValueError,match="integers"):
        validate_tokens("P060 D004",min_tokens=True)
    with pytest.raises(ValueError,match="pitch classes"):
        validate_tokens("P060 D004",key_pitch_classes={12})
    with pytest.raises(ValueError,match="finite positive"):
        LoggedTeacher(object(),tmp_path/"teacher.log",timeout=float("nan"))
    with pytest.raises(ValueError,match="non-negative integer"):
        LoggedTeacher(object(),tmp_path/"teacher.log",retries=1.5)
    with pytest.raises(ValueError,match="non-negative integer"):
        SnapshotStore(tmp_path/"snapshots").commit(
            MusicNGramModel(2),MotifMemory(),tmp_path/"corpus.txt",llm_samples=-1
        )

def test_abc_zero_rest_duration_denominator_is_rejected(tmp_path):
    path=tmp_path/"invalid-rest.abc"
    path.write_text("X:1\nL:1/4\nK:C\nz1/0 D |\n")
    with pytest.raises(ValueError,match="denominator must be non-zero"):
        encode_file(path)

def test_midi_rejects_trailing_bytes_outside_declared_tracks(tmp_path):
    path=tmp_path/"trailing.mid"
    _midi(path)
    path.write_bytes(path.read_bytes()+b"junk")
    with pytest.raises(ValueError,match="trailing data"):
        encode_file(path)
