# Implementation Procedure: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` (EBAUTHGEN001 Phase 3)

**Plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` (REQ-008, AC-7)

## Goal
Amend ADR-013 with the generation contract, stale rejection, TTL semantics, and restart
behavior, and correct the stale audit `detail` description.

## Scope
- Rules items `1.`-`12.` at `:65-97`; item 9 one-generation invariant `:85`; item 10
  runtime-only persistence `:89` (verified verbatim); item 11 privileged-action audit
  `:93` — states `detail="updated"`, stale against the landed count-summary format
  (plan Background `:30`); item 12 empty/no-op rejection `:97` (last item).
- INV list `:187-193`; INV-05 no-secrets rule `:191`.
- Item 1 (`:65`) names `auth.py`'s `_TOKEN_PRINCIPAL_MAP` — becomes stale once doc 01
  removes the bare map.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Item 11 `:93`: replace `detail="updated"` with the actual format
   `detail="<name>:<count>;...;persistent:false"` and note it now also carries
   `gen:<prev>-><new>` plus the additive `previous_generation`/`new_generation` record
   fields (REQ-008 staleness fix).
2. Extend item 9 `:85` to the `AuthzGeneration` snapshot wording (config + principals +
   generation number + effective time + baseline hash published by one assignment;
   failed build keeps the previous generation, number, and hash).
3. Extend item 10 `:89` with the optimistic-concurrency contract: mandatory
   `expected_generation`, HTTP 409 `generation_conflict` on mismatch with zero state
   touch, and the additive response fields (`previous_generation`, `new_generation`,
   `changed_count`, `effective_at`, `baseline_hash`); note the deliberate breaking change
   for callers that omit the field (owner decision 2026-10-30).
4. Add new items 13-15 after `:97`: TTL semantics (`ttl_seconds` bounds from
   `config/eventbus.toml`, expiry via periodic sweep as an atomic removal generation,
   `target="ttl_expiry"` audit); restart semantics (runtime overrides never persist;
   startup emits one `consumer_id="system"`, `target="authz_baseline"` audit record with
   the loaded baseline hash; generation numbering restarts from the baseline).
5. Update item 1 `:65`: replace the `_TOKEN_PRINCIPAL_MAP` reference with the published
   generation snapshot wording.
6. Keep INV-05 `:191` unchanged; state that generation numbers and baseline hashes obey
   it (hashes are not contents).
7. Operational behavior and failure semantics only — no implementation code in the ADR
   (`skills/DESIGN.md` Docs content policy).

## Compatibility considerations
**Dependencies**:
- Upstream: docs 01-06 landed (the ADR must describe the contract as landed)
**Blocks**: none

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert the single doc file; no code or test depends on the wording at runtime.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus`,
  `uv run python tools/check_adr_structure.py` (plan Validation plan `:200`).

## Completion criteria
- AC-7: the ADR states the generation contract, stale rejection, TTL semantics, restart
  behavior; `detail="updated"` no longer appears anywhere in the file.

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

## Marker record
- `(new)` markers applied: none in this document — every construct it names
  (`AuthzGeneration`, `generation_conflict`, `ttl_expiry`, `authz_baseline`, ...) is
  introduced and marked in docs 01-06.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-008; AC-7
- **Source issue**: `issues/20261029-104509_ebauthgen001_eventbus-authz-generation-ttl.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` — Implementation Target Files row 12
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-141000
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
