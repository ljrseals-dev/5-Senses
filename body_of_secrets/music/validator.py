"""Music-theory validation and uncertainty scoring."""
# ruff: noqa: E701, E702, E704
from __future__ import annotations
from dataclasses import dataclass
from .hopfield import MotifMemory
from .ngram import MusicNGramModel
from .tokens import validate_tokens

@dataclass(frozen=True)
class UncertaintyVerdict:
    is_uncertain: bool
    reason: str
    context: str
    candidate: str
    entropy: float
    hopfield_overlap: float
    violations: tuple[str,...]

def evaluate_uncertainty(model:MusicNGramModel,memory:MotifMemory,context:str,candidate:str,
                         *,entropy_threshold:float=2.0,hopfield_threshold:float=.35):
    result=validate_tokens(candidate); distribution=model.distribution(context)
    entropy=model.entropy(context); overlap=memory.recall_overlap(candidate.split())
    reasons=[]
    if not distribution: reasons.append("unseen_context")
    elif entropy>entropy_threshold: reasons.append("entropy_exceeded")
    if not memory.patterns or memory.energy_gap(candidate.split())>hopfield_threshold: reasons.append("hopfield_unrecognized")
    if not result.valid: reasons.append("rule_validation_failed")
    return UncertaintyVerdict(bool(reasons),reasons[0] if reasons else "confident",context,candidate,
                              entropy,overlap,result.violations)

def candidate_from_model(model,context,length=8):
    prefix=context.split(); output=[]
    for _ in range(length):
        choices=model.continuations(prefix+output)
        if not choices: break
        output.append(choices[0][0])
    return " ".join(output)
