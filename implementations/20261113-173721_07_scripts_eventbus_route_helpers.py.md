## Goal
Make `get_counter_value` in `scripts/eventbus/route_helpers.py` read only the public Counter API (`metric.name`) and remove the pseudo-shebang line 1 (REQ-005 / AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers are from the 2026-11-13 plan revalidation; locate each passage by its quoted text and skip and report it if it is already correct.
- Verified 2026-11-13 with the installed `prometheus_client` (Plan Corrections probe): a `Counter` family name is `<name>` and its sample is `<name>_total`, and `collect()` exposes the family through the loop variable `metric` already present in `get_counter_value` (`for metric in metrics:`), so `metric.name + "_total"` replaces `counter._name + "_total"` (line 66) with identical selection.
- Line 1 is `# /usr/bin/env python3` — a commented shebang (not executable intent); the module is imported, never run directly (verified: no `if __name__` entry).
- The only caller of `get_counter_value` is `health_route.py:94` (Plan Design scan); the health test covers it through the lock-contention metric (Plan Tests REQ-005).

## Design decisions
- Remove the shebang line rather than convert it to `#!...`: the module is never an entry point, and the Plan accepts "a valid shebang or none" (AC-5).

## Alternatives considered
- Keep `counter._name` with a type-ignore: rejected — private-attribute access breaks silently on a client-library upgrade (Plan Problem).

## Implementation
### Target file
`scripts/eventbus/route_helpers.py`

### Procedure
1. Delete line 1 `# /usr/bin/env python3`.
2. Replace `if sample.name == counter._name + "_total":` (line 66) with `if sample.name == metric.name + "_total":`.

### Method
- The `except (AttributeError, TypeError, ValueError)` guard in `get_counter_value` stays; it still covers a `collect()` API absence.

### Details
- No other private-attribute read exists in the file (AC-5: `get_counter_value` uses no attribute starting with an underscore).

## Compatibility considerations
- `test_eventbus_health.py` is not a target row and needs no edit (name-based metric lookup is unchanged from its point of view).

## Security considerations
N/A: no security surface.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| Metrics helper | Integration | `uv run pytest tests/eventbus/test_eventbus_health.py` | Pass |
| AC-5 | Search | `rg -n "counter._name" scripts/eventbus/route_helpers.py` | No match |
| Changed file | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages`, `uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run python tools/check_module_size.py` | No new finding |

## Completion criteria
- AC-5: no underscore-prefixed attribute read in `get_counter_value`; no shebang line remains.

## Out of Scope
- All other helpers in `route_helpers.py` (untouched).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-005 / AC-5
- **Source issue**: issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-173721
- **Related target files**: `scripts/eventbus/route_helpers.py`
