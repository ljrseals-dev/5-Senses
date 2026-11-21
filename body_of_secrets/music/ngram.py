"""Music adapter over the existing NGramModel, preserving exact symbolic tokens."""
# ruff: noqa: E401, E701, E702, E704
from __future__ import annotations
import json,math
from pathlib import Path
from body_of_secrets.language.ngram import NGramModel
from .tokens import strip_comments

class MusicNGramModel(NGramModel):
    """Use the repository's existing n-gram counts with case-sensitive tokenization."""
    def __init__(self,order:int=5):
        super().__init__(n=order,level="token")
    def train_lines(self,lines):
        for line in lines:
            clean=strip_comments(line)
            if clean: self.train([clean])
    def update(self,sample):
        clean=strip_comments(sample)
        if not clean: raise ValueError("empty training sample")
        self.train([clean])
    @classmethod
    def from_file(cls,path,order=5):
        model=cls(order)
        model.train_lines(Path(path).read_text(encoding="utf-8").splitlines())
        return model
    def distribution(self,context):
        tokens=self._tokens(context) if isinstance(context,str) else list(context)
        if len(tokens)<self.n-1 or not self.vocab: return {}
        key=() if self.n == 1 else tuple(tokens[-(self.n-1):])
        counts=self.counts.get(key)
        if not counts: return {}
        total=self.context_totals[key]+len(self.vocab)
        return {token:(counts.get(token,0)+1)/total for token in sorted(self.vocab)}
    def entropy(self,context):
        return -sum(p*math.log2(p) for p in self.distribution(context).values())
    def continuations(self,context,limit=5):
        if limit<1: raise ValueError("limit must be positive")
        return sorted(self.distribution(context).items(),key=lambda x:(-x[1],x[0]))[:limit]
    def perplexity(self,lines):
        logp=0.0; count=0; fallback=1/max(1,len(self.vocab))
        for line in lines:
            tokens=strip_comments(line).split()
            for i in range(self.n-1,len(tokens)):
                context = [] if self.n == 1 else tokens[i-self.n+1:i]
                probabilities=self.distribution(context)
                probability=probabilities.get(tokens[i],fallback)
                logp+=math.log(max(probability,1e-300)); count+=1
        return math.exp(-logp/count) if count else float("inf")
    def to_dict(self):
        return {"schema":1,"order":self.n,"vocab":sorted(self.vocab),
                "counts":[{"context":list(k),"next":dict(sorted(v.items()))}
                          for k,v in sorted(self.counts.items())]}
    @classmethod
    def from_dict(cls,data):
        if data.get("schema")!=1: raise ValueError("unsupported music n-gram schema")
        model=cls(int(data["order"])); model.vocab=set(data["vocab"])
        for item in data["counts"]:
            key=tuple(item["context"]); model.counts[key].update(item["next"])
            model.context_totals[key]=sum(item["next"].values())
        model._trained=True
        return model
    def save(self,path):
        Path(path).write_text(json.dumps(self.to_dict(),sort_keys=True,indent=2)+"\n",encoding="utf-8")
    @classmethod
    def load(cls,path):
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
