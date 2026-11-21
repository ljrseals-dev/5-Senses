"""Deterministic MIDI (SMF 0/1) and basic ABC encoders; no extra dependencies."""
# ruff: noqa: E701, E702, E704
from __future__ import annotations
import math
import re
import struct
from collections import defaultdict, deque
from pathlib import Path
from .tokens import DURATION_BEATS

def _duration(beats: float) -> str:
    return min(DURATION_BEATS, key=lambda key: (abs(DURATION_BEATS[key] - beats), -DURATION_BEATS[key]))

def _vlq(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    for _ in range(4):
        if pos >= len(data):
            raise ValueError("truncated MIDI variable-length quantity")
        byte = data[pos]; pos += 1
        value = (value << 7) | (byte & 127)
        if not byte & 128:
            return value, pos
    raise ValueError("invalid MIDI variable-length quantity")

def _midi(path: Path) -> str:
    data = path.read_bytes()
    if len(data) < 14 or data[:4] != b"MThd":
        raise ValueError("not a Standard MIDI File")
    hlen = struct.unpack(">I", data[4:8])[0]
    if hlen < 6 or len(data) < 8 + hlen:
        raise ValueError("invalid MIDI header")
    fmt, tracks, division = struct.unpack(">HHH", data[8:14])
    if fmt not in (0, 1) or tracks < 1 or (fmt == 0 and tracks != 1) or division == 0 or division & 0x8000:
        raise ValueError("only PPQ-based MIDI formats 0 and 1 are supported")
    pos, active, notes = 8 + hlen, defaultdict(deque), []
    for _ in range(tracks):
        if pos + 8 > len(data):
            raise ValueError("truncated MIDI track header")
        if data[pos:pos+4] != b"MTrk":
            raise ValueError("missing MIDI track")
        size = struct.unpack(">I", data[pos+4:pos+8])[0]
        track = data[pos+8:pos+8+size]; pos += 8 + size
        if len(track) != size:
            raise ValueError("truncated MIDI track")
        cur = tick = running = 0
        while cur < len(track):
            delta, cur = _vlq(track, cur); tick += delta
            if cur >= len(track):
                raise ValueError("MIDI track ends with an incomplete event")
            status = track[cur]
            if status < 128:
                if not running: raise ValueError("running status without prior status")
                status = running
            else:
                cur += 1
                if status < 240: running = status
                else: running = 0
            if status == 255:
                if cur >= len(track): raise ValueError("truncated MIDI meta event")
                cur += 1; length, cur = _vlq(track, cur)
                if cur + length > len(track): raise ValueError("truncated MIDI meta event payload")
                cur += length
                continue
            if status in (240, 247):
                length, cur = _vlq(track, cur)
                if cur + length > len(track): raise ValueError("truncated MIDI system-exclusive payload")
                cur += length; running = 0
                continue
            if status >= 240:
                raise ValueError(f"unsupported MIDI system status: 0x{status:02x}")
            kind, channel = status & 240, status & 15
            if kind not in (128, 144, 160, 176, 192, 208, 224):
                raise ValueError(f"unsupported MIDI channel status: 0x{status:02x}")
            width = 1 if kind in (192, 208) else 2
            if cur + width > len(track): raise ValueError("truncated MIDI channel event")
            values = track[cur:cur+width]
            if any(value >= 128 for value in values):
                raise ValueError("MIDI data byte has its status bit set")
            pitch = values[0]; velocity = values[1] if width == 2 else 0; cur += width
            key = (channel, pitch)
            if kind == 144 and velocity:
                active[key].append(tick)
            elif kind == 128 or (kind == 144 and velocity == 0):
                if active[key]:
                    start = active[key].popleft()
                    if tick > start: notes.append((start, tick, pitch))
    grouped = defaultdict(list)
    for start, end, pitch in notes: grouped[start].append((pitch, end-start))
    tokens, previous_end = [], 0
    for start in sorted(grouped):
        event = sorted(grouped[start])
        if start - previous_end >= division / 8:
            tokens.append("DRST")
        for pitch, ticks in event:
            if len(event) > 1: tokens.append("CHD")
            tokens.extend((f"P{pitch:03d}", _duration(ticks / division)))
        previous_end = max(previous_end, max(start + duration for _, duration in event))
    return " ".join(tokens)

_ABC_NOTE = re.compile(r"([_^=]*)([A-Ga-g])([,']*)(\d*(?:/\d*)?)")
_ABC_EVENT = re.compile(r"\[([^\]]+)\](\d*(?:/\d*)?)|([_^=]*)([A-Ga-g])([,']*)(\d*(?:/\d*)?)|([zx])(\d*(?:/\d*)?)")

def _abc(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig")
    unit = .5
    for line in text.splitlines():
        match = re.match(r"\s*L:\s*(\d+)\s*/\s*(\d+)", line)
        if match:
            numerator, denominator = int(match.group(1)), int(match.group(2))
            if numerator <= 0 or denominator <= 0:
                raise ValueError("ABC default note length must be positive")
            unit = 4 * numerator / denominator
    body = "\n".join(line for line in text.splitlines() if not re.match(r"\s*[A-Za-z]:", line))
    body = re.sub(r'"[^"]*"|![^!]*!|%.*', " ", body)
    semitones = dict(zip("CDEFGAB", (0, 2, 4, 5, 7, 9, 11)))

    def note_sort_key(note):
        accidental, letter, marks, _ = note
        octave = (5 if letter.islower() else 4) + marks.count("\'") - marks.count(",")
        pitch = 60 + (octave - 4) * 12 + semitones[letter.upper()]
        pitch += accidental.count("^") - accidental.count("_")
        return pitch

    def append_note(tokens, note, duration_override="", chord=False):
        accidental, letter, marks, length = note
        octave = (5 if letter.islower() else 4) + marks.count("'") - marks.count(",")
        pitch = 60 + (octave - 4) * 12 + semitones[letter.upper()]
        if "^" in accidental:
            pitch += accidental.count("^")
        if "_" in accidental:
            pitch -= accidental.count("_")
        if "=" in accidental:
            pitch = 60 + (octave - 4) * 12 + semitones[letter.upper()]
        if not 0 <= pitch <= 127:
            raise ValueError("ABC note pitch is outside MIDI range 0..127")
        length = duration_override or length
        multiplier = 1.0
        if length:
            if "/" in length:
                numerator, _, denominator = length.partition("/")
                multiplier = (float(numerator) if numerator else 1.0) / (float(denominator) if denominator else 2.0)
            else:
                multiplier = float(length)
            if not math.isfinite(multiplier) or multiplier <= 0:
                raise ValueError("ABC note duration must be finite and positive")
        if chord:
            tokens.append("CHD")
        tokens.extend((f"P{pitch:03d}", _duration(unit * multiplier)))

    tokens = []
    for event in _ABC_EVENT.finditer(body):
        if event.group(1) is not None:
            notes = _ABC_NOTE.findall(event.group(1))
            if len(notes) > 1:
                for note in sorted(notes, key=note_sort_key):
                    append_note(tokens, note, event.group(2), chord=True)
            elif notes:
                append_note(tokens, notes[0], event.group(2))
        elif event.group(3) is not None:
            append_note(tokens, (event.group(3), event.group(4), event.group(5), event.group(6)))
        else:
            tokens.append("DRST")
    return " ".join(tokens)

def encode_file(path: str | Path) -> str:
    source = Path(path)
    if source.suffix.lower() in (".mid", ".midi"): return _midi(source)
    if source.suffix.lower() == ".abc": return _abc(source)
    raise ValueError(f"unsupported music file type: {source.suffix}")

def encode_directory(directory: str | Path, output: str | Path | None = None) -> list[dict[str, str]]:
    root = Path(directory)
    if not root.is_dir(): raise NotADirectoryError(root)
    records = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".mid", ".midi", ".abc"}):
        tokens = encode_file(path)
        if tokens: records.append({"source": path.relative_to(root).as_posix(), "tokens": tokens})
    if output is not None:
        target = Path(output); target.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        for item in records:
            lines.extend((f"# SRC {item['source']}", f"{item['tokens']} # src=file:{item['source']}"))
        target.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return records
