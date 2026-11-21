"""Music token vocabulary and structural/theory validation."""
from __future__ import annotations

import re
from dataclasses import dataclass

TOKEN_RE=re.compile(r"^(?:P(?:0[0-9]{2}|1[01][0-9]|12[0-7])|D(?:016|008|004|002|001)|DRST|CHD|B)$")
PITCH_RE=re.compile(r"^P(\d{3})$")
DURATION_BEATS={"D016":.25,"D008":.5,"D004":1.,"D002":2.,"D001":4.}
def strip_comments(line:str)->str: return line.split("#",1)[0].strip()
def parse_tokens(value): return strip_comments(value).split() if isinstance(value,str) else list(value)
@dataclass(frozen=True)
class ValidationResult:
    valid:bool
    violations:tuple[str,...]=()
    tokens:tuple[str,...]=()
def validate_tokens(value,*,min_tokens=4,max_tokens=64,max_interval=12,
                    key_pitch_classes:set[int]|None=None,max_events_per_four_beats=16):
    try:
        tokens=parse_tokens(value)
    except (TypeError,ValueError) as exc:
        raise ValueError("tokens must be a string or iterable of strings") from exc
    if any(not isinstance(token,str) for token in tokens):
        raise ValueError("tokens must contain only strings")
    errors=[]
    bounds=(min_tokens,max_tokens,max_interval,max_events_per_four_beats)
    if any(not isinstance(value,int) or isinstance(value,bool) for value in bounds):
        raise ValueError("token validation bounds must be integers")
    if min_tokens < 0 or max_tokens < min_tokens:
        raise ValueError("invalid token length bounds")
    if max_interval < 0:
        raise ValueError("max_interval must be a non-negative integer")
    if max_events_per_four_beats < 1:
        raise ValueError("max_events_per_four_beats must be positive")
    if key_pitch_classes is not None and (
        not isinstance(key_pitch_classes,(set,frozenset))
        or any(not isinstance(pitch,int) or isinstance(pitch,bool) or not 0 <= pitch <= 11
               for pitch in key_pitch_classes)
    ):
        raise ValueError("key_pitch_classes must contain pitch classes 0..11")
    if any(not TOKEN_RE.fullmatch(t) for t in tokens):
        return ValidationResult(False,("invalid_token",),tuple(tokens))
    if len(tokens)<min_tokens: errors.append("sequence_too_short")
    if len(tokens)>max_tokens: errors.append("sequence_too_long")
    i,previous_pitch,beat_window,event_count=0,None,0.,0
    while i<len(tokens):
        if tokens[i]=="B":
            beat_window=0.; event_count=0; i+=1; continue
        if tokens[i]=="DRST":
            beat_window+=.25; event_count+=1; i+=1
            if beat_window>=4:
                if event_count>max_events_per_four_beats: errors.append("rhythm_density_exceeded")
                beat_window%=4; event_count=0
            continue
        chord=tokens[i]=="CHD"; pitches=[]; durations=[]
        if chord:
            # CHD prefixes each simultaneous tone, making the end of a chord unambiguous.
            while i<len(tokens) and tokens[i]=="CHD":
                i+=1
                if i+1>=len(tokens) or not (m:=PITCH_RE.fullmatch(tokens[i])) or tokens[i+1] not in DURATION_BEATS:
                    errors.append("invalid_event_structure"); break
                pitches.append(int(m.group(1))); durations.append(tokens[i+1]); i+=2
        else:
            m=PITCH_RE.fullmatch(tokens[i])
            if not m or i+1>=len(tokens) or tokens[i+1] not in DURATION_BEATS:
                errors.append("invalid_event_structure"); i+=1; continue
            pitches.append(int(m.group(1))); durations.append(tokens[i+1]); i+=2
        if not pitches: continue
        if chord and (len(pitches)<2 or pitches != sorted(pitches)):
            errors.append("invalid_event_structure")
        # Chord tones are simultaneous: compare the chord root with the prior
        # melodic event, but never compare notes within the chord as a melody.
        if previous_pitch is not None and abs(pitches[0]-previous_pitch)>max_interval:
            errors.append("interval_exceeded")
        previous_pitch=pitches[0]
        if key_pitch_classes is not None and any(p%12 not in key_pitch_classes for p in pitches):
            errors.append("outside_key")
        beat_window+=max(DURATION_BEATS[d] for d in durations); event_count+=1
        if beat_window>=4:
            if event_count>max_events_per_four_beats: errors.append("rhythm_density_exceeded")
            beat_window%=4; event_count=0
    return ValidationResult(not errors,tuple(dict.fromkeys(errors)),tuple(tokens))
