"""Deterministic motif vectors and bounded Hopfield-compatible memory."""
# ruff: noqa: E401, E701, E702, E704
from __future__ import annotations
import hashlib, json
from collections import Counter
from pathlib import Path
from body_of_secrets.neural import HopfieldNetwork

def project_motif(motif: tuple[str, ...], dimensions: int = 128) -> list[int]:
    if dimensions < 8: raise ValueError("dimensions must be >= 8")
    seed = " ".join(motif).encode()
    bits, counter = [], 0
    while len(bits) < dimensions:
        digest = hashlib.sha256(b"5-senses-music-v1\0"+seed+counter.to_bytes(4,"big")).digest()
        for byte in digest:
            bits.extend(1 if byte & (1 << bit) else -1 for bit in range(8))
            if len(bits) >= dimensions: break
        counter += 1
    return bits[:dimensions]

class MotifMemory:
    def __init__(self, max_patterns=5000, dimensions=128):
        if max_patterns < 1: raise ValueError("max_patterns must be positive")
        self.max_patterns, self.dimensions, self.patterns = max_patterns, dimensions, []
        self._network = None
    def build(self, lines, min_frequency=3):
        if min_frequency < 1: raise ValueError("min_frequency must be positive")
        counts = Counter()
        for line in lines:
            t = line.split("#",1)[0].split()
            for width in range(4,9):
                counts.update(tuple(t[i:i+width]) for i in range(max(0,len(t)-width+1)))
        ranked = sorted(((m,n) for m,n in counts.items() if n >= min_frequency),
                        key=lambda x: (-x[1], x[0]))[:self.max_patterns]
        self.patterns = [{"tokens": list(m), "frequency": n, "source": "ngram_motif",
                          "vector": project_motif(m,self.dimensions)} for m,n in ranked]
        self._network = self.rebuild_network()
    def recall_overlap(self, tokens):
        if not self.patterns: return 0.
        cue = project_motif(tuple(tokens), self.dimensions)
        return max(sum(a*b for a,b in zip(cue,p["vector"]))/self.dimensions for p in self.patterns)
    def rebuild_network(self):
        # Existing HopfieldNetwork is dense; only materialize small banks.
        if not self.patterns or len(self.patterns) > 128: return None
        net = HopfieldNetwork(self.dimensions); net.store([p["vector"] for p in self.patterns]); return net
    def energy_gap(self, tokens):
        if not self.patterns: return float("inf")
        cue=project_motif(tuple(tokens),self.dimensions)
        if any(cue==pattern["vector"] for pattern in self.patterns): return 0.0
        if self._network is None: return 1.0-self.recall_overlap(tokens)
        cue_energy=self._network.energy(cue)
        stored_energy=min(self._network.energy(p["vector"]) for p in self.patterns)
        return max(0.0,cue_energy-stored_energy)
    def to_dict(self):
        return {"schema":1,"max_patterns":self.max_patterns,"dimensions":self.dimensions,"patterns":self.patterns}
    @classmethod
    def from_dict(cls,data):
        if data.get("schema") != 1: raise ValueError("unsupported motif snapshot schema")
        obj=cls(int(data["max_patterns"]),int(data["dimensions"])); obj.patterns=data["patterns"]
        if len(obj.patterns)>obj.max_patterns: raise ValueError("pattern capacity exceeded")
        obj._network=obj.rebuild_network()
        return obj
    def save(self,path): Path(path).write_text(json.dumps(self.to_dict(),sort_keys=True,indent=2)+"\n",encoding="utf-8")
    @classmethod
    def load(cls,path): return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
