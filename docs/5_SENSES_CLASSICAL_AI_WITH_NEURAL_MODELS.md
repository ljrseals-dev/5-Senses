# 5 Senses: Creating a Classical AI System with Neural Models

**Author:** Laila Star Seals  
**Manuscript status:** Working manuscript — Part I of a planned 30,000-word paper  
**Research area:** Classical artificial intelligence, neural computation, knowledge representation, associative memory, information retrieval, and hybrid system architecture

> **Editorial note:** This repository copy contains the foundational opening part of the manuscript, not the completed 30,000-word paper. Subsequent parts will expand the architecture, implementation, experiments, evaluation, limitations, and bibliography. Descriptions of project capabilities must be checked against the implementation before publication; proposed capabilities are identified as design proposals.

## Abstract

Artificial intelligence has developed through several intellectual traditions. Symbolic reasoning, expert systems, search algorithms, statistical learning, neural networks, and information retrieval have each offered different answers to the problem of creating machines capable of performing intelligent tasks. These traditions are often described as competing paradigms. Yet practical problems frequently require their capabilities simultaneously. A system may need to recognize patterns, retrieve historical information, compare competing claims, apply explicit rules, preserve the origin of its knowledge, and communicate a reasoned result. No single computational technique is automatically sufficient for all these responsibilities.

This paper presents **5 Senses**, a classical artificial intelligence system designed around the integration of explicit knowledge structures and neural models. Its central proposition is that useful machine intelligence need not depend exclusively on a large, opaque, end-to-end neural model. Instead, an intelligent system can be constructed from cooperating components: a knowledge archive, symbolic and expert reasoning, statistical language processing, associative memory, neural networks, evidence evaluation, and an orchestration layer responsible for selecting and coordinating methods.

The system takes inspiration from classical AI research, particularly symbolic knowledge representation, production systems, expert systems, connectionist learning, and early statistical language models. It also incorporates modern engineering principles where they strengthen reliability, including local-first operation, persistent provenance, structured document storage, explicit uncertainty labels, reproducible experiments, and modular software boundaries.

The five-senses metaphor is used as an architectural model. It describes five complementary information-processing responsibilities: **perception, memory, reasoning, association, and expression**. These are not claims that software literally possesses biological senses or consciousness. They are functional categories through which information enters, is retained, interpreted, connected, and communicated.

The paper argues that the combination of classical and neural methods can provide a practical alternative to systems that rely on neural generation alone. Neural networks can identify patterns and construct useful representations, while symbolic structures can preserve explicit relationships and rules. Retrieval systems can provide documentary evidence. Associative memory can recover related patterns. Expert rules can constrain decisions. Provenance can make it possible to inspect where information originated and how a conclusion was reached.

The resulting design is intended to be inspectable, extensible, and capable of operating without a permanent external service. It is not presented as a finished general intelligence. Rather, it is a research architecture and engineering program for building a disciplined classical AI system that uses neural models as components within a broader reasoning environment.

**Keywords:** classical artificial intelligence; neural networks; neuro-symbolic systems; expert systems; knowledge representation; associative memory; Hopfield networks; statistical language models; information retrieval; BM25; provenance; local-first AI; uncertainty; hybrid reasoning.

## 1. Introduction: The Need for a Different Kind of AI Architecture

Artificial intelligence is often discussed as though the history of the field were a sequence of technologies in which each new generation makes the preceding generation obsolete. Symbolic AI is described as an early approach, neural networks as its replacement, and large language models as the latest and perhaps final stage of development.

This interpretation is incomplete.

The history of artificial intelligence is not simply a succession of abandoned ideas. It is a continuing investigation into different ways of representing information, learning relationships, searching for solutions, and producing useful decisions. Some problems are naturally expressed as logical rules. Others require statistical estimation. Some are best approached through pattern recognition, while others require the retrieval and examination of documentary evidence.

A system designed to perform several of these tasks must be capable of using different methods without confusing their responsibilities.

The central design question behind 5 Senses is therefore:

**Can a practical artificial intelligence system combine classical knowledge engineering and neural computation while retaining explicit memory, inspectable evidence, and control over its own information-processing methods?**

The answer proposed in this paper is yes, provided the architecture is modular and its components have clearly defined responsibilities.

A neural model should not automatically become the system's entire memory. A document archive should not be expected to perform every form of reasoning. A collection of rules should not be mistaken for a complete model of the world. A statistical language model should not be assumed to know whether a statement is true merely because it can produce a plausible sentence.

These distinctions are fundamental.

5 Senses approaches intelligence as a coordinated computational process. Its components are intended to work together, with each method contributing what it does best.

A neural model may identify a pattern in an input. A retrieval subsystem may locate relevant documents. An associative memory may recover related stored patterns. A symbolic component may apply a rule. An evidence evaluator may distinguish a verified statement from an unconfirmed proposition. An output component may then communicate the result with appropriate qualifications.

This architecture does not eliminate uncertainty. It makes uncertainty an explicit part of the system.

## 2. What Is Meant by Classical Artificial Intelligence?

The term *classical artificial intelligence* is used in different ways. In this paper, it primarily refers to the family of methods associated with explicit representations, formal rules, symbolic manipulation, search, planning, and knowledge-based problem solving.

Classical AI asks how a machine can represent facts and relationships in forms that permit systematic manipulation.

A computer can represent the statement:

- Every bird is an animal.
- A robin is a bird.

A rule-based inference process can then derive that a robin is an animal. The significance is not the complexity of this particular example. It is that the reasoning process can be represented explicitly, inspected, and tested.

A symbolic system can record the rule, identify the facts used, and show the inference that produced its conclusion. This differs from a neural network in which a decision may depend on a large collection of learned numerical parameters whose individual contributions are difficult to interpret.

Classical AI includes several important methodological families:

1. **Logical reasoning:** deriving conclusions from formal premises.
2. **Production systems:** applying condition-action rules to a changing knowledge state.
3. **Expert systems:** encoding domain-specific knowledge and decision procedures.
4. **Search algorithms:** exploring possible states or solutions.
5. **Planning:** constructing sequences of actions that achieve specified goals.
6. **Knowledge representation:** encoding entities, attributes, relationships, and constraints.
7. **Heuristic reasoning:** using practical estimates to guide problem solving.

These approaches are not interchangeable. A production rule is not the same thing as a search algorithm, and a knowledge graph is not itself a complete inference engine. A successful architecture must preserve these distinctions.

### 2.1 Historical foundations

The intellectual roots of artificial intelligence include mathematical logic, computation theory, cybernetics, cognitive science, and early models of neural activity.

McCulloch and Pitts demonstrated how simplified neuron-like elements could be described using formal logic. Their work helped establish a connection between neural models and computation. Later research explored perceptrons, symbolic reasoning, search, and methods for representing knowledge.

The field was formally established as an identifiable research discipline during the 1950s. Early researchers investigated whether computers could perform activities associated with intelligence, including theorem proving, game playing, problem solving, and language processing.

By the 1960s and 1970s, researchers had developed increasingly sophisticated methods for representing knowledge and solving specialized problems. Expert systems became particularly important because they demonstrated that carefully encoded domain knowledge could produce useful results in constrained areas.

The 1980s were especially significant for the development of both knowledge-based systems and connectionist models. The period should not be understood as belonging exclusively to symbolic AI. Neural learning, distributed representations, associative memory, and expert systems were all important research directions.

The later development of machine learning did not make explicit knowledge representation irrelevant. Instead, it created additional opportunities and additional problems. Systems capable of learning patterns from data still need mechanisms for managing facts, resolving contradictions, evaluating evidence, and communicating limitations.

The historical lesson for 5 Senses is that intelligence can be investigated through multiple computational traditions. Their integration is a legitimate design objective, not a rejection of either tradition.

## 3. Why Neural Models Belong Inside a Classical System

A classical AI architecture does not need to reject neural networks. Neural models can provide capabilities that are difficult to obtain through hand-authored rules alone.

A neural network consists of computational units connected through weighted relationships. During training, the system adjusts those weights according to an optimization procedure. The resulting model can learn patterns from examples rather than requiring every relevant relationship to be written as an explicit rule.

This capability is valuable for:

- Pattern classification.
- Feature extraction.
- Similarity estimation.
- Approximate prediction.
- Sequence modeling.
- Associative reconstruction.
- Learning relationships from numerical data.

The 1986 work by Rumelhart, Hinton, and Williams on learning representations through backpropagation is a major reference point. It described how adjusting network connection weights could reduce output error while allowing internal hidden units to develop useful representations of the task.

This is an important distinction: a neural model does not merely memorize a list of answers. Its learned parameters can encode distributed relationships that support generalization across examples.

However, neural models have limitations. They can learn undesirable correlations. Their outputs can be sensitive to training data and optimization choices. They can produce confident errors. A learned representation does not automatically provide a documentary source for a claim. A model's internal numerical state is not equivalent to a carefully maintained historical archive.

For these reasons, 5 Senses treats neural computation as a capability within the larger system rather than as a substitute for every other component.

### 3.1 Neural models as specialized instruments

The architecture treats a neural model in much the same way that an engineer treats a specialized instrument. An instrument is useful because it performs a defined operation. It should not be asked to perform unrelated operations simply because it is sophisticated.

A classification network may estimate whether an input belongs to a particular category. It should not independently determine the legal status of a document, establish the authenticity of a historical quotation, or decide whether a source is licensed for training.

Those responsibilities require other forms of information and evaluation.

The neural component can contribute an estimate. The reasoning system can examine that estimate in context. The archive can retrieve supporting material. The provenance layer can preserve the source of the material. The final response can communicate the distinction between an estimate and a verified fact.

### 3.2 Preserving model behavior

Neural systems must be evaluated against their actual architecture and behavior.

A test that merely records a handful of expected outputs is insufficient when the research objective is to recover or preserve an existing model. A meaningful comparison should examine the model's internal structure, parameter organization, intermediate activations, output behavior, and response to controlled inputs.

This is especially important when historical or archived neural code is being studied.

The objective should be to understand the original computation before attempting to improve it. Replacing an unusual architecture with a familiar modern network may make implementation easier, but it can destroy the very behavior the research is intended to recover.

For 5 Senses, the guiding principle is:

**Recover the architecture, repair the training, and do not replace the underlying computational idea without evidence.**

That principle also applies to the larger system. Its classical components should be understood and tested before they are discarded or replaced.

## 4. The Five Senses as a Computational Metaphor

The name 5 Senses describes five functional responsibilities in the proposed system.

It is a metaphor for information processing, not a claim that the software possesses biological perception, subjective experience, or consciousness.

### 4.1 Perception — receiving and interpreting input

Perception is the entry point for information.

A system must be able to receive text, structured records, numerical data, and other supported inputs. It must identify their formats, extract relevant features, and determine which processing methods are appropriate.

Perception can include text normalization, tokenization, metadata extraction, classification, feature construction, basic validation, and input-format detection.

The purpose is to transform raw input into a form that other components can process.

Perception should not silently turn an uncertain interpretation into a verified fact. An extracted statement remains an extracted statement until it has been evaluated.

### 4.2 Memory — retaining information and its origins

Memory is the persistent knowledge environment.

A useful AI system requires more than a temporary conversation context. It needs a structured way to retain documents, facts, metadata, and the relationships among them.

The 5 Senses project uses a local archive concept with SQLite-backed document storage and search. Its intended responsibilities include document import, document listing, counting, and retrieval.

The archive is not merely a collection of text. It should preserve enough metadata to answer questions such as:

- Where did this document originate?
- Which edition or version was imported?
- What is its publication date?
- Who is identified as its author?
- What rights status has been established?
- Was the content transformed?
- Is the current text original, extracted, normalized, or OCR-derived?

The archive must also distinguish a source document from a statement extracted from that document.

A source may contain an incorrect statement. A quotation may be incomplete. Two sources may contradict each other. Memory must preserve those distinctions rather than flattening all imported information into one undifferentiated body of knowledge.

### 4.3 Reasoning — applying rules and evaluating relationships

Reasoning is the process of evaluating information and deriving conclusions.

It includes explicit rules, logical relationships, expert knowledge, statistical estimates, and procedures for handling uncertainty.

A reasoning component might determine that a conclusion follows from two established premises, that a proposed answer conflicts with an existing record, that a source is insufficient to support a claim, that a question requires retrieval rather than generation, or that a result should be classified as speculative.

The objective is not to force every problem into formal logic. Instead, the system should identify which reasoning method is appropriate and preserve the assumptions behind its use.

### 4.4 Association — recovering related patterns

Association connects information that may not be directly linked by an explicit rule.

This responsibility is particularly relevant to neural networks and associative memory.

A classical associative memory can retrieve a stored pattern from a partial or corrupted input. Hopfield's 1982 work on neural networks introduced an influential model in which network states evolve toward stable configurations. These stable states can be interpreted as stored patterns or memories.

Associative retrieval is not the same as documentary retrieval.

A document search system finds records based on textual or statistical relevance. An associative memory attempts to recover a pattern from learned relationships. Both are useful, but they answer different questions.

The architecture should therefore keep the two operations separate.

### 4.5 Expression — communicating the result

Expression is the output responsibility.

A system that calculates a result but cannot explain its origin is difficult to evaluate. A system that produces fluent language without preserving the distinction between evidence and inference is difficult to trust.

Expression should communicate the answer, the evidence supporting it, the reasoning method used, important assumptions, uncertainty or disagreement, and relevant limitations.

It should not disguise an unverified conclusion as a documented fact.

## 5. Cooperation Without Confusion

The five responsibilities are most useful when they cooperate without being collapsed into a single process.

Consider a question about a historical event.

The perception component receives the question and identifies its subject. Memory searches the archive for relevant documents. Association identifies related names, concepts, or patterns. Reasoning compares the retrieved information and applies relevant rules. An evidence evaluator determines which claims are supported. Expression produces a response that identifies what is supported, what is inferred, and what remains uncertain.

The process can be represented as:

**Input → Perception → Memory and Association → Reasoning → Evidence Evaluation → Expression**

This is a conceptual flow rather than a requirement that every request pass through every component in exactly the same order.

A simple arithmetic problem may require little or no archival retrieval. A historical research question may depend heavily on memory and provenance. A classification problem may use a neural model. A constrained decision may rely on explicit expert rules.

The architecture should select methods according to the problem.

A hybrid system is not automatically superior merely because it contains more components. Every component introduces complexity, maintenance obligations, and potential failure modes. The objective is to use the smallest set of methods that adequately solves the task while preserving the ability to inspect the result.

## 6. An Operational Definition of Intelligence

The project requires an operational definition of intelligence.

For this paper, intelligence is not defined as consciousness or human equivalence. It is defined as the ability of a computational system to perform useful information-processing tasks with appropriate adaptation, memory, reasoning, and evaluation.

A system demonstrates useful intelligent behavior when it can:

1. Receive and interpret an input.
2. Identify relevant information.
3. Retrieve stored knowledge.
4. Recognize relationships and patterns.
5. Apply appropriate rules or models.
6. Evaluate the quality of supporting evidence.
7. Produce a result suited to the task.
8. Preserve enough information to reproduce or inspect its process.

This definition is intentionally practical.

It allows the system to be evaluated through measurable capabilities rather than philosophical claims.

A system that retrieves the correct source and explains its limitations may be more useful for historical research than a system that produces a more elaborate but unsupported answer. Similarly, a neural classifier that accurately identifies a pattern may be valuable even if it cannot explain every internal numerical operation.

The system's components should be judged according to their responsibilities, and the integrated system should be judged according to whether the components cooperate reliably.

## 7. Symbolic Knowledge and Explicit Representation

Symbolic representation gives a system a way to store information in structured forms.

A simple representation might be:

```text
ENTITY: Hopfield Network
TYPE: Associative Neural Model
INTRODUCED: 1982
RELATED_CONCEPT: Content-Addressable Memory
SOURCE: Hopfield, 1982
STATUS: DOCUMENTED
```

The benefit is not that this representation captures every detail of the underlying research. Its benefit is that the information is explicit and can be inspected.

A symbolic representation can be connected to rules:

```text
IF:
    entity.type == "Associative Neural Model"

AND:
    entity.has_property("content-addressable retrieval")

THEN:
    classify(entity, "Associative Memory")
```

In a larger system, rules must be designed carefully. A rule should have a defined scope, a known source where applicable, and a test demonstrating its behavior.

Rules can also conflict. One source may support a statement while another contradicts it. A reasoning engine must not silently discard the conflict.

For this reason, 5 Senses should treat knowledge as something that can be revised when new evidence appears.

## 8. Expert Systems and the Knowledge Engineering Problem

Expert systems were an important achievement of classical AI because they demonstrated that specialized knowledge could be encoded into computer programs.

A traditional expert system often separates a knowledge base, an inference engine, working memory, an explanation facility, and a user interface.

The knowledge base contains facts and rules. The inference engine applies those rules. Working memory contains the current problem state. An explanation facility can identify which rules contributed to a result.

This organization offers useful lessons for 5 Senses.

The archive can serve as a source of documentary information, but it should not be confused with the expert knowledge base. The expert system should contain explicit rules and their conditions. The inference engine should apply those rules. The explanation layer should retain the chain of relevant decisions.

A central difficulty in expert-system development is knowledge acquisition. Human expertise is not always available in a form that can be directly translated into rules. Experts may disagree, omit assumptions, or rely on tacit knowledge.

The system must therefore distinguish between a rule supported by a documented source, a rule supplied by a domain expert, a rule proposed as a hypothesis, a rule introduced as an engineering convenience, and a rule that has not yet been validated.

This prevents the system's own design assumptions from becoming mistaken for universal facts.

## 9. Neural Networks and Distributed Representations

Neural networks provide another form of representation.

Instead of storing every relationship as a named rule, a network adjusts numerical parameters in response to examples. Information can be distributed across many units and weights.

This can make neural models effective at recognizing patterns that would be difficult to describe exhaustively.

The 1986 backpropagation paper by Rumelhart, Hinton, and Williams is particularly relevant because it demonstrated how hidden units could develop internal representations through the minimization of an error measure.

The distinction between explicit and distributed representation is important.

An explicit representation may state that a robin is a bird and a bird is an animal. A neural model may learn that certain features tend to occur together and use those relationships to classify an unfamiliar example.

These methods can cooperate.

A neural model may suggest that two documents concern similar topics. A symbolic component may then examine whether they refer to the same person, event, or concept. The archive can preserve both source records. The evidence evaluator can determine whether the documents actually support the same claim.

The neural model contributes association. The symbolic component contributes explicit relationships. The archive contributes evidence.

## 10. Associative Memory as a Bridge Between Classical and Neural AI

Associative memory connects neural computation with the broader idea of machine memory.

A conventional database retrieves information through a query. A content-addressable memory retrieves information through similarity to a stored pattern.

Hopfield networks offer a historical and mathematical foundation for this concept.

In a simplified Hopfield network, units are connected through weighted relationships. The network evolves according to an update rule until it reaches a stable state. Stored patterns correspond to stable configurations under appropriate conditions.

This provides a model of memory that differs from ordinary file storage.

However, associative retrieval has limitations. Stored patterns can interfere with one another. Retrieval may converge to an unintended stable state. Capacity depends on network structure and learning conditions. A recovered pattern is not automatically a verified statement about the world.

Therefore, associative memory should be treated as a candidate-retrieval mechanism, not an authority.

A recalled association should be checked against the archive or another appropriate source before being promoted to a factual conclusion.

## 11. Statistical Language Processing and Retrieval

Language processing provides another important foundation.

A classical language model can estimate the probability of a token or word sequence based on previous context. An n-gram model, for example, estimates the next token using a limited history of preceding tokens.

This approach is smaller and more inspectable than a contemporary large neural language model, although it has significant limitations.

N-gram systems can be useful for basic language prediction, frequency analysis, simple text classification, historical language experiments, baseline comparisons, and offline operation with modest resources.

Retrieval is a separate problem.

A document archive must identify which records are relevant to a query. Statistical retrieval methods such as BM25 provide a principled way to rank documents according to term occurrence, document length, and collection statistics.

The probabilistic relevance framework described by Robertson and Zaragoza provides an important account of BM25 and related retrieval methods.

For 5 Senses, retrieval should be treated as a core knowledge operation. The system should be able to find the documents that support an answer rather than relying entirely on a model's learned parameters.

A strong retrieval result is not necessarily a true result. Ranking estimates relevance to the query, not the truth of every statement in a document. Evidence evaluation remains necessary.

## 12. The Importance of Provenance

Provenance is the recorded history of information.

Without provenance, an archive can become a collection of disconnected claims. It may be impossible to determine whether a statement came from a primary source, a secondary publication, an OCR extraction, a generated summary, or an unverified user contribution.

A responsible archive should preserve:

- Original source identity.
- Source location.
- Author and publisher when known.
- Publication date or edition.
- Import date.
- File format.
- Cryptographic checksum.
- Rights and licensing status.
- Transformation history.
- Relationship between original and derived files.

The original source should remain unchanged. Cleaned text, OCR output, normalized text, and summaries should be stored as derived artifacts with links back to the source.

This is particularly important for historical corpora and digitized books. A text file that appears to be public domain may contain a modern editorial introduction, a copyrighted translation, or a rights notice that applies to the electronic edition.

The system should not assume that a document is unrestricted merely because it is accessible online.

## 13. Foundational Architecture: A Coordinated Information Process

The foundational argument of 5 Senses is that artificial intelligence should be designed as a coordinated system of capabilities rather than identified with one particular model family.

Classical AI contributes explicit rules, structured knowledge, search, and inspectable reasoning. Neural models contribute learned representations and pattern recognition. Associative memory contributes content-addressable retrieval. Statistical language processing contributes compact language models. Information retrieval contributes a method for finding relevant documents. Provenance and evidence evaluation provide the discipline necessary to distinguish information from established knowledge.

The five-senses architecture gives these capabilities a common organization:

- **Perception** receives and interprets information.
- **Memory** retains information and its origins.
- **Reasoning** evaluates facts, rules, and relationships.
- **Association** recovers related patterns.
- **Expression** communicates results and limitations.

The purpose is not to recreate a human brain or to claim that a software system possesses consciousness. It is to build an artificial intelligence environment in which different computational methods can work together under explicit engineering controls.

The next part develops the architecture in greater detail, including component boundaries, information flow, data structures, memory organization, model selection, and the separation between evidence retrieval and neural inference.

## Preliminary References

1. Hopfield, J. J. (1982). “Neural Networks and Physical Systems with Emergent Collective Computational Abilities.” *Proceedings of the National Academy of Sciences*, 79(8), 2554–2558. https://doi.org/10.1073/pnas.79.8.2554
2. Rumelhart, D. E., Hinton, G. E., & Williams, R. J. (1986). “Learning Representations by Back-Propagating Errors.” *Nature*, 323, 533–536. https://doi.org/10.1038/323533a0
3. Robertson, S., & Zaragoza, H. (2009). “The Probabilistic Relevance Framework: BM25 and Beyond.” *Foundations and Trends in Information Retrieval*, 3(4), 333–389. https://doi.org/10.1561/1500000019
4. McCulloch, W. S., & Pitts, W. (1943). “A Logical Calculus of the Ideas Immanent in Nervous Activity.” *The Bulletin of Mathematical Biophysics*, 5, 115–133.
5. Newell, A., & Simon, H. A. (1976). “Computer Science as Empirical Inquiry: Symbols and Search.” *Communications of the ACM*, 19(3), 113–126. https://doi.org/10.1145/360018.360022
6. Buchanan, B. G., & Shortliffe, E. H. (Eds.). (1984). *Rule-Based Expert Systems: The MYCIN Experiments of the Stanford Heuristic Programming Project*. Addison-Wesley.
7. Russell, S. J., & Norvig, P. *Artificial Intelligence: A Modern Approach*. Pearson. The edition used should be specified in the final bibliography.
8. Minsky, M. (Ed.). (1968). *Semantic Information Processing*. MIT Press.
9. Rosenblatt, F. (1962). *Principles of Neurodynamics: Perceptrons and the Theory of Brain Mechanisms*. Spartan Books.
10. Hopfield, J. J. (1984). “Neurons with Graded Response Have Collective Computational Properties Like Those of Two-State Neurons.” *Proceedings of the National Academy of Sciences*, 81(10), 3088–3092.

---

**End of Part I — foundational manuscript.**
