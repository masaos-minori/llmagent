# Decide the fate of the Reference document class via ADR

## Priority
High

## Summary
`docs/00_governance_01_documentation-policy.md`'s Document Classification defines a
"Reference" class (API/command/configuration reference material), but a proposed
documentation-slimming policy's mechanical-content removal criteria conflict with
hand-written Reference documents by design — their entire content is exactly the kind
of code-derivable listing the policy wants removed. This must be resolved as an
explicit architectural decision before any Reference-class document is edited under
that policy.

## Background
Three options were identified: (A) retire the Reference class, keep only
canonical-source pointers; (B) treat Reference documents as generated artifacts
(auto-produced from code/docstrings, hand-editing prohibited); (C) keep the status quo
and accept drift. `tools/generate_reference_table.py` already implements option (B)'s
pattern for MCP/RAG/deployment reference tables (guard-commented blocks — actual
format `<!-- AUTO-GENERATED: <generator>.py <purpose> -->`, e.g.
`GUARD_START_MCP`/`GUARD_START_DEPLOYMENT` — refreshed from `config/agent.toml` and
source). `docs/00_governance_04_documentation-checks.md`'s `GV-021`
(`check_docs_content_policy.py`) documents an intent to exempt this guarded content
from its mechanical-content warnings, but the exemption is currently implemented only
in `check_literal_port_number`, and its literal string check (`"<!-- AUTO-GENERATED -->"
in line`) does not match the actual guard format above — confirmed:
`"<!-- AUTO-GENERATED -->" in "<!-- AUTO-GENERATED: gen_mcp_reference.py
port-tool-reference -->"` evaluates to `False`. This has not surfaced as a live false
positive only because neither existing guarded block currently contains text the
literal-port-number regex matches. The exemption is therefore a stated intent, not yet
a working precedent, for Option B — see
`issues/20260918-130159_docschk01_extend-check_docs_content_policy-instead-of-new-tool.md`,
which should fix this before Option B is implemented against it.

## Problem
Without this decision, mechanical-content removal work cannot proceed against
Reference-class documents (e.g. an "Agent Reference API" or "Event Bus: Reference API"
document) without first knowing whether their content should be deleted, generated, or
left alone.

## Reason for Change
This decision gates several other follow-up items: extending
`tools/generate_reference_table.py`'s coverage, deciding which Reference documents are
in-scope for mechanical-content removal, and how `class: Reference` documents should be
detected.

## Implementation Intent
Write an ADR (in `docs/adr/`) recording the decision, its rationale, and consequences,
following `docs/00_governance_01_documentation-policy.md`'s ADR Section Header
Standardization. Recommend Option B (generated artifact) on the grounds that it
preserves the "one place to look" value Reference documents provide while keeping the
canonical source unique (a generated projection is not a competing copy), consistent
with `GV-021`'s existing exemption precedent — but this issue does not itself force
that outcome; the ADR review process decides.

## Target Files or Areas
`docs/adr/` (new ADR file); `docs/adr-index.md` (register the new ADR)

## Required Changes
- Draft a new ADR proposing the Reference-class disposition, covering the three
  options, their trade-offs, and a recommendation.
- Register the new ADR in `docs/adr-index.md` per its existing structure.
- If Option B is adopted, record the specific existing Reference-class documents that
  would migrate to generated status as an ADR "Implementation Notes" item (not
  implemented by this issue).

## Constraints
This issue produces the ADR only — it does not implement any generation tooling or
edit any existing Reference document's content (see Dependencies for the follow-up
issue that does).

## Acceptance Criteria
- A new ADR exists under `docs/adr/`, follows the standard section headers, and is
  registered in `docs/adr-index.md`.
- The ADR reaches an explicit Accepted/Proposed status per the project's ADR
  Acceptance Evidence Standard.

## Testing Expectations
Not required — this issue produces a governance document only, no code or runtime
behavior.

## Documentation Impact
Adds one new ADR and updates `docs/adr-index.md`'s ADR list/dependency graph.

## Out of Scope
Implementing the chosen option (tool changes, document edits) — tracked as separate,
dependent follow-up issues.

## Dependencies
Gates `issues/20260918-130225_docsref01_extend-generate_reference_table-for-agent-eventbus-memory.md`
(extends `tools/generate_reference_table.py`), and informs
`issues/20260918-130249_docsmeta01_add-class-front-matter-field.md` (specifically what
counts as `class: Reference`).

## Unresolved Questions
N/A: none — the three options and the existing `generate_reference_table.py`/`GV-021`
precedent were directly confirmed in the repository.

## AI Implementation Instruction
Produce the ADR only; do not pre-implement Option B's tooling in this issue even
though it is the recommended option — the ADR's own review/approval step is the gate.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260918-130115
- **Related target files**: docs/adr/, docs/adr-index.md
