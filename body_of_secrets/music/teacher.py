"""Provider-neutral optional teacher plugin, timeout/retry and raw-response audit."""
from __future__ import annotations
import hashlib,importlib.metadata,json,threading
from concurrent.futures import ThreadPoolExecutor,TimeoutError
from datetime import datetime,timezone
from pathlib import Path
from typing import Protocol

class MusicTeacher(Protocol):
    def complete(self,prompt:str)->str: ...

def build_prompt(context,candidate,violations):
    return ("You are a music theory teacher. Given this symbolic motif context:\n"+context+
            "\n\nThe student model generated:\n"+candidate+
            "\n\nThis candidate failed validation: "+(", ".join(violations) or "uncertainty threshold")+
            ".\nProvide a corrected continuation as a space-separated token sequence using the same token vocabulary. Output ONLY the token sequence.")

def load_teacher_plugin(name=None):
    eps=importlib.metadata.entry_points()
    selected=next((ep for ep in eps.select(group="body_of_secrets.music_teachers")
                   if name is None or ep.name==name),None)
    if selected is None: raise LookupError("no plugin in entry-point group body_of_secrets.music_teachers")
    factory=selected.load()
    return factory() if callable(factory) else factory

class LoggedTeacher:
    def __init__(self,teacher,log_path,*,timeout=30.,retries=1):
        if timeout<=0 or retries<0: raise ValueError("timeout must be positive and retries non-negative")
        self.teacher,self.log_path,self.timeout,self.retries=teacher,Path(log_path),timeout,retries
        self.lock=threading.Lock()
    def complete(self,prompt):
        prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(); raw=""; error=None
        for _ in range(self.retries+1):
            pool=ThreadPoolExecutor(max_workers=1); future=pool.submit(self.teacher.complete,prompt)
            try:
                raw=future.result(timeout=self.timeout)
                if not isinstance(raw,str): raise TypeError("teacher must return text")
                error=None; break
            except Exception as exc:
                error=f"{type(exc).__name__}: {exc}"; future.cancel()
            finally: pool.shutdown(wait=False,cancel_futures=True)
        self.log_path.parent.mkdir(parents=True,exist_ok=True)
        record={"timestamp":datetime.now(timezone.utc).isoformat(),"prompt_hash":prompt_hash,
                "response":raw,"error":error}
        with self.lock,self.log_path.open("a",encoding="utf-8",newline="\n") as f:
            f.write(json.dumps(record,ensure_ascii=False,sort_keys=True)+"\n")
        if error: raise RuntimeError("llm_unavailable: "+error)
        return raw
