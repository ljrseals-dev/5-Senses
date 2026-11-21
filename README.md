# 5-Senses: BODY OF SECRETS 🧠

**A classical AI laboratory inspired by the foundational research of the 1980s, built for today.**

Combining neural networks, Hopfield associative memory, expert systems, statistical language models, and private knowledge archives.

**No generic chatbot.** Classical intelligence. Transparent reasoning. Local-first architecture.  
Your knowledge, your control.

**Learn. Reason. Remember. Verify.**

🔗 https://github.com/ljrseals-dev/5-Senses

---

## What this is

BODY OF SECRETS (packaged as 5-Senses) is a private, local-first classical intelligence engine. It is deliberately **not** another large-language-model wrapper.

It implements and combines:

- Multilayer perceptrons and Hopfield associative memory (1980s neural computation)
- Rule-based expert systems with explicit provenance
- n-gram statistical language models
- BM25 document archive with source tracking
- Truth-status discipline (`OFFICIAL | CONSENSUS | PLAUSIBLE | SPECULATIVE | UNKNOWN`)
- Fully offline operation by default

Modern LLMs are optional plugins only.

---

## Quick start

```bash
pip install -e ".[dev]"

# Status
body-of-secrets status

# Import the sample corpus (classical AI notes + public-domain Britannica volume + disease-origin consensus notes)
body-of-secrets import data/sample_corpus/

# Search
body-of-secrets search "Hopfield energy"
body-of-secrets search "Brescia"

# Ask (classical-first — works with zero network)
body-of-secrets ask "What is a Hopfield network?"
body-of-secrets ask "Who started West Nile virus and what are the 1900 early spells?"
body-of-secrets ask "origin of HIV"

# Classical neural demos
body-of-secrets neural hopfield
body-of-secrets neural mlp

# n-gram
body-of-secrets ngram --train data/sample_corpus/hopfield_notes.txt --generate
```

---

## Anatomical Architecture

| Subsystem     | Responsibility                                      | Status      |
|---------------|-----------------------------------------------------|-------------|
| **Brain**     | Language + reasoning + expert logic                 | Working     |
| **Memory**    | Associative / key-value store                       | Working     |
| **Archive**   | Local documents + BM25 + provenance                 | Working     |
| **Expert**    | Rule engine (classical AI + verified origin facts)  | Working     |
| **Language**  | n-gram statistical models                           | Working     |
| **Neural**    | Hopfield network + minimal MLP                      | Working     |
| **Eyes**       | Document / image sensing                           | Placeholder |
| **Ears**       | Optional local MSD MusicNN tag features             | Experimental; parity and tag quality unverified |
| **Spine / Blood / Heart / Soul** | Governance, provenance, integrity, ethics | Partial / Present |

---


## Ears: optional MSD MusicNN

The Ears integration is an optional local music-tag feature extractor. It
preserves the classical MLP, Hopfield, Expert, Archive, and n-gram architecture;
it does not generate audio or replace those components.

Install the optional dependencies and provide the checkpoint yourself (the
weights are deliberately not redistributed by this repository):

```bash
pip install -e ".[musicnn,audio]"
```

```python
from body_of_secrets.sensory.musicnn_msd import load_msd_musicnn
from body_of_secrets.sensory.musicnn_frontend import audio_file_to_patches
from body_of_secrets.sensory.musicnn_adapters import predict_msd_tags

model = load_msd_musicnn("/local/path/MSD_musicnn_optimized_fp16.pt")
patches, _ = audio_file_to_patches("/local/path/track.wav")
analysis = predict_msd_tags(model, patches)
for tag in analysis.mean_scores:
    print(tag.label, tag.probability)
```

The loader is local-file-only. Predictions are model-generated candidate
annotations with UNKNOWN truth status. Numerical equivalence, preprocessing
parity, and musical tag quality are separate, currently unverified gates.
Human-confirmed labels are required before the MLP, Hopfield, or n-gram
learning adapters accept examples. See
[docs/EARS_MSD_CHECKPOINT.md](docs/EARS_MSD_CHECKPOINT.md) for provenance,
licensing, and verification status.

## Included knowledge (sample corpus)

- Classical AI notes: Hopfield, Kohonen SOM, Parallel Distributed Processing
- Verified scientific consensus notes: West Nile virus, HIV/AIDS origins, SARS-CoV-2 origins
- **Encyclopaedia Britannica, 11th Edition, Volume 4 Part 3** (Project Gutenberg public-domain text, sourced via andrehacker/mapred testdata)

---

## Design principles

- Local-first, zero telemetry
- Provenance on every factual claim
- Classical architectures first; modern models optional
- Provider isolation (domain logic never talks directly to a vendor SDK)
- Explicit truth-status vocabulary
- Fully auditable

---

## Development

```bash
make install
make test
make lint
```

---

## License

MIT. See `LICENSE`.

This project is an original design. It is not affiliated with any government agency, intelligence service, or commercial LLM provider.

#ArtificialIntelligence #ClassicalAI #NeuralNetworks #OpenSource #AIResearch
