"""Provider-neutral optional teacher plugin with bounded calls and response audit."""
# ruff: noqa: E401, E701, E702, E704
from __future__ import annotations
import hashlib,importlib.metadata,json,queue,threading
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
    entries=importlib.metadata.entry_points()
    selected=next((ep for ep in entries.select(group="body_of_secrets.music_teachers")
                   if name is None or ep.name==name),None)
    if selected is None: raise LookupError("no plugin in entry-point group body_of_secrets.music_teachers")
    factory=selected.load()
    return factory() if callable(factory) else factory

class LoggedTeacher:
    def __init__(self,teacher,log_path,*,timeout=30.,retries=1):
        if timeout<=0 or retries<0: raise ValueError("timeout must be positive and retries non-negative")
        self.teacher,self.log_path,self.timeout,self.retries=teacher,Path(log_path),timeout,retries
        self.lock=threading.Lock()
    def _call(self,prompt):
        result=queue.Queue(maxsize=1)
        def invoke():
            try: result.put((True,self.teacher.complete(prompt)))
            except Exception as exc: result.put((False,exc))
        # A daemon worker ensures a hung optional plugin cannot hold process shutdown.
        threading.Thread(target=invoke,name="music-teacher",daemon=True).start()
        try: ok,value=result.get(timeout=self.timeout)
        except queue.Empty as exc: raise TimeoutError("music teacher timed out") from exc
        if not ok: raise value
        if not isinstance(value,str): raise TypeError("teacher must return text")
        return value
    def complete(self,prompt):
        prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(); raw=""; error=None
        for _ in range(self.retries+1):
            try:
                raw=self._call(prompt); error=None; break
            except TimeoutError as exc:
                error=f"TimeoutError: {exc}"
                break  # cannot cancel a running provider request safely; avoid duplicate billable retries
            except Exception as exc:
                error=f"{type(exc).__name__}: {exc}"
        self.log_path.parent.mkdir(parents=True,exist_ok=True)
        record={"timestamp":datetime.now(timezone.utc).isoformat(),"prompt_hash":prompt_hash,
                "response":raw,"error":error}
        with self.lock,self.log_path.open("a",encoding="utf-8",newline="\n") as stream:
            stream.write(json.dumps(record,ensure_ascii=False,sort_keys=True)+"\n")
        if error: raise RuntimeError("llm_unavailable: "+error)
        return raw
