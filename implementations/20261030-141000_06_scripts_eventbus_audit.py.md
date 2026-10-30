# Implementation Procedure: `scripts/eventbus/audit.py` (EBAUTHGEN001 Phase 2)

**Plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` (REQ-004; Design `:170`)

## Goal
Extend `log_privileged_action` with additive generation parameters; no secrets in any
field (ADR-013 INV-05).

## Scope
- `log_privileged_action(consumer_id, request_id, route, target, detail="", actor="")`
  `:132-139`; record built via `_build_audit_record(event="privileged_action", ...)`
  `:150-159`; `actor` attached only when non-empty `:160-161`; JSON-lines emission with
  `OPT_SORT_KEYS` `:162`.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- Signature gains keyword-only parameters `previous_generation: int | None = None` and
  `new_generation: int | None = None` (after `actor` `:138`).
- When both are provided, add them to the emitted record as
  `record["previous_generation"]` / `record["new_generation"]` next to the existing
  `actor` conditional-attach pattern `:160-161` (omitted entirely when `None` — records
  without generations stay byte-identical to today).
- `detail` keeps the landed `name:count;...;persistent:false` format; the `gen:<prev>-><new>`
  suffix is composed by the callers (docs 03/04), not here (Design `:170`).
- No new fields may carry token values or config contents; `baseline_hash` values are
  hashes (INV-05, AC-5).

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Extend the signature and docstring Args block `:140-149`.
2. Add the two conditional record attaches before the log call `:162`.

## Compatibility considerations
**Dependencies**:
- Upstream: none (additive signature first; doc 03 and doc 04 call the new parameters)
**Blocks**: docs 03, 04 (call sites), doc 10 (secret-hygiene test)

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_auth.py` (row 10 extends the secret-leak
  regression `test_no_credential_leakage_in_audit_records` `:1272` to the new fields).
- Existing callers with no generation kwargs must remain valid (keyword-only defaults).

## Completion criteria
- AC-5: no audit record (including generation fields) contains secrets; legacy call
  sites unchanged.

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
| `20261030-141000_03_scripts_eventbus_admin_route.py.md` | 1 (dependency) | Procedure | Pending | — | — |
| `20261030-141000_04_scripts_eventbus_authz_ttl.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `previous_generation`, `new_generation` record fields
  (Contract section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20261029-104509_ebauthgen001_eventbus-authz-generation-ttl.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` — Implementation Target Files row 06
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-141000
- **Related target files**: `scripts/eventbus/audit.py`
