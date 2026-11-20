5 Senses: Creating a Classical AI System with Neural Models

A Comprehensive Research Thesis on the Integration of Neural Computation, Symbolic Reasoning, Associative Memory, and Evidence-Based Knowledge

---

Author: Laila Star Seals

Research Area: Artificial Intelligence, Knowledge Representation, Neural Computation, and Information Retrieval

Document Type: Full Research Thesis

Citation Style: APA 7th Edition

---

Abstract

Artificial intelligence has developed through several computational traditions that are frequently treated as competing approaches rather than complementary mechanisms. Symbolic artificial intelligence represents knowledge through explicit structures, rules, and logical relationships, enabling inspectable reasoning and formal inference (Marra et al., 2024). Connectionist systems learn statistical representations through networks of adjustable computational units, capturing patterns that resist manual specification (Rumelhart et al., 1986). Associative memory systems retrieve stored patterns through relationships between distributed representations, supporting content-addressable recall from partial or corrupted inputs (Hopfield, 1982). Information retrieval systems locate relevant material within collections of documents, providing candidate evidence for further examination (Robertson & Zaragoza, 2009). These approaches solve different classes of problems, yet an intelligent system operating over complex knowledge often needs to coordinate them.

This thesis investigates the design principles of 5 Senses, a proposed classical artificial intelligence architecture that combines neural models with symbolic reasoning, associative computation, structured knowledge storage, language processing, and evidence evaluation. Its central proposition is that learning and reasoning should not be treated as interchangeable operations. Neural models can estimate patterns, identify associations, and transform data into useful representations. Symbolic mechanisms can represent explicit relationships, apply rules, identify contradictions, and expose the steps by which conclusions are reached. Retrieval and provenance mechanisms can connect those conclusions to the source material from which they were derived.

The thesis argues that integration should preserve the distinct computational responsibilities of each method. A neural prediction must not automatically become a verified fact. A retrieved document must not automatically become authoritative evidence. A symbolic inference must not be treated as correct merely because its rules executed successfully. Each operation requires an explicit representation of its inputs, assumptions, uncertainty, and limitations.

Research in neuro-symbolic computing provides the theoretical foundation for this investigation (Marra et al., 2024; Wang et al., 2025; Yu et al., 2023). Research on associative memory, neural representation learning, information retrieval, and data provenance provides additional foundations (Buneman et al., 2001; Hopfield, 1982; Robertson & Zaragoza, 2009; Rumelhart et al., 1986).

The research objective is to determine whether a carefully structured hybrid system can improve the reliability, traceability, and inspectability of knowledge processing without sacrificing the adaptive capabilities of neural computation. The thesis develops a conceptual architecture, defines research questions, establishes an evaluation strategy, and distinguishes proposed capabilities from verified implementation.

Keywords: classical artificial intelligence, neuro-symbolic computing, neural networks, symbolic reasoning, associative memory, expert systems, knowledge representation, information retrieval, provenance, evidence evaluation.

---

1. Introduction

1.1 The Problem: Learning Is Not the Same as Knowing

A computational system can recognize a pattern without understanding the conditions under which that pattern should be accepted as true. This distinction, seemingly simple, carries profound implications for the design of artificial intelligence systems that operate over knowledge.

A neural network may identify a relationship between two variables because the relationship appears repeatedly in its training data (Rumelhart et al., 1986). The network learns statistical regularities, adjusting its internal parameters to minimize prediction error across observed examples. However, the network does not learn why the relationship exists, under what conditions it might fail, or whether the observed correlation reflects a genuine causal mechanism or an artifact of the training distribution.

A retrieval system may return a document because its terminology resembles a query (Robertson & Zaragoza, 2009). The system ranks documents according to relevance scores computed from term frequencies, document lengths, and other statistical features. A high-ranking document is relevant to the query, but relevance does not establish accuracy, authority, or currency. The document may contain errors, outdated information, or unsupported interpretations.

A rule engine may derive a conclusion because a collection of formal conditions has been satisfied (Marra et al., 2024). The engine applies logical rules to premises, producing conclusions that follow validly from the given information. However, logical validity does not guarantee factual correctness. If a premise is false, the conclusion may be validly derived yet factually wrong.

These operations establish different things. Pattern recognition establishes that an input resembles previously encountered data. Retrieval establishes that a document is relevant under a particular ranking method. Rule execution establishes that a conclusion follows from specified premises and rules. None of these operations, independently, establishes that a conclusion is true in the world.

This distinction is fundamental to the design of 5 Senses. The system should not treat all computational outputs as equivalent forms of knowledge. It should preserve the differences between observations and interpretations, statistical predictions and logical conclusions, retrieved information and verified evidence, stored facts and inferred relationships, and confidence estimates and demonstrated correctness.

The distinction matters because errors can propagate when one computational subsystem transfers its output to another without preserving its origin or epistemic status. According to Marra et al. (2024), neuro-symbolic systems must carefully manage the interface between learned representations and symbolic reasoning to avoid conflating different types of computational products.

Consider a neural classifier that identifies a document as describing a particular historical event. The classification may be useful for locating the document. It does not establish that the document's account of the event is accurate. A retrieval subsystem can locate supporting and conflicting material. A knowledge representation subsystem can record the claims and their relationships. A reasoning subsystem can evaluate whether a conclusion follows from available premises. A provenance subsystem can preserve the documents and passages supporting each claim (Buneman et al., 2001).

The architectural question is therefore not simply how to combine neural networks and symbolic rules. It is how to coordinate different computational operations without confusing their outputs. This requires explicit representation of what each component produces, what assumptions underlie its outputs, what uncertainty accompanies its predictions, and what limitations constrain its applicability.

1.2 Historical Foundations and the Research Gap

The history of artificial intelligence reveals recurring tensions between symbolic and connectionist approaches, each emphasizing different aspects of intelligence and knowledge representation.

Symbolic approaches represent problems through formal structures and explicit operations. Their strengths include structured representation, rule execution, and the ability to inspect the premises of a derivation. According to Yu et al. (2023), symbolic systems provide transparency and interpretability that connectionist systems often lack. A symbolic derivation can be examined step by step, with each inference justified by explicit rules applied to explicit premises.

However, symbolic approaches face significant limitations. Acquiring and maintaining extensive knowledge structures requires substantial expert effort. The brittleness that can arise when real-world information does not match predefined representations remains a persistent challenge. Real-world knowledge is often uncertain, incomplete, and context-dependent in ways that resist clean formalization.

Connectionist approaches represent information through distributed numerical parameters. Rumelhart, Hinton, and Williams (1986) demonstrated how back-propagation could adjust network weights to learn useful internal representations. This breakthrough enabled systems to capture regularities that are difficult to express through manually specified rules. Neural networks could learn from examples, generalize to novel inputs, and adapt to new data distributions.

Hopfield's (1982) work on recurrent neural networks established an important model of content-addressable memory, in which a partial or corrupted pattern can lead toward a stored configuration. This provided a different computational mechanism from conventional document retrieval or explicit rule lookup. The network dynamics naturally perform pattern completion, recovering stored memories from noisy or incomplete cues.

These approaches should not be collapsed into one general concept of intelligence. They have different assumptions, failure modes, and evaluation criteria. A neural network's success is measured by its generalization performance on held-out data. A symbolic system's success is measured by its logical correctness and coverage of the problem domain. These metrics are not interchangeable.

Modern neuro-symbolic research examines ways to combine neural learning with symbolic representation and inference. According to Marra et al. (2024), the field has evolved from early statistical relational learning through increasingly sophisticated integration mechanisms. Wang et al. (2025) survey data- and knowledge-driven neuro-symbolic computing, identifying patterns in how neural and symbolic components can be composed. Yu et al. (2023) examine neural-symbolic learning systems, focusing on how learning and reasoning can be integrated.

These works establish that integration is an active research field, not an entirely new idea introduced by 5 Senses. The contribution of this thesis must therefore be defined more narrowly: a particular architecture and method for coordinating learning, memory, reasoning, retrieval, and evidence evaluation, subject to implementation and experimental verification.

The research gap that 5 Senses addresses concerns the explicit management of epistemic status across heterogeneous computational components. While existing neuro-symbolic systems combine neural and symbolic operations, they often leave implicit the boundaries between different types of computational products. 5 Senses proposes that these boundaries should be explicitly represented and maintained throughout the system's operation.

1.3 Central Research Problem

Many hybrid AI designs focus on combining a neural model with a symbolic component. However, the existence of both components does not by itself establish meaningful integration.

A system may contain a neural classifier, a database, and a rule engine while still operating as three loosely connected programs. If the classifier cannot communicate the uncertainty of its prediction, if the database cannot preserve the origin of its records, or if the rule engine cannot distinguish verified premises from tentative ones, the architecture remains conceptually fragmented.

The central research problem is:

How can a classical AI system coordinate neural learning, associative memory, symbolic inference, document retrieval, and evidence evaluation while preserving the provenance, uncertainty, and computational responsibility of each operation?

This question requires the architecture to specify how information moves between components, how one component is permitted to influence another, and how the system handles incomplete or contradictory information. It demands explicit answers to questions that are often left implicit in system design:

· When a neural model produces a prediction, how is that prediction represented when it enters the symbolic reasoning component?
· When a symbolic inference depends on a retrieved document, how is the chain of dependence preserved?
· When two sources conflict, how does the system represent and reason about the conflict?
· When a component fails or produces low-confidence output, how does the system prevent error propagation?

According to Wang et al. (2025), answering these questions requires careful attention to the interfaces between components, not merely to the capabilities of individual components in isolation.

1.4 Thesis Statement

This thesis advances the proposition that a classical AI architecture can become more reliable and inspectable when neural computation is used for learned representations and association, while explicit symbolic structures govern formal relationships, rule-based inference, and the derivation of conclusions from recorded premises.

The proposed 5 Senses architecture treats retrieval, memory, inference, learning, and evidence evaluation as distinct but cooperating functions. It does not assume that neural models provide truth, that symbolic rules guarantee correctness, or that retrieved documents are authoritative. Instead, it requires each component to expose the information needed by the next component while retaining the origin and status of its outputs.

The thesis will evaluate whether this separation of responsibilities, combined with controlled interaction between components, improves retrieval quality, inference correctness, explanation completeness, and the traceability of system conclusions.

1.5 Research Questions

The thesis is organized around five primary research questions, each addressing a different aspect of the proposed architecture:

RQ1 — Architectural Integration: How should neural models, symbolic reasoning, associative memory, and knowledge archives communicate so that their different computational responsibilities remain explicit?

This question concerns the interfaces between components. It asks how information should be represented as it moves between subsystems, what metadata should accompany computational products, and how the system should handle cases where components disagree or produce incompatible outputs.

RQ2 — Knowledge Representation: How can the system represent facts, observations, predictions, and inferred claims without treating them as equivalent?

This question concerns the internal representation of knowledge. It asks how different epistemic categories should be distinguished, what fields each type of knowledge object should contain, and how the representation should support reasoning about uncertainty and evidence.

RQ3 — Evidence and Provenance: How can a conclusion be connected to the documents, passages, transformations, and inference steps that contributed to it?

This question concerns traceability. It asks how the system should record the chain of dependencies that led to a conclusion, how this record should be queried and displayed, and how provenance information should be maintained as conclusions are revised.

RQ4 — Reliability: Does combining neural and symbolic components improve performance on selected tasks compared with appropriately configured neural-only and classical baselines?

This question concerns empirical evaluation. It asks whether the proposed architecture provides measurable benefits, under what conditions those benefits appear, and whether the benefits justify the additional complexity.

RQ5 — Failure Analysis: What happens when the system encounters incomplete evidence, contradictory documents, incorrect predictions, corrupted memory patterns, or invalid inference rules?

This question concerns robustness. It asks how the system behaves under adverse conditions, whether failures are detected and reported, and whether the system degrades gracefully or catastrophically.

These questions are intended to be experimentally answerable. They are not rhetorical questions whose answers can be established through architectural description alone. According to Marra et al. (2024), the evaluation of neuro-symbolic systems requires careful experimental design that isolates the contributions of different components.

1.6 Research Objectives

The thesis pursues eight interconnected objectives:

1. Establish a precise conceptual distinction between neural learning, associative recall, retrieval, and symbolic inference. This objective requires clarifying what each operation produces and how these products differ in epistemic status.
2. Define a hybrid architecture with explicit information boundaries between its components. This objective requires specifying the interfaces through which components communicate and the metadata that accompanies information as it moves between subsystems.
3. Specify how claims, sources, uncertainty, and inference records should be represented. This objective requires designing data structures that capture the information needed for reasoning, provenance, and explanation.
4. Identify which capabilities are implemented in the 5 Senses repository and which remain proposed. This objective requires honest assessment of the current state of implementation, distinguishing between designed capabilities and working code.
5. Construct reproducible experiments for the individual components. This objective requires designing experiments that can be run by other researchers, with documented procedures, datasets, and evaluation metrics.
6. Compare the integrated architecture against relevant baselines. This objective requires establishing appropriate comparison conditions and measuring whether the integrated system outperforms simpler alternatives.
7. Examine failures rather than reporting only successful examples. This objective requires systematic investigation of error cases, edge conditions, and adverse scenarios.
8. Establish whether the architecture provides measurable benefits in correctness, traceability, or interpretability. This objective requires empirical evidence, not merely theoretical argument.

1.7 Scope and Boundaries

This thesis is concerned with a local-first classical AI research architecture. It does not attempt to establish that the proposed system possesses human consciousness, human-like understanding, or general intelligence. These are philosophical and scientific questions beyond the scope of engineering research.

It does not assume that a neural model can independently establish factual truth. Neural models learn statistical patterns from training data. They can identify correlations, classify inputs, and generate predictions. They cannot, by themselves, verify that their outputs correspond to reality.

It does not assume that a formal rule system is immune to incorrect premises. Symbolic reasoning operates on representations. If those representations are inaccurate or incomplete, the conclusions derived from them may be wrong even when the reasoning is logically valid.

It does not treat a large document collection as a knowledge base merely because its contents can be indexed. A collection of documents contains information, but that information may be inaccurate, contradictory, or incomplete. A knowledge base requires structured representation and evaluation of evidence.

The research is concerned with computationally testable properties: representation accuracy, retrieval relevance, associative recall, rule correctness, inference traceability, source attribution, contradiction handling, reproducibility, and system performance. These properties can be measured through controlled experiments and compared against baselines.

The project also distinguishes the architecture described in this thesis from the state of the software repository. A proposed module is not an implemented module. An implemented module is not necessarily a validated module. A passing unit test does not establish broad real-world reliability. Throughout this thesis, claims about implementation status must be tied to inspected source code and test evidence.

---

2. Theoretical Foundations

2.1 Neural Computation as Learned Representation

A neural network transforms inputs through parameterized computational operations. During training, its parameters are adjusted according to an objective function and an optimization procedure (Rumelhart et al., 1986).

The significance of this process is not merely that a network produces an output. Its internal parameters can encode useful representations of recurring structures in the training data. These representations capture regularities that may be difficult to specify manually, enabling the network to generalize from observed examples to novel inputs.

Rumelhart et al. (1986) showed how back-propagation could adjust internal connection weights to reduce output error. This made it possible for hidden units to develop task-relevant representations through learning rather than requiring every feature to be specified manually. The algorithm propagates error gradients backward through the network, allowing each weight to be adjusted in proportion to its contribution to the overall error.

For 5 Senses, neural computation can identify patterns, produce representations, and estimate relationships. It should not automatically determine the factual status of the information it processes. A neural network that classifies a document as relevant to a query has performed a useful operation, but that classification is a prediction, not a verification.

A neural prediction should therefore be represented as a prediction, with its model identity, input context, uncertainty information, and applicable limitations. According to Wang et al. (2025), preserving this distinction is essential for building trustworthy neuro-symbolic systems. A prediction that loses its identity as a prediction can be mistaken for a verified fact, leading to inappropriate reliance on uncertain information.

The representation of neural outputs should include:

· Model identity: Which model produced the prediction, including version and configuration.
· Input context: What input the model received, enabling reproduction and analysis.
· Output values: The raw output of the model, whether classification probabilities, regression values, or embeddings.
· Uncertainty information: Calibration data, confidence intervals, or other measures of prediction reliability.
· Applicable limitations: Known constraints on the model's validity, such as training data limitations or distributional assumptions.

This metadata enables downstream components to reason about the prediction appropriately, treating it as learned evidence rather than established fact.

2.2 Associative Computation as Content-Addressable Memory

Associative memory differs from conventional address-based storage. In an address-based system, the caller identifies a location or key. In an associative system, retrieval can be initiated by presenting a pattern related to the stored information (Hopfield, 1982).

Hopfield (1982) developed a recurrent network model in which collective network dynamics support content-addressable memory. The network can move from a partial pattern toward a stored configuration under appropriate conditions. The energy landscape of the network defines attractors corresponding to stored patterns, and the dynamics naturally converge toward these attractors from nearby initial states.

This is relevant because a system may need to recover related information from incomplete or noisy representations. If a query provides only partial information, associative memory can complete the pattern based on stored associations. This capability differs from exact-match retrieval, which requires precise correspondence between query and stored content.

However, associative recall and factual verification must remain separate. A recovered pattern is a candidate memory, not proof that the remembered content is correct. The network may converge to a spurious attractor, producing a pattern that resembles stored memories but does not correspond to any stored item. Alternatively, the network may converge to a stored pattern that is itself inaccurate or outdated.

According to Yu et al. (2023), associative memory systems require careful validation to ensure that recalled patterns correspond to genuine memories rather than artifacts of network dynamics. The recovered representation must be connected to its stored record and provenance if it is to support a factual claim.

For 5 Senses, associative memory provides a mechanism for identifying related concepts and recovering associated information. Its outputs should be treated as candidates for further examination, not as verified facts. The system should preserve the relationship between recalled patterns and their stored sources, enabling downstream evaluation of their relevance and accuracy.

2.3 Symbolic Representation as Explicit Structure

Symbolic systems represent information through defined entities, properties, relations, and rules. According to Marra et al. (2024), this explicit representation enables formal reasoning, interpretable inference, and systematic knowledge management.

A knowledge base might contain an entity representing a historical publication, a relation connecting that publication to an author, a date associated with a particular edition, a source record supporting the date, and a rule that determines whether the available information satisfies a defined condition.

The important characteristic is that these relationships are represented explicitly. A reasoning engine can operate over known structures rather than relying exclusively on statistical similarity. Each inference step can be traced to specific premises and rules, enabling explanation and verification.

However, symbolic inference is only as dependable as its representations, premises, and rules. A logically valid conclusion can still be factually wrong if one of its premises is incorrect. According to Marra et al. (2024), the evaluation of symbolic reasoning systems must consider not only logical correctness but also the accuracy of the representations on which reasoning operates.

5 Senses must therefore distinguish logical validity from evidential support. A conclusion may be validly derived from premises, yet those premises may lack evidential support or may be contradicted by other information. The system should track both the logical structure of inferences and the evidential status of the premises on which they depend.

2.4 Retrieval as Candidate Discovery

Information retrieval provides a mechanism for finding documents relevant to a query. Robertson and Zaragoza (2009) describe the probabilistic relevance framework and BM25, a family of ranking methods that use term-frequency and document-length information.

The probabilistic relevance framework models retrieval as a process of estimating the probability that a document is relevant to a query. BM25, a widely used instantiation of this framework, combines term frequency, inverse document frequency, and document length normalization to produce relevance scores.

In the proposed architecture, retrieval has a specific responsibility: identify candidate information for further examination. Retrieval does not establish truth, authority, or currency. It identifies documents that may contain information relevant to a query, leaving the evaluation of that information to other components.

A high-ranking document is not automatically a reliable document. Relevance and authority are different properties. A document may be highly relevant while containing errors, outdated information, or unsupported interpretation. A document may be authoritative while not directly relevant to the specific query.

The retrieval subsystem should preserve document identifiers, passage locations, metadata, query information, and retrieval configuration. A score estimates relevance; it does not establish truth. According to Robertson and Zaragoza (2009), retrieval scores should be interpreted as relative rankings within a particular retrieval configuration, not as absolute measures of document quality.

For 5 Senses, retrieved documents enter the system as candidate evidence. They must be evaluated for relevance, authority, currency, and consistency with other sources before their contents can be used to support factual claims.

2.5 Provenance as Part of Knowledge Representation

Data provenance concerns the origin of information and the process through which it entered a derived result. Buneman et al. (2001) distinguish between sources that influenced the existence of a result and locations from which information was extracted.

Provenance is not merely metadata added for record-keeping. It is a fundamental component of knowledge representation. Without provenance, a claim is a free-floating assertion with no connection to the evidence that supports or challenges it.

For 5 Senses, provenance should not be treated as an optional citation added after an answer has been generated. It should be part of the internal representation of a claim. According to Buneman et al. (2001), provenance must be tracked throughout the derivation process, not reconstructed after the fact.

A claim should be traceable to its original source, relevant document version, passage or data location, extraction or transformation process, inference rules applied, and resulting claim status. This chain enables:

· Verification: Checking whether the source actually supports the claim.
· Auditing: Examining how a conclusion was reached.
· Revision: Updating claims when sources change or new evidence emerges.
· Explanation: Communicating to users how conclusions were derived.

Without this chain, the system may produce a plausible answer without being able to demonstrate how it arrived at that answer. Such answers cannot be trusted, because their derivation cannot be inspected or verified.

---

3. The Proposed 5 Senses Architecture

3.1 Architectural Principle

The architecture is based on functional separation with controlled cooperation. This principle holds that different computational functions should be performed by distinct components with well-defined responsibilities and interfaces, while these components should cooperate to achieve overall system goals.

The existing Part II manuscript describes five responsibilities as perception, memory, reasoning, association, and expression. This thesis preserves those names rather than silently replacing them with a different five-part model. Other subsystems—such as document retrieval, neural execution, language processing, orchestration, and evidence evaluation—are supporting mechanisms that may contribute to one or more of the five responsibilities.

The five senses of the architecture are summarized in Table 1.

Table 1

The Five Senses of the 5 Senses Architecture

Sense Primary Responsibility Representative Mechanisms
Perception Receive and interpret input Parsers, tokenizers, validators, feature extraction
Memory Retain information SQLite archive, document metadata, knowledge records
Reasoning Evaluate information Expert rules, inference procedures, evidence evaluation
Association Identify related patterns Neural networks, Hopfield memory, similarity methods
Expression Communicate results Response construction, citations, explanations

This is an architectural classification, not a claim that every subsystem has already been implemented as a complete module. The table describes intended responsibilities and representative mechanisms, not verified capabilities.

A subsystem may contribute to more than one responsibility. A neural model may assist perception by classifying an input and association by identifying a related pattern. Its outputs must nevertheless retain their computational identity. A neural prediction must not silently become a verified archive record.

According to Wang et al. (2025), the boundaries between functional responsibilities are often blurry in practice. The same component may serve multiple roles, and the same information may flow through multiple paths. The 5 Senses architecture addresses this complexity by making the boundaries explicit in the design, even when implementation details blur them.

3.2 Why the Functions Must Remain Distinct

Consider a system asked whether a particular historical claim is supported by its archive.

Perception validates the question and prepares its representation. This involves parsing the query, identifying entities and relations, and constructing an internal representation suitable for further processing.

Memory and retrieval locate candidate documents. This involves searching the archive for documents that may contain relevant information, ranking them by relevance, and returning them for examination.

Association may identify related concepts or patterns. This might involve using neural embeddings to find semantically similar passages, or using associative memory to recall related concepts.

Reasoning represents claims and evaluates explicit relationships. This involves constructing formal representations of the claim and supporting evidence, applying inference rules to derive conclusions, and checking for consistency.

Evidence evaluation examines source support and identifies conflicts. This involves assessing the authority and reliability of sources, identifying contradictory information, and determining the overall evidential status of the claim.

Expression communicates the result and its limitations. This involves generating a response that accurately represents the system's conclusions and the uncertainty associated with them.

If the neural model classifies a document as relevant, that classification must not be interpreted as confirmation of the historical claim. Relevance and accuracy are different properties. A relevant document may contain inaccurate information.

If a symbolic rule derives a date from two premises, the system must retain both premises and the rule. The conclusion depends on the premises, and the premises must be available for inspection if the conclusion is to be trusted.

If two documents disagree, the system must preserve the disagreement rather than silently selecting whichever passage has the highest retrieval score. The existence of disagreement is itself important information that should be reported to the user.

According to Marra et al. (2024), preserving these distinctions is essential for building systems that can be trusted and audited. Systems that collapse distinctions may appear to function correctly in simple cases but fail in ways that are difficult to diagnose.

3.3 Claim-Centered Information Model

The proposed architecture treats the claim as a central object of evaluation. A claim is a proposition that can be true or false, supported or unsupported, consistent or contradictory.

The claim-centered model provides a structured representation for information that the system evaluates. Rather than treating documents as the primary unit of information, the model treats claims extracted from documents as the primary unit. This enables comparison of claims across documents, tracking of evidence for and against specific propositions, and reasoning about the relationships between claims.

Table 2 presents the proposed schema for claim representation.

Table 2

Proposed Claim Representation Schema

Field Purpose
Claim identifier Stable identity for the claim
Claim text The proposition being evaluated
Claim type Observation, prediction, reported fact, or inference
Subject and relation Structured representation where available
Source references Documents and passages supporting or challenging the claim
Derivation record Rules and premises used to infer the claim
Confidence or uncertainty Appropriate uncertainty information
Evidence status Current evaluation status
Version information History of changes and evaluations

This is a proposed schema, not a statement that the repository already implements all these fields. The schema represents a design target that implementation should strive to achieve.

The claim identifier provides a stable reference that can be used to track the claim through multiple processing stages. This enables the system to maintain consistency and support revision.

The claim text is the natural language expression of the proposition. This is what users see and what downstream components reason about.

The claim type distinguishes different categories of claims. An observation is a claim about directly perceived data. A prediction is a claim produced by a model. A reported fact is a claim extracted from a document. An inference is a claim derived through reasoning. Different claim types have different evidential requirements and different failure modes.

The subject and relation fields provide structured representation where available. This enables formal reasoning about the claim, checking consistency with other claims, and identifying relationships between claims.

The source references connect the claim to the documents and passages from which it was extracted or which support or challenge it. According to Buneman et al. (2001), these references are essential for verification and auditing.

The derivation record captures the rules and premises used to infer the claim. This is applicable to inferred claims and enables inspection of the reasoning process.

The confidence or uncertainty field represents the system's assessment of the claim's reliability. The system should avoid confusing a confidence score with a probability of truth unless the score has been calibrated and its interpretation has been experimentally established.

The evidence status field records the current evaluation status of the claim. This might include the evidence states discussed in the next section.

The version information field tracks the history of changes and evaluations. This enables auditing and supports revision when new evidence emerges.

3.4 Evidence States

The project has previously used the following evidence vocabulary:

· OFFICIAL
· CONSENSUS
· PLAUSIBLE
· SPECULATIVE
· UNKNOWN

These labels should describe the current evidence assessment, not the rhetorical strength of an answer. According to the framework, OFFICIAL indicates that the claim is supported by an authoritative source with recognized standing. CONSENSUS indicates that the claim is supported by multiple independent sources that agree. PLAUSIBLE indicates that the claim is consistent with available evidence but lacks strong support. SPECULATIVE indicates that the claim is proposed but not well-supported. UNKNOWN indicates that the available evidence is insufficient to assign a stronger status.

UNKNOWN should not mean that a claim is false; it means the available evidence is insufficient to assign a stronger status. This distinction is important. A claim that is not supported is different from a claim that is refuted. The absence of evidence is not evidence of absence.

The system should preserve conflicting sources and the reasons for the assigned status. A status without an explanation is only another opaque label. Users should be able to understand why a claim received a particular status and what evidence would change that status.

According to Wang et al. (2025), evidence assessment in neuro-symbolic systems requires careful attention to the quality and reliability of sources. Not all sources are equally reliable, and the system should track source reliability as part of its evidence model.

3.5 Component Interaction Patterns

The 5 Senses architecture defines several patterns for interaction between components. These patterns specify how information flows between components while preserving the distinctions discussed above.

Pattern 1: Perception to Memory. Input is parsed and validated, then stored in memory with appropriate metadata. The metadata includes the source of the input, the processing applied, and the confidence in the interpretation.

Pattern 2: Memory to Retrieval to Reasoning. A query triggers retrieval of candidate documents, which are then examined by reasoning components. The reasoning components receive both the retrieved content and metadata about the retrieval process, including relevance scores and source information.

Pattern 3: Association to Reasoning. Neural or associative processes produce candidate patterns or relationships, which are then evaluated by reasoning components. The reasoning components receive the candidates along with metadata about the association process, including confidence and model information.

Pattern 4: Reasoning to Evidence Evaluation. Reasoning produces conclusions that are then evaluated for evidential support. The evidence evaluation receives the conclusions along with the derivation records and source references.

Pattern 5: Evidence Evaluation to Expression. Evaluated claims are communicated to users with appropriate hedging and citation. The expression component receives the claims along with their evidence status and supporting sources.

These patterns ensure that information flows between components while preserving the distinctions discussed above. Each component receives not just the content produced by other components, but also metadata about how that content was produced and what confidence should be placed in it.

---

4. Neural Models and Associative Computation

4.1 Neural Network Fundamentals

Neural networks are computational systems composed of interconnected units that transform inputs through parameterized operations. According to Rumelhart et al. (1986), the key insight of neural computation is that useful representations can be learned from data rather than specified manually.

A typical neural network consists of layers of units, with each unit receiving input from units in the previous layer and producing output that is passed to units in the next layer. The connections between units have weights that determine the strength of the influence. During training, these weights are adjusted to minimize a loss function that measures the discrepancy between the network's outputs and desired outputs.

The back-propagation algorithm, introduced by Rumelhart et al. (1986), computes the gradient of the loss with respect to each weight by propagating error signals backward through the network. This enables efficient optimization of networks with many parameters.

For 5 Senses, neural networks serve several functions:

· Classification: Determining which category an input belongs to.
· Embedding: Producing dense vector representations of inputs that capture semantic content.
· Prediction: Estimating values or probabilities based on input features.
· Pattern recognition: Identifying recurring structures in data.

Each of these functions produces outputs that should be treated as learned representations, not verified facts. The system should track the model that produced each output, the confidence associated with the output, and the limitations of the model.

4.2 Associative Memory Models

Associative memory systems store and retrieve patterns based on content rather than address. Hopfield (1982) introduced a model of associative memory based on recurrent neural network dynamics.

In a Hopfield network, patterns are stored as attractors in the network's energy landscape. When presented with a partial or noisy version of a stored pattern, the network dynamics converge toward the nearest attractor, effectively completing the pattern.

The capacity of Hopfield networks is limited. According to Hopfield (1982), a network with N units can reliably store approximately 0.15N patterns. Beyond this capacity, the network may converge to spurious attractors that do not correspond to any stored pattern.

For 5 Senses, associative memory provides a mechanism for content-addressable recall. Given a partial cue, the system can retrieve related patterns from memory. This capability is useful for:

· Pattern completion: Recovering full patterns from partial inputs.
· Similarity search: Finding stored patterns similar to a query.
· Error correction: Recovering correct patterns from corrupted inputs.

However, associative memory outputs should be treated as candidates, not verified facts. The network may converge to spurious attractors, or may retrieve patterns that are themselves inaccurate. The system should validate recalled patterns against stored records and provenance.

4.3 Uncertainty in Neural Predictions

Neural networks produce point estimates, but these estimates are accompanied by uncertainty. According to Wang et al. (2025), quantifying and communicating this uncertainty is essential for trustworthy AI systems.

Several sources of uncertainty affect neural predictions:

· Aleatoric uncertainty: Irreducible uncertainty due to noise in the data or inherent randomness in the phenomenon being modeled.
· Epistemic uncertainty: Uncertainty due to limited knowledge, which could be reduced with more data or better models.
· Distributional uncertainty: Uncertainty due to test inputs that differ from the training distribution.

The system should represent uncertainty in a form that downstream components can use. This might include:

· Calibrated probabilities: Probabilities that reflect actual frequencies in held-out data.
· Confidence intervals: Ranges within which the true value is likely to fall.
· Ensemble disagreement: Variation across multiple models trained on different data or with different initializations.

According to Marra et al. (2024), uncertainty representation is particularly important in neuro-symbolic systems, where neural predictions feed into symbolic reasoning. If symbolic reasoning treats uncertain predictions as certain facts, the resulting conclusions may be unjustified.

4.4 Neural-Symbolic Integration Patterns

Several patterns exist for integrating neural and symbolic computation. According to Yu et al. (2023), these patterns differ in how tightly the neural and symbolic components are coupled.

Pattern 1: Neural-to-Symbolic Pipeline. Neural components process input and produce structured outputs that are then processed by symbolic components. The neural component might classify text into categories, extract entities and relations, or produce embeddings that are then discretized into symbols.

Pattern 2: Symbolic-to-Neural Pipeline. Symbolic components produce structured representations that are then processed by neural components. The symbolic component might provide knowledge graph embeddings, logical constraints, or structured features.

Pattern 3: Joint Training. Neural and symbolic components are trained jointly, with gradients flowing through both. This requires the symbolic component to be differentiable or to have differentiable approximations.

Pattern 4: Iterative Refinement. Neural and symbolic components alternate, with each refining the outputs of the other. The neural component might produce candidate solutions that the symbolic component verifies, with the results fed back to the neural component.

5 Senses primarily uses Pattern 1, with neural components producing structured outputs that are then processed by symbolic and evidence evaluation components. This pattern maintains clear separation between neural and symbolic responsibilities while enabling cooperation.

4.5 Implementation Considerations

Implementing neural and associative components requires attention to several practical concerns.

Data preparation: Neural models require training data. The data must be representative of the distribution the model will encounter in deployment. According to Wang et al. (2025), data quality is often the most important factor in neural model performance.

Model selection: Different tasks require different model architectures. Classification tasks may use feedforward networks or transformers. Embedding tasks may use autoencoders or contrastive learning. The choice of architecture affects both performance and interpretability.

Training procedures: Training requires careful selection of hyperparameters, optimization algorithms, and regularization techniques. According to Rumelhart et al. (1986), proper training is essential for achieving good performance.

Evaluation: Neural models should be evaluated on held-out data that was not used during training or hyperparameter selection. Metrics should be appropriate for the task and should include measures of uncertainty calibration.

Deployment: Deployed models should be versioned and monitored. If the data distribution changes, model performance may degrade, requiring retraining or adaptation.

---

5. Symbolic Reasoning and Knowledge Representation

5.1 Knowledge Representation Fundamentals

Knowledge representation concerns how information is structured for use by computational systems. According to Marra et al. (2024), effective knowledge representation must balance expressiveness, computational tractability, and interpretability.

Several representation formalisms are relevant to 5 Senses:

Relational databases store information in tables with rows and columns. They provide efficient querying and well-understood semantics, but may be limited in expressiveness for complex relationships.

Graph databases store information as nodes and edges. They naturally represent relationships and support traversal queries, but may be less efficient for certain types of aggregation.

Description logics provide formal semantics for concepts and roles. They support automated reasoning and consistency checking, but may be computationally expensive for large knowledge bases.

Logic programming represents knowledge as facts and rules. It supports declarative specification and query evaluation, but may have limited scalability.

5 Senses uses a combination of relational storage (SQLite) for structured records and logic-based representations for reasoning. This hybrid approach balances practical storage efficiency with expressive reasoning capabilities.

5.2 Facts, Rules, and Inference

Symbolic reasoning operates on facts and rules to derive conclusions.

Facts are assertions about the world. They may be directly observed, extracted from documents, or inferred from other facts. Each fact should have provenance indicating its source and derivation.

Rules specify relationships between facts. A rule has a condition (the antecedent) and a conclusion (the consequent). When the condition is satisfied, the conclusion can be derived.

Inference is the process of applying rules to facts to derive new facts. According to Marra et al. (2024), inference procedures should be sound (deriving only valid conclusions) and complete (deriving all valid conclusions) when possible.

For 5 Senses, the reasoning component should:

· Store facts with provenance information.
· Store rules with clear semantics.
· Apply rules to derive conclusions.
· Record the derivation of each conclusion.
· Handle uncertainty and contradiction.

The reasoning component should not assume that facts are true merely because they are stored. Facts may be uncertain, outdated, or contradicted by other facts. The reasoning component should track the evidential status of facts and propagate this status through inferences.

5.3 Handling Contradictions

Contradictions arise when the system holds beliefs that cannot all be true simultaneously. According to Yu et al. (2023), handling contradictions is a critical challenge for knowledge-based systems.

Contradictions may arise from:

· Source disagreement: Different sources make incompatible claims.
· Extraction errors: Automated extraction produces incorrect facts.
· Reasoning errors: Incorrect rules or premises lead to false conclusions.
· World changes: Facts that were true at different times are both stored.

5 Senses should handle contradictions by:

1. Detecting contradictions through consistency checking.
2. Preserving contradiction information rather than silently resolving it.
3. Evaluating sources to determine which claim is better supported.
4. Reporting contradictions to users rather than hiding them.

The system should not assume that one claim in a contradiction must be false. Both claims may be partially correct, or the contradiction may reflect genuine uncertainty. The system should represent the contradiction and its resolution (if any) explicitly.

5.4 Explanation Generation

Explanation generation concerns communicating how conclusions were reached. According to Marra et al. (2024), explanations are essential for trust and accountability.

For 5 Senses, explanations should include:

· The claim being explained: What conclusion is being justified.
· The evidence supporting the claim: Which sources and passages support it.
· The reasoning used: Which rules and premises led to the conclusion.
· The uncertainty involved: How confident the system is and why.
· Alternative conclusions considered: What other conclusions were possible and why they were rejected.

Explanations should be tailored to the audience. A technical explanation might include formal derivation steps, while a non-technical explanation might focus on the sources and general reasoning.

According to Buneman et al. (2001), provenance information is essential for explanation. Without knowing where information came from, it is impossible to explain why a conclusion should be trusted.

5.5 Uncertainty Propagation

Uncertainty propagation concerns how uncertainty in premises affects uncertainty in conclusions. According to Wang et al. (2025), this is a challenging problem in neuro-symbolic systems.

Several approaches exist:

Probability theory provides a principled framework for uncertainty. Each fact is associated with a probability, and inference rules specify how probabilities combine. This approach is theoretically sound but may be computationally expensive.

Fuzzy logic represents uncertainty as degrees of membership in sets. This approach is computationally efficient but may not have clear probabilistic interpretation.

Possibility theory distinguishes between uncertainty (which outcome will occur) and imprecision (what the outcome is). This approach can represent different types of uncertainty but may be complex to implement.

5 Senses should adopt a pragmatic approach to uncertainty, representing it in forms that downstream components can use. The key requirement is that uncertainty should not be silently dropped as information flows through the system. A conclusion derived from uncertain premises should itself be marked as uncertain.

---

6. Archives, Language, and Evidence

6.1 Corpus Acquisition and Management

The quality of a knowledge system depends on the quality of its corpus. According to Robertson and Zaragoza (2009), retrieval effectiveness depends on both the retrieval algorithm and the corpus being searched.

For 5 Senses, corpus acquisition should consider:

· Relevance: Does the corpus contain information relevant to the system's intended use?
· Quality: Are the sources authoritative and accurate?
· Coverage: Does the corpus cover the full range of topics the system will encounter?
· Diversity: Does the corpus include multiple perspectives and sources?
· Rights: Are the sources legally usable?

Corpus management should include:

· Version control: Tracking changes to the corpus over time.
· Metadata: Recording source, date, rights status, and other relevant information.
· Checksums: Verifying corpus integrity.
· Documentation: Recording acquisition procedures and known limitations.

According to Buneman et al. (2001), provenance tracking should begin at corpus acquisition, not at query time. The source of each document should be recorded when the document enters the system.

6.2 Document Processing and Indexing

Documents must be processed before they can be retrieved and analyzed. Processing typically includes:

· Text extraction: Converting documents to plain text.
· Tokenization: Dividing text into words or other units.
· Normalization: Standardizing case, punctuation, and other features.
· Indexing: Creating data structures for efficient retrieval.

According to Robertson and Zaragoza (2009), the choice of processing steps affects retrieval effectiveness. Different tokenization schemes may be appropriate for different languages or document types.

For 5 Senses, processing should preserve information needed for provenance. This includes:

· Document boundaries: Where each document begins and ends.
· Passage boundaries: Where relevant passages are located within documents.
· Character offsets: Precise locations of extracted content within source documents.

This information enables precise citation and verification.

6.3 Retrieval Methods

Several retrieval methods are relevant to 5 Senses.

Keyword search matches query terms against document terms. It is simple, fast, and interpretable, but may miss documents that use different terminology.

BM25 extends keyword search with term frequency weighting and document length normalization. According to Robertson and Zaragoza (2009), BM25 is a strong baseline for many retrieval tasks.

Vector similarity represents documents and queries as dense vectors and measures similarity. This enables semantic matching but requires training embedding models.

Hybrid methods combine multiple retrieval signals. This can improve performance but increases complexity.

5 Senses should support multiple retrieval methods and allow comparison between them. The choice of method should depend on the task and corpus.

6.4 Source Quality Assessment

Retrieved documents vary in quality and reliability. According to Wang et al. (2025), source quality assessment is essential for evidence evaluation.

Factors affecting source quality include:

· Authority: Is the source recognized as authoritative in its domain?
· Accuracy: Has the source been accurate in the past?
· Currency: Is the information up to date?
· Bias: Does the source have known biases?
· Methodology: Was the information gathered through sound methods?

5 Senses should track source quality as part of its evidence model. Claims from high-quality sources should receive more weight than claims from low-quality sources, all else being equal.

6.5 Provenance Tracking

Provenance tracking records the origin and derivation of information. According to Buneman et al. (2001), provenance should be maintained throughout the system.

For 5 Senses, provenance should include:

· Document provenance: Where each document came from.
· Extraction provenance: How content was extracted from documents.
· Transformation provenance: What processing was applied to extracted content.
· Inference provenance: What reasoning led to derived conclusions.

Provenance should be queryable, enabling users to trace conclusions back to their sources. This supports verification, auditing, and explanation.

---

7. Implementation and Engineering

7.1 System Architecture

The 5 Senses system architecture consists of several interconnected modules. According to the research-status notice in the thesis foundation document, implementation claims must be tied to inspected source code and test evidence.

The proposed architecture includes:

· Input processing module: Handles user queries and system inputs.
· Storage module: Manages document and knowledge storage.
· Retrieval module: Implements retrieval algorithms.
· Neural module: Executes neural models.
· Reasoning module: Applies rules and derives conclusions.
· Evidence module: Evaluates sources and assesses claims.
· Expression module: Generates responses and explanations.

Each module should have clear interfaces that specify what inputs it accepts, what outputs it produces, and what metadata accompanies its outputs.

7.2 Data Structures

Data structures should represent information in forms that support both storage efficiency and reasoning capability.

Document records should include content, metadata, and source information. They should support efficient retrieval and provenance tracking.

Claim records should follow the claim-centered schema discussed in Section 3.3. They should support comparison across documents and tracking of evidence.

Inference records should capture the derivation of conclusions, including premises, rules, and confidence.

Provenance records should connect claims and inferences to their sources.

7.3 Interfaces and APIs

Interfaces between components should be explicit and well-documented. According to Marra et al. (2024), interface design is critical for neuro-symbolic integration.

Each interface should specify:

· Input format: What data the component accepts.
· Output format: What data the component produces.
· Metadata: What additional information accompanies the data.
· Error handling: How errors are communicated.
· Performance characteristics: Expected latency and throughput.

7.4 Testing and Validation

Testing should verify that components function as specified. According to Wang et al. (2025), testing is essential for building reliable systems.

Testing should include:

· Unit tests: Verify individual functions and methods.
· Integration tests: Verify that components work together.
· Property tests: Verify that invariants hold.
· Performance tests: Verify that latency and throughput meet requirements.

A passing unit test establishes only the behavior covered by that test. It does not prove general correctness, production readiness, or research superiority.

7.5 Reproducibility

Reproducibility requires that experiments can be repeated by other researchers. According to Marra et al. (2024), reproducibility is essential for scientific validity.

Reproducibility requires documenting:

· Dataset versions: Exact datasets used, with checksums.
· Preprocessing steps: How data was prepared.
· Model configurations: Architecture, hyperparameters, and training procedures.
· Evaluation procedures: How performance was measured.
· Environment: Hardware and software versions.

---

8. Experimental Design

8.1 Research Design

The thesis adopts a comparative experimental design. According to Marra et al. (2024), comparative experiments are essential for establishing whether integration provides benefits.

The comparison should include:

1. Classical baseline: Structured records, keyword retrieval, and explicit rules.
2. Neural baseline: Learned representations and classification.
3. Hybrid system: Combining neural and symbolic operations.
4. Ablation variants: Removing one functional component at a time.

This design helps determine whether the combined system provides an actual benefit or merely contains more software.

8.2 Evaluation Dimensions

Different research areas require different evaluation metrics. Table 3 summarizes candidate measurements.

Table 3

Evaluation Dimensions and Candidate Measurements

Research Area Candidate Measurements
Document retrieval Precision@k, Recall@k, MRR, nDCG, latency
Neural learning Accuracy, macro-F1, loss, calibration, inference time
Associative memory Exact recall, bit-error rate, corrupted-pattern recovery, spurious attractors
Symbolic reasoning Inference correctness, rule coverage, contradiction handling
Evidence evaluation Citation precision, provenance completeness, unsupported-claim rate
Integrated architecture End-to-end correctness, explanation completeness, latency, component failure propagation

Metrics must correspond to defined test cases and ground-truth annotations. Metrics alone do not establish that a system is reliable.

8.3 Experimental Controls

Experiments must document:

· Dataset name and version.
· Dataset license or applicable usage restrictions.
· Acquisition date and source.
· Cryptographic checksum where appropriate.
· Preprocessing operations.
· Training/validation/test splits.
· Model architecture and parameter count.
· Hyperparameters.
· Random seeds.
· Hardware and software environment.
· Evaluation scripts.
· Baseline configurations.

The test set must not be used to select hyperparameters or repeatedly tune the system. According to Robertson and Zaragoza (2009), using test data for model selection invalidates evaluation.

Where a model uses a differentiable training objective, the loss must remain connected to the model computation graph. A detached scalar loss cannot provide the intended gradient signal to model parameters.

8.4 Ablation Experiments

The integrated architecture should be tested with individual components disabled:

· Remove symbolic reasoning while retaining neural predictions. This tests whether symbolic reasoning adds value beyond neural processing alone.
· Remove neural representations while retaining symbolic and retrieval functions. This tests whether neural representations add value beyond symbolic processing alone.
· Remove associative recall while retaining ordinary archive retrieval. This tests whether associative memory adds value beyond conventional retrieval.
· Remove provenance tracking while retaining answer generation. This tests whether provenance tracking affects answer quality.
· Remove evidence evaluation while retaining the other components. This tests whether evidence evaluation affects answer reliability.

The results should show whether each component contributes measurable value and whether some components introduce additional failure modes. A component should not be justified merely because it is historically interesting or theoretically attractive.

8.5 Candidate Benchmark Groups

The following are candidate experiments, not completed results.

Document retrieval: Compare SQLite keyword search and BM25. Measure Precision@5, Recall@10, mean reciprocal rank, nDCG@10, latency, and index size.

Neural classification: Compare a majority-class baseline, a classical classifier such as logistic regression, and a compact neural model. Measure accuracy, macro-F1, loss behavior, calibration, inference latency, and seed stability.

Associative memory: Evaluate exact recovery, noisy and partial recall, bit-error rate, spurious attractors, capacity, and recall time. Compare against a nearest-neighbor baseline.

Symbolic reasoning: Test valid and invalid inference, rule coverage, conflicting rules, missing premises, and explanation completeness.

Evidence and provenance: Test correct and incorrect source attribution, conflicting sources, incomplete citations, unsupported claims, OCR errors, and unresolved rights status.

Integrated system: Compare classical, neural, and hybrid configurations, followed by ablations that remove one component at a time.

8.6 Datasets

Datasets such as Iris, UCI Wine, UCI Breast Cancer Wisconsin, MNIST, Reuters RCV1, and carefully selected public-domain texts may be considered. According to Wang et al. (2025), the choice of dataset should be appropriate to the research question.

Each dataset requires:

· Recorded version.
· License assessment.
· Checksum.
· Reproducible split.

8.7 No Fabricated Results

No numerical result should appear in the results chapter until the corresponding experiment has been executed and its output preserved. Expected outcomes, hypotheses, and proposed metrics must not be written as findings.

According to Marra et al. (2024), fabricated or selectively reported results undermine the scientific validity of research. The thesis must maintain strict integrity in reporting experimental outcomes.

---

9. Discussion

9.1 Expected Contributions

The thesis does not claim to invent neural-symbolic computing, associative memory, expert systems, or information retrieval. Those areas have established research histories (Hopfield, 1982; Marra et al., 2024; Robertson & Zaragoza, 2009; Rumelhart et al., 1986).

Its proposed contribution is an integrated design discipline in which the system maintains explicit boundaries between learned predictions, stored information, formal inference, retrieved evidence, and evaluated claims.

The intended contribution has four dimensions:

Architectural: A defined division of responsibility between neural learning, associative memory, symbolic reasoning, and evidence evaluation. This contribution specifies how components should interact while preserving their distinct computational identities.

Representational: A claim-centered model that retains source provenance and distinguishes predictions, observations, and inferences. This contribution provides data structures that support reasoning about evidence and uncertainty.

Methodological: A reproducible evaluation plan using baselines, ablations, controlled datasets, and explicit failure tests. This contribution enables empirical validation of the architecture's claims.

Practical: An implementation that can be inspected and tested locally, with capabilities and limitations documented rather than inferred from its description. This contribution provides a concrete artifact for research and development.

These contributions remain hypotheses until supported by repository inspection, implementation evidence, and experimental results.

9.2 Limitations

The architecture may encounter several limitations. According to Wang et al. (2025), all AI systems have limitations that must be acknowledged.

Symbolic knowledge representation requires careful construction and maintenance. Building and maintaining knowledge bases is labor-intensive and error-prone.

Neural models may produce incorrect predictions or poorly calibrated confidence estimates. Models trained on limited data may not generalize to new situations.

Associative systems may retrieve spurious patterns. Hopfield networks have limited capacity and may converge to attractors that do not correspond to stored memories.

Retrieval ranking may favor textual similarity over source quality. Documents that use similar terminology to a query may rank highly even if they are not authoritative.

Evidence evaluation may remain difficult when sources are incomplete, biased, or contradictory. Determining the truth of claims is fundamentally challenging.

The thesis must also account for the cost of integration. More components can increase latency, maintenance requirements, and the number of possible failure paths. The experimental program must evaluate not only whether the architecture works, but also under what conditions it fails.

9.3 Ethical Considerations

The development of AI systems that operate over knowledge raises ethical considerations. According to Marra et al. (2024), researchers have responsibilities regarding the systems they build.

Accuracy: The system should not make claims that are not supported by evidence. It should communicate uncertainty appropriately.

Transparency: The system should be inspectable and explainable. Users should be able to understand how conclusions were reached.

Fairness: The system should not perpetuate biases present in its training data or sources. Source diversity should be considered.

Privacy: The system should respect privacy rights when processing personal information.

Accountability: The system should be designed so that responsibility for its outputs can be traced and assigned.

These considerations should inform both the design of the system and the evaluation of its performance.

9.4 Future Work

Several directions for future work are apparent.

Scaling: The architecture should be tested on larger corpora and more complex reasoning tasks. Scalability is a practical concern for real-world deployment.

Learning: The system could incorporate learning mechanisms that improve performance over time based on user feedback and new data.

Multimodal: The system could be extended to handle images, audio, and other modalities beyond text.

Collaboration: The system could support collaborative knowledge building, with multiple users contributing and evaluating information.

Evaluation: More comprehensive evaluation frameworks are needed for assessing neuro-symbolic systems. According to Yu et al. (2023), existing benchmarks may not adequately capture the capabilities and limitations of integrated systems.

---

10. Conclusion

This thesis has investigated the design principles of 5 Senses, a proposed classical AI architecture that combines neural models with symbolic reasoning, associative computation, structured knowledge storage, language processing, and evidence evaluation.

The central argument is that learning and reasoning should not be treated as interchangeable operations. Neural models can estimate patterns and transform data into useful representations, but they cannot independently establish factual truth. Symbolic mechanisms can represent explicit relationships and expose derivation steps, but they are only as reliable as their premises. Retrieval and provenance mechanisms can connect conclusions to sources, but they cannot guarantee source quality.

The 5 Senses architecture addresses these distinctions through functional separation with controlled cooperation. Different computational responsibilities are assigned to distinct components, each with explicit interfaces that preserve the origin and status of computational products. A claim-centered information model provides structured representation for information the system evaluates, with fields for source references, derivation records, and evidence status. Evidence states provide a vocabulary for describing the current assessment of claims.

The thesis has defined five research questions addressing architectural integration, knowledge representation, evidence and provenance, reliability, and failure analysis. These questions are intended to be experimentally answerable, and the thesis has specified a comparative experimental design to address them.

The expected contribution has four dimensions: architectural, representational, methodological, and practical. These contributions remain hypotheses until supported by implementation evidence and experimental results.

The development of reliable and inspectable AI systems is an ongoing challenge. According to Marra et al. (2024), Wang et al. (2025), and Yu et al. (2023), neuro-symbolic approaches offer promising directions, but much work remains. The 5 Senses architecture represents one approach to this challenge, combining insights from multiple research traditions while maintaining explicit boundaries between their distinct contributions.

---

References

Buneman, P., Khanna, S., & Tan, W.-C. (2001). Why and where: A characterization of data provenance. In J. Van den Bussche & V. Vianu (Eds.), Database theory—ICDT 2001 (pp. 316–330). Springer. https://doi.org/10.1007/3-540-44503-X_20

Hopfield, J. J. (1982). Neural networks and physical systems with emergent collective computational abilities. Proceedings of the National Academy of Sciences, 79(8), 2554–2558. https://doi.org/10.1073/pnas.79.8.2554

Marra, G., Dumančić, S., Manhaeve, R., & De Raedt, L. (2024). From statistical relational to neurosymbolic artificial intelligence: A survey. Artificial Intelligence, 328, Article 104062. https://doi.org/10.1016/j.artint.2023.104062

Robertson, S. E., & Zaragoza, H. (2009). The probabilistic relevance framework: BM25 and beyond. Foundations and Trends in Information Retrieval, 3(4), 333–389. https://doi.org/10.1561/1500000019

Rumelhart, D. E., Hinton, G. E., & Williams, R. J. (1986). Learning representations by back-propagating errors. Nature, 323, 533–536. https://doi.org/10.1038/323533a0

Wang, W., Yang, Y., & Wu, F. (2025). Towards data-and knowledge-driven AI: A survey on neuro-symbolic computing. IEEE Transactions on Pattern Analysis and Machine Intelligence, 47(2), 878–899. https://doi.org/10.1109/TPAMI.2024.3483273

Yu, D., Yang, B., Liu, D., Wang, H., & Pan, S. (2023). A survey on neural-symbolic learning systems. Neural Networks, 166, 105–126. https://doi.org/10.1016/j.neunet.2023.06.028

---

Appendix A: Glossary of Terms

Aleatoric uncertainty: Irreducible uncertainty due to noise in data or inherent randomness in the phenomenon being modeled.

Associative memory: A memory system that retrieves stored patterns based on content similarity rather than address.

BM25: A family of ranking functions used in information retrieval that combine term frequency, inverse document frequency, and document length normalization.

Claim: A proposition that can be true or false, supported or unsupported, consistent or contradictory.

Connectionism: A computational approach that represents information through distributed numerical parameters in networks of interconnected units.

Content-addressable memory: A memory system in which retrieval is initiated by presenting content related to the stored information.

Epistemic uncertainty: Uncertainty due to limited knowledge, which could be reduced with more data or better models.

Evidence status: An assessment of the current support for a claim, such as OFFICIAL, CONSENSUS, PLAUSIBLE, SPECULATIVE, or UNKNOWN.

Hopfield network: A recurrent neural network model of associative memory in which patterns are stored as attractors in an energy landscape.

Knowledge representation: The field concerned with how information is structured for use by computational systems.

Neuro-symbolic computing: An approach that combines neural learning with symbolic representation and inference.

Provenance: Information about the origin and derivation of data or conclusions.

Retrieval: The process of finding documents or information relevant to a query.

Symbolic AI: A computational approach that represents knowledge through explicit structures, rules, and logical relationships.

---

Appendix B: Research Status Checklist

The following checklist summarizes the status of various claims made in this thesis.

Claim Category Status Evidence Required
Neural computation as learned representation Theoretical Literature review; no implementation claim
Associative memory as content-addressable Theoretical Literature review; no implementation claim
Symbolic representation as explicit structure Theoretical Literature review; no implementation claim
Retrieval as candidate discovery Theoretical Literature review; no implementation claim
Provenance as part of knowledge representation Theoretical Literature review; no implementation claim
5 Senses architecture (five responsibilities) Proposed Design specification; implementation status to be verified
Claim-centered information model Proposed Schema design; implementation status to be verified
Evidence states Proposed Vocabulary specification; implementation status to be verified
Neural-symbolic integration patterns Proposed Design specification; implementation status to be verified
Experimental design Proposed Experimental protocol; no results yet
Candidate benchmarks Proposed Benchmark specifications; no results yet

---

End of Thesis
