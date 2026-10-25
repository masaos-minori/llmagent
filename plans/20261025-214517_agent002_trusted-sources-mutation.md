# Plan: agent002 trusted sources mutation

## Goal
- Remove the dead runtime mutation of `TRUSTED_SOURCES` from
  `scripts/agent/llm_turn_runner.py`'s `_finalize_after_guard`, making
  `scripts/agent/message_schema.py` the single declarative source of the trusted-source
  registry, with zero behavior change.

## Priority
Medium

## Scope
- **In-Scope**:
  - Delete the mutation at `scripts/agent/llm_turn_runner.py:247-248`
    (`if loop_guard_source not in TRUSTED_SOURCES: TRUSTED_SOURCES[...] = {...}`).
  - Delete the `TRUSTED_SOURCES` import at `scripts/agent/llm_turn_runner.py:18`, which
    becomes unused (it has no other use in the file; leaving it would fail ruff F401 —
    `F` is in the ruff `select`).
- **Out-of-Scope**:
  - The Issue's "add the `loop_guard` entry to `TRUSTED_SOURCES`" change — **already
    implemented** (see Verification Results): `message_schema.py:21` declares
    `"loop_guard": {"_ephemeral"}`. No edit to `message_schema.py` is needed.
  - Changes to `scripts/agent/context.py` (registry reader), loop-guard trigger logic,
    or the ephemeral-key model.
- **Dependencies**: N/A: none.

## Background
Review finding F-002 flagged that a trust-boundary allowlist (`TRUSTED_SOURCES`, with
`_ALL_EPHEMERAL_KEYS` computed once at import time) was being mutated from a per-turn
runtime path. Verification at HEAD `b0415bd3d` shows the specific `loop_guard` entry has
since been declared statically, so the mutation is a no-op at runtime (the `not in`
guard is always False) and only the code-hygiene half of the finding remains open.

## Problem
`_finalize_after_guard` still writes to the registry (llm_turn_runner.py:247-248).
Although today the write is dead — `message_schema.py:21` already contains
`"loop_guard": {"_ephemeral"}` — the pattern itself keeps open the divergence hazard
between the runtime-mutated registry and import-time derivations like
`_ALL_EPHEMERAL_KEYS` (`message_schema.py`, computed at import).

## Reason for Change
Removing the write path permanently closes the "allowlist mutated from a per-turn code
path" hole the review identified, and deletes now-dead code plus its unused import.

## Implementation Intent
Pure deletion: remove the three-line mutation block and the import line. The
declarative entry, its tests, and all consumers (`context.py` reads via
`TRUSTED_SOURCES.get(source, ...)`) already exist and stay untouched.

## Requirements
- `REQ-001`: No write to `TRUSTED_SOURCES` exists outside its definition in
  `message_schema.py` (verifiable by grep over `scripts/` and `tests/`).
- `REQ-002`: Behavior is unchanged: the `loop_guard` source keeps its
  `{"_ephemeral"}` grant from the static declaration; `validate_message` outcomes for
  every source are identical.
- `REQ-003`: mypy, ruff (including F401 on the edited file), and the full test suite
  pass after the deletion.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/llm_turn_runner.py | Delete mutation lines 247-248 in `_finalize_after_guard` and the now-unused `TRUSTED_SOURCES` import at line 18 | Mutation is dead code (entry already declared statically) and is the last write outside the registry definition | REQ-001, REQ-002, REQ-003 / AC-1..AC-3 | llm_turn_runner.py:18, :246-248; `loop_guard_source` remains used at :252 so line 246 stays; message_schema.py:21 already declares the entry | tests/agent/test_llm_turn_runner.py (calls `_finalize_after_guard` directly), tests/agent/test_message_schema.py:244-256, tests/agent/test_ephemeral_filtering_security.py:300-308 | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/message_schema.py | Confirm `TRUSTED_SOURCES` already contains `"loop_guard": {"_ephemeral"}` (:21) and `_ALL_EPHEMERAL_KEYS` is import-time derived from all entries — REQ-001's grep check anchors on this definition | REQ-001, REQ-002 |
| scripts/agent/context.py | Registry consumer (`TRUSTED_SOURCES.get(source, set())` at :79) — confirms read-only usage and unchanged behavior | REQ-002 |

## Acceptance Criteria
- `AC-1` (REQ-001): `grep -rn "TRUSTED_SOURCES\[" scripts/ tests/` and equivalent write
  pattern searches show no assignment/update outside `message_schema.py`'s definition.
- `AC-2` (REQ-002): Existing regression tests for the loop_guard source pass
  unchanged: `test_message_schema.py::test_validate_message_accepts_loop_guard_ephemeral_key`,
  `test_ephemeral_filtering_security.py` registry-entry assertions (accept with
  `_ephemeral`, reject unlisted ephemeral keys semantics preserved).
- `AC-3` (REQ-003): `uv run mypy --no-namespace-packages scripts/`, `uv run ruff check
  scripts/agent`, and `uv run pytest tests/agent -q` all pass.

## Tests
- `REQ-002`: No new tests. The Issue's expected regression coverage (validate_message
  accept/reject for `loop_guard`) already exists and asserts the *static* registry, so
  it remains valid after deletion. tests/agent/test_llm_turn_runner.py exercises
  `_finalize_after_guard` directly and must pass unchanged.

## Documentation Impact
N/A: the Issue's own check found no doc describing the registry as runtime-extensible;
re-verified — no `docs/*.md` mentions `TRUSTED_SOURCES` mutation.

## Assumptions
- No test relies on `TRUSTED_SOURCES` being empty of `loop_guard` before the guard
  fires (verified: `test_message_schema.py:234` asserts presence at import time).
- Removing the import does not affect `context.py`'s separate import of
  `TRUSTED_SOURCES` (independent import statements).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | None. The Issue's claim is partially stale (entry already declared); the remaining actionable scope is fully verified against source at HEAD `b0415bd3d`. | N/A: no unresolved evidence gap | N/A | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/llm_turn_runner.py | Delete 3 dead lines + 1 import | None: mutation is a verified no-op; only the turn-runner module affected | N/A: Path A skipped historical analysis | N/A: Path A skipped historical analysis | rsynced to `/opt/llm/scripts/` by deploy.sh; no new dependencies; no service restarts required beyond the next regular deploy |

## Design
None beyond the deletion itself. The Issue's constraint "keep the registry a
module-level definition in message_schema.py; no new abstraction" is already the
current state; no change is needed to satisfy it.

## Implementation steps

1. **Phase 1: Dead-code deletion**
   - [ ] Delete mutation lines 247-248 in `_finalize_after_guard` (keep `loop_guard_source = "loop_guard"` at :246, still used at :252) (REQ-001; scripts/agent/llm_turn_runner.py)
   - [ ] Delete the unused `TRUSTED_SOURCES` import line 18 (REQ-003; scripts/agent/llm_turn_runner.py)
2. **Phase 2: Verification and deployment check**
   - [ ] Grep-verify no `TRUSTED_SOURCES` writes outside `message_schema.py` (REQ-001; scripts/agent/llm_turn_runner.py)
   - [ ] Run `uv run mypy --no-namespace-packages scripts/`, `uv run ruff check scripts/agent`, `uv run pytest tests/agent -q` (REQ-002, REQ-003; scripts/agent/llm_turn_runner.py)
   - [ ] Deployment validation: file is rsynced by deploy.sh; no new deps; no restart required (REQ-003; scripts/agent/llm_turn_runner.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/llm_turn_runner.py | Policy grep | `grep -n "TRUSTED_SOURCES" scripts/agent/llm_turn_runner.py` | no matches (import and mutation both gone) |
| scripts/agent/llm_turn_runner.py | Static gates | `uv run mypy --no-namespace-packages scripts/` ; `uv run ruff check scripts/agent` | both exit 0 (no F401: import removed) |
| scripts/agent/llm_turn_runner.py | Regression (existing suites, unchanged) | `uv run pytest tests/agent/test_llm_turn_runner.py tests/agent/test_message_schema.py tests/agent/test_ephemeral_filtering_security.py -q` | all pass |

## Risks
- **Risk**: A hidden consumer imports `TRUSTED_SOURCES` *via* `llm_turn_runner` (patch
  targets in tests could reference `agent.llm_turn_runner.TRUSTED_SOURCES`). →
  **Mitigation**: grep over `tests/` shows no such patch target;
  `test_llm_turn_runner.py` patches `validate_message`, not the registry. AC-3's
  full-suite run catches any remainder.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete mutation lines 247-248 | Pending | — | — | Phase 1 |
| 2 | Delete unused import at line 18 | Pending | — | — | Phase 1 |
| 3 | Grep + mypy + ruff + pytest verification, deploy.sh check | Pending | — | — | Phase 2 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blockers identified | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261025-210105_agent002_trusted-sources-mutation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261025-214517
- **Related target files**: scripts/agent/llm_turn_runner.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Summary / Required Changes item 2; verified mutation at llm_turn_runner.py:247-248 | scripts/agent/llm_turn_runner.py | Phase 1 | AC-1 | Validation plan row 1 | Explicit in issue |
| REQ-002 | Issue Constraints / Acceptance Criteria; verified static entry at message_schema.py:21 makes the mutation dead | scripts/agent/llm_turn_runner.py | Phase 2 | AC-2 | Validation plan row 3 | Confirmed by repository evidence |
| REQ-003 | Issue Acceptance Criteria; unused-import consequence derived from ruff `select` containing `F` | scripts/agent/llm_turn_runner.py | Phase 1-2 | AC-3 | Validation plan row 2 | Derived from confirmed evidence |
