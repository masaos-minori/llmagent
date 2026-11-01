# Implementation Procedure: `docs/24_eventbus/eventbus_08_reference_api.md` (EBAUTHGEN001 Phase 3)

**Plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` (REQ-003, REQ-008)

## Goal
Refresh the admin endpoint and audit function signature rows of the reference API so the
documented surface matches the generation/TTL contract.

## Scope
- Auto-generated guard block `:45-139`
  (`AUTO-GENERATED: generate_reference_table.py eventbus-class-function-reference`;
  "Generated from `registry/manifests/eventbus_api.yaml` ... Do not hand-edit between the
  guard comments; run `python tools/generate_reference_table.py --manifests` to refresh"
  `:46`). Re-verified at HEAD `d14bf433f` on 2026-11-01; freeze-time anchors were
  `:42-130`.
- `update_topics_authorization` table row `:53`; `log_privileged_action` table row `:67`
  (the plan cites `:65` — freeze-time anchor `c5a8285dd`, off by two after `474dc2888`;
  same table region).

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Do not hand-edit the guarded table. After docs 01-06 land (their docstrings and
   signatures are the source), run
  `uv run python tools/generate_reference_table.py --manifests` (optionally with
  `--type eventbus` to restrict to this domain): it regenerates
  `registry/manifests/eventbus_api.yaml` from the live `scripts/eventbus/*.py` surface
  and re-renders the guarded docs from it, so the new rows (`AuthzGeneration`,
  `publish_generation`, `current_generation`, `authorization_baseline_hash`,
  `authz_sweep_loop` and the extended `update_topics_authorization` /
  `log_privileged_action` signatures) appear automatically.
2. Verify the refreshed `update_topics_authorization` and `log_privileged_action` rows
  and confirm `## Module Responsibilities` (`:36-40`) prose still matches the landed
  module boundaries; update only if a sentence became false.

## Compatibility considerations
**Dependencies**:
- Upstream: docs 01-06 landed (the reference table is generated from the code surface)
**Blocks**: docs 14, 15 (index/ops pages cross-reference the regenerated table)

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert the single doc file; no code or test depends on the wording at runtime.

## Validation plan
- `uv run python tools/generate_reference_table.py --check --type eventbus` and
  `uv run python tools/check_docs_consistency.py --domain eventbus` pass after refresh.

## Completion criteria
- AC-7: `generate_reference_table.py --check --type eventbus` green; the documented admin
  endpoint and audit signatures match the landed code.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Completed | — | 20261101-095421 |  |
| 2 | Apply the Implementation procedure | Completed | 20261101-095421 | 20261101-095453 |  |
| 3 | Run the Validation plan gates | Completed | — | 20261101-095453 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-141000_01_scripts_eventbus_auth.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- Docs-only row: no new constructs; no markers applied (names are marked in docs 01-06).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-008
- **Source issue**: `issues/20261029-104509_ebauthgen001_eventbus-authz-generation-ttl.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` — Implementation Target Files row 13
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-141000
- **Related target files**: `docs/24_eventbus/eventbus_08_reference_api.md`