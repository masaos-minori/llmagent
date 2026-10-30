# Implementation Procedure: `scripts/eventbus/auth.py` (EBAUTHGEN001 Phase 1)

**Plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` (REQ-001, REQ-009; Design `:167`)

## Goal
Introduce the `AuthzGeneration` immutable snapshot and the monotonic generation
counter, published through the existing single-assignment-under-GIL mechanism, and
route internal readers to the single generation object. Preserve the landed
build-first-then-publish semantics (`REQ-009`).

## Scope
- `Principal` frozen dataclass `:34-49`; `_TOKEN_PRINCIPAL_MAP` module global `:71`.
- `_build_principal_map(config)` `:105-203`: builds the whole map into a fresh local dict;
  docstring `:108-110` "If building raises ... the previous generation stays in force";
  duplicate-token guard `:122-143`; returns `new_map` `:203`.
- `_populate_token_maps(config)` `:206-213`: calls `publish_principals(_build_principal_map(config))` `:213`.
- `publish_principals(new_map)` `:216-224`: `global _TOKEN_PRINCIPAL_MAP; _TOKEN_PRINCIPAL_MAP = new_map` `:223-224`.
- `resolve_principal` reads `_TOKEN_PRINCIPAL_MAP` `:261`, `:277`.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
### Context and prior decisions
- Landed behavior to reuse, not re-implement: build-first-then-publish
  (`implementations/done/20261029-101422_01..03`), one-generation publication
  (ADR-013 item 9), `publish_principals` single module-level assignment under the GIL.
- Plan Assumption `:139`: generation numbers are process-local; after restart numbering
  restarts from the baseline generation. UNK-03 (no cross-restart persistence) carries
  its plan default — still Needs Confirmation for `code-implementation`.
- Anchor drift note: the plan table cites `:105-110`/`:216-224`/`:35`, re-verified against
  current HEAD `124e340b4` on 2026-10-30 and exact.

- `AuthzGeneration` (new) frozen dataclass: `generation: int`, `config: EventBusConfig`,
  `principals: dict[str, Principal]`, `effective_at: float` (unix epoch),
  `baseline_hash: str`, `expiries: frozenset[tuple[str, str, float]]`
  (`(consumer_id, topic, expires_at_epoch)`; empty for the baseline generation).
- Module-level `_CURRENT_GENERATION` (new) plus `publish_generation(new)` (new): one
  assignment under the GIL, replacing `publish_principals` `:216-224` (call sites
  `_populate_token_maps` `:213` and `admin_route.py:147` are both plan-modifiable rows).
- `current_generation()` (new) accessor for routes and the TTL sweep; raises nothing —
  lifespan always publishes the baseline generation first.
- Baseline generation at startup: `generation=0`, `effective_at`=process start,
  `expiries=frozenset()`. Every effective update publishes `generation+1`.
  (Numbering choice 0-based is a proposal; Needs Confirmation.)
- `_TOKEN_PRINCIPAL_MAP` is removed; `resolve_principal` `:261/:277` reads
  `current_generation().principals`.
- `_build_principal_map` keeps its name and build-first semantics (characterization test
  `tests/eventbus/test_admin_topics_authorization.py:220` monkeypatches
  `eventbus.admin_route._build_principal_map`; the re-import target and signature must stay).
- `_populate_token_maps` builds the baseline `AuthzGeneration` (principals via
  `_build_principal_map`, `baseline_hash` via `authorization_baseline_hash` from doc 02)
  and publishes it once via `publish_generation`.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Add `AuthzGeneration` after `Principal` (`:49`).
2. Replace the `_TOKEN_PRINCIPAL_MAP` global (`:71`) with `_CURRENT_GENERATION` + `current_generation()`.
3. Rewrite `publish_principals` (`:216-224`) as `publish_generation` with the identical
   single-assignment body (`skills/DESIGN.md` import-layer contract unchanged).
4. Update `_populate_token_maps` (`:206-213`) to compose the baseline generation.
5. Update `resolve_principal` (`:261`, `:277`) to read `current_generation().principals`.
6. Update the `_build_principal_map` docstring `:108-110` wording to the generation
   vocabulary ("previous generation stays in force" stays literally true).

## Compatibility considerations
**Dependencies**:
- Upstream: none (Phase 1 core; config.py baseline hash is row 02 and lands in the same Phase 1 commit group)
**Blocks**: `scripts/eventbus/admin_route.py` (doc 03), `scripts/eventbus/authz_ttl.py` (doc 04), `scripts/eventbus/app.py` (doc 05), all test rows

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/eventbus/test_authz_generation_ttl.py tests/eventbus/test_eventbus_auth.py`
  (snapshot immutability, counter monotonicity, failed-build preservation — AC-1/AC-3).
- Characterization: `tests/eventbus/test_eventbus_consumer_authorization.py` run
  before/after (plan Risk `:204`).

## Completion criteria
- One published generation at a time; failed rebuild keeps previous generation, its
  number, config, principals, and hash byte-identical (AC-3); `mypy` clean; no reader
  touches a principal map outside the generation object.

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
| — | — | — | — | — | — |

## Needs Confirmation (record for `code-implementation`)
- Removing `_TOKEN_PRINCIPAL_MAP` leaves `tests/eventbus/conftest.py::_reset_auth_state`
  (`:55-68`, a Reference-Files row that MUST NOT be modified) resetting a dead attribute:
  it will no longer preserve generation state across tests. Mitigation must live in the
  modifiable test rows (docs 08-11: a generation-reset helper in `eventbus_helpers.py`),
  or a plan amendment adding the conftest row is required. Do not touch conftest.py.
- Baseline generation number 0 (vs 1) — proposal above.

## Marker record
- `(new)` markers applied: `AuthzGeneration`, `_CURRENT_GENERATION`, `publish_generation`,
  `current_generation` (all in "Contract after change").

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-009
- **Source issue**: `issues/20261029-104509_ebauthgen001_eventbus-authz-generation-ttl.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` — Implementation Target Files row 01
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-141000
- **Related target files**: `scripts/eventbus/auth.py`
