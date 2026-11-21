"""Idempotent corpus writer with source-aware deduplication and provenance."""
from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from .tokens import strip_comments

_LOCK = threading.Lock()

class CorpusWriter:
    def __init__(self,corpus_path,rejected_path=None):
        self.path=Path(corpus_path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.rejected_path=Path(rejected_path) if rejected_path else self.path.with_name("rejected_samples.log")
        self.manifest_path=self.path.with_name("provenance.jsonl")
        self._tokens_cache=None
        self._sources_cache=None
    def _existing_tokens(self):
        # Reload under the process-wide append lock: another CorpusWriter instance
        # may have changed the file since this instance was constructed.
        if not self.path.exists(): self._tokens_cache=set()
        else: self._tokens_cache={strip_comments(x) for x in self.path.read_text(encoding="utf-8").splitlines() if strip_comments(x)}
        return self._tokens_cache
    def _existing_sources(self):
        # The corpus line is the write-ahead record. Recover source idempotency
        # if the process died before the separate provenance manifest was updated.
        self._sources_cache=set()
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                _, marker, metadata = line.partition("#")
                if not marker:
                    continue
                source_field=metadata.partition("src=")[2]
                if source_field:
                    try:
                        source,_=json.JSONDecoder().raw_decode(source_field.lstrip())
                    except (json.JSONDecodeError,TypeError):
                        continue
                    clean=strip_comments(line)
                    if isinstance(source,str) and clean:
                        self._sources_cache.add((source,clean))
        if self.manifest_path.exists():
            for line in self.manifest_path.read_text(encoding="utf-8").splitlines():
                try:
                    row=json.loads(line)
                except (json.JSONDecodeError,TypeError):
                    continue
                if isinstance(row,dict) and isinstance(row.get("source"),str) and isinstance(row.get("tokens"),str):
                    self._sources_cache.add((row["source"],row["tokens"]))
        return self._sources_cache
    def append(self,tokens,*,source,prompt_hash=None):
        if not isinstance(source,str) or not source:
            raise ValueError("source must be a non-empty string")
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
            self._existing_tokens().add(clean)
            self._existing_sources().add((source,clean))
        return True
    def reject(self,raw,*,reason,context=""):
        self.rejected_path.parent.mkdir(parents=True,exist_ok=True)
        record={"timestamp":datetime.now(timezone.utc).isoformat(),"reason":list(reason),
                "context":context,"raw":raw}
        with _LOCK,self.rejected_path.open("a",encoding="utf-8",newline="\n") as stream:
            stream.write(json.dumps(record,ensure_ascii=False,sort_keys=True)+"\n")
