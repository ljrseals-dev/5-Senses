# BODY OF SECRETS — Architecture

## Overview

BODY OF SECRETS is organized as an anatomical system. Each major capability is a named subsystem with clear responsibilities and interfaces.

```text
User
  │
  ▼
Interface (CLI)
  │
  ▼
Nerves  ──►  Brain (language + reasoning + expert logic)
  │              │
  │              ├── Modes (CLASSICAL / RESEARCH / ARCHIVE / AUDIT / HYBRID)
  │              ├── Evidence tagging
  │              └── Truth-status reconciliation
  │
  ├── Memory   (associative KV store)
  ├── Archive  (documents + BM25 + provenance)
  ├── Neural   (Hopfield, MLP)
  ├── Expert   (rule engine)
  ├── Language (n-gram models)
  ├── Sensory  (Eyes, Ears) — future
  ├── Muscle   (execution / providers)
  ├── Blood    (provenance)
  ├── Heart    (integrity)
  ├── Spine    (rules & governance)
  └── Soul     (ethics & purpose)
```

## Classical-first answering path

1. **Archive retrieval** — BM25 search over imported documents; provenance attached.
2. **Expert rules** — Deterministic pattern → answer rules (Hopfield, PDP, Kohonen, n-gram, provenance…).
3. **LLM fallback** (optional) — Only if a provider is configured and no classical answer is found.

This ordering keeps the system useful with zero network access.

## Component status (v0.1)

| Subsystem   | Status     | Implementation notes                                      |
|-------------|------------|-----------------------------------------------------------|
| Brain       | Working    | Classical-first Engine; modes; evidence; truth-status     |
| Interface   | Working    | Full CLI (`ask`, `import`, `search`, `memory`, `ngram`, `neural`, `status`) |
| Archive     | Working    | SQLite + BM25, provenance, snippet generation             |
| Memory      | Working    | Persistent KV with source + tags                          |
| Expert      | Working    | Forward-chaining rule engine + default classical rules    |
| Language    | Working    | Word/char n-gram model, generation, continuations, perplexity |
| Neural      | Working    | Discrete Hopfield + pure-Python MLP (XOR demo)            |
| Sensory     | Placeholder| Eyes / Ears                                               |
| Security    | Placeholder| Encryption & stronger audit                               |

## Design principles

1. **Provider isolation** — Domain logic never imports a vendor SDK.
2. **Provenance first** — Every claim carries its source or epistemic tag.
3. **Classical first** — Measurable 1980s architectures before modern models.
4. **Local-first** — Fully offline operation is a hard requirement.
5. **Auditability** — The system records what it knew and when.

## Next targets

- Stronger document ingestion (PDF, structured metadata)
- Persistent audit log
- Expand expert rule base from the sample corpus
- Optional C++ core for neural components (later)
