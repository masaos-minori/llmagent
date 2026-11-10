## Goal
- Update the `eventbus_08` prose and refresh its generated block so it matches the new route registration (REQ-007; ADR-015 keeps this a generated Reference document).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `## Module Responsibilities` and the lead paragraph; the guarded block is refreshed by the generator, not edited.
- Not in scope: retiring the symbol table (UNK-02 of the Plan, owner decision).
- Execution order follows the Plan's phases, not the `seq` order: Phase 1 (document 09) first, then Phase 2 (documents 02, 03, 04, 05, 08, then 01 and 10 for the Phase 2 share), then Phase 3 (documents 06, 07, then 01, 10, 15 for the Phase 3 share), then Phase 4 (documents 11-14). Phase 4, after document 14.

## Assumptions
- ADR-015 designates this document as the eventbus generated Reference; the lead sentence "the authoritative symbol inventory" overstates the table and may be reworded without removing the table. Falsifiable by `check_docs_content_policy.py --strict` (currently passing).

## Design decisions
- Module Responsibilities: say route modules own their routers and role dependencies, and `app.py` wires them and owns startup; do not list symbols (docs content policy).

## Alternatives considered
N/A: the table stays by ADR-015 (Plan UNK-02).

## Implementation
### Target file
`docs/24_eventbus/eventbus_08_reference_api.md`

### Procedure
1. Rewrite the first bullet of `## Module Responsibilities` to the router-per-module statement.
2. Reword the lead paragraph's last sentence so it calls the table a generated reference, not the authoritative inventory.
3. Run `uv run python tools/generate_reference_table.py --manifests --type eventbus` (after document 14's manifest refresh) so the guarded block matches the code; do not hand-edit between the guard comments.

### Method
- Prose edit plus generator run; keep front matter and Keywords.

### Details
- Run `generate_reference_table.py --check` last; it must exit 0.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check`, `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain eventbus`.

## Completion criteria
- Prose matches the code; the guarded block is regenerated; the checkers pass.

## Out of Scope
- Retiring the symbol table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the prose in `docs/24_eventbus/eventbus_08_reference_api.md` | Pending | — | — | |
| 2 | Regenerate the guarded block with the generator and run `--check` | Pending | — | — | |
| 3 | Run the documentation checkers listed in Validation plan | Pending | — | — | |

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
- **Related target files**: `docs/24_eventbus/eventbus_08_reference_api.md`
