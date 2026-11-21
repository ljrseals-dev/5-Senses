"""Case-preserving symbolic token n-gram model."""
from __future__ import annotations
import json,math
from collections import Counter,defaultdict
from pathlib import Path
from .tokens import strip_comments
class MusicNGramModel:
    def __init__(self,order:int=5):
        if order<2: raise ValueError("order must be >= 2")
        self.order=order; self.counts:dict[tuple[str,...],Counter[str]]=defaultdict(Counter)
        self.vocab:set[str]=set(); self.total_tokens=0
    @property
    def context_size(self): return self.order-1
    def _add(self,tokens):
        self.vocab.update(tokens); self.total_tokens+=len(tokens)
        for i in range(self.context_size,len(tokens)):
            self.counts[tuple(tokens[i-self.context_size:i])][tokens[i]]+=1
    def train_lines(self,lines):
        for line in lines: self._add(strip_comments(line).split())
    def update(self,sample):
        tokens=strip_comments(sample).split()
        if not tokens: raise ValueError("empty training sample")
        self._add(tokens)
    @classmethod
    def from_file(cls,path,order=5):
        obj=cls(order); obj.train_lines(Path(path).read_text(encoding="utf-8").splitlines()); return obj
    def distribution(self,context):
        tokens=strip_comments(context).split() if isinstance(context,str) else list(context)
        if len(tokens)<self.context_size or not self.vocab: return {}
        counts=self.counts.get(tuple(tokens[-self.context_size:]))
        if not counts: return {}
        denom=sum(counts.values())+len(self.vocab)
        # Include unseen vocabulary mass: probabilities now sum to one, so entropy is correct.
        return {token:(counts.get(token,0)+1)/denom for token in sorted(self.vocab)}
    def entropy(self,context):
        return -sum(p*math.log2(p) for p in self.distribution(context).values())
    def continuations(self,context,limit=5):
        if limit<1: raise ValueError("limit must be positive")
        return sorted(self.distribution(context).items(),key=lambda x:(-x[1],x[0]))[:limit]
    def to_dict(self):
        return {"schema":1,"order":self.order,"total_tokens":self.total_tokens,"vocab":sorted(self.vocab),
                "counts":[{"context":list(k),"next":dict(sorted(v.items()))} for k,v in sorted(self.counts.items())]}
    @classmethod
    def from_dict(cls,data):
        if data.get("schema")!=1: raise ValueError("unsupported n-gram schema")
        obj=cls(int(data["order"])); obj.total_tokens=int(data["total_tokens"]); obj.vocab=set(data["vocab"])
        for item in data["counts"]: obj.counts[tuple(item["context"])]=Counter(item["next"])
        return obj
    def save(self,path):
        Path(path).write_text(json.dumps(self.to_dict(),sort_keys=True,indent=2)+"\n",encoding="utf-8")
    @classmethod
    def load(cls,path): return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
