# andrehacker account source audit — BODY OF SECRETS / 5-Senses

**Audit date:** 2026-11-20  
**Scope:** public repositories owned by `andrehacker`, plus the account's public project website.  
**Detailed machine-readable inventory:** `data/inventory/andrehacker_evidence.json`

## Result

The account-level crawl surfaced substantially more source material than the initial repository-name review. Eighteen public repositories were enumerated and screened. Seven repositories/sites contain material worth retaining as source evidence for BODY OF SECRETS; the remaining repositories are principally software, editor, configuration, or database-integration projects rather than general knowledge corpora.

The inventory currently contains **2,065 file records** across the seven relevant repositories/sites. Each record includes repository, branch, Git tree SHA, path, Git blob SHA, byte size, asset classification, and a rights state or rights warning. This is a metadata inventory; it did not download the corpus payloads into this repository.

## High-value findings

### 1. Historical reference text in `andrehacker/mapred`

The `testdata/books/` directory contains eight book/reference text files:

| Text | Source identity | Rights disposition |
|---|---|---|
| Encyclopaedia Britannica, 11th ed., Vol. 4, Part 3 (“Brescia” to “Bulgaria”) | Project Gutenberg #19699 | `PUBLIC_DOMAIN_VERIFIED` in the USA |
| The Art of War, Lionel Giles translation (1910) | Project Gutenberg #132 | `PUBLIC_DOMAIN_VERIFIED` in the USA |
| The Devil's Dictionary | Project Gutenberg #972 | `PUBLIC_DOMAIN_VERIFIED` in the USA |
| The Outline of Science, Vol. 1 of 4 | Project Gutenberg #20417 | `PUBLIC_DOMAIN_VERIFIED` in the USA |
| The Adventures of Sherlock Holmes | Project Gutenberg #1661 | `PUBLIC_DOMAIN_VERIFIED` in the USA |
| Ulysses | Project Gutenberg #4300; pre-1923 print text | `PUBLIC_DOMAIN_VERIFIED` in the USA |
| The Notebooks of Leonardo da Vinci, Complete | Legacy Gutenberg header; exact release mapping not established | `UNKNOWN_HOLD` |
| Hamlet | Legacy World Library electronic text; embedded notice states copyright 1990–1993 and personal-use/non-commercial restrictions | `RESTRICTED` |

The Britannica item is not a complete encyclopedia. It is exactly **Volume 4, Part 3**, covering entries “Brescia” through “Bulgaria”. Its source header identifies Project Gutenberg eBook #19699. The same exact Git blob (SHA-1 `eeaedce9f1b3d784f23d383786714daf68974931`, 1,945,886 bytes) appears at:
- `andrehacker/mapred/testdata/books/encyclopaedia-britannica.txt`
- `andrehacker/mapred/test-hadoop/input-big/encyclopaedia-britannica.txt`
- `ljrseals-dev/5-Senses/data/sample_corpus/encyclopedia/encyclopaedia-britannica-11th-vol4-part3.txt`

This proves that the existing 5-Senses sample is the same Git object as the text in the original mapred repository; it is not merely a similarly named file. The Project Gutenberg record confirms the edition, volume, part, entry range, and US public-domain status.

Do not treat the other seven texts as a single undifferentiated rights group. In particular, the embedded Hamlet notice is a restriction, and the Leonardo notebook file needs exact-version matching before reuse.

### 2. Pattern-recognition research archive: `andrehacker/fu-pattern-rec`

This is the strongest source for classical machine-learning methods and visual experiment evidence. Its twelve numbered exercise areas cover:

1. k-nearest neighbours (KNN)
2. Gaussian classification
3. Fisher linear discriminant
4. Linear regression / prostate data
5. Ridge regression, bootstrap, and feature selection
6. PCA and perceptron
7. Neural networks and backpropagation
8. Online/batch learning and resilient backpropagation (RPROP)
9. AdaBoost and face/non-face classification
10. Non-negative matrix factorization (NMF)
11. ID3 / smoke-feature classification study
12. WEKA and random forests

The detailed inventory records **319 non-image assets** and **418 image/plot assets** from this repository, including:
- 20 PDFs (reports and experiment visualizations)
- 13 TeX report sources
- 93 MATLAB `.m` files
- 135 MATLAB `.mat` numeric/model-state files
- 58 text/data/result files
- 418 EPS, PNG, and JPG visual assets

Important source files include:
- `u07-neural/neural.m` — two-layer sigmoid neural network with online backpropagation, random initialization, error tracking, XOR/AND/OR examples, and digit classification.
- `u08-rprop/bprop.m` and `u08-rprop/neural.m` — backpropagation and RPROP variants; the report compares online and batch learning.
- `u09-adaboost/adaboost.m` — AdaBoost implementation; accompanying face/non-face MAT arrays and plots are present.
- `u10-nmf/nmf.m`, `u10-nmf/doku-10.tex` — NMF implementation, factor matrices, reconstruction artifacts, and USPS handwritten-digit data.
- `u12-randforests/rf.m` — random-forest implementation with tree helpers and results.
- `u11-id3-smoke/doku-10.tex` — smoke classification problem analysis. The report explicitly says only three image sequences were available and that this was insufficient to train the classifiers they had studied. Treat this as a problem formulation and experiment record, not a trained smoke detector.

The MAT files are legacy numerical artifacts and factor matrices. They are not automatically equivalent to pretrained neural-network checkpoints. No conventional ready-to-use neural checkpoint bundle was identified in this pass.

The reports are coursework/technical reports by André Hacker and Dimitri Schachmann, not verified peer-reviewed papers. Their source code, report PDFs, data, and visualizations are valuable primary evidence, but their repository has no root license declaration. Keep reuse on `UNKNOWN_HOLD` until the applicable code, dataset, and report rights are checked separately.

### 3. Parallel logistic regression and RCV1: `andrehacker/logreg`

This repository contains 62 Java source files in the indexed set, nine small experiment fixtures, and a README. The README describes:
- ensemble and SGD training
- iterative batch gradient descent
- iterative L-BFGS
- parallel gradient computation
- forward feature selection using single-feature optimization

It includes RCV1-v2 preprocessing support and a dataset information class, but **does not contain the Reuters Corpus Volume I dataset itself**. The source explicitly cites:

Lewis, David D.; Yang, Yiming; Rose, Tony G.; and Li, Fan. “RCV1: A New Benchmark Collection for Text Categorization Research.” *Journal of Machine Learning Research*, 5 (2004), 361–397.

The paper is openly available from JMLR. The Reuters dataset is a separate research-use resource; do not assume that its absence from this repository grants redistribution or training rights.

### 4. Technical knowledge articles: `andrehacker/Public-Knowledgebase`

This repository is a fork of `exasol/public-knowledgebase`, not a general encyclopedia. The indexed tree contains **341 Markdown articles and 445 screenshots/illustrations** organized into five Exasol product categories:
- Connect With Exasol
- Data Science
- Database Features
- Environment Management
- Support and Services

It contains four reusable article structures:
- Question and Answer
- Solution to a Problem
- Tutorial
- Explanation

These templates are useful for the Archive's article schema and provenance discipline. The content is product-specific Exasol troubleshooting and tutorials, not general world knowledge. Neither the fork nor the upstream repository declares a repository-level license in the inspected metadata, so do not bulk-copy or train on the articles/images until rights are resolved.

### 5. Food statistics visualization: `andrehacker/foodbrowser`

This is a visualization and ETL project that states it uses FAOSTAT data for crop/food statistics. Its repository contains reference CSVs for countries, country groups, items, units, flags, and abbreviations, plus SQL transformations and notes. It does **not** appear to include the complete FAOSTAT statistical time-series corpus. The upstream FAOSTAT data should be acquired separately with its source/version and reuse terms recorded.

### 6. Other document and visualization evidence: `andrehacker/misc`

This repository includes three advanced C++ course PDFs/notes and one web-technology seminar PDF, plus project screenshots/icons and text notes. The detailed inventory includes 426 records from this repository, but many of its 415 image files are application/icon assets rather than knowledge visualizations. It is not an encyclopedia corpus.

### 7. Bachelor thesis lead: `andrehacker/andrehacker.de`

The personal site links to:

`https://www.andrehacker.de/cv/thesis-andre-hacker-printed-20131105.pdf`

The site describes the BSc thesis as implementing a machine-learning algorithm and evaluating Stratosphere and Hadoop qualitatively and through benchmarking. The PDF could not be retrieved in this pass, so its title, contents, citations, and license remain **unreviewed / UNKNOWN_HOLD**. It is a high-priority next source to recover because it may connect the logistic-regression work, Stratosphere, Hadoop, and the author's original research.

## Papers and textbook leads found in source text

| Source | Bibliographic evidence | State |
|---|---|---|
| RCV1 paper | Lewis, Yang, Rose, Li, JMLR 5 (2004), 361–397 | Full citation found in `logreg` source |
| Bishop textbook | Christopher M. Bishop, *Pattern Recognition and Machine Learning*, Springer, 2006 | `fu-pattern-rec/u08-rprop/doku-8.tex` cites “Bishop” without full bibliography |
| Hastie reference | “Hastie (2011)” | `fu-pattern-rec/u05-selection/doku-5.tex` cites surname/year only; exact book/edition unresolved |
| BSc thesis | PDF linked from personal site | Link found, PDF not inspected |

The RCV1 citation is verified against the JMLR record. The Bishop title/year is verified against Springer. The Hastie reference is intentionally left unresolved rather than guessing which edition or work was intended.

## What the earlier crawl missed

The most consequential misses were:
- the entire `fu-pattern-rec` course archive and its MATLAB algorithms, data, PDFs, and experiment plots;
- the eight-book corpus in `mapred/testdata/books`;
- the exact identity match between the mapred Britannica file and the existing 5-Senses sample;
- the RCV1 JMLR paper citation inside the logistic-regression source;
- the BSc thesis link on the account's personal website;
- hundreds of visual assets and screenshots across the repositories;
- FAOSTAT reference metadata and its visualization/ETL project.

## Acquisition and preservation rules

1. Preserve original repository paths, Git tree SHAs, Git blob SHAs, and file sizes. Do not flatten or rename originals.
2. Preserve duplicate paths when they demonstrate use in separate projects; deduplicate only the stored payload, not the provenance records.
3. Keep raw files immutable. Any OCR cleanup, normalization, or conversion must produce a separate derivative with its own checksum and transformation log.
4. Do not import the restricted Hamlet text into a training corpus. Keep the Leonardo notebook file on hold until its exact edition is resolved.
5. Treat course reports, source code, datasets, and plots as separate rights-bearing asset classes.
6. Do not call MAT factor matrices pretrained neural weights. Inspect the variable names, dimensions, training method, and source report first.
7. A downloaded public-domain volume is not evidence that a complete multi-volume encyclopedia has been acquired. Track every volume/part independently.

## Inventory coverage and limitations

The inventory is a recursive-tree snapshot of the selected public repositories, not a complete Git-history crawl. It does not enumerate every historical commit, every external link target, or every file in third-party submodules. Some binary PDFs were inventoried by Git blob SHA and size but not text-extracted. The thesis PDF remains an unreviewed external link. No new corpus payloads were downloaded by this audit.

The current machine-readable inventory has 2,065 artifact records. Re-run the tree crawl after any upstream repository changes; compare tree SHAs before assuming the snapshot is current.
