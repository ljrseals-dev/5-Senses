# Vendored audited offline document MCP artifacts

The audited upstream deliverables are preserved byte-for-byte under this directory:

- `refactored-spoon-audited.zip` — upstream audited source archive.
- `0001-Audit-fixes-safe-FTS-search-idempotent-indexing-hone.patch` — upstream audit patch.

Upstream: https://github.com/ljrseals-dev/refactored-spoon  
Source revision: `b318f4149b770bc6bda264beba998ebaf7fe4661`

The archive and patch are intentionally kept as separate, immutable inputs. The integrity workflow pins their Git blob object IDs, validates the ZIP container, and parses the patch. It does not silently apply the patch or claim that the document MCP is already wired into the BODY OF SECRETS runtime. Runtime integration remains a separate, test-gated change because the upstream package requires Python 3.11+ while this repository's existing CI matrix includes Python 3.10.
