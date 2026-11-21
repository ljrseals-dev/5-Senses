"""Idempotent corpus writer with source-aware deduplication and provenance."""
from __future__ import annotations
import hashlib,json,threading
from datetime import datetime,timezone
from pathlib import Path
from .tokens import strip_comments
_LOCK=threading.Lock()

class CorpusWriter:
    def __init__(self,corpus_path,rejected_path=None):
        self.path=Path(corpus_path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.rejected_path=Path(rejected_path) if rejected_path else self.path.with_name("rejected_samples.log")
        self.manifest_path=self.path.with_name("provenance.jsonl")
    def _existing_tokens(self):
        if not self.path.exists(): return set()
        return {strip_comments(x) for x in self.path.read_text(encoding="utf-8").splitlines() if strip_comments(x)}
    def _existing_sources(self):
        pairs=set()
        if not self.manifest_path.exists(): return pairs
        for line in self.manifest_path.read_text(encoding="utf-8").splitlines():
            try:
                row=json.loads(line); pairs.add((row.get("source"),row.get("tokens")))
            except (json.JSONDecodeError,TypeError):
                continue
        return pairs
    def append(self,tokens,*,source,prompt_hash=None):
        clean=strip_comments(tokens)
        if not clean: raise ValueError("cannot append empty sample")
        digest=hashlib.sha256(clean.encode()).hexdigest()
        with _LOCK:
            existing=self._existing_tokens()
            if source.startswith("file:"):
                if (source,clean) in self._existing_sources(): return False
            elif clean in existing:
                return False
            timestamp=datetime.now(timezone.utc).isoformat()
            safe_source=json.dumps(source,ensure_ascii=False)
            qh=prompt_hash or "-"
            with self.path.open("a",encoding="utf-8",newline="\n") as stream:
                stream.write(f"{clean} # src={safe_source} ts={timestamp} qh={qh} sha256={digest}\n")
            record={"timestamp":timestamp,"source":source,"sha256":digest,
                    "prompt_hash":prompt_hash,"tokens":clean}
            with self.manifest_path.open("a",encoding="utf-8",newline="\n") as stream:
                stream.write(json.dumps(record,ensure_ascii=False,sort_keys=True)+"\n")
        return True
    def reject(self,raw,*,reason,context=""):
        self.rejected_path.parent.mkdir(parents=True,exist_ok=True)
        record={"timestamp":datetime.now(timezone.utc).isoformat(),"reason":list(reason),
                "context":context,"raw":raw}
        with _LOCK,self.rejected_path.open("a",encoding="utf-8",newline="\n") as stream:
            stream.write(json.dumps(record,ensure_ascii=False,sort_keys=True)+"\n")
