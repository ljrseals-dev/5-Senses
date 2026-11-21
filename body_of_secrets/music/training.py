"""Offline-first training and opt-in active teacher loop."""
from __future__ import annotations
import hashlib
from pathlib import Path
from .corpus import CorpusWriter
from .encoder import encode_directory
from .hopfield import MotifMemory
from .ngram import MusicNGramModel
from .snapshots import SnapshotStore
from .teacher import LoggedTeacher,build_prompt
from .tokens import validate_tokens
from .validator import candidate_from_model,evaluate_uncertainty

def train_music(seed_directory,*,work_dir="music_data",order=5,max_iterations=0,
                teacher:LoggedTeacher|None=None,entropy_threshold=2.,max_patterns=5000):
    root=Path(work_dir); corpus=root/"corpus"/"symbolic_music.txt"; corpus.parent.mkdir(parents=True,exist_ok=True)
    writer=CorpusWriter(corpus)
    for record in encode_directory(seed_directory):
        writer.append(record["tokens"],source="file:"+record["source"])
    if not corpus.exists(): corpus.write_text("",encoding="utf-8")
    lines=corpus.read_text(encoding="utf-8").splitlines()
    model=MusicNGramModel.from_file(corpus,order)
    memory=MotifMemory(max_patterns=max_patterns)
    memory.build([line.split("#",1)[0] for line in lines])
    store=SnapshotStore(root/"snapshots")
    version=store.commit(model,memory,corpus); accepted=0
    for _ in range(max_iterations):
        if teacher is None: break
        candidates=[line.split("#",1)[0].strip() for line in lines
                    if len(line.split("#",1)[0].split())>=order]
        if not candidates: break
        # Keep the final observed token as the training target; the context itself must have a successor.
        context=" ".join(candidates[-1].split()[-order:-1])
        candidate=candidate_from_model(model,context,8)
        verdict=evaluate_uncertainty(model,memory,context,candidate,entropy_threshold=entropy_threshold)
        if not verdict.is_uncertain: break
        prompt=build_prompt(context,candidate,verdict.violations)
        prompt_hash=hashlib.sha256(prompt.encode()).hexdigest()
        try: raw=teacher.complete(prompt)
        except RuntimeError: break
        result=validate_tokens(raw)
        if not result.valid:
            writer.reject(raw,reason=result.violations,context=context); continue
        # Store the context together with its corrected continuation so the n-gram learns P(next|context).
        sample=" ".join((context,*result.tokens))
        combined=validate_tokens(sample)
        if not combined.valid:
            writer.reject(raw,reason=combined.violations,context=context); continue
        if not writer.append(sample,source="llm",prompt_hash=prompt_hash): continue
        accepted+=1; lines=corpus.read_text(encoding="utf-8").splitlines()
        model=MusicNGramModel.from_file(corpus,order); memory.build([x.split("#",1)[0] for x in lines])
        version=store.commit(model,memory,corpus,llm_samples=accepted)
    return version
