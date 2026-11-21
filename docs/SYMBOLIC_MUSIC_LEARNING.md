# Symbolic Music Learning

This extension adds symbolic MIDI/ABC learning to BODY OF SECRETS without waveform synthesis or changes to the existing Brain/Ears path.

## Scope and token grammar

- Pitch: P000 through P127.
- Duration: D016 (sixteenth), D008 (eighth), D004 (quarter), D002 (half), D001 (whole).
- Rest: DRST; chord marker: CHD; optional bar marker: B.
- A note is a Pxxx/Dxxx pair. A chord is CHD followed by at least two pitch/duration pairs sorted by pitch.
- MIDI input supports PPQ-based SMF format 0/1, note on/off, running status and simultaneous-note grouping. SMPTE timing is rejected.
- ABC support covers basic letters, octave marks, accidentals and simple duration suffixes. Tuplets, broken rhythms, inline key changes and complex decorations are not interpreted.

## Commands

\`\`\`bash
python -m body_of_secrets.music.cli encode ./midi --output music_data/corpus/symbolic_music.txt
python -m body_of_secrets.music.cli train ./midi --work-dir music_data --order 5
python -m body_of_secrets.music.cli predict --work-dir music_data --context "P060 D004 P064 D004"
python -m body_of_secrets.music.cli rollback v001 --work-dir music_data
\`\`\`

The existing natural-language n-gram tokenizer is deliberately untouched: this model preserves case and token boundaries.

## Provenance, snapshots and teacher plugins

Accepted lines carry source and SHA-256 comments; provenance.jsonl records timestamp, source, content hash and optional prompt hash. Invalid teacher data is written to rejected_samples.log. Snapshots contain the model, motif bank, exact corpus, SHA-256 manifest and parent metadata. Rollback verifies hashes before restoring the corpus and CURRENT pointer.

Teacher plugins are optional Python entry points in group body_of_secrets.music_teachers. They must implement complete(prompt: str) -> str or provide a zero-argument factory returning such an object. No provider SDK or network dependency is bundled. LoggedTeacher records raw response, timestamp, prompt hash and errors, with timeout/retry handling. Teacher output is untrusted and is validated before corpus ingestion.

## Integration limits

The existing HopfieldNetwork uses dense Hebbian weights. MotifMemory therefore builds an actual HopfieldNetwork only for banks up to 128 patterns; larger banks remain a bounded deterministic bipolar motif index. This avoids quadratic memory/time blowups while preserving the configured 5,000-pattern ceiling. The current core has no LRU or motif-registration API, so frequency-ranked deterministic retention is used instead of claiming LRU behavior. Key validation requires an explicit pitch-class set; no key is guessed from context. The LLM is never part of normal inference.
