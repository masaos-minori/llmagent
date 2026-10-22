## Goal
Reduce the "Legacy Offset Files" operations section to the statement that the service does not read offset files and that `consumer_offsets` is the only resume source (REQ-004).

## Scope
- The section "Legacy Offset Files" and the link to the removed open-decisions heading.

## Assumptions
- After the code change the service never reads, writes, or deletes the files in `offsets_dir`; the `offsets_dir` key still exists in `config/eventbus.toml` and `scripts/eventbus/config.py`.
- The heading `Legacy Offset Files` is the target of an inbound link from `db_03` (the offset-seeding subsection, removed by its own procedure); keeping the heading keeps any other link valid.

## Design decisions
- Keep the heading; replace the body with one or two sentences: the service does not read offset files; operators may archive or delete the directory contents; `consumer_offsets` is the only resume source.
- Remove the owner/retention/end-condition bullets, the read-only check commands, and the closing link to the removed open-decisions section.

## Alternatives considered
- Deleting the whole section: allowed by the Issue, rejected here to keep the heading and avoid breaking links.

## Implementation
### Target file
`docs/24_eventbus/eventbus_07_configuration-and-operations.md`

### Procedure
1. Rewrite the section body as described, deleting the bullets, the shell block, and the trailing link.

### Method
- Minimal in-place edit; no history wording.
- Re-read the file before editing (it has high churn).

### Details
- Keep the `---` separator and the following "Delivery Operations" section unchanged.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`; the anchor check if available.

## Completion criteria
- The section states only that offset files are not used by the service and `consumer_offsets` is the only resume source; no link to a removed heading remains; docs checkers pass.

## Out of Scope
- Other sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reduce the "Legacy Offset Files" section | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (reduce the operations section)
- **Source issue**: `issues/20261021-102244_rmoffimp_remove-the-legacy-offset-import.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094316_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101417
- **Related target files**: docs/24_eventbus/eventbus_07_configuration-and-operations.md
