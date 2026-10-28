# Decide on and apply the removal of the eventbus.db re-export facade

## Goal
- Record the owner's retention decision for `scripts/eventbus/db.py`: the facade stays as
  the documented canonical single entry point for EventBus persistence, with one README
  sentence capturing the decision and its rationale. No caller migration, no deletion.

## Priority
Medium

## Scope
- **In-Scope**:
  - Recording the decision (retain) in this Plan and in
    `scripts/eventbus/README.md`'s "Stub Module Pattern" section.
  - Confirming the retention is already consistent with the compatibility checker, the
    canonical-source registry, and the ADR (verification commands, no edits).
- **Out-of-Scope**:
  - Caller migration to layer modules (the removal branch of the Issue is explicitly not
    chosen).
  - Deleting `scripts/eventbus/db.py` or adding a "facade must not return" checker rule —
    under retention, `eventbus.db` imports are the intended API, and a reintroduction
    guard would guard against the wrong event.
  - Any change to `tools/check_compat_shims.py`, `tools/compat_exceptions.toml`, the
    ADR-006 text, or `docs/`.
  - Changing transaction, lock, or shutdown behavior of EventBus.
- **Dependencies**: The Issue's `check_compat_shims.py` sequencing dependency on
  mcpcompat001/mcpcompat003 is moot for this Plan: this Plan does not edit the checker or
  its manifest (verified: `scripts/eventbus/db.py` produces no checker finding today, so
  no manifest entry is required). Recorded in `Assumptions`. Related done issue
  `issues/done/20261022-124204_ebdocwording_align-eventbus-facade-wording.md` is
  reaffirmed, not superseded.

## Background
Source: `memo-issue.md` item H-02. The memo called the facade "likely a removable stub";
the ADR, README, and the 2026-10-22 done issue treat it as the intended single entry
point. The Issue named the contradiction as a blocking owner decision
(`issues/20261027-104252...md`, Unresolved Questions). On 2026-10-27 the owner decided:
**retain**. This Plan executes the Issue's retention branch.

Verification findings (2026-10-27, current source):
- `scripts/eventbus/db.py` re-exports the 13 names listed in the Issue from
  `eventbus.db_conn` / `eventbus.event_repo` / `eventbus.delivery_repo` /
  `eventbus.dlq_repo`, with a header warning "Do not add new functions here".
- Production importers (7 files verified): `ack_route.py` (module-level line 13 + deferred
  line 53), `app.py:38`, `dlq_route.py:10`, `health_route.py:9`, `publish_route.py:13`,
  `replay_route.py:12`, `route_helpers.py:133` (deferred).
- Test importers exceed the Issue's "9 files": verified direct `from eventbus.db import`
  usage in `test_eventbus_ack_nack.py`, `test_eventbus_offsets.py`,
  `test_eventbus_restart_resume.py`, `test_eventbus_concurrent.py` (and further facade
  references, e.g. `test_eventbus_ack_endpoint.py:284`). Deferred imports in tests are
  the dominant pattern; `test_eventbus_publish.py:159` patches
  `eventbus.publish_route.insert_event`, i.e. the route-module binding produced by the
  facade import — retention leaves every patch target valid.
- Deferred production imports (`ack_route.py:53`, `route_helpers.py:133`) sit next to
  deferred imports from `eventbus.db_conn` in the same function, so they are not
  circular-import avoidance; the Issue's UNK is resolved as test-patching convenience.
- Checker state: `tools/check_compat_shims.py` passes today with zero findings against the
  facade (no "re-export stub"/shim phrase matches `db.py` or the README section), so no
  `compat_exceptions.toml` entry is needed to keep retention green.
- Registry state: `config/documentation_canonical_sources.toml` maps `eventbus.core-behavior`
  to `scripts/eventbus/` (directory covers `db.py`); the facade is not a conflicting
  canonical source.
- Docs state: the facade is named only in ADR-006's Implementation References line 326
  and `scripts/eventbus/README.md` (plus `docs/24_eventbus/eventbus_08_reference_api.md`
  listing `db-py` as a reference-API member). Under retention all three statements are
  already true; no doc edit is required.

## Problem
The retain/remove question was undecided across artifacts. The decision is now recorded
by the owner (retain), which this Plan captures in the one artifact whose wording carries
the maintenance rule — the module README.

## Reason for Change
The memo challenged the facade's status; leaving the challenge unanswered would invite a
future removal attempt against a deliberately retained API. Recording the decision in the
README closes the question where maintainers read it.

## Implementation Intent
Single documentation edit: append one sentence to the README's "Stub Module Pattern"
section stating that the entry point is a deliberate, owner-confirmed decision (2026-10-27,
carrying the 2026-10-22 wording decision forward) and that callers import persistence
names through `eventbus.db`. Run the verification commands from the Issue's Testing
Expectations to confirm the retention is already checker-, contract-, and test-consistent.

## Requirements
- `REQ-001`: The retention decision is recorded in this Plan's Traceability and in
  `scripts/eventbus/README.md` with its date and rationale (ownership clarity is handled
  by the existing layer list; the facade stays as the single consumer entry point).
- `REQ-002`: No code change: `scripts/eventbus/db.py` and all 16+ importers stay as-is;
  transaction/lock/shutdown behavior is untouched.
- `REQ-003`: Verification commands pass unchanged: full eventbus suite, import-linter
  `eventbus-is-isolated` contract, `check_compat_shims.py` (with
  `--check-removed-names --check-doc-symbols`), `check_mock_patch_targets.py`,
  `check_adr_preservation.py` (ADR untouched), and the docs checkers (docs untouched).

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/eventbus/README.md | Add one decision-record sentence to the "Stub Module Pattern" section | REQ-001 | REQ-001 / AC-01 | section lines 15-19 (verified) | none (prose) | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/eventbus/db.py | Facade surface (13 re-exports, header rule) the README sentence describes | REQ-001, REQ-002 |
| scripts/eventbus/ack_route.py | Deferred-import example confirming imports are unchanged | REQ-002 |
| config/documentation_canonical_sources.toml | Confirms `eventbus.core-behavior` registry entry covers the facade | REQ-003 |
| docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md | Line 326 facade reference stays valid under retention (read-only, no edit allowed per ADR preservation) | REQ-003 |
| tools/check_compat_shims.py | Checker semantics proving no manifest entry is needed for retention | REQ-003 |
| tools/compat_exceptions.toml | Manifest inspected to confirm the facade needs no exception entry | REQ-003 |
| issues/done/20261022-124204_ebdocwording_align-eventbus-facade-wording.md | Prior retain decision this Plan reaffirms | REQ-001 |

## Acceptance Criteria
- `AC-01` (REQ-001): the README's Stub Module Pattern section states the retained
  decision with its date; the sentence names `db.py` as the consumer entry point.
- `AC-02` (REQ-002): `git diff` for this Plan touches exactly
  `scripts/eventbus/README.md` (plus this Plan file and the Issue move); `db.py` and all
  importers unchanged.
- `AC-03` (REQ-003): `uv run pytest tests/eventbus -q`, the full suite,
  `PYTHONPATH=scripts uv run lint-imports`, `ruff`, `mypy --no-namespace-packages`,
  `tools/check_compat_shims.py --check-removed-names --check-doc-symbols`,
  `tools/check_mock_patch_targets.py`, `tools/check_adr_preservation.py`, and
  `check_docs_quality.py` / `check_docs_structure.py` /
  `check_docs_consistency.py --domain eventbus` all pass.

## Tests
- `REQ-002`/`REQ-003`: no test changes; existing suites are the regression net —
  `tests/eventbus` (ACK/NACK, offsets, DLQ, shutdown, schema) then the full suite.
  `tools/check_mock_patch_targets.py` confirms no patch target moved (none can: imports
  are unchanged).

## Documentation Impact
N/A: no `docs/*.md` change. The only prose edit is
`scripts/eventbus/README.md` (a module README, not a `docs/` file); ADR-006 and the
eventbus docs already describe retention correctly.

## Assumptions
- The owner's "retain" answer (2026-10-27) supersedes the memo's removal recommendation
  and reaffirms the 2026-10-22 ebdocwording decision; the memo is not re-approved.
- A manifest entry in `tools/compat_exceptions.toml` is unnecessary because the facade
  produces no checker finding today (verified by running the checker); adding one with a
  future expiry would wrongly frame a permanent decision as a temporary exception.
- Cross-plan overlap: the Issue's shared-file dependency on
  `tools/check_compat_shims.py` (mcpcompat001/mcpcompat003) does not bind this Plan
  because this Plan does not touch that file. Recorded for the overlap tool.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | The Issue's three unresolved questions are all resolved: owner decision (retain, recorded 2026-10-27); deferred-import reason (test-patching convenience, adjacent deferred `db_conn` imports in the same function); facade-level patch targets exist (`test_eventbus_publish.py:159`) but retention invalidates none | — | — | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/eventbus/README.md | One decision-record sentence | none (prose only) | 6 (README + db.py combined) | low | No deploy.sh impact |

## Design
N/A: no architecture change. Retention keeps the documented layer contract: routes import
persistence names through the facade; layer modules own the transactions and locks.

## Implementation steps
1. **Phase 1: Record the decision**
   - [ ] Append the decision sentence to the Stub Module Pattern section (REQ-001; scripts/eventbus/README.md)
2. **Phase 2: Verification**
   - [ ] Run the Issue's full verification command set unchanged (REQ-003; no target-file change; operational check)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/README.md | Prose review + docs checkers | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_consistency.py --domain eventbus` | pass; README names the retained entry point |
| scripts/eventbus (whole module) | Regression, unchanged behavior | `uv run pytest tests/eventbus -q` then `uv run pytest` | green |
| import contract | Static | `PYTHONPATH=scripts uv run lint-imports` | `eventbus-is-isolated` passes |
| compat tooling | Static | `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols`; `tools/check_mock_patch_targets.py`; `tools/check_adr_preservation.py` | all pass, zero findings against the facade |

## Risks
- **Risk**: a future contributor re-opens the retain/remove question → **Mitigation**: the
  README decision sentence plus this Plan and the Issue archive give a citable record with
  a date and owner.
- **Risk**: misreading this Plan as authorizing removal work → **Mitigation**: Scope
  explicitly lists the removal branch as out-of-scope; AC-02 pins the diff to the README.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: record the decision in README | Completed | — | 20261028-153121 |  |
| 2 | Phase 2: verification commands | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261028-070453_01_scripts_eventbus_README.md.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-104252_ebcompat002_decide-eventbus-db-facade.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-120858
- **Related target files**: scripts/eventbus/README.md

### Requirement Traceability
| Requirement | Source | Plan Section | Target File | Test / Validation | Status |
|---|---|---|---|---|---|
| REQ-001 | issues/20261027-104252 (Required Changes, owner decision 2026-10-27) | Background, Target Files row 1 | scripts/eventbus/README.md | AC-01 | Planned |
| REQ-002 | issues/20261027-104252 (Constraints, AI Implementation Instruction) | Scope, Design | N/A (no code change) | AC-02 git-diff pin | Planned |
| REQ-003 | issues/20261027-104252 (Testing Expectations) | Validation plan | N/A (commands only) | AC-03 command set | Planned |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261028-070453 -->