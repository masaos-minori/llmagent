## Goal
- Regenerate the eventbus symbol manifest after the route renames (REQ-007); the file is generated, never hand-edited.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: running the generator for the eventbus manifests.
- Not in scope: any manual edit of the YAML.
- Execution order follows the Plan's phases, not the `seq` order: Phase 1 (document 09) first, then Phase 2 (documents 02, 03, 04, 05, 08, then 01 and 10 for the Phase 2 share), then Phase 3 (documents 06, 07, then 01, 10, 15 for the Phase 3 share), then Phase 4 (documents 11-14). Phase 4, first.

## Assumptions
- `tools/generate_reference_table.py --manifests --type eventbus` rewrites `registry/manifests/eventbus_api.yaml` (and `eventbus_route_roles.yaml` if its source changed) from `scripts/eventbus/*.py`. Falsifiable by `--check`.

## Design decisions
- Use the generator only; commit the regenerated file.

## Alternatives considered
N/A: generated file.

## Implementation
### Target file
`registry/manifests/eventbus_api.yaml`

### Procedure
1. After Phases 2-3 are complete, run `uv run python tools/generate_reference_table.py --manifests --type eventbus`.
2. Inspect `git diff registry/manifests/` and confirm the changes are the removed `app.py` handler entries and updated route-module signatures (if `eventbus_route_roles.yaml` changes, report it as a generator side effect).

### Method
- Generator run only.

### Details
- If the generator also rewrites a file that is not in the Plan's target table, report it as an additional-target discovery (Blocked) instead of committing it.

## Compatibility considerations
N/A: generated reference.

## Security considerations
N/A: generated reference.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` exits 0.

## Completion criteria
- The manifest matches the code; `--check` exits 0.

## Out of Scope
- Hand edits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run the generator for the eventbus manifests | Completed | 20261110-113335 | 20261110-113335 | generate_reference_table.py --manifests --type eventbus also rewrote eventbus_route_roles.yaml with no diff; eventbus_08 guarded block refreshed (document 13). |
| 2 | Run `uv run python tools/generate_reference_table.py --check` | Completed | 20261110-113335 | 20261110-113335 |  |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20261109-112504_adrrev001_eventbus-route-handlers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-090758_adrrev001_eventbus-route-handlers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-100805
- **Related target files**: `registry/manifests/eventbus_api.yaml`