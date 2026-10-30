# Implementation Procedure: `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (EBAUTHGEN001 Phase 3)

**Plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` (REQ-005, REQ-006, REQ-008, AC-7)

## Goal
Document the TTL bounds keys, the sweep's operational behavior, and restart semantics for
operators.

## Scope
- `## Configuration` `:45`, `### Configuration Fields` `:53`, `### Unsupported Keys`
  `:79`, `## Health Endpoint Semantics` `:118` (ops-doc structure; 394 lines).

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Configuration Fields (`:53-64`): add rows for `authz_max_ttl_seconds` (default 86400)
   and `authz_sweep_interval_seconds` (default 60.0), matching doc 02/doc 07 names and
   defaults.
2. New ops subsection after the Configuration block: authorization TTL sweep behavior —
   what an expired temporary grant does, the `target="ttl_expiry"` audit record, how an
   operator reads previous/new generation numbers from `previous_generation` /
   `new_generation` and the `gen:<prev>-><new>` detail suffix, and that a concurrent
   admin update makes the sweep abort and retry next cycle.
3. Restart semantics: runtime authorization overrides never persist; each startup emits
   one audit record with `consumer_id="system"`, `route="/startup"`,
   `target="authz_baseline"` carrying the loaded baseline hash; document this vocabulary
   so it is not mistaken for a security event (plan Risk `:206`), and that generation
   numbering restarts from the baseline after restart.
4. Update `### Unsupported Keys` (`:79-84`) if it enumerates accepted keys.
5. Operational behavior and failure semantics only; no code snippets
   (`skills/DESIGN.md` Docs content policy).

## Compatibility considerations
**Dependencies**:
- Upstream: docs 02, 04, 05, 07 landed (config keys, sweep, restart audit vocabulary)
**Blocks**: none

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert the single doc file; no code or test depends on the wording at runtime.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus` passes after the update.

## Completion criteria
- AC-7: operators can read generation conflicts, TTL expiry, and restart baseline drift
  from the documented audit vocabulary; checker green.

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
| `20261030-141000_02_scripts_eventbus_config.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `authz_max_ttl_seconds`, `authz_sweep_interval_seconds`,
  `ttl_expiry`, `authz_baseline` (Procedure section) — names introduced by docs 02/04/05.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005, REQ-006, REQ-008; AC-7
- **Source issue**: `issues/20261029-104509_ebauthgen001_eventbus-authz-generation-ttl.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` — Implementation Target Files row 15
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-141000
- **Related target files**: `docs/24_eventbus/eventbus_07_configuration-and-operations.md`
