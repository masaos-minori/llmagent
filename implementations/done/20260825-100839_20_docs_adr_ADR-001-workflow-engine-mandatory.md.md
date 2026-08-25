## Goal
- Correct `docs/adr/ADR-001-workflow-engine-mandatory.md`'s stale forward-references
  to ADR-002/ADR-003 as future workflow-schema/monitoring ADRs — those numbers are
  now `Accepted` decisions for unrelated topics per `docs/adr-index.md` (REQ-009,
  with the ADR numbers corrected from the Issue's stated ADR-011/ADR-012 to the
  actually-stale ADR-002/ADR-003).

## Scope
- In scope: `docs/adr/ADR-001-workflow-engine-mandatory.md`'s front-matter `related:`
  field and its `## Related Documents` > `### Related ADRs` section.
- `docs/adr-index.md` is read for reference only, not edited by this document.

## Assumptions
- `docs/adr-index.md`'s current content (ADR-002 = "プロセス単位の設定所有権と
  Config Isolation", Accepted; ADR-003 = "RuntimeToolRegistryを唯一のルーティング
  権威とする", Accepted; highest assigned number = ADR-013) is unchanged by this
  document.
- `docs/00_governance_01_documentation-policy.md` does not define a "reserve the next
  number in advance" convention (ADR numbers are assigned sequentially at authoring
  time) — so this document does not pre-assign a replacement number.

## Design decisions
- Replace the ADR-002/ADR-003 references with a "number not yet assigned" phrasing
  rather than pre-assigning a specific future number (e.g. ADR-014/ADR-015): the
  current numbering is sequential-at-authoring-time, so writing in a guessed future
  number risks reproducing the exact stale-forward-reference problem this document is
  fixing.
- Set the front-matter `related:` to an empty list, since no currently-existing ADR
  corresponds to the intended future topics.

## Alternatives considered
- Pre-assigning the next free numbers (ADR-014, ADR-015) — rejected; no documented
  convention reserves numbers in advance, and the actual ADR could be assigned a
  different number by the time it's written, reproducing the same staleness this fix
  addresses.
- Deleting all mention of the future workflow-schema/monitoring topics — rejected;
  the forward-looking intent itself remains valid information, only the specific
  wrong numbers need correcting.

## Implementation
### Target file
`docs/adr/ADR-001-workflow-engine-mandatory.md`

### Procedure
1. Remove `- ADR-002` from the front-matter `related:` list, leaving `related: []`.
2. Rewrite the two `### Related ADRs` lines to state the topics without an ADR
   number, per Design decisions.

### Method
- Direct documentation edit; identify edit locations by section/field name, not line
  number.

### Details
- Phrases being corrected (quoted only, not reproduced in full):
  - Front-matter: `related:\n  - ADR-002`
  - Body: the two `### Related ADRs` lines listing "ADR-002: ワークフロー定義ファ
    イルのスキーマ設計（提案中）" and "ADR-003: ワークフロー監視・メトリクス設計
    （提案中）".
- Replacement approach:
  - Front-matter `related:` becomes an empty list.
  - The two `### Related ADRs` lines are rewritten, without ADR numbers, to state
    that the workflow-schema-design and workflow-monitoring/metrics-design topics do
    not yet have an assigned ADR number (ADR-002/ADR-003 are already `Accepted` for
    unrelated decisions), and that a new number will be assigned per
    `docs/adr-index.md`'s numbering convention when each is actually authored.
- `## Decision` > `### Out of Scope`'s existing two lines (mentioning these same two
  topics as "handled in a separate ADR") do not contain ADR numbers and are therefore
  not in scope for this correction (`Confirmed`, no change needed).

## Compatibility considerations
- N/A: documentation-only change, no backward-compatibility impact.

## Security considerations
- N/A: no security impact; documentation accuracy only.

## Rollback considerations
- Documentation-only change; revert via `git revert`. No dependency on other ADRs or
  code.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain mcp` (or the applicable
  domain check) to confirm no new inconsistency is introduced.
- Manual review: grep ADR-001's full text for "ADR-002"/"ADR-003" and confirm neither
  appears outside a context that correctly refers to their real, already-assigned
  decisions.

## Out of scope
- Editing `docs/adr-index.md` itself (e.g. adding a reverse `related` entry back to
  ADR-001).
- Changing the wording of the `## Decision` > `### Out of Scope` lines, which contain
  no ADR numbers and are therefore not part of this correction (confirmed above).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the documentation correction described in Implementation > Procedure/Method/Details | Completed | 20260825-153300 | 20260825-153700 | Re-verified ADR-002/ADR-003's current titles/status in `docs/adr-index.md` before editing (adversarial re-check); set front-matter `related: []` and rewrote the two `### Related ADRs` lines without ADR numbers |
| 2 | N/A: documentation-only, no test suite applies | N/A | — | — | N/A: REQ-009 is verified by doc-consistency tooling and manual review, per the Plan's Tests section |
| 3 | Run `uv run python tools/check_docs_consistency.py --domain mcp` | Completed | 20260825-153700 | 20260825-153800 | No new findings introduced; `validate_docs_structure.py` findings dropped from 7 to 6 (this fix resolved the pre-existing "front matter references missing file 'ADR-002'" error as a side effect — confirmed via `git stash`) |
| 4 | N/A: no further documentation depends on this correction beyond what Validation plan covers | N/A | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `docs/adr/ADR-001-workflow-engine-mandatory.md` correction | 1 | Doc Change | Completed | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: docs/adr/ADR-001-workflow-engine-mandatory.md
