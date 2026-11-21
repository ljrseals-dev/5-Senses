# 5-Senses CB-MultiOS REMATCH Defensive Learning Set

**Status: draft, quarantined, not training-ready.** This corpus contains one defensive summary for each of the six top-level REMATCH challenges in Trail of Bits' `cb-multios` repository.

## Scope and provenance

- Upstream: https://github.com/trailofbits/cb-multios
- Upstream ref reviewed: `master`
- Upstream tree SHA recorded in `rematch_manifest.json`: `810d7b24b1f62f56ef49b148fe155b0d0629cad2`
- Six challenge READMEs reviewed; eight author-supplied CWE labels transcribed.
- The challenge binaries are synthetic DARPA Cyber Grand Challenge artifacts. No CVE is assigned to these synthetic challenge binaries. Historical CVE references in upstream READMEs are retained only as inspiration/context metadata.

## Label discipline

`cwe_mappings[].name` preserves the label as supplied by the challenge README. `cwe_mappings[].mitre_catalogue` stores a separately checked MITRE catalogue title, catalogue entry version, URL, and mapping guidance. These are not interchangeable. In particular:

- CWE-215's current MITRE title is **Insertion of Sensitive Information Into Debugging Code**; the older upstream wording is preserved.
- MITRE currently marks CWE-788 as discouraged for mapping real-world vulnerabilities. The corpus retains CWE-788 only because it is the challenge author's explicit classification; it is not represented as a new analyst-approved real-world vulnerability mapping.
- Historical CVEs are not challenge identifiers and must never be converted into CVE labels for these synthetic artifacts.

MITRE catalogue references: https://cwe.mitre.org/data/definitions/120.html, https://cwe.mitre.org/data/definitions/121.html, https://cwe.mitre.org/data/definitions/135.html, https://cwe.mitre.org/data/definitions/193.html, https://cwe.mitre.org/data/definitions/215.html, https://cwe.mitre.org/data/definitions/788.html, https://cwe.mitre.org/data/definitions/798.html.

## Safety and use

The records contain high-level defensive descriptions and provenance only. They do not include vulnerable challenge source, POV payloads, exploit instructions, or operational trigger sequences. They are suitable for controlled Archive retrieval and human review, **not** automatic model training, exploit generation, or automatic Expert rule promotion.

Every record remains `training_status: quarantined_not_training_ready`. Independent review of the challenge semantics, schema tests, and any future corpus acceptance are separate gates. Importing into Archive does not imply training acceptance.

## Files

- `rematch_cwe.jsonl` — six structured challenge summaries with upstream labels and separate MITRE catalogue metadata.
- `rematch_labels.csv` — compact review index; upstream labels are preserved.
- `rematch_manifest.json` — scope, source tree identity, counts, and validation state.
