# Symbolic Music Learning

This extension adds symbolic MIDI/ABC learning to BODY OF SECRETS without waveform synthesis or changes to the existing Brain/Ears path.

## Token grammar

Pitch P000-P127; duration D016/D008/D004/D002/D001; rest DRST; chord marker CHD; optional bar marker B. Notes are Pxxx/Dxxx pairs. To make chord boundaries unambiguous without inventing another token, each chord tone is prefixed by CHD: CHD P060 D004 CHD P067 D004. The following unmarked P/D pair is the next melodic event.

MIDI supports PPQ-based SMF format 0/1, note on/off, running status and same-onset polyphonic grouping. SMPTE timing is rejected. ABC covers basic note letters, octave marks, accidentals, simple duration suffixes, bracket chords and z/x rests; tuplets, broken rhythms, inline key changes, key-signature accidental propagation and complex decorations are not interpreted.

## Commands

```bash
body-of-secrets music encode ./midi --output music_data/corpus/symbolic_music.txt
body-of-secrets music train ./midi --work-dir music_data --order 5 --holdout ./holdout_tokens.txt
body-of-secrets music predict --work-dir music_data --context "P060 D004 P064 D004"
body-of-secrets music rollback v001 --work-dir music_data
```

Use --teacher-plugin PLUGIN_NAME with train to enable an installed plugin from Python entry-point group body_of_secrets.music_teachers. It must implement complete(prompt: str) -> str or be a zero-argument factory returning that interface. No provider SDK/network dependency is bundled. LoggedTeacher logs raw response, timestamp, prompt hash and errors to llm_responses.log; exception retries and timeouts are configurable. A timed-out call is not retried because the in-flight provider request cannot be cancelled safely; its daemon worker cannot hold up process shutdown. A still-running timed-out worker prevents further concurrent worker creation, avoiding unbounded thread accumulation.

## Metrics, provenance and snapshots

The active loop appends JSONL metrics to metrics.jsonl: corpus_lines_total, llm_query_rate, llm_rejection_rate, hopfield_hit_rate and ngram_perplexity_on_holdout. Holdout perplexity is null unless --holdout points to a separate token corpus.

Accepted lines carry source, timestamp, prompt hash and SHA-256 comments; provenance.jsonl records the same metadata. Seed imports are idempotent per source file while identical LLM samples are deduplicated against the whole corpus. Teacher continuations are stored together with their originating context so the n-gram learns the conditional transition. Rejected teacher samples go to rejected_samples.log. Snapshots contain n-gram model, motif patterns, exact corpus, provenance manifest, SHA-256 hashes and parent metadata. Rollback verifies hashes before restoring both corpus and provenance manifest plus the CURRENT pointer.

The natural-language n-gram tokenizer is untouched; this music model preserves case and exact token boundaries. The teacher is not part of ordinary inference.

## Integration limits

The existing HopfieldNetwork uses dense Hebbian weights. MotifMemory materializes an actual HopfieldNetwork only for banks up to 128 patterns; larger banks remain a bounded deterministic bipolar motif index. This avoids quadratic memory/time blowups while preserving the configured 5,000-pattern ceiling. The current core has no LRU or motif-registration API, so deterministic frequency ranking is used instead of claiming LRU behavior. Key validation requires an explicit pitch-class set; no key is guessed from context.
