## Goal
Extend this ADR's front matter `related:` so it covers every document its body Related Documents block references (REQ-005: front matter becomes the flat superset for ADR documents).

## Scope
- In: this file's front matter `related:` block only.
- Out: the body, including the `## Related Documents` block and its sub-headings; every other file.

## Assumptions
- Verified by scan on 20261004: the body block references 7 document(s) of which 7 are absent from front matter.
- ADR bodies stay (owner review at the Step 3 gate of the Plan, UNK-01); if that decision changes, this row changes.
- The tool's output, not this list, is authoritative at apply time.

## Design decisions
- Apply through the `merge-related` subcommand rather than by hand so ordering and notation match the other documents.
- Front matter entries use basenames.

## Alternatives considered
- Hand edit: rejected; error-prone across 13 ADR documents.
- Remove the body block: rejected; the ADR section list is mandated and `check_known_deviation_sync.py` reads it.

## Implementation
### Target file
`docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure
1. Run the dry-run for this file and confirm the additions: `eventbus_01_system-overview.md`, `eventbus_03_dlq_operations.md`, `eventbus_07_persistence_schema_and_replay.md`, `eventbus_06_dlq_offsets_and_delivery_semantics.md`, `eventbus_09_configuration-and-operations.md`, `eventbus_10_reference_api.md`, `governance_03_issue-and-uncertainty-management.md`.
2. Run `merge-related --fix` for this file.
3. Confirm only the front matter `related:` block changed and the body is byte-identical.

### Method
- `uv run python tools/manage_frontmatter.py merge-related docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` (dry-run), then the same command with `--fix`.
- Expected additions: `eventbus_01_system-overview.md`, `eventbus_03_dlq_operations.md`, `eventbus_07_persistence_schema_and_replay.md`, `eventbus_06_dlq_offsets_and_delivery_semantics.md`, `eventbus_09_configuration-and-operations.md`, `eventbus_10_reference_api.md`, `governance_03_issue-and-uncertainty-management.md`.

### Details
- Existing entries keep their order; new entries are appended in body order.
- Front matter `related:` shape in this file: block.

## Compatibility considerations
- No link target changes; inbound references and the body block are unaffected.

## Security considerations
- Documentation only; no secrets or configuration values are involved.

## Rollback considerations
- Revert the commit that applied this ADR group (ADR documents are applied together in one commit).

## Validation plan
- `uv run python tools/check_docs_structure.py` (ADR coverage rule once row 005 lands).
- `uv run python tools/check_known_deviation_sync.py` to confirm the body block is still readable.
- `git diff` shows changes only inside the front matter.

## Completion criteria
- Front matter `related:` covers every document referenced in the body block.
- The body is unchanged.
- Structure and quality checkers report no new findings for this file.

## Out of scope
- Any body edit, ADR renumbering, or edits to other ADR documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the front matter extension via `merge-related --fix` | Completed | 20261004-125212 | 20261004-125212 | applied via merge-related --fix; non-link sections handled per owner review |
| 2 | N/A: documentation file; covered by checker runs | Completed | 20261004-125212 | 20261004-125212 | N/A: documentation file; covered by checker runs |
| 3 | Run `check_docs_structure.py` and `check_known_deviation_sync.py` | Completed | 20261004-125212 | 20261004-125212 | check_docs_structure/quality/content_policy/consistency run over docs (no new findings); full suite 8092 passed, 6 failed (same unrelated baseline) |
| 4 | N/A: this file is the documentation change | Completed | 20261004-125212 | 20261004-125212 | N/A: this file is the documentation change |

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
- **Requirement ID**: `REQ-005` (extend ADR front matter `related:` to cover body references)
- **Source issue**: issues/done/20261004-111518_relateddocsmerge_consolidate-front-matter-related-and-body-related-documents.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-111806_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-112553
- **Related target files**: docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md