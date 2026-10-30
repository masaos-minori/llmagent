# Implementation Procedure: `tests/eventbus/test_authz_generation_ttl.py` (EBAUTHGEN001 Phase 2)

**Plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` (REQ-001, REQ-005, REQ-006)

## Goal
Execute the file-level procedure for `tests/eventbus/test_authz_generation_ttl.py` (batch 20261030-141000, Phase 2).

## Scope

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
### Evidence (new file)
- `ls tests/eventbus/` shows no such file (2026-10-30); plan row `:83` marks it new.

### Test matrix
1. Generation monotonicity (REQ-001, AC-1): N effective updates -> strictly increasing
   `generation` numbers via `current_generation()`; exactly one generation object
   published per update.
2. Snapshot immutability (REQ-001): `AuthzGeneration` is frozen; mutating its fields
   raises; the published object identity changes only through `publish_generation`.
3. Racing updates (REQ-002): same `expected_generation` twice -> one 200, one 409
   (complement of doc 08's matrix; exercised at the generation-object level here).
4. Expiry with injected clock (REQ-005, AC-2): grant with `ttl_seconds` -> inject clock
   past expiry -> sweep publishes exactly one new generation, pair gone from grants, one
   `target="ttl_expiry"` audit record; sweep on a generation with no expired pairs
   publishes nothing.
5. Sweep atomicity + abort-on-bump (plan Risk `:205`): bump the generation concurrently
   with a pending sweep -> sweep aborts, no out-of-order publish, retries next interval.
6. Restart audit record (REQ-006, AC-4): lifespan startup emits one
   `target="authz_baseline"` record carrying the loaded baseline hash; state after
   restart is baseline-only (pattern: `eventbus_two_lifecycle_clients` in
   `tests/eventbus/eventbus_helpers.py:181-213`).
7. Failed rebuild keeps generation number unchanged (REQ-001/REQ-009, AC-3): monkeypatch
   the principal build to raise during a TTL removal generation -> number, config,
   principals, and hash unchanged.
8. Baseline hash permutation invariance (plan Risk `:207`): permuted pair sets hash equal.

### Conventions
- Build the app/client through `eventbus_helpers.make_eventbus_client` (doc 11 extended
  generation reset); do NOT touch `tests/eventbus/conftest.py` (Reference Files only).
- Clock injection uses the helper from doc 11; no wall-clock sleeps.

## Compatibility considerations
**Dependencies**:
- Upstream: docs 01-06 (generation core, TTL sweep, lifespan wiring), doc 11 (helpers)
**Blocks**: none

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert or remove the added test rows; no production change to unwind.

## Validation plan
- `uv run pytest tests/eventbus/test_authz_generation_ttl.py` (row gate).

## Completion criteria
- AC-1 through AC-4 covered deterministically (no real-time waits); file runs green in
  the full `uv run pytest tests/eventbus` pass.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Pending | — | — | |
| 2 | Apply the Implementation procedure | Pending | — | — | |
| 3 | Run the Validation plan gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-141000_01_scripts_eventbus_auth.py.md` | 1 (dependency) | Procedure | Pending | — | — |
| `20261030-141000_11_tests_eventbus_eventbus_helpers.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- No production constructs introduced by this row; references doc 11's `injectable_clock`
  (new) and `reset_generation_state` (new). No `(new)` markers applied in this document
  beyond those named references.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-005, REQ-006
- **Source issue**: `issues/20261029-104509_ebauthgen001_eventbus-authz-generation-ttl.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` — Implementation Target Files row 09
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-141000
- **Related target files**: `tests/eventbus/test_authz_generation_ttl.py`
