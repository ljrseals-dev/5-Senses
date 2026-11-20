# BODY OF SECRETS

**Classical Intelligence & Language Architecture**

A private, local-first knowledge and language engine inspired by the organizational and historical themes in James Bamford’s *Body of Secrets*.

It combines 1980s-style classical AI (associative memory, rule-based expert systems, n-gram models, Hopfield networks, multilayer perceptrons), modern information retrieval, provenance tracking, and a clean interface for optional modern language models.

> This is an original design. It is **not** a reconstruction of any classified system.

---

## Quick start

```bash
# Install (editable)
pip install -e ".[dev]"

# Status
body-of-secrets status

# Import sample classical-AI notes
body-of-secrets import data/sample_corpus/

# Search
body-of-secrets search "Hopfield energy capacity"

# Ask (classical-first — works offline)
body-of-secrets ask "What is a Hopfield network?"
body-of-secrets ask "Explain Parallel Distributed Processing"

# Classical neural demos
body-of-secrets neural hopfield
body-of-secrets neural mlp

# n-gram language model
body-of-secrets ngram --train data/sample_corpus/hopfield_notes.txt --generate --length 30

# Associative memory
body-of-secrets memory put hopfield.capacity 0.15
body-of-secrets memory get hopfield.capacity
```

Optional hybrid mode (LLM): set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`.

---

## Anatomical Architecture

| Subsystem     | Responsibility                                      | Status (v0.1)      |
|---------------|-----------------------------------------------------|--------------------|
| **Brain**     | Language processing, reasoning, expert-system logic | Working            |
| **Memory**    | Historical knowledge and associative recall         | Working (KV store) |
| **Archive**   | Local documents, BM25 search, provenance            | Working            |
| **Expert**    | Rule-based expert system                            | Working            |
| **Language**  | n-gram statistical language models                  | Working            |
| **Neural**    | Hopfield + minimal MLP                              | Working            |
| **Eyes**      | Document / image interpretation                     | Placeholder        |
| **Ears**      | Speech / audio                                      | Placeholder        |
| **Spine**     | Rules & governance                                  | Partial (modes)    |
| **Blood**     | Provenance tracking                                 | Working (tags)     |
| **Heart**     | Integrity / truth-status                            | Working            |
| **Soul**      | Ethics & purpose constraints                        | Present            |

---

## Design Principles

- **Local-first** — Runs completely offline. No telemetry.
- **Provenance by default** — Every factual claim carries its source or epistemic tag.
- **Classical first** — Start with measurable 1980s architectures; modern LLMs are optional plugins.
- **Provider isolation** — Domain logic never talks directly to a vendor SDK.
- **Truth-status discipline** — Explicit vocabulary: `OFFICIAL | CONSENSUS | PLAUSIBLE | SPECULATIVE | UNKNOWN`.
- **Auditability** — Full history of what the system knew and when.

---

## Project Layout

```text
body-of-secrets/
├── body_of_secrets/
│   ├── brain/          # Engine, modes, evidence, truth-status, providers
│   ├── archive/        # SQLite + BM25 document store
│   ├── memory/         # Persistent associative KV store
│   ├── expert/         # Rule engine
│   ├── language/       # n-gram models
│   ├── neural/         # Hopfield + MLP
│   ├── interface/      # CLI
│   └── ...
├── data/sample_corpus/ # Starter classical-AI notes
├── tests/
└── docs/
```

---

## Development

```bash
make install   # pip install -e ".[dev]"
make test      # pytest
make lint      # ruff + mypy
```

---

## Recommended Reading

1. *Parallel Distributed Processing* (Rumelhart & McClelland, 1986)
2. *Self-Organization and Associative Memory* (Kohonen)
3. *The Fifth Generation*
4. DARPA Strategic Computing materials
5. *The Puzzle Palace* / *Body of Secrets* (Bamford) — institutional inspiration only

See `docs/READING_LIST.md` and `docs/ARCHITECTURE.md`.

---

## License

MIT. See `LICENSE`.

Not affiliated with any government agency, the International Baccalaureate Organization, or any LLM provider.
