"""Atomic, hash-verified snapshots and rollback."""
# ruff: noqa: E701, E702, E704
from __future__ import annotations
import hashlib,json,os,shutil,tempfile
from datetime import datetime,timezone
from pathlib import Path
from .hopfield import MotifMemory
from .ngram import MusicNGramModel

def sha256_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

class SnapshotStore:
    def __init__(self,root):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True); self.current_file=self.root/"CURRENT"
    def commit(self,model,memory,corpus_path,*,llm_samples=0):
        versions=sorted(p.name for p in self.root.glob("v[0-9][0-9][0-9]") if p.is_dir())
        name=f"v{(int(versions[-1][1:])+1) if versions else 1:03d}"
        parent=self.current_file.read_text(encoding="ascii").strip() if self.current_file.exists() else (versions[-1] if versions else None)
        if parent: self.verify(parent)
        temp=Path(tempfile.mkdtemp(prefix=".snapshot-",dir=self.root))
        try:
            model.save(temp/"ngram_music.json"); memory.save(temp/"hopfield_patterns.json")
            shutil.copyfile(corpus_path,temp/"corpus.txt")
            files=("ngram_music.json","hopfield_patterns.json","corpus.txt")
            hashes={f:sha256_file(temp/f) for f in files}
            (temp/"corpus_hash.txt").write_text(hashes["corpus.txt"]+"\n",encoding="ascii")
            corpus_lines=sum(1 for x in (temp/"corpus.txt").read_text(encoding="utf-8").splitlines()
                             if x.strip() and not x.lstrip().startswith("#"))
            metadata={"schema":1,"version":name,"parent":parent,
                      "timestamp":datetime.now(timezone.utc).isoformat(),"corpus_lines":corpus_lines,
                      "llm_samples":llm_samples,"sha256":hashes}
            (temp/"metadata.json").write_text(json.dumps(metadata,sort_keys=True,indent=2)+"\n",encoding="utf-8")
            os.replace(temp,self.root/name)
            pointer=self.root/".CURRENT.tmp"; pointer.write_text(name+"\n",encoding="ascii")
            os.replace(pointer,self.current_file)
            return name
        except Exception:
            shutil.rmtree(temp,ignore_errors=True); raise
    def verify(self,version):
        if not version.startswith("v") or not version[1:].isdigit(): raise ValueError("invalid snapshot version")
        directory=self.root/version
        metadata=json.loads((directory/"metadata.json").read_text(encoding="utf-8"))
        if metadata.get("schema")!=1 or metadata.get("version")!=version: raise ValueError("snapshot metadata mismatch")
        for filename,expected in metadata["sha256"].items():
            if sha256_file(directory/filename)!=expected: raise ValueError(f"snapshot integrity failure: {filename}")
        return metadata
    def rollback(self,version,corpus_path):
        self.verify(version); target=Path(corpus_path); target.parent.mkdir(parents=True,exist_ok=True)
        temp=target.with_name(target.name+".rollback.tmp")
        shutil.copyfile(self.root/version/"corpus.txt",temp); os.replace(temp,target)
        pointer=self.root/".CURRENT.tmp"; pointer.write_text(version+"\n",encoding="ascii")
        os.replace(pointer,self.current_file)
    def load(self,version=None):
        selected=version or (self.current_file.read_text(encoding="ascii").strip() if self.current_file.exists() else "")
        if not selected: raise FileNotFoundError("no current music snapshot")
        self.verify(selected); directory=self.root/selected
        return MusicNGramModel.load(directory/"ngram_music.json"),MotifMemory.load(directory/"hopfield_patterns.json")
