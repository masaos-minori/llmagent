## Goal
Draft a new ADR (`docs/adr/ADR-015-reference-document-class-disposition.md`)
recording the Reference-class document disposition decision (`REQ-001`, `REQ-003`,
`REQ-004`).

## Scope
In scope: creating this one new ADR file with the standard section headers,
covering all three options (retire / generate / status-quo), a recommendation,
and reaching an explicit Status. Out of scope: implementing the chosen option
(tool changes, document edits) — tracked by
`issues/20260918-130225_docsref01_extend-generate_reference_table-for-agent-eventbus-memory.md`
(now `plans/20260919-105034_plan.md`).

## Assumptions
- ADR-015 is still the next available number: re-confirmed `docs/adr/` currently
  contains ADR-001 through ADR-010, ADR-012, ADR-013, ADR-014 — no ADR-011 or
  ADR-015 file exists.
- `docs/00_governance_01_documentation-policy.md`'s ADR Section Header
  Standardization (Context (Problem, Constraints), Assumptions, Decision,
  Rationale, Alternatives Considered, Consequences (Positive/Negative),
  Invariants, Verification, Implementation Notes, Known Deviations, Review
  Triggers, Approval, Related Documents, Completion Checklist) is unchanged since
  the Plan was written — re-confirmed at `docs/00_governance_01_documentation-policy.md:381`.

## Design decisions
Structure the ADR's Alternatives Considered section around the 3 options exactly
as the source issue's Background lists them (A: retire the Reference class; B:
generated artifact; C: status quo/accept drift), and recommend Option B — this
mirrors the existing, working precedent (`tools/generate_reference_table.py`'s
guard-comment pattern for MCP/RAG/deployment reference tables) rather than
inventing a new mechanism, keeping the "one place to look" value Reference
documents provide while making the canonical source (the code) unique.

## Alternatives considered
Recommending Option A (retire the Reference class entirely) was considered, but
Option B better fits this repository's existing "generate from code" pattern (see
Design decisions) and preserves more reader value; Option C (status quo) was
rejected as the source issue's Reason for Change explicitly identifies drift as
the problem being solved.

## Implementation
### Target file
docs/adr/ADR-015-reference-document-class-disposition.md

### Procedure
1. Create the new file with YAML front matter (`title`, `area: governance`, per
   the existing ADR-file convention — e.g. `docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md`'s
   front matter as the style precedent).
2. Write each of the 14 standard sections in the required order (see Assumptions
   above for the exact list), including the 3 duplicate boilerplate notes every
   ADR carries (per `docs/00_governance_01_documentation-policy.md`'s ADR Section
   Header Standardization: "この章は設計判断の根拠にしない", "該当しない場合は「対象外」と記載する",
   "ADR本文を現行実装へ無条件に合わせず、差異はKnown Issueで管理する").
3. Set an explicit Status (`Proposed` or `Accepted`) in the Approval section,
   satisfying the ADR Acceptance Evidence Standard (a Named Approval Record, or
   an explicit task-level approval decision stated as such — never `pending`).

### Method
Direct file creation (`Write` tool) following an existing ADR file (e.g.
`docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md`) as the
structural template for front matter and section order.

### Details
- **Context (Problem, Constraints)**: state the conflict between the Reference
  document class and the mechanical-content removal policy, per the source
  issue's Problem section.
- **Decision**: the chosen option (recommend Option B per Design decisions, but
  the ADR's own review/approval step decides — do not pre-commit the Status to
  Accepted in this document if review has not actually occurred).
- **Rationale**: the "one place to look" + "canonical source stays unique"
  argument from Design decisions above, cross-referencing the existing
  `tools/generate_reference_table.py` precedent by file path (not restating its
  code).
- **Alternatives Considered**: Options A/B/C with trade-offs, per Design
  decisions/Alternatives considered above.
- **Consequences (Positive/Negative)**: Positive — drift-proofing, single source
  of truth; Negative — requires building 3 new generator functions (tracked
  separately) before any migration can happen; the guard-detection bug
  (`tools/check_docs_content_policy.py`'s `check_literal_port_number` exemption
  not matching the actual guard format) must also be fixed first (tracked by
  `plans/20260919-104809_plan.md`) or the guarded blocks this ADR's Option B
  implies will not actually be exempt from mechanical-content warnings.
- **Invariants**: "A Reference-class document that is Option-B-migrated has
  content generated only from its guard-comment pair, never hand-edited between
  the guards."
- **Verification**: "Run the corresponding `generate_reference_table.py --type`
  and confirm the guarded block matches current source" (once implemented).
- **Implementation Notes**: if Option B is adopted, name the specific
  Reference-class documents planned for migration — cite
  `plans/20260919-105034_plan.md`'s target list (Agent: `docs/agent_13_reference-api.md`;
  EventBus: `docs/06_eventbus_06_reference-api.md`; Memory: the 6-candidate list
  recorded in that Plan's REQ-003/UNK-01) rather than re-deriving it here.
- **Known Deviations**: "対象外" if none identified.
- **Review Triggers**: e.g. "A new Reference-class document is proposed" or "the
  generated-artifact tooling's scope changes materially."
- **Approval**: state the Status decision and its evidence per the ADR
  Acceptance Evidence Standard (see Completion criteria).
- **Related Documents**: `docs/00_governance_01_documentation-policy.md`
  (Document Classification), `tools/generate_reference_table.py`,
  `tools/check_docs_content_policy.py`,
  `issues/20260918-130225_docsref01_extend-generate_reference_table-for-agent-eventbus-memory.md`
  (now `plans/20260919-105034_plan.md`).
- **Completion Checklist**: registered in `docs/adr-index.md` (this pass's row 2),
  Status set, Related Documents cross-referenced.

## Compatibility considerations
New, additive file — no existing document is modified by this row (the
`docs/adr-index.md` registration is a separate row, seq 02). No runtime or
schema impact; this is a governance document only.

## Security considerations
N/A: no code, credentials, or runtime behavior is described or changed by this
document.

## Rollback considerations
Trivial: delete the new file and revert `docs/adr-index.md`'s row addition (seq
02's row) — no other document depends on this ADR's existence yet, since no
Option-B implementation has started.

## Validation plan
- Run `uv run python tools/check_docs_quality.py` and `uv run python
  tools/check_docs_structure.py` against the new file — expect the standard ADR
  section headers and front matter to pass structural checks with no findings.
- Manual review: confirm the 14 required section headers appear in the exact
  required order.

## Completion criteria
- The file exists at `docs/adr/ADR-015-reference-document-class-disposition.md`
  with all 14 standard section headers in order.
- Status is explicitly `Proposed` or `Accepted`, with Approval evidence recorded
  per the ADR Acceptance Evidence Standard.
- `tools/check_docs_quality.py`/`tools/check_docs_structure.py` report no new
  findings.

## Out of scope
Implementing Option B's tooling (`tools/generate_reference_table.py` extension)
or any document migration — tracked by `plans/20260919-105034_plan.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260919-120537 | 20260919-120537 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260919-120537 | 20260919-120537 | N/A: documentation-only — manual review + structural checks only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260919-120537 | 20260919-120537 | Scoped to `tools/check_docs_quality.py` + `tools/check_docs_structure.py` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260919-120537 | 20260919-120537 | N/A: this document's own Target file IS the new documentation |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-003, REQ-004 (draft the ADR; record Implementation Notes if Option B; reach a Status decision)
- **Source issue**: issues/done/20260918-130115_adrref01_decide-reference-class-fate-via-adr.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-104524_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-114210
- **Related target files**: docs/adr/ADR-015-reference-document-class-disposition.md