---
title: "Documentation Checks"
area: governance
tags:
  - governance
related:
  - 00_index.md
  - overview_00_document-guide.md
---

# Documentation Checks

## Purpose

This document defines the automated and manual checks that validate the quality, consistency, and correctness of the LLM agent design documentation set. It ensures documentation remains aligned with implementation and maintains structural integrity.

## Automated Checks

The full, current list of documentation checkers and when to run each one is the Tools table in `routing.md` ("When to run which tool"); that table is the single source of truth for invocation. The sections below describe what each governance-relevant check verifies and where it is enforced (pre-commit or CI).

### 1. Document Quality Check (`check_docs_quality.py`)

Checks all documents under `docs/*.md` for quality issues.

**Core checks:**
- Broken headings (malformed section headers)
- Malformed Markdown tables
- Unclosed inline code blocks
- JSON examples without fence markers
- Duplicate heading numbers
- Resolved issue mentions in active documents

**Custom rules:**
- Dynamically loaded from `config/doc_quality_rules.json`

**Usage:**
```bash
python tools/check_docs_quality.py                          # run all core + custom
python tools/check_docs_quality.py --core-only              # only core checks
python tools/check_docs_quality.py --custom-only            # only custom rules
python tools/check_docs_quality.py --skip broken_headings   # skip specific check
python tools/check_docs_quality.py --only stale_patterns    # only specific check
python tools/check_docs_quality.py docs/*.md                # check specific files
```

### 2. Domain Consistency Check (`check_docs_consistency.py`)

Checks consistency between documentation and source code for each domain.

**Domains:**
- `agent` — Agent-related docs vs `scripts/agent/`
- `mcp` — MCP server docs vs `scripts/mcp_servers/`
- `rag` — RAG docs vs `scripts/rag/`
- `deployment` — Deployment docs vs config/deployment files
- `overview` — Overview docs vs overall project structure

**Checks performed per domain:**
- Schema drift (DB schema vs documented schema)
- Config key presence (documented config keys exist in actual config)
- Port drift (documented ports match actual configuration). Decision under
  the docs content policy (`skills/DESIGN.md` Docs content policy —
  remove, "literal port number" category): `check_port_drift()` and
  `check_port_range_claim()` remain active pending a documented, explicit
  exemption list, because deprecating or narrowing either function would silently stop
  catching real port-configuration drift in files that still legitimately state a port
  number.
- Tool name drift (documented tool names match actual implementations)
- Crawler config drift (documented crawler configs match actual configs)
- Debug output existence (documented debug outputs exist)
- DB count claim (documented DB counts match actual)
- DB table completeness (documented tables exist in actual DB)
- Command drift (documented commands match actual CLI commands)
- File path references (documented file paths exist)
- Function references (documented function signatures match actual)
- Broken internal links (`.md` links resolve correctly)
- Removed file references (references to deleted files detected)

**Usage:**
```bash
python tools/check_docs_consistency.py --domain agent              # check agent docs
python tools/check_docs_consistency.py --domain mcp                # check mcp docs
python tools/check_docs_consistency.py --domain rag                # check rag docs
python tools/check_docs_consistency.py --domain deployment         # check deployment docs
python tools/check_docs_consistency.py --domain overview           # check overview docs
python tools/check_docs_consistency.py --domain agent --skip schemadrift  # skip a check
```

### 3. Needs Confirmation Inventory Check (`check_needs_confirmation_inventory.py`)

Verifies the NC inventory stays in sync with `docs/*.md`.

**Checks:**
- "Needs confirmation" mentions in docs are registered in the centralized inventory (`governance_03_issue-and-uncertainty-management.md`)
- Resolved NC items do not leave markers in source documents
- Field count declarations match actual list item counts

**Exit behavior:** WARNING findings (including untracked inline markers) do not cause a non-zero exit; only ERROR findings produce a non-zero exit.

### 4. Backward Compatibility Check (`check_compat_shims.py`)

Checks for stale compatibility layers left behind after API migrations.

**Scanned directories:**
- `scripts/`
- `docs/`
- `tests/`
- `tools/`

**Removed-name reintroduction detection** (`check_removed_name_reintroduction()`,
opt-in via `--check-removed-names`, default off): flags a name confirmed absent
from source code being presented as current in `docs/*.md`, outside historical
context. Two cases require different detection strategies:
- **Name confirmed fully absent from source** (e.g. `_update_null_fill`;
  `ToolRouteResolver`+`server_configs` co-occurrence, section-scoped) — a simple
  grep-vs-source-absence check suffices. Implemented.
- **Name that remains in source but is no longer the current production path**
  (e.g. `read_json_file`, still defined in
  `scripts/rag/ingestion/pipeline_utils.py` but no longer the current production
  reader) — requires checking whether a *current-specification* section presents
  it as production, not merely whether the identifier string appears in `docs/`.
  Not yet implemented (follow-up).

**Historical-reference allowlist**: a line within 10 lines of an explicit marker
(`legacy`, `historical`, `archive only`, `resolved`, `was:`, `removed`) is exempt
from this check (`_HISTORICAL_CONTEXT_MARKERS` / `_is_historical_context()`).

### 5. Suppression Justification Check (`check_suppression_justification.py`)

Validates that `# noqa`, `# type: ignore`, and `# nosec` comments have proper rule/error-code justification with em-dash separator.

**Scanned directories:**
- `scripts/`
- `tests/`

### 6. Docstring Format Check (`check_docstrings.py`)

Validates Python module-level docstring format in `scripts/`.

**Checks:**
- Presence of em-dash (U+2014)
- Correct `scripts/<path> — description` format

**Note:** This script only validates existing docstrings; it does NOT add or modify them.

### 7. Tool Descriptions Sync Check (`check_tool_descriptions_sync.py`)

Compares file names listed in `tools/TOOL_DESCRIPTIONS.md` against actual `tools/*.py` files to detect drift in both directions (unlisted additions / deleted references).

### 8. Documentation Structure Validation (`check_docs_structure.py`)

Validates structural conventions for `docs/*.md`:
- File size limits (a per-file exception list covers documents the owner accepted above the limit)
- H1 heading count (exactly one per document)
- Front Matter presence and required fields
- Keywords section; no body Related section in any document (general or ADR); ADRs keep `## Related ADRs` and `## Implementation References` as ordinary sections
- Front matter `related:` of each ADR covers the documents its body `.md` references
- Internal `.md` link reachability

**Usage:**
```bash
uv run python tools/check_docs_structure.py [glob ...]
uv run python tools/check_docs_structure.py 'docs/23_agent/*.md' --area agent
```

### 15. Docs Content Policy Check (`check_docs_content_policy.py`)

Checks all `docs/*.md` for implementation-detail content the docs content
policy prohibits: full file trees, per-file descriptions embedded in a tree
or table, class/function/method index tables, implementation-location
mappings, and literal port numbers (see `skills/DESIGN.md` Docs content
policy — remove). Report-only (Warning) — findings never block CI; see
`GV-021` below.

**Usage:**
```bash
uv run python tools/check_docs_content_policy.py
```

### 16. ADR Structure Check (`check_adr_structure.py`)

Validates `docs/10_adr/*.md` structure:
- `## Known Deviations` heading presence (missing → Error)
- Notes vs References path drift (a `scripts/`/`tests/` path in
  Implementation Notes absent from Implementation References → Warning;
  skipped if Notes cites zero such paths)

**Usage:**
```bash
python tools/check_adr_structure.py
python tools/check_adr_structure.py --format json
```

### 17. Known Deviation Sync Check (`check_known_deviation_sync.py`)

Verifies that Known Issue IDs cited by an ADR's `## Known Deviations` section exist as entries in `governance_03_issue-and-uncertainty-management.md` Part 1, and that an ADR bullet's resolved-or-open signal agrees with the entry's Status. A cited ID with no entry is reported as a dangling reference (Warning).

**Enforcement:** local run only — not wired into pre-commit or `.github/workflows/`.

**Usage:**
```bash
uv run python tools/check_known_deviation_sync.py
```

### 18. ADR Invariant Matrix Checks (`check_adr_invariant_matrix.py`, `check_adr_reference.py`)

Verify the ADR Invariant Verification Matrix in `docs/10_adr/adr-index.md`: every pytest node id or test path cited in a `Verification Status` cell exists, and every `scripts/` source file cited there carries an `ADR-XXX` comment.

**Enforcement:** pre-commit.

### 19. Canonical Source Registry Checks (`check_canonical_source_registry.py`, `check_canonical_source_conflicts.py`)

Validate `config/documentation_canonical_sources.toml`: schema conformance, path existence, a single normative source per claim type, ADR-status conformance, and semantic conflicts between registered sources (`GV-022`, `GV-023`, `GV-024`).

**Enforcement:** `.github/workflows/governance-docs-consistency.yml`.

### 20. Issue Inventory Conformance Check (`check_issue_inventory_conformance.py`)

Verifies `governance_03_issue-and-uncertainty-management.md` against its own template: vocabulary values, per-entry field counts, and referential integrity (`GV-008`).

**Enforcement:** `.github/workflows/governance-docs-consistency.yml`.

## Manual Checks

Numbering continues from `## Automated Checks` above (items 1-8 and 15-20); items 9-14 below were assigned before items 15-20 were added, so the full sequence appears across both sections in creation order, not strict document order.

### 9. Canonical Source Verification

When conflicts arise between documentation and code/config, apply the precedence hierarchy defined in `governance_01_documentation-policy.md`:

1. Canonical authority resolved per claim type and decision target — see `governance_01_documentation-policy.md`'s Claim Type Taxonomy and Decision Target Canonical Source Matrix
2. Recency (review/modification/commit date) never determines canonical authority — see `governance_01_documentation-policy.md`'s Recency Is Not Authority subsection
3. The area's document-guide identifies the canonical source within that area

### 10. Evidence Label Validation

Verify evidence labels on statements match their actual grounding level:

1. **Explicit in code** — Directly observable in source code
2. **Strongly implied by code** — Inferred from code structure/patterns
3. **Documentation only** — Exists only in documentation without code verification
4. **Needs confirmation** — Accuracy unverified against implementation
5. **Deprecated** — Describes an obsolete feature no longer in use. Distinct from `docs/00_governance/governance_02_documentation-metadata.md`'s Terminology Glossary terms `Obsolete` (a name still present and callable, but no longer the current production path) and `Dead Code` (a name with zero current callers): this evidence label classifies how well a *statement* is grounded, not the compatibility lifecycle of the thing the statement describes.
6. **Verified by test** — Confirmed through automated tests
7. **Operationally observed** — Based on runtime behavior observations

### 11. ADR Section Header Compliance

All ADRs must use the following section headers in this order:

1. Context (Problem, Constraints)
2. Assumptions
3. Decision
4. Rationale
5. Alternatives Considered
6. Consequences (Positive Consequences, Negative Consequences)
7. Invariants (non-negotiable constraints)
8. Verification
9. Implementation Notes
10. Known Deviations
11. Review Triggers
12. Approval
13. Related ADRs
14. Implementation References
15. Completion Checklist

See [Policy's ADR Section Header Standardization](governance_01_documentation-policy.md#adr-section-header-standardization) for duplicate notes shared across all ADRs.

### 12. Area Dependency Graph Validation

Canonical source: the dependency-graph taxonomy (Software Runtime Dependency Graph,
Deployment Management Graph, Documentation Reference Graph, Governance Applicability
Matrix) is defined in `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` — see that
document's sections by these names. This document does not duplicate the edge list.

**Automated** (Software Runtime Dependency Graph only): `tools/check_dependency_graph_cycles.py`
parses the Software Runtime Dependency Graph's edge list from
`docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` and fails if a cycle exists among its
5 in-scope nodes (Agent, MCP, RAG, EventBus, Shared/DB). Wired into
`.github/workflows/governance-docs-consistency.yml`.

**Manual** (all other relation types): the Deployment Management Graph, Documentation
Reference Graph, and Governance Applicability Matrix are not cycle-checked by any
tool — see each section's own cycle-tolerance statement in
`docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` — and remain subject to human review
only.

### 13. Merge Condition Validation

Merge is gated on [Policy's Merge Conditions](governance_01_documentation-policy.md#merge-conditions)
(Blocking/Non-Blocking conditions and the Merge Workflow) — see that
section for the full list, including the `GV-020`-specific
removed-name-reintroduction condition this checker enforces.

A `GV-020` finding is not itself blocking, but every finding must be resolved or
covered by an approved temporary exception before merge — an unexplained finding
left neither fixed nor excepted is treated as incomplete review, not a passing PR.

### 14. Cross-Area Reference Validation

Verify that cross-document references follow the Link Rules in [governance_02_documentation-metadata.md](governance_02_documentation-metadata.md#link-rules).

**Link format examples:**
- Same area: `[Documentation Policy](governance_01_documentation-policy.md)`
- Cross area: `[RAG Guide](../21_rag/rag_00_document-guide.md)`
- ADR: `[ADR-001](../10_adr/ADR-001-workflow-engine-mandatory.md)`
- Internal anchor: `[Section](governance_01_documentation-policy.md#review-rule)`

## Governance Verification Matrix

Maps governance rules to their enforcement methods, distinguishing auto-validated
rules from Manual Review rules. Tracks whether each rule currently has an inspection
tool and identifies follow-up work needed.

Canonical document codes: **Pol** = `governance_01_documentation-policy.md`, **Meta**
= `governance_02_documentation-metadata.md`, **Iss** =
`governance_03_issue-and-uncertainty-management.md`, **Chk** = this document.

| Rule ID | Rule | Doc | Method | Tool/Review | Timing | Gate | Status | Follow-up |
|---------|------|-----|--------|--------------|--------|------|--------|-----------|
| GV-001 | Required Front Matter | Meta | Auto | `check_docs_structure.py` | PR | Blocking | Existing | None |
| GV-002 | Valid Document Status | Meta | Auto | `check_docs_structure.py` | PR | Blocking | Existing | None |
| GV-003 | Unique ADR ID | Pol | Auto | `check_docs_structure.py` | PR | Blocking | Existing | None |
| GV-005 | Related section placement (no body Related section anywhere; ADRs keep `## Related ADRs`/`## Implementation References`; front matter `related:` covers body `.md` references) | Meta | Auto | `check_docs_structure.py` | PR | Warning | Existing | None |
| GV-006 | Self-reference prohibition | Meta | Auto | `check_docs_structure.py` | PR | Warning | Existing | None |
| GV-007 | Duplicate Related Link prohibition | Meta | Auto | `check_docs_structure.py` | PR | Warning | Existing | None |
| GV-008 | Issue inventory conformance: vocabulary, template, referential integrity | Iss | Auto | `check_issue_inventory_conformance.py` | PR | Blocking | Existing | Implement |
| GV-009 | Needs Confirmation owner and deadline | Iss | Auto | `check_needs_confirmation_inventory.py` | PR | Warning | Existing | None |
| GV-011 | Duplicate canonical document specification | Pol | Manual | Human review | PR | Warning | Partial | Automate cross-document canonical source conflict detection (currently manual) |
| GV-012 | Multiple Primary Canonical Sources within the same area | Pol | Manual | Human review | PR | Warning | Partial | Automate cross-document canonical source conflict detection (currently manual) |
| GV-013 | References to non-existent canonical documents | Pol | Auto | `check_docs_structure.py` + `check_docs_quality.py` | PR | Warning | Partial | Extend stale_patterns config |
| GV-014 | Code is NOT canonical for adopted design decisions | Pol | Auto | `check_compat_shims.py`, `check_adr_invariant_matrix.py`, `check_adr_reference.py` | PR | Warning | Existing | Optional: run cited tests in CI, not just verify path existence |
| GV-015 | Software vs Documentation dependency graph separation | Pol | Manual | Human review | PR | Warning | Existing | None |
| GV-016 | No unimplemented auto-checks documented as implemented | Chk | Manual | Human review | Periodic | Warning | Partial | Automate auto-check implementation audit (currently manual) |
| GV-018 | Glossary limited to project-specific terms | Meta | Manual | Human review | Periodic | Warning | Partial | Automate glossary term classification validation (currently manual) |
| GV-019 | No unnecessary Metadata or Status fields added | Meta | Manual | Human review | Periodic | Warning | Partial | Automate metadata field usage policy enforcement (currently manual) |
| GV-020 | Removed-name reintroduction in current specifications | Chk | Auto | `check_compat_shims.py --check-removed-names` | PR | Warning | Partial | Implement the context-aware (retained-but-superseded) detection case; promote to default-on once the corpus is compliant |
| GV-021 | Docs content policy violation (implementation detail in docs/*.md) | Chk | Auto | `check_docs_content_policy.py` | PR | Warning | Partial | Not yet wired into CI (`.github/workflows/`); promote to default-on (PR-gated) once wired |
| GV-022 | Canonical source conflict routing and deduplication | Pol | Auto | `check_canonical_source_conflicts.py` | PR | Blocking | Existing | None |
| GV-023 | Canonical Source Registry schema/path/ADR-status conformance | Pol | Auto | `check_canonical_source_registry.py` | PR | Blocking | Existing | None |
| GV-024 | Canonical source registry schema wrapping (missing/invalid source, unknown claim type, Draft/Proposed normative source) | Pol | Auto | `check_canonical_source_conflicts.py` | PR | Blocking | Existing | None |

### Follow-up Work Needed

Rules marked "Missing" or "Partial" above need new inspection tools or processes:

1. **GV-011, GV-012**: Automate cross-document canonical source conflict detection (currently manual)
2. **GV-013**: Extend `stale_patterns` custom rule config to cover canonical document references
3. **GV-014**: Optional scope — run each cited test in CI, not just verify that the cited path
     exists.
4. **GV-016**: Automate auto-check implementation audit (currently manual)
5. **GV-018**: Automate glossary term classification validation (currently manual)
6. **GV-019**: Automate metadata field usage policy enforcement (currently manual)
7. **GV-020**: Implement the `read_json_file`-style context-aware detection case (a name
     retained in source but no longer the current production path); promote
     `--check-removed-names` from opt-in to default-on once the corpus is compliant, per
     `check_compat_shims.py`'s own "report-only until compliant" convention. The retired
     identifier patterns and historical-context markers are defined in
     `tools/check_compat_shims.py` (`_REMOVED_NAME_PATTERNS`, `_HISTORICAL_CONTEXT_MARKERS`).
8. **GV-021**: `check_docs_content_policy.py` is not wired into any CI workflow
     (`.github/workflows/`) — its Warning findings are report-only, produced by a
     local/manual run rather than enforced on every PR. Promote it to default-on
     (PR-gated) once wired into CI; until then, the Matrix Status is `Partial`, not
     `Existing`.

## Change Impact Assessment

See [Change Impact Rule and Change-Impact Matrix](governance_05_change-impact-and-dependency-graphs.md#change-impact-rule)
for the full procedure and matrix determining which documents are
affected by a change.

## Review Gate Conditions

See [Policy's Review Rule](governance_01_documentation-policy.md#review-rule)
for the conditions that require review before merging.

## Maintenance Rules

See [Policy's Maintenance Rules](governance_01_documentation-policy.md#maintenance-rules).

## Non-Goals

Same as the Non-Goals in [governance_01_documentation-policy.md](governance_01_documentation-policy.md#non-goals).

## Keywords

documentation checks
validation
automated checks
manual checks
quality assurance
consistency
ADR compliance
evidence validation
verification matrix
