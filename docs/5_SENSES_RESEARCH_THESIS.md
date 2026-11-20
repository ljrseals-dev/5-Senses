# 5 Senses: Creating a Classical AI System with Neural Models

**A Research Thesis on the Integration of Neural Computation, Symbolic Reasoning, Associative Memory, and Evidence-Based Knowledge**

**Author:** Laila Star Seals  
**Research area:** Artificial Intelligence, Knowledge Representation, Neural Computation, and Information Retrieval  
**Status:** Reconstructed thesis foundation — research draft  
**Citation style:** APA 7th edition

> **Research-status notice:** This document is a thesis reconstruction and research framework. It does not claim that every proposed subsystem is implemented, tested, or benchmarked in the repository. Implementation claims must be tied to inspected source code and test evidence. Experimental findings must be added only after reproducible experiments have been run.

---

## Abstract

Artificial intelligence has developed through several computational traditions that are frequently treated as competing approaches. Symbolic artificial intelligence represents knowledge through explicit structures, rules, and logical relationships. Connectionist systems learn statistical representations through networks of adjustable computational units. Associative memory systems retrieve stored patterns through relationships between distributed representations. Information retrieval systems locate relevant material within collections of documents. These approaches solve different classes of problems, yet an intelligent system operating over complex knowledge often needs to coordinate them.

This thesis investigates the design principles of **5 Senses**, a proposed classical artificial intelligence architecture that combines neural models with symbolic reasoning, associative computation, structured knowledge storage, language processing, and evidence evaluation. Its central proposition is that learning and reasoning should not be treated as interchangeable operations. Neural models can estimate patterns, identify associations, and transform data into useful representations. Symbolic mechanisms can represent explicit relationships, apply rules, identify contradictions, and expose the steps by which conclusions are reached. Retrieval and provenance mechanisms can connect those conclusions to the source material from which they were derived.

The thesis argues that integration should preserve the distinct computational responsibilities of each method. A neural prediction must not automatically become a verified fact. A retrieved document must not automatically become authoritative evidence. A symbolic inference must not be treated as correct merely because its rules executed successfully. Each operation requires an explicit representation of its inputs, assumptions, uncertainty, and limitations.

Research in neuro-symbolic computing provides the theoretical foundation for this investigation (Marra et al., 2024; Wang et al., 2025; Yu et al., 2023). Research on associative memory, neural representation learning, information retrieval, and data provenance provides additional foundations (Buneman et al., 2001; Hopfield, 1982; Robertson & Zaragoza, 2009; Rumelhart et al., 1986).

The research objective is to determine whether a carefully structured hybrid system can improve the reliability, traceability, and inspectability of knowledge processing without sacrificing the adaptive capabilities of neural computation. The thesis develops a conceptual architecture, defines research questions, establishes an evaluation strategy, and distinguishes proposed capabilities from verified implementation.

**Keywords:** classical artificial intelligence, neuro-symbolic computing, neural networks, symbolic reasoning, associative memory, expert systems, knowledge representation, information retrieval, provenance, evidence evaluation.

---

# 1. Introduction

## 1.1 The problem: learning is not the same as knowing

A computational system can recognize a pattern without understanding the conditions under which that pattern should be accepted as true.

A neural network may identify a relationship between two variables because the relationship appears repeatedly in its training data. A retrieval system may return a document because its terminology resembles a query. A rule engine may derive a conclusion because a collection of formal conditions has been satisfied.

These operations establish different things.

Pattern recognition establishes that an input resembles previously encountered data. Retrieval establishes that a document is relevant under a particular ranking method. Rule execution establishes that a conclusion follows from specified premises and rules. None of these operations, independently, establishes that a conclusion is true in the world.

This distinction is fundamental to the design of 5 Senses. The system should not treat all computational outputs as equivalent forms of knowledge. It should preserve the differences between observations and interpretations, statistical predictions and logical conclusions, retrieved information and verified evidence, stored facts and inferred relationships, and confidence estimates and demonstrated correctness.

The distinction matters because errors can propagate when one computational subsystem transfers its output to another without preserving its origin or epistemic status.

Consider a neural classifier that identifies a document as describing a particular historical event. The classification may be useful for locating the document. It does not establish that the document's account of the event is accurate. A retrieval subsystem can locate supporting and conflicting material. A knowledge representation subsystem can record the claims and their relationships. A reasoning subsystem can evaluate whether a conclusion follows from available premises. A provenance subsystem can preserve the documents and passages supporting each claim.

The architectural question is therefore not simply how to combine neural networks and symbolic rules. It is how to coordinate different computational operations without confusing their outputs.

## 1.2 Historical foundations and the research gap

Symbolic approaches represent problems through formal structures and explicit operations. Their strengths include structured representation, rule execution, and the ability to inspect the premises of a derivation. Their limitations include the difficulty of acquiring and maintaining extensive knowledge structures and the brittleness that can arise when real-world information does not match predefined representations.

Connectionist approaches represent information through distributed numerical parameters. Rumelhart, Hinton, and Williams (1986) demonstrated how back-propagation could adjust network weights to learn useful internal representations. Such systems can capture regularities that are difficult to express through manually specified rules.

Hopfield's (1982) work on recurrent neural networks established an important model of content-addressable memory, in which a partial or corrupted pattern can lead toward a stored configuration. This provides a different computational mechanism from conventional document retrieval or explicit rule lookup.

These approaches should not be collapsed into one general concept of intelligence. They have different assumptions, failure modes, and evaluation criteria.

Modern neuro-symbolic research examines ways to combine neural learning with symbolic representation and inference. Marra et al. (2024) survey relationships between neuro-symbolic and statistical relational approaches through their representations, inference mechanisms, and learning procedures. Wang et al. (2025) survey data- and knowledge-driven neuro-symbolic computing, while Yu et al. (2023) examine neural-symbolic learning systems. These works establish that integration is an active research field, not an entirely new idea introduced by 5 Senses.

The contribution of this thesis must therefore be defined more narrowly: a particular architecture and method for coordinating learning, memory, reasoning, retrieval, and evidence evaluation, subject to implementation and experimental verification.

## 1.3 Central research problem

Many hybrid AI designs focus on combining a neural model with a symbolic component. However, the existence of both components does not by itself establish meaningful integration.

A system may contain a neural classifier, a database, and a rule engine while still operating as three loosely connected programs. If the classifier cannot communicate the uncertainty of its prediction, if the database cannot preserve the origin of its records, or if the rule engine cannot distinguish verified premises from tentative ones, the architecture remains conceptually fragmented.

The central research problem is:

**How can a classical AI system coordinate neural learning, associative memory, symbolic inference, document retrieval, and evidence evaluation while preserving the provenance, uncertainty, and computational responsibility of each operation?**

This question requires the architecture to specify how information moves between components, how one component is permitted to influence another, and how the system handles incomplete or contradictory information.

## 1.4 Thesis statement

This thesis advances the proposition that a classical AI architecture can become more reliable and inspectable when neural computation is used for learned representations and association, while explicit symbolic structures govern formal relationships, rule-based inference, and the derivation of conclusions from recorded premises.

The proposed 5 Senses architecture treats retrieval, memory, inference, learning, and evidence evaluation as distinct but cooperating functions. It does not assume that neural models provide truth, that symbolic rules guarantee correctness, or that retrieved documents are authoritative. Instead, it requires each component to expose the information needed by the next component while retaining the origin and status of its outputs.

The thesis will evaluate whether this separation of responsibilities, combined with controlled interaction between components, improves retrieval quality, inference correctness, explanation completeness, and the traceability of system conclusions.

## 1.5 Research questions

**RQ1 — Architectural integration:** How should neural models, symbolic reasoning, associative memory, and knowledge archives communicate so that their different computational responsibilities remain explicit?

**RQ2 — Knowledge representation:** How can the system represent facts, observations, predictions, and inferred claims without treating them as equivalent?

**RQ3 — Evidence and provenance:** How can a conclusion be connected to the documents, passages, transformations, and inference steps that contributed to it?

**RQ4 — Reliability:** Does combining neural and symbolic components improve performance on selected tasks compared with appropriately configured neural-only and classical baselines?

**RQ5 — Failure analysis:** What happens when the system encounters incomplete evidence, contradictory documents, incorrect predictions, corrupted memory patterns, or invalid inference rules?

These questions are intended to be experimentally answerable. They are not rhetorical questions whose answers can be established through architectural description alone.

## 1.6 Research objectives

1. Establish a precise conceptual distinction between neural learning, associative recall, retrieval, and symbolic inference.
2. Define a hybrid architecture with explicit information boundaries between its components.
3. Specify how claims, sources, uncertainty, and inference records should be represented.
4. Identify which capabilities are implemented in the 5 Senses repository and which remain proposed.
5. Construct reproducible experiments for the individual components.
6. Compare the integrated architecture against relevant baselines.
7. Examine failures rather than reporting only successful examples.
8. Establish whether the architecture provides measurable benefits in correctness, traceability, or interpretability.

## 1.7 Scope and boundaries

This thesis is concerned with a local-first classical AI research architecture. It does not attempt to establish that the proposed system possesses human consciousness, human-like understanding, or general intelligence.

It does not assume that a neural model can independently establish factual truth. It does not assume that a formal rule system is immune to incorrect premises. It does not treat a large document collection as a knowledge base merely because its contents can be indexed.

The research is concerned with computationally testable properties: representation accuracy, retrieval relevance, associative recall, rule correctness, inference traceability, source attribution, contradiction handling, reproducibility, and system performance.

The project also distinguishes the architecture described in this thesis from the state of the software repository. A proposed module is not an implemented module. An implemented module is not necessarily a validated module. A passing unit test does not establish broad real-world reliability.

---

# 2. Theoretical Foundations

## 2.1 Neural computation as learned representation

A neural network transforms inputs through parameterized computational operations. During training, its parameters are adjusted according to an objective function and an optimization procedure.

The significance of this process is not merely that a network produces an output. Its internal parameters can encode useful representations of recurring structures in the training data.

Rumelhart et al. (1986) showed how back-propagation could adjust internal connection weights to reduce output error. This made it possible for hidden units to develop task-relevant representations through learning rather than requiring every feature to be specified manually.

For 5 Senses, neural computation can identify patterns, produce representations, and estimate relationships. It should not automatically determine the factual status of the information it processes.

A neural prediction should therefore be represented as a prediction, with its model identity, input context, uncertainty information, and applicable limitations.

## 2.2 Associative computation as content-addressable memory

Associative memory differs from conventional address-based storage. In an address-based system, the caller identifies a location or key. In an associative system, retrieval can be initiated by presenting a pattern related to the stored information.

Hopfield (1982) developed a recurrent network model in which collective network dynamics support content-addressable memory. The network can move from a partial pattern toward a stored configuration under appropriate conditions.

This is relevant because a system may need to recover related information from incomplete or noisy representations. However, associative recall and factual verification must remain separate. A recovered pattern is a candidate memory, not proof that the remembered content is correct. The recovered representation must be connected to its stored record and provenance if it is to support a factual claim.

## 2.3 Symbolic representation as explicit structure

Symbolic systems represent information through defined entities, properties, relations, and rules.

A knowledge base might contain an entity representing a historical publication, a relation connecting that publication to an author, a date associated with a particular edition, a source record supporting the date, and a rule that determines whether the available information satisfies a defined condition.

The important characteristic is that these relationships are represented explicitly. A reasoning engine can operate over known structures rather than relying exclusively on statistical similarity.

However, symbolic inference is only as dependable as its representations, premises, and rules. A logically valid conclusion can still be factually wrong if one of its premises is incorrect. 5 Senses must therefore distinguish logical validity from evidential support.

## 2.4 Retrieval as candidate discovery

Information retrieval provides a mechanism for finding documents relevant to a query. Robertson and Zaragoza (2009) describe the probabilistic relevance framework and BM25, a family of ranking methods that use term-frequency and document-length information.

In the proposed architecture, retrieval has a specific responsibility: identify candidate information for further examination.

A high-ranking document is not automatically a reliable document. Relevance and authority are different properties. A document may be highly relevant while containing errors, outdated information, or unsupported interpretation.

The retrieval subsystem should preserve document identifiers, passage locations, metadata, query information, and retrieval configuration. A score estimates relevance; it does not establish truth.

## 2.5 Provenance as part of knowledge representation

Data provenance concerns the origin of information and the process through which it entered a derived result. Buneman et al. (2001) distinguish between sources that influenced the existence of a result and locations from which information was extracted.

For 5 Senses, provenance should not be treated as an optional citation added after an answer has been generated. It should be part of the internal representation of a claim.

A claim should be traceable to its original source, relevant document version, passage or data location, extraction or transformation process, inference rules applied, and resulting claim status.

Without this chain, the system may produce a plausible answer without being able to demonstrate how it arrived at that answer.

---

# 3. The Proposed 5 Senses Architecture

## 3.1 Architectural principle

The architecture is based on functional separation with controlled cooperation.

The existing Part II manuscript describes five responsibilities as **perception, memory, reasoning, association, and expression**. This thesis preserves those names rather than silently replacing them with a different five-part model. Other subsystems—such as document retrieval, neural execution, language processing, orchestration, and evidence evaluation—are supporting mechanisms that may contribute to one or more of the five responsibilities.

| Sense | Primary responsibility | Representative mechanisms |
|---|---|---|
| Perception | Receive and interpret input | Parsers, tokenizers, validators, feature extraction |
| Memory | Retain information | SQLite archive, document metadata, knowledge records |
| Reasoning | Evaluate information | Expert rules, inference procedures, evidence evaluation |
| Association | Identify related patterns | Neural networks, Hopfield memory, similarity methods |
| Expression | Communicate results | Response construction, citations, explanations |

This is an architectural classification, not a claim that every subsystem has already been implemented as a complete module.

A subsystem may contribute to more than one responsibility. A neural model may assist perception by classifying an input and association by identifying a related pattern. Its outputs must nevertheless retain their computational identity. A neural prediction must not silently become a verified archive record.

## 3.2 Why the functions must remain distinct

Consider a system asked whether a particular historical claim is supported by its archive.

Perception validates the question and prepares its representation. Memory and retrieval locate candidate documents. Association may identify related concepts or patterns. Reasoning represents claims and evaluates explicit relationships. Evidence evaluation examines source support and identifies conflicts. Expression communicates the result and its limitations.

If the neural model classifies a document as relevant, that classification must not be interpreted as confirmation of the historical claim. If a symbolic rule derives a date from two premises, the system must retain both premises and the rule. If two documents disagree, the system must preserve the disagreement rather than silently selecting whichever passage has the highest retrieval score.

## 3.3 Claim-centered information model

The proposed architecture treats the claim as a central object of evaluation.

| Field | Purpose |
|---|---|
| Claim identifier | Stable identity for the claim |
| Claim text | The proposition being evaluated |
| Claim type | Observation, prediction, reported fact, or inference |
| Subject and relation | Structured representation where available |
| Source references | Documents and passages supporting or challenging the claim |
| Derivation record | Rules and premises used to infer the claim |
| Confidence or uncertainty | Appropriate uncertainty information |
| Evidence status | Current evaluation status |
| Version information | History of changes and evaluations |

This is a proposed schema, not a statement that the repository already implements all these fields.

The system should avoid confusing a confidence score with a probability of truth unless the score has been calibrated and its interpretation has been experimentally established.

## 3.4 Evidence states

The project has previously used the following evidence vocabulary:

- `OFFICIAL`
- `CONSENSUS`
- `PLAUSIBLE`
- `SPECULATIVE`
- `UNKNOWN`

These labels should describe the current evidence assessment, not the rhetorical strength of an answer. `UNKNOWN` should not mean that a claim is false; it means the available evidence is insufficient to assign a stronger status.

The system should preserve conflicting sources and the reasons for the assigned status. A status without an explanation is only another opaque label.

---

# 4. Research Methodology and Evaluation

## 4.1 Research design

The thesis adopts a comparative experimental design. The proposed architecture must be evaluated against baselines that isolate the contributions of its components.

The comparison should include:

1. A classical baseline using structured records, keyword retrieval, and explicit rules.
2. A neural baseline using learned representations or classification.
3. A hybrid system combining neural and symbolic operations.
4. Ablation variants that remove one functional component at a time.

This design helps determine whether the combined system provides an actual benefit or merely contains more software.

## 4.2 Evaluation dimensions

| Research area | Candidate measurements |
|---|---|
| Document retrieval | Precision@k, Recall@k, MRR, nDCG, latency |
| Neural learning | Accuracy, macro-F1, loss, calibration, inference time |
| Associative memory | Exact recall, bit-error rate, corrupted-pattern recovery, spurious attractors |
| Symbolic reasoning | Inference correctness, rule coverage, contradiction handling |
| Evidence evaluation | Citation precision, provenance completeness, unsupported-claim rate |
| Integrated architecture | End-to-end correctness, explanation completeness, latency, component failure propagation |

Metrics must correspond to defined test cases and ground-truth annotations. Metrics alone do not establish that a system is reliable.

## 4.3 Experimental controls

Experiments must document dataset name and version, dataset license or applicable usage restrictions, acquisition date and source, cryptographic checksum where appropriate, preprocessing operations, training/validation/test splits, model architecture and parameter count, hyperparameters, random seeds, hardware and software environment, evaluation scripts, and baseline configurations.

The test set must not be used to select hyperparameters or repeatedly tune the system.

Where a model uses a differentiable training objective, the loss must remain connected to the model computation graph. A detached scalar loss cannot provide the intended gradient signal to model parameters.

## 4.4 Ablation experiments

The integrated architecture should be tested with individual components disabled:

- Remove symbolic reasoning while retaining neural predictions.
- Remove neural representations while retaining symbolic and retrieval functions.
- Remove associative recall while retaining ordinary archive retrieval.
- Remove provenance tracking while retaining answer generation.
- Remove evidence evaluation while retaining the other components.

The results should show whether each component contributes measurable value and whether some components introduce additional failure modes. A component should not be justified merely because it is historically interesting or theoretically attractive.

## 4.5 Research limitations

The architecture may encounter several limitations. Symbolic knowledge representation requires careful construction and maintenance. Neural models may produce incorrect predictions or poorly calibrated confidence estimates. Associative systems may retrieve spurious patterns. Retrieval ranking may favor textual similarity over source quality. Evidence evaluation may remain difficult when sources are incomplete, biased, or contradictory.

The thesis must also account for the cost of integration. More components can increase latency, maintenance requirements, and the number of possible failure paths. The experimental program must evaluate not only whether the architecture works, but also under what conditions it fails.

---

# 5. Expected Research Contribution

The thesis does not claim to invent neural-symbolic computing, associative memory, expert systems, or information retrieval. Those areas have established research histories.

Its proposed contribution is an integrated design discipline in which the system maintains explicit boundaries between learned predictions, stored information, formal inference, retrieved evidence, and evaluated claims.

The intended contribution has four dimensions:

**Architectural:** a defined division of responsibility between neural learning, associative memory, symbolic reasoning, and evidence evaluation.

**Representational:** a claim-centered model that retains source provenance and distinguishes predictions, observations, and inferences.

**Methodological:** a reproducible evaluation plan using baselines, ablations, controlled datasets, and explicit failure tests.

**Practical:** an implementation that can be inspected and tested locally, with capabilities and limitations documented rather than inferred from its description.

These contributions remain hypotheses until supported by repository inspection, implementation evidence, and experimental results.

---

# 6. Implementation and Evidence Plan

This thesis must be reconciled with the actual repository before implementation claims are made. The implementation chapter will map each architectural responsibility to concrete modules, public interfaces, data structures, tests, and known limitations.

For every claimed capability, the final manuscript should record:

| Evidence category | Required support |
|---|---|
| Implemented | Source path and relevant interface or function |
| Tested | Test path, test command, and observed result |
| Integrated | Integration test or reproducible execution path |
| Benchmarked | Dataset, configuration, script, raw result, and comparison |
| Proposed | Explicitly labeled design, not presented as existing functionality |
| Unverified | Known gap requiring inspection or experiment |

A passing unit test establishes only the behavior covered by that test. It does not prove general correctness, production readiness, or research superiority.

## 6.1 Candidate benchmark groups

The following are candidate experiments, not completed results.

**Document retrieval:** Compare SQLite keyword search and BM25. Measure Precision@5, Recall@10, mean reciprocal rank, nDCG@10, latency, and index size.

**Neural classification:** Compare a majority-class baseline, a classical classifier such as logistic regression, and a compact neural model. Measure accuracy, macro-F1, loss behavior, calibration, inference latency, and seed stability.

**Associative memory:** Evaluate exact recovery, noisy and partial recall, bit-error rate, spurious attractors, capacity, and recall time. Compare against a nearest-neighbor baseline.

**Symbolic reasoning:** Test valid and invalid inference, rule coverage, conflicting rules, missing premises, and explanation completeness.

**Evidence and provenance:** Test correct and incorrect source attribution, conflicting sources, incomplete citations, unsupported claims, OCR errors, and unresolved rights status.

**Integrated system:** Compare classical, neural, and hybrid configurations, followed by ablations that remove one component at a time.

Datasets such as Iris, UCI Wine, UCI Breast Cancer Wisconsin, MNIST, Reuters RCV1, and carefully selected public-domain texts may be considered. Each dataset requires a recorded version, license assessment, checksum, and reproducible split before use.

## 6.2 No fabricated results

No numerical result should appear in the results chapter until the corresponding experiment has been executed and its output preserved. Expected outcomes, hypotheses, and proposed metrics must not be written as findings.

---

# 7. Thesis Structure and Remaining Work

The complete thesis is planned as follows:

1. **Introduction:** Research problem, thesis statement, questions, objectives, and scope.
2. **Theoretical Foundations:** Classical AI, connectionism, associative memory, knowledge representation, retrieval, and provenance.
3. **The 5 Senses Architecture:** Functional responsibilities, data flow, claim representation, interfaces, and status transitions.
4. **Neural Models and Associative Computation:** Model selection, training, memory recovery, uncertainty, and failure analysis.
5. **Symbolic Reasoning and Knowledge Representation:** Facts, relations, rules, inference, contradiction handling, and explanations.
6. **Archives, Language, and Evidence:** Corpus acquisition, retrieval, language processing, source quality, and provenance.
7. **Implementation and Engineering:** Actual repository modules, software boundaries, testing, reproducibility, and implementation limitations.
8. **Experimental Design:** Datasets, baselines, metrics, ablations, and experimental controls.
9. **Results and Analysis:** Measured outcomes, statistical comparisons, error analysis, and interpretation. This chapter will be completed only after experiments have been run.
10. **Discussion and Conclusion:** Research contributions, limitations, implications, and future work.

---

# References

Buneman, P., Khanna, S., & Tan, W.-C. (2001). Why and where: A characterization of data provenance. In J. Van den Bussche & V. Vianu (Eds.), *Database theory—ICDT 2001* (pp. 316–330). Springer. https://doi.org/10.1007/3-540-44503-X_20

Hopfield, J. J. (1982). Neural networks and physical systems with emergent collective computational abilities. *Proceedings of the National Academy of Sciences, 79*(8), 2554–2558. https://doi.org/10.1073/pnas.79.8.2554

Marra, G., Dumančić, S., Manhaeve, R., & De Raedt, L. (2024). From statistical relational to neurosymbolic artificial intelligence: A survey. *Artificial Intelligence, 328*, Article 104062. https://doi.org/10.1016/j.artint.2023.104062

Robertson, S. E., & Zaragoza, H. (2009). The probabilistic relevance framework: BM25 and beyond. *Foundations and Trends in Information Retrieval, 3*(4), 333–389. https://doi.org/10.1561/1500000019

Rumelhart, D. E., Hinton, G. E., & Williams, R. J. (1986). Learning representations by back-propagating errors. *Nature, 323*, 533–536. https://doi.org/10.1038/323533a0

Wang, W., Yang, Y., & Wu, F. (2025). Towards data-and knowledge-driven AI: A survey on neuro-symbolic computing. *IEEE Transactions on Pattern Analysis and Machine Intelligence, 47*(2), 878–899. https://doi.org/10.1109/TPAMI.2024.3483273

Yu, D., Yang, B., Liu, D., Wang, H., & Pan, S. (2023). A survey on neural-symbolic learning systems. *Neural Networks, 166*, 105–126. https://doi.org/10.1016/j.neunet.2023.06.028
