# 5 Senses: Creating a Classical AI System with Neural Models

**Author:** Laila Star Seals  
**Part II:** System Architecture, Component Boundaries, Information Flow, and Memory Design  
**Research area:** Classical artificial intelligence, neuro-symbolic systems, knowledge engineering, neural computation, and information retrieval

> **Editorial status:** This is Part II of the working manuscript. It describes the project's architectural direction and distinguishes documented foundations from proposed interfaces. Illustrative schemas and code are design examples, not claims that those exact interfaces are already implemented.

---

# Part II — The Architecture of 5 Senses

## 14. From an Intellectual Model to an Engineering Architecture

Part I introduced 5 Senses as a system organized around five computational responsibilities: perception, memory, reasoning, association, and expression. These responsibilities provide the conceptual foundation. Part II addresses the engineering problem: how should those responsibilities be represented in software, how should information move between them, and how can the system remain understandable as its capabilities increase?

An architectural model must accomplish more than naming components. It must define their responsibilities, their boundaries, the information they exchange, and the conditions under which one component may rely on another.

A system can contain a neural network, a document archive, an expert system, and a language model without becoming a coherent hybrid architecture. If these components operate independently, duplicate state, or exchange unverified information without a defined contract, the result is simply a collection of unrelated tools.

The objective of 5 Senses is to create a coordinated environment in which each computational method performs a defined operation and contributes a result that can be inspected by the rest of the system.

This requires five architectural principles:

1. **Separation of responsibilities:** each component has a defined purpose.
2. **Explicit information exchange:** components communicate through documented data structures and interfaces.
3. **Preservation of provenance:** information retains its source and transformation history.
4. **Controlled inference:** model predictions, retrieved documents, and logical conclusions remain distinguishable.
5. **Reproducibility:** the same inputs, configurations, and model versions should make it possible to investigate a result.

These principles are more important than selecting a particular framework or programming language. Frameworks change. The responsibility of a memory subsystem, the distinction between evidence and prediction, and the need for reproducible inference do not.

## 15. Architectural Overview

The system can be described as a collection of cooperating subsystems:

- Input and perception.
- Document archive and retrieval.
- Structured knowledge representation.
- Expert rules and symbolic inference.
- Neural model execution.
- Associative memory.
- Language processing.
- Evidence and provenance evaluation.
- Orchestration.
- Response construction.

The five-senses model groups these subsystems according to their function.

| Sense | Architectural responsibility | Representative components |
|---|---|---|
| Perception | Receive and interpret input | Parsers, tokenizers, validators, feature extraction |
| Memory | Retain information | SQLite archive, document metadata, knowledge records |
| Reasoning | Evaluate information | Expert rules, inference procedures, evidence evaluation |
| Association | Identify related patterns | Neural networks, Hopfield memory, similarity methods |
| Expression | Communicate results | Response construction, citations, explanations |

The table describes an architectural classification, not a claim that every subsystem has already been implemented as a complete module.

A subsystem may contribute to more than one responsibility. For example, a neural model may assist perception by classifying an input and association by identifying a related pattern. Its outputs must nevertheless retain their computational identity. A neural prediction must not silently become a verified archive record.

### 15.1 Logical architecture

The following diagram represents the intended organization:

```text
                       USER / APPLICATION
                              |
                              v
                    +-------------------+
                    | INPUT INTERFACE   |
                    +-------------------+
                              |
                              v
                    +-------------------+
                    |    PERCEPTION     |
                    | Parse / Normalize|
                    | Validate / Route |
                    +-------------------+
                              |
                              v
                    +-------------------+
                    |   ORCHESTRATOR    |
                    | Select Operations|
                    | Manage Workflow  |
                    +-------------------+
                       /      |      \
                      /       |       \
                     v        v        v
               +---------+ +--------+ +----------+
               | MEMORY  | | NEURAL | | SYMBOLIC |
               | ARCHIVE | | MODELS | | REASONER |
               +---------+ +--------+ +----------+
                    |          |          |
                    v          v          v
               +---------+ +--------+ +----------+
               |DOCUMENT | |ASSOCIA-| | EXPERT   |
               |RETRIEVAL| |TIVE    | | RULES    |
               +---------+ |MEMORY  | +----------+
                    |      +--------+      |
                    |          |            |
                    +----------+------------+
                               |
                               v
                    +-------------------+
                    | EVIDENCE EVALUATOR|
                    | Source / Conflict |
                    | Uncertainty       |
                    +-------------------+
                               |
                               v
                    +-------------------+
                    |     EXPRESSION    |
                    | Answer / Explain  |
                    | Cite / Qualify    |
                    +-------------------+
                               |
                               v
                         USER / OUTPUT
```

The diagram represents a logical design. It does not require every operation to execute in a fixed sequence. A request may need only one subsystem, or it may require several.

The orchestrator selects the operations required by a task. It should not be treated as an independent source of truth. Its job is coordination, not the creation of unsupported facts.

### 15.2 Why modularity matters

Modularity makes it possible to improve one method without rewriting the entire system.

A new retrieval algorithm should not require changes to the neural model's internal implementation. A different neural network should not require changes to the archive's document schema. A new expert rule should not require a redesign of the response interface.

This is particularly important for a research system. Experiments frequently involve replacing one algorithm, changing a model, comparing two retrieval methods, or disabling one component to determine its contribution.

If the architecture is tightly coupled, these experiments become difficult to conduct and their results become difficult to interpret. A modular architecture makes controlled comparison possible.

## 16. The Input and Perception Subsystem

Perception is the system's entry point. Its responsibility is to transform incoming information into a representation that downstream components can process.

Inputs may include natural-language questions, plain-text documents, structured records, numerical observations, classification examples, previously stored document identifiers, and model-generated candidate outputs.

The first operation should be validation. A system should establish whether an input is present, whether its format is supported, whether its size is within configured limits, and whether required fields are available.

It should not assume that every string is a valid document or that every numerical array is suitable for a neural model.

### 16.1 Input normalization

Normalization prepares an input for processing. For text, this may include encoding validation, Unicode normalization, whitespace handling, optional case normalization, tokenization, language or format identification, and metadata extraction.

Normalization must be controlled because transformations can alter meaning. Case folding may be appropriate for a search index but inappropriate for preserving an original source document. Removing punctuation may help a particular retrieval task but damage quotations or mathematical expressions.

The system should preserve the original input and treat normalized content as a derived representation:

```text
Original input
    |
    +----> Preserved source
    |
    +----> Normalized text
    |
    +----> Search representation
    |
    +----> Model features
```

These representations may be related, but they are not interchangeable.

### 16.2 Task classification and routing

After validation, the system can classify the task.

| Task | Likely processing route |
|---|---|
| Find a document | Archive retrieval |
| Classify a numerical sample | Neural classifier or classical classifier |
| Apply a known decision rule | Expert reasoning |
| Recover a corrupted pattern | Associative memory |
| Explain a historical claim | Retrieval and evidence evaluation |
| Predict a word sequence | N-gram language model |
| Compare competing statements | Retrieval, provenance, and reasoning |

Routing should be based on the task's requirements rather than on the assumption that the most complex model is always preferable.

A direct archive lookup does not require a neural network. A numerical classification problem may not require a historical document search. A question about conflicting sources requires more than a language model's prediction.

The routing component should permit multiple methods to operate together when necessary.

## 17. Memory Architecture: The Archive as Persistent Knowledge Infrastructure

Memory is one of the central elements of 5 Senses.

A neural model stores learned numerical parameters. An archive stores identifiable records. These are different forms of memory and must not be confused.

The archive should retain documents, metadata, source identity, and the relationships between original and derived material.

The project has documented a SQLite-backed archive concept with an API that includes:

```python
Archive(db_path)
```

and operations including:

```python
archive.import_text_file(...)
archive.import_document(...)
archive.list_documents(...)
archive.count()
archive.search(...)
archive.close()
```

These operations provide a foundation for persistent document storage and retrieval. They should not be interpreted as proof that every proposed provenance, rights-management, or evidence-evaluation feature described in this paper is already implemented.

### 17.1 Why SQLite is appropriate

SQLite offers several advantages for a local-first research system:

1. It does not require a separate database server.
2. It stores information in a persistent database file.
3. It supports structured queries and transactions.
4. It can operate without an internet connection.
5. It is suitable for small and medium-sized local knowledge collections.
6. It can support full-text retrieval through its full-text search extensions.

SQLite is not necessarily the best database for every workload. A large distributed archive, a high-concurrency service, or a specialized vector-retrieval environment may eventually require additional storage technologies.

The important design decision is to keep the archive interface separate from the implementation of its storage engine.

### 17.2 Documents and derived records

A document should be treated as an identifiable source object.

A derived record is any representation created from that source, including extracted text, OCR output, normalized text, search tokens, summaries, extracted facts, and model-generated annotations.

The relationship between these objects should be preserved:

```text
SOURCE DOCUMENT
    |
    +----> Extracted text
    |          |
    |          +----> Normalized text
    |          |
    |          +----> Search index
    |
    +----> Metadata record
    |
    +----> Rights assessment
    |
    +----> Evidence references
```

A summary should not replace the source document. An OCR transcript should not be mistaken for an original publication. A model-generated annotation should not become an authenticated quotation.

### 17.3 Proposed document metadata

An expanded document record could include:

```json
{
  "document_id": "stable-document-id",
  "title": "Example source title",
  "author": "Author when known",
  "publisher": "Publisher when known",
  "publication_date": null,
  "edition": null,
  "source_location": "Original source reference",
  "imported_at": "Recorded import timestamp",
  "file_format": "text/plain",
  "sha256": "content checksum",
  "rights_status": "UNKNOWN_HOLD",
  "content_origin": "EXTRACTED",
  "parent_document_id": null
}
```

This is a proposed record shape, not a representation of a verified current database schema.

Metadata fields should be optional when information is unknown. The system must not manufacture an author, publication date, edition, or license merely to fill a database column.

### 17.4 Rights status as a first-class property

A research archive must distinguish access from permission.

A document being publicly downloadable does not establish that it may be redistributed, modified, or used in model training.

The archive should support explicit rights states such as:

- `PUBLIC_DOMAIN_VERIFIED`
- `OPEN_LICENSE_VERIFIED`
- `RESEARCH_ONLY`
- `UNKNOWN_HOLD`
- `RESTRICTED`

Each status should be supported by a record of the evidence used to assign it.

The assessment must consider the relevant jurisdiction, edition, translation, publisher, and electronic transcription. A public-domain underlying work may be distributed in a modern edition containing protected material.

Where the rights status is unknown, the system should preserve the record for review rather than treating it as unrestricted training data.

### 17.5 Archive retrieval

Retrieval allows the system to find relevant documents.

The project direction includes SQLite-backed search and BM25-style ranking. BM25 ranks documents using term-frequency and document-length information rather than simply counting whether a query term appears.

A retrieval result should identify the document, matching passage, location within the document, retrieval score, query, index or retrieval configuration, and source metadata.

A score estimates relevance. It does not establish truth.

A document can be highly relevant to a question and still contain an error. Retrieval therefore supplies candidates for evaluation rather than final authority.

## 18. Structured Knowledge Representation

Documents are not the only form of memory. A system also needs a way to represent individual entities, facts, relationships, and rules.

A structured knowledge record may describe an entity, a property, a relationship, a source, an evidence classification, and a date or period of validity.

For example:

```text
ENTITY:
    Hopfield Network

TYPE:
    Associative Neural Model

RELATED_CONCEPT:
    Content-Addressable Memory

INTRODUCED:
    1982

SOURCE:
    Hopfield, 1982

EVIDENCE_STATUS:
    DOCUMENTED
```

This representation makes the relationship between an entity and its attributes explicit.

### 18.1 Facts must retain their evidence

A fact should not be stored as an isolated sentence when its source can be recorded.

A proposed fact record could contain:

```json
{
  "fact_id": "fact-identifier",
  "subject": "Hopfield Network",
  "predicate": "introduced_in",
  "object": "1982",
  "source_document_id": "source-identifier",
  "source_location": "bibliographic reference",
  "evidence_status": "DOCUMENTED"
}
```

This is an illustrative schema. It does not imply that the current project already implements this exact structure.

The principle is that a fact and its supporting evidence should remain connected. If a source is later found to be unreliable, the system should be able to identify which conclusions depended on it.

### 18.2 Contradictions are data

Two records may disagree. The system should preserve both statements and record the disagreement. It should not silently overwrite one with the other merely because the second record was imported later.

Contradiction handling requires the system to distinguish between a genuine factual disagreement, different interpretations, different calendar systems, different editions or publication dates, a transcription error, an incomplete source, and a claim that has not been independently verified.

The system may rank sources according to documented criteria, but ranking should not erase the underlying records.

## 19. The Symbolic Reasoning Subsystem

Reasoning is responsible for applying explicit rules and evaluating relationships.

A symbolic system can represent conditions and consequences in a form that is inspectable.

A simple production rule may be expressed as:

```text
RULE: classify_bird

IF:
    entity.category == "robin"
    AND entity.is_living == true

THEN:
    entity.type = "animal"

EXPLANATION:
    A robin is classified as an animal under the
    system's declared knowledge rules.
```

The example is deliberately simple. A real knowledge base must define its terms, assumptions, rule scope, and exceptions.

### 19.1 Production rules

A production system commonly uses condition-action rules. A rule is activated when its conditions match the current working state. Its action may add a conclusion, update a temporary record, or request additional information.

A simplified rule engine can be described as:

```python
class Rule:
    def __init__(self, name, condition, action):
        self.name = name
        self.condition = condition
        self.action = action

    def matches(self, facts):
        return self.condition(facts)

    def apply(self, facts):
        if self.matches(facts):
            return self.action(facts)
        return None
```

This code is illustrative, not a verified implementation of the project's current reasoning engine. A production implementation should define rule validation, execution limits, conflict resolution, explanation records, and error handling.

### 19.2 Forward chaining

Forward chaining begins with known facts and applies rules to derive additional facts.

```text
FACT:
    Robin is a bird.

RULE:
    Every bird is an animal.

DERIVED FACT:
    Robin is an animal.
```

The system continues applying applicable rules until no new conclusions are produced or a defined execution limit is reached.

### 19.3 Backward chaining

Backward chaining begins with a question or goal and works backward to determine whether the required premises can be established.

```text
GOAL:
    Is Robin an animal?

REQUIRED:
    Is Robin a bird?

RULE:
    Every bird is an animal.

RESULT:
    The goal is supported if the required premise is established.
```

Backward chaining is useful for question answering and expert consultation because it focuses computation on the conclusion being investigated.

### 19.4 Conflict resolution

A rule engine may encounter several applicable rules. Some may produce compatible conclusions. Others may conflict.

Possible strategies include rule priority, specificity, source authority, temporal validity, explicitly declared exceptions, or returning multiple conclusions for review.

No single strategy is universally appropriate. For research questions, preserving a conflict may be more responsible than automatically selecting one result.

### 19.5 Explanation records

Every significant inference should be capable of producing an explanation record:

```text
CONCLUSION:
    Robin is an animal.

INPUT FACT:
    Robin is a bird.

RULE:
    Every bird is an animal.

RESULT:
    Rule successfully applied.

STATUS:
    DERIVED
```

The explanation should identify whether the conclusion was retrieved, directly supplied, or derived. A retrieved fact, a rule-derived conclusion, and a neural prediction may all be useful, but they are not the same kind of result.

## 20. Neural Model Subsystem

The neural subsystem provides learned computational capabilities. Its responsibilities may include classification, feature extraction, numerical prediction, similarity estimation, and other tasks for which learned representations are appropriate.

The architecture should not assume that all neural models have the same input format or output structure. A classifier, an autoencoder, a recurrent network, and an associative network have different computational contracts.

Each model should declare its purpose and supported input and output forms.

### 20.1 Model interface

A proposed model interface can be expressed conceptually as:

```python
class ModelAdapter:
    def load(self, model_path):
        raise NotImplementedError

    def validate_input(self, value):
        raise NotImplementedError

    def predict(self, value):
        raise NotImplementedError

    def describe(self):
        raise NotImplementedError
```

The adapter isolates model execution from the rest of the system. The orchestrator should not need to know the internal layout of every neural network. It should know which operation is available, what inputs are required, what outputs are returned, and what limitations apply.

### 20.2 Model identity and reproducibility

A model result is meaningful only when the model that produced it can be identified.

A model record should ideally preserve its identifier, architecture description, version, weight checksum, input and output dimensions, training-data reference, training configuration, random seed where applicable, software and runtime versions, and known limitations.

The weights alone are not a complete record of a model.

Two systems may load the same numerical weights but produce different behavior because of different preprocessing, activation functions, normalization, numerical precision, or output interpretation. Reproducibility therefore requires preserving the surrounding computation.

### 20.3 Training and inference are separate responsibilities

Training changes model parameters. Inference uses existing parameters to calculate an output.

These operations should be separated in the architecture. A running research system should not unexpectedly retrain a model merely because it receives a new query.

Training should use a controlled dataset, a declared objective, a recorded configuration, and an evaluation procedure. Inference should identify the model version and return its result without silently changing the model.

### 20.4 Differentiable training

A neural network can only learn through an optimization process when the loss function remains connected to the model's computation graph.

If a loss value is detached from the model output and then wrapped in a new tensor with gradient tracking enabled, that operation does not restore the missing computational relationship. The optimizer may execute, but the model parameters will not receive the intended gradients through that detached path.

The correct engineering principle is to preserve the computation graph from model output through loss calculation and backward propagation.

The loss must also express the intended task. A training objective that rewards an undesirable property, such as simply increasing output magnitude, may optimize successfully while producing a worse model.

The architecture must therefore treat loss validation and evaluation as essential parts of neural model development.

## 21. Associative Memory Subsystem

Associative memory is the bridge between learned neural relationships and the system's broader memory environment.

A Hopfield network provides a classical example. In its traditional form, the network contains interconnected units with weighted relationships. Its state evolves through an update procedure until it reaches a stable configuration.

The purpose is to recover a stored pattern from an incomplete or corrupted input.

### 21.1 Retrieval by pattern completion

Suppose a binary pattern is stored:

```text
1 0 1 1 0 1 0 0
```

A partial or corrupted input may be:

```text
1 0 1 ? 0 1 1 0
```

The associative memory attempts to recover a compatible stored pattern.

This is not equivalent to searching for a document containing the same sequence of characters. The memory operates through learned relationships among its units.

### 21.2 Associative memory is not factual authority

A stable recalled pattern may be mathematically valid within the network and still be unrelated to a true external fact.

The associative subsystem should return a candidate pattern together with information about the retrieval process:

```text
MODEL:
    HopfieldMemory-v1

INPUT:
    Partial pattern identifier

OUTPUT:
    Recovered pattern identifier

CONVERGENCE:
    Stable state reached

ITERATIONS:
    Recorded iteration count

STATUS:
    ASSOCIATIVE_CANDIDATE
```

The candidate can then be compared with known patterns or documentary records. This prevents the system from treating an internally recovered association as proof.

### 21.3 Measuring associative memory

Associative memory should be evaluated with controlled patterns. Relevant measurements include exact pattern recovery, bit-error rate, recovery from partial inputs, recovery from noisy inputs, false or spurious attractors, convergence behavior, retrieval latency, and capacity under defined conditions.

The number of patterns stored is not sufficient by itself to establish memory quality. The system must also measure whether those patterns can be recovered reliably under the intended operating conditions.

## 22. Classical Language Processing

The language subsystem should distinguish between understanding a query, retrieving information, and generating or predicting text. These operations are related but different.

A compact n-gram language model provides a useful classical baseline.

For a trigram model, the next-token probability is estimated using the preceding two tokens:

[
P(w_n mid w_{n-2}, w_{n-1})
]

The model can be trained by counting observed sequences and applying an appropriate smoothing method.

### 22.1 Why retain n-gram models?

N-gram models have limitations. They have difficulty representing long-range dependencies, their vocabulary can become sparse, and their predictions depend heavily on the training corpus.

Nevertheless, they remain useful in 5 Senses because they provide a compact statistical baseline, inspectable token counts, simple training procedures, low computational requirements, offline operation, and a point of comparison for neural language models.

The objective is not to claim that an n-gram model is equivalent to a modern large language model. It is to preserve a classical language-processing capability that can be tested independently.

### 22.2 Language models do not establish truth

A language model estimates which sequence is statistically likely under its learned distribution. It does not independently establish whether a historical event occurred, whether a quotation is authentic, or whether a scientific claim is supported.

This distinction applies to neural language models as well as n-gram models. 5 Senses should use language models to assist with language tasks, not to replace documentary verification.

## 23. Evidence Evaluation and Provenance

Evidence evaluation connects the archive, reasoning subsystem, and output process. Its purpose is to determine what kind of support exists for a statement.

A useful system must distinguish at least four cases:

1. A statement is directly supported by a source.
2. A statement is derived from other supported statements.
3. A statement is predicted by a model.
4. A statement remains unresolved.

The project has used truth and evidence classifications including:

```text
OFFICIAL
CONSENSUS
PLAUSIBLE
SPECULATIVE
UNKNOWN
```

These classifications should be treated as an explicit evidence vocabulary, not as numerical probabilities.

For example, `CONSENSUS` should require a defined basis for identifying agreement among relevant sources. `OFFICIAL` should identify the authority responsible for the statement. `PLAUSIBLE` should not be confused with verified. `UNKNOWN` should remain available when the evidence is insufficient.

### 23.1 Evidence is not confidence

A neural model may return a confidence score of 0.92. That value describes a property of the model's output under its own scoring procedure. It does not mean that a claim has a 92 percent probability of being historically true.

Similarly, a retrieval system may return a high relevance score. That score does not establish the accuracy of the retrieved document.

Evidence evaluation must consider the actual source material.

### 23.2 Source comparison

A useful evidence evaluator should be able to compare records by source identity, publication history, directness of evidence, relevant passage, agreement or disagreement, temporal relevance, known limitations, and rights and authenticity status.

The evaluator should preserve the source records and the basis for its assessment. A conclusion may change when new evidence is added. The earlier assessment should remain traceable rather than disappearing without explanation.

### 23.3 Provenance chain

The proposed provenance chain is:

```text
ORIGINAL SOURCE
      |
      v
SOURCE METADATA
      |
      v
IMPORTED DOCUMENT
      |
      v
EXTRACTED / TRANSFORMED CONTENT
      |
      v
RETRIEVED PASSAGE
      |
      v
EXTRACTED OR DERIVED CLAIM
      |
      v
EVIDENCE ASSESSMENT
      |
      v
FINAL RESPONSE
```

Every derived stage should retain a relationship to its predecessor. This makes it possible to investigate where a claim originated and whether the transformation process may have introduced an error.

## 24. The Orchestration Layer

The orchestrator coordinates the components. It receives a task description, determines which operations are required, invokes the appropriate subsystems, collects their results, and sends the results to evidence evaluation and expression.

The orchestrator should not become a hidden monolithic reasoning engine. Its responsibilities should remain limited and explicit.

### 24.1 Request lifecycle

A typical request may follow this process:

1. Receive the input.
2. Validate its structure.
3. Identify the task.
4. Select the required subsystems.
5. Execute the selected operations.
6. Collect results.
7. Evaluate evidence and conflicts.
8. Construct the response.
9. Preserve appropriate execution metadata.

A simplified conceptual interface is:

```python
class Orchestrator:
    def handle(self, request):
        validated = self.validate(request)
        task = self.classify_task(validated)
        results = self.execute(task, validated)
        assessment = self.evaluate(results)
        return self.express(assessment)
```

This is an architectural illustration, not a claim that this exact class currently exists in the repository.

### 24.2 Avoiding unnecessary computation

Not every request should activate every subsystem.

A direct document count should use the archive. A numerical classification task should use the appropriate classifier. A simple rule question should use the symbolic subsystem. A pattern-completion experiment should use associative memory. A historical question should use retrieval and evidence evaluation.

Activating unnecessary components increases latency and creates more opportunities for error. The orchestrator should select the smallest adequate workflow.

### 24.3 Failure handling

A subsystem may fail or return incomplete information. The orchestrator should distinguish invalid input, unsupported operation, missing model, missing document, empty retrieval result, model execution failure, rule conflict, incomplete evidence, and unavailable optional subsystem.

A failure should not be converted into a fabricated answer.

If the archive is unavailable, the system should not claim to have checked it. If a neural model cannot load, the system should not report a prediction. If a rule cannot be evaluated because a required fact is missing, the system should identify the missing premise.

Graceful failure is part of a reliable architecture.

## 25. The Expression Subsystem

Expression is responsible for converting evaluated results into a response that a person or another application can use.

It should preserve the distinction between retrieved information, directly supplied information, rule-derived conclusions, neural predictions, associative candidates, and unresolved questions.

A response should not make all of these appear equally certain.

### 25.1 Response structure

A proposed response record could contain:

```json
{
  "answer": "The supported conclusion.",
  "evidence_status": "DOCUMENTED",
  "sources": [
    {
      "document_id": "source-identifier",
      "location": "relevant passage"
    }
  ],
  "reasoning": [
    "Relevant inference or comparison"
  ],
  "model_outputs": [],
  "uncertainties": [],
  "limitations": []
}
```

This is a proposed output contract, not a verified current API response. The structure permits a user interface to display the answer, supporting sources, reasoning, and limitations separately.

### 25.2 Explanation without false certainty

An explanation should be proportional to the available evidence.

When the system has one source, it should not claim broad consensus. When two sources disagree, it should identify the disagreement. When a model provides a prediction without documentary support, it should identify the result as a prediction.

For example:

```text
The archive contains one relevant source.

The source supports the following statement.

No independent corroborating source was located.

The conclusion is therefore recorded as provisional.
```

This is not a weakness. It is an indication that the system has preserved the difference between what it found and what it can establish.

## 26. Data Exchange Contracts

A modular architecture requires stable contracts. A component should know what information it receives and what it must return.

| Component | Input | Output |
|---|---|---|
| Perception | Raw input | Validated and normalized request |
| Archive | Query or document operation | Document records and passages |
| Knowledge representation | Entity or fact data | Structured records |
| Rule engine | Facts and rules | Derived conclusions and explanations |
| Neural adapter | Model-compatible input | Prediction or learned representation |
| Associative memory | Partial pattern | Recovered candidate |
| Evidence evaluator | Claims and sources | Evidence assessment |
| Orchestrator | Validated task | Coordinated execution result |
| Expression | Evaluated result | User-facing response |

The contracts should be versioned. Changing a field name, return type, or status vocabulary can affect several components. Interface changes should therefore be treated as engineering decisions and covered by tests.

### 26.1 Stable identifiers

Documents, facts, models, rules, and execution records should have stable identifiers, such as:

```text
document_id
fact_id
model_id
rule_id
execution_id
```

Identifiers make objects addressable; their associated metadata explains what those objects represent. Identifiers should not be used as substitutes for provenance.

### 26.2 Explicit status values

Status values should be defined centrally. A system should not allow one module to use `UNKNOWN` to mean missing data while another uses it to mean an evaluated but unresolved claim.

The status vocabulary should document its meaning, permitted transitions, which component may assign the status, whether supporting evidence is required, and whether the status is provisional.

This prevents semantic drift as the project grows.

## 27. Local-First Operation and System Boundaries

5 Senses is intended to support local-first operation.

Local-first does not mean that every capability must run on every computer or that external services can never be used. It means the system's core knowledge and processing capabilities should not depend on a permanent remote service.

The archive should remain accessible locally. Classical rules should remain executable without an external language model. Supported neural models should be loadable from controlled local files. Optional external services should not become the only means of accessing the project's knowledge.

### 27.1 Offline operation

An offline workflow should be capable of loading the local archive, searching stored documents, applying available rules, running available local models, recording execution results, and producing an answer based on the available evidence.

If a requested capability is not available offline, the system should identify that limitation. It should not pretend that an external lookup occurred.

### 27.2 Optional external models

An external model may be useful for additional language generation or specialized analysis. However, an external model should be treated as an optional provider behind an explicit interface.

The archive should not silently transmit its contents to an external provider. Data transfer should be governed by a clear policy and user authorization.

The local system should retain control over which documents, inputs, and results are shared.

### 27.3 Reproducibility and isolation

Research experiments should be capable of running in a controlled environment.

A benchmark should record the model version, dataset version, configuration, random seed, and relevant software versions. Where possible, experiments should avoid hidden network dependencies, unrecorded downloads, and automatic changes to model parameters.

This makes results easier to reproduce and audit.

## 28. Security and Integrity of the Knowledge Environment

A knowledge archive is only useful if its records can be trusted to retain their identity and integrity. The system should therefore treat file integrity, source identity, and execution history as architectural concerns.

### 28.1 Checksums

A cryptographic checksum such as SHA-256 can identify whether a file's contents have changed. The checksum should be calculated over the original file bytes and stored with the corresponding source record.

A checksum does not prove that a source is authentic or accurate. It establishes a way to detect whether the file being examined matches the recorded content.

### 28.2 Original and derived content

Original files should be preserved separately from transformed files.

If a document is normalized, OCR-processed, or summarized, the derived artifact should have its own identity and a recorded relationship to the original.

This makes it possible to reproduce transformations and identify where errors may have entered the process.

### 28.3 Controlled model files

Neural weights and model configuration files should be treated as executable research assets.

The system should identify the model, verify expected file integrity where checksums are available, and validate input and output dimensions before execution.

It should not assume that an arbitrary file is a valid or safe model merely because it has a familiar extension.

## 29. Architecture Testing

The architecture must be tested at several levels.

- **Unit testing:** verifies an individual component's behavior.
- **Contract testing:** verifies that components agree on input and output structures.
- **Integration testing:** verifies that multiple components work together.
- **Regression testing:** verifies that changes do not unintentionally alter established behavior.
- **Reproducibility testing:** verifies that a recorded experiment can be repeated under its declared conditions.
- **Failure testing:** verifies that missing or invalid inputs produce controlled failures rather than fabricated results.

### 29.1 Example integration scenario

Consider a question that requires a historical document and a rule-based conclusion.

The test should:

1. Load a known document into the archive.
2. Verify that the document can be retrieved.
3. Identify a passage containing the relevant statement.
4. Create or load a structured fact referencing that passage.
5. Apply the appropriate rule.
6. Verify the derived conclusion.
7. Verify that the explanation identifies the rule and supporting fact.
8. Verify that the final response retains the source reference.

A test that checks only the final sentence is insufficient. The intermediate records are necessary to establish that the system reached the result through the intended process.

### 29.2 Testing neural components

Neural models require additional tests:

- Input-shape validation.
- Output-shape validation.
- Deterministic inference where the implementation supports it.
- Parameter loading and checksum verification.
- Gradient-flow tests for trainable models.
- Loss-function tests.
- Baseline comparison.
- Seed stability.
- Performance measurement.

A test should distinguish a model that loads successfully from a model that learns successfully. Likewise, a model that produces an output is not necessarily a model that performs its intended task accurately.

## 30. Architectural Limitations and Open Decisions

The proposed architecture is deliberately modular, but modularity does not eliminate difficult engineering decisions.

### 30.1 Knowledge representation

The system must determine how much information belongs in relational tables, how much should be represented as structured facts, and whether a graph representation is justified for particular workloads.

A graph database should not be introduced merely because the project contains relationships. The choice should follow measured query and maintenance requirements.

### 30.2 Neural model selection

Different tasks may require different models. The system should not adopt a single neural architecture as a universal solution. Each model should be selected according to the task, available training data, computational constraints, and evaluation results.

### 30.3 Retrieval quality

BM25 provides a useful baseline, but retrieval performance depends on the corpus, tokenization, query formulation, document structure, and ranking configuration.

The project must measure whether retrieval is sufficiently accurate for its intended research tasks.

### 30.4 Evidence assessment

Evidence classification requires explicit criteria. The labels `OFFICIAL`, `CONSENSUS`, `PLAUSIBLE`, `SPECULATIVE`, and `UNKNOWN` are useful only if the project defines how they are assigned and how disagreements are handled.

### 30.5 Orchestration complexity

A growing collection of components can make routing difficult. The orchestrator must remain testable and should not become a collection of undocumented special cases.

### 30.6 Performance

A hybrid architecture may be more capable than a single-method system for some tasks, but it can also be slower.

The project must measure the cost of retrieval, model execution, inference, evidence evaluation, and response construction. No performance advantage should be claimed before the relevant experiments have been performed.

## 31. Architectural Summary

The architecture of 5 Senses is based on a separation of computational responsibilities.

Perception receives and prepares information. Memory retains documents and structured knowledge. Reasoning applies explicit rules and evaluates relationships. Association identifies related patterns through neural and associative methods. Expression communicates the result and its limitations.

The orchestrator coordinates these responsibilities without replacing them.

The archive supplies documentary material. Neural models supply learned estimates and representations. Symbolic reasoning supplies explicit derivations. Associative memory supplies pattern recovery. Evidence evaluation connects conclusions to their sources.

The most important architectural distinction is that these components do not have identical authority.

A neural prediction is not a verified document. A retrieved passage is not automatically true. A rule-derived conclusion depends on its premises. An associative memory may recover a pattern that does not correspond to an external fact.

The architecture must preserve these differences.

This is the basis of a disciplined hybrid AI system: not the accumulation of algorithms, but the controlled cooperation of different methods.

Part III will examine the classical reasoning tradition in greater depth, including production systems, expert systems, search, knowledge representation, inference, and the engineering of explicit rules.

---

**End of Part II — System Architecture, Component Boundaries, Information Flow, and Memory Design.**

**Manuscript status:** Parts I and II drafted. Implementation-specific claims and proposed interfaces remain subject to repository verification and experimental validation.
