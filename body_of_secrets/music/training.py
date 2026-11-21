"""Offline-first training and opt-in active teacher loop."""
# ruff: noqa: E701, E702, E704
from __future__ import annotations
import hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path
from .corpus import CorpusWriter
from .encoder import encode_directory
from .hopfield import MotifMemory
from .ngram import MusicNGramModel
from .snapshots import SnapshotStore
from .teacher import LoggedTeacher,build_prompt
from .tokens import DURATION_BEATS,validate_tokens
from .validator import candidate_from_model,evaluate_uncertainty

def _record_metrics(root,*,iteration,queries,rejected,hopfield_hits,lines,model,holdout,status):
    holdout_perplexity=None
    if holdout is not None:
        holdout_lines=Path(holdout).read_text(encoding="utf-8").splitlines()
        value=model.perplexity(holdout_lines)
        holdout_perplexity=value if math.isfinite(value) else None
    record={"timestamp":datetime.now(timezone.utc).isoformat(),"iteration":iteration,
            "status":status,"corpus_lines_total":sum(1 for line in lines
            if line.strip() and not line.lstrip().startswith("#")),
            "llm_queries":queries,"llm_query_rate":queries/max(1,iteration),
            "llm_rejections":rejected,"llm_rejection_rate":rejected/max(1,queries),
            "hopfield_hit_rate":hopfield_hits/max(1,queries),
            "ngram_perplexity_on_holdout":holdout_perplexity}
    path=Path(root)/"metrics.jsonl"
    with path.open("a",encoding="utf-8",newline="\n") as stream:
        stream.write(json.dumps(record,sort_keys=True)+"\n")

def train_music(seed_directory,*,work_dir="music_data",order=5,max_iterations=0,
                teacher:LoggedTeacher|None=None,entropy_threshold=2.,max_patterns=5000,
                holdout_corpus=None):
    if not isinstance(max_iterations,int) or max_iterations < 0:
        raise ValueError("max_iterations must be a non-negative integer")
    if not math.isfinite(entropy_threshold) or entropy_threshold < 0:
        raise ValueError("entropy_threshold must be finite and non-negative")
    if holdout_corpus is not None and not Path(holdout_corpus).is_file():
        raise FileNotFoundError(holdout_corpus)
    root=Path(work_dir); corpus=root/"corpus"/"symbolic_music.txt"; corpus.parent.mkdir(parents=True,exist_ok=True)
    writer=CorpusWriter(corpus)
    for record in encode_directory(seed_directory):
        writer.append(record["tokens"],source="file:"+record["source"])
    if not corpus.exists(): corpus.write_text("",encoding="utf-8")
    lines=corpus.read_text(encoding="utf-8").splitlines()
    if not any(line.split("#",1)[0].strip() for line in lines):
        raise ValueError("no symbolic music events found in seed corpus")
    model=MusicNGramModel.from_file(corpus,order)
    memory=MotifMemory(max_patterns=max_patterns)
    memory.build([line.split("#",1)[0] for line in lines])
    store=SnapshotStore(root/"snapshots")
    version=store.commit(model,memory,corpus); accepted=queries=rejected=hopfield_hits=0
    for iteration in range(1,max_iterations+1):
        if teacher is None: break
        candidates=[line.split("#",1)[0].strip() for line in lines
                    if len(line.split("#",1)[0].split())>=order]
        if not candidates: break
        # Select the latest context that ends at a note boundary and has a following pitch/chord token.
        sequence=candidates[-1].split(); context_tokens=None
        for target_index in range(order-1,len(sequence)):
            window=sequence[target_index-(order-1):target_index]
            if window and window[-1] in DURATION_BEATS: context_tokens=window
        if context_tokens is None: break
        context=" ".join(context_tokens)
        candidate=candidate_from_model(model,context,8)
        verdict=evaluate_uncertainty(model,memory,context,candidate,entropy_threshold=entropy_threshold)
        if not verdict.is_uncertain: break
        queries+=1
        if memory.patterns and memory.energy_gap(candidate.split())<=.35: hopfield_hits+=1
        prompt=build_prompt(context,candidate,verdict.violations)
        prompt_hash=hashlib.sha256(prompt.encode()).hexdigest()
        try: raw=teacher.complete(prompt)
        except RuntimeError:
            _record_metrics(root,iteration=iteration,queries=queries,rejected=rejected,
                            hopfield_hits=hopfield_hits,lines=lines,model=model,
                            holdout=holdout_corpus,status="llm_unavailable")
            break
        result=validate_tokens(raw)
        if not result.valid:
            rejected+=1; writer.reject(raw,reason=result.violations,context=context)
            _record_metrics(root,iteration=iteration,queries=queries,rejected=rejected,
                            hopfield_hits=hopfield_hits,lines=lines,model=model,
                            holdout=holdout_corpus,status="rejected")
            continue
        # Store context with its continuation so the n-gram learns P(next|context).
        sample=" ".join((context,*result.tokens)); combined=validate_tokens(sample)
        if not combined.valid:
            rejected+=1; writer.reject(raw,reason=combined.violations,context=context)
            _record_metrics(root,iteration=iteration,queries=queries,rejected=rejected,
                            hopfield_hits=hopfield_hits,lines=lines,model=model,
                            holdout=holdout_corpus,status="rejected")
            continue
        if not writer.append(sample,source="llm",prompt_hash=prompt_hash):
            _record_metrics(root,iteration=iteration,queries=queries,rejected=rejected,
                            hopfield_hits=hopfield_hits,lines=lines,model=model,
                            holdout=holdout_corpus,status="duplicate")
            continue
        accepted+=1; lines=corpus.read_text(encoding="utf-8").splitlines()
        model=MusicNGramModel.from_file(corpus,order); memory.build([x.split("#",1)[0] for x in lines])
        version=store.commit(model,memory,corpus,llm_samples=accepted)
        _record_metrics(root,iteration=iteration,queries=queries,rejected=rejected,
                        hopfield_hits=hopfield_hits,lines=lines,model=model,
                        holdout=holdout_corpus,status="accepted")
    return version
