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
| **Eyes / Ears** | Sensory (documents / speech)                      | Placeholder |
| **Spine / Blood / Heart / Soul** | Governance, provenance, integrity, ethics | Partial / Present |

---

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

## Optional external offline document corpus (MCP)

BODY OF SECRETS can query `ljrseals-dev/refactored-spoon` as a separate local MCP
service. The service owns acquisition, processing, and its own index; BODY OF
SECRETS does not vendor its runtime package or copy remote documents into its
Archive. Search results retain the upstream title and source path as provenance.

Install `refactored-spoon` in its own environment from its repository root,
acquire and index the corpus there, then configure BODY OF SECRETS:

```bash
# In the refactored-spoon checkout / environment:
pip install -e .
python -m offline_doc_mcp.cli acquire --service project_gutenberg
python -m offline_doc_mcp.cli index --root . --db data/index.db

# In the BODY OF SECRETS environment:
pip install -e '.[mcp-client]'
export BOS_OFFLINE_DOC_MCP_COMMAND="python -m offline_doc_mcp.mcp_server"
export BOS_OFFLINE_DOC_MCP_CWD="/absolute/path/to/refactored-spoon"
body-of-secrets ask "your question" --mode ARCHIVE
```

The MCP server is started on demand over stdio for each query. Set
`BOS_OFFLINE_DOC_MCP_TIMEOUT` (seconds, default 15) to adjust the request
deadline. If the command is unset, MCP is disabled. If the service is missing,
times out, or returns an error, the Brain falls back to the local Archive.
CLASSICAL, ARCHIVE, and AUTO retrieval never invoke an LLM provider. The MCP
client extra is optional and requires Python 3.11+; the core package retains
Python 3.10 compatibility.

The upstream acquisition adapters may be placeholders depending on the source;
successful acquisition/indexing must be confirmed in the refactored-spoon
environment before expecting search results.
