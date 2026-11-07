## Goal

- Update the stale comment in `scripts/eventbus/config.py` (line 384) so it names `build_and_publish_generation()` instead of the removed `_populate_token_maps()` (REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

- Comment-only change; the normalization behavior it describes is untouched. Part of the Plan's single atomic Phase 1 cutover.

## Assumptions

- The empty-vs-missing distinction the comment describes (`consumer_authorization = data.get(...)` staying `None` when absent, lines 386-387) is the behavior `build_and_publish_generation` (new)/`_build_principal_map` depends on — verified at HEAD `1a13653e8`, unchanged.

## Design decisions

- Reword only the function name in the sentence; keep the surrounding REQ-002 normalization explanation as-is.

## Alternatives considered

- Deleting the comment: rejected — it documents a real contract of the config loader; only the name is stale.

## Implementation
### Target file
`scripts/eventbus/config.py`

### Procedure
1. In the comment block at lines 380-384, change "the empty-vs-missing distinction `_populate_token_maps()` depends on is preserved" to "the empty-vs-missing distinction `build_and_publish_generation()` depends on is preserved".
2. Confirm `grep -n "_populate_token_maps" scripts/eventbus/config.py` returns nothing.

### Method
- Verified anchor: `config.py:384` is the only `_populate_token_maps` mention in this file (comment); `config.py` does not import the function (grep-verified 2026-11-07).

### Details
- No code, no behavior, no public API change.

## Compatibility considerations

- The `check_compat_shims.py` `\b_populate_token_maps\b` pattern (sibling document 17) scans `docs/` and `scripts/`; this comment must be renamed in the same commit for the checker to stay clean.

## Security considerations

- N/A: comment only.

## Rollback considerations

- Revert of the single atomic commit restores the comment (one line).

## Validation plan

- `uv run python tools/check_compat_shims.py` — clean after Phase 1 (AC-001, AC-007).
- `grep -n "_populate_token_maps" scripts/eventbus/config.py` -> no matches.
- Completion gates per `rules/toolchain.md` run in the Plan Phase 3 pass.

## Completion criteria

- No reference to the removed name anywhere in `scripts/eventbus/config.py` (AC-001).

## Out of Scope

- Config schema, key normalization logic, and `EventBusConfig` annotations — unchanged (Plan Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename the function mentioned in the `config.py:384` comment — Plan Phase 1 | Completed | 20261107-152722 | 20261107-152722 | comment renamed; grep gate clean |
| 2 | Run the validation sequence (`rules/toolchain.md`) in the Plan Phase 3 pass | Completed | 20261107-152722 | 20261107-152722 | full suite 11784 passed diff-cover 100pct |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261106-125143_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063003_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-083645
- **Related target files**: `scripts/eventbus/config.py`