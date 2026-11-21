# Symbolic Music Learning

This extension adds symbolic MIDI/ABC learning to BODY OF SECRETS without waveform synthesis or changes to the existing Brain/Ears path.

## Token grammar

Pitch P000-P127; duration D016/D008/D004/D002/D001; rest DRST; chord marker CHD; optional bar marker B. Notes are Pxxx/Dxxx pairs. To make chord boundaries unambiguous without inventing another token, each chord tone is prefixed by CHD: CHD P060 D004 CHD P067 D004. The following unmarked P/D pair is the next melodic event.

MIDI supports PPQ-based SMF format 0/1, note on/off, running status and same-onset polyphonic grouping. SMPTE timing is rejected. ABC covers basic note letters, octave marks, accidentals and simple duration suffixes; tuplets, broken rhythms, inline key changes and complex decorations are not interpreted.

## Commands

\`\`\`bash
body-of-secrets music encode ./midi --output music_data/corpus/symbolic_music.txt
body-of-secrets music train ./midi --work-dir music_data --order 5
body-of-secrets music predict --work-dir music_data --context "P060 D004 P064 D004"
body-of-secrets music rollback v001 --work-dir music_data
\`\`\`

Use --teacher-plugin PLUGIN_NAME with train to enable an installed plugin from Python entry-point group body_of_secrets.music_teachers. It must implement complete(prompt: str) -> str or be a zero-argument factory returning that interface. No provider SDK/network dependency is bundled. LoggedTeacher logs raw response, timestamp, prompt hash and errors to llm_responses.log; timeout/retries are configurable.

## Provenance and snapshots

Accepted lines carry source and SHA-256 comments; provenance.jsonl records timestamp, source, content hash and optional prompt hash. Rejected teacher samples go to rejected_samples.log. Snapshots contain n-gram model, motif patterns, exact corpus, SHA-256 manifest and parent metadata. Rollback verifies hashes before restoring the corpus and CURRENT pointer.

The natural-language n-gram tokenizer is untouched; this music model preserves case and exact token boundaries. The teacher is not part of ordinary inference.

## Integration limits

The existing HopfieldNetwork uses dense Hebbian weights. MotifMemory materializes an actual HopfieldNetwork only for banks up to 128 patterns; larger banks remain a bounded deterministic bipolar motif index. This avoids quadratic memory/time blowups while preserving the configured 5,000-pattern ceiling. The current core has no LRU or motif-registration API, so deterministic frequency ranking is used instead of claiming LRU behavior. Key validation requires an explicit pitch-class set; no key is guessed from context.
