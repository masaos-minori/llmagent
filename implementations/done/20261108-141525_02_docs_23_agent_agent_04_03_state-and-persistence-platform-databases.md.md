## Goal
Restate the `tool_call_state` key semantics in the state-and-persistence doc to match the composed `{transport key}:{task_id}` form that `tool_runner.py` will write, replacing the current text's false claim that the lifecycle key shares identity with the dispatcher's durable store key (`REQ-005`).

## Scope
**Release unit**: wfaudit002-full

- Covers Plan `plans/20261108-084005_wfaudit002_tool-state-key-collisions.md` row 2 only: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`.
- Two text locations in that doc: the key-conflation paragraph (L72) and the `tool_call_state` table row (L78). No other section changes.

## Assumptions
- `141525_01` (the `tool_runner.py` composition procedure) lands with this document; the doc describes the post-change state, matching this repository's documentation policy.
- `135741_03` (wfaudit007's procedure for the same file) appends its recovery-reconciliation narrative to the `StateStore`/`begin_stage_if_new` operational bullets (verification
  2026-11-09: those bullets are at L101+ in the current doc, not the `tool_call_state` table row); that procedure has the lower seq and lands first, and this document's edits touch
  only the key-conflation paragraph (L72) and the key-description phrase in the table row (L78) — the two edits touch disjoint regions.

## Design decisions
- Keep the doc describing behavior, not the composition expression's code — state the composed shape and the per-task effect in prose, matching the row's existing descriptive style.
- Preserve the transport-key description unchanged: the wire `X-Idempotency-Key` and the dispatcher's durable store keep the raw content-derived key (`REQ-002`), and the paragraph's core warning (do not conflate `task_nonce` with lifecycle keys) stays valid.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`

### Procedure
Rewrite the two key descriptions to the composed form.

### Method
1. In the key-conflation paragraph (L72), replace the clause "while `tool_call_state.idempotency_key` is the content-derived transport dedup key (sha256 of method/tool/args/session uid) and shares its identity with the dispatcher's durable store" with: "while `tool_call_state.idempotency_key` is the content-derived transport dedup key (sha256 of method/tool/args/session uid) with the owning `task_id` appended, so two tasks making an identical call keep separate lifecycle rows; the wire `X-Idempotency-Key` sent to the dispatcher remains the raw content-derived key".
2. In the `tool_call_state` table row (L78), replace "keyed by the transport idempotency key and scoped to a `task_id`" with "keyed by the composed state key (the transport idempotency key with `task_id` appended), which enforces per-task separation of identical calls". Leave the rest of the row (states, stale-timeout behavior) untouched.

### Details
- The current L78 phrase "scoped to a `task_id`" is a stale promise (the plan's re-verification): today the column only carries `task_id` as data, not as part of the key. After `141525_01`, task scoping is key-level and the sentence becomes true.
- No changes to the DDL description in `docs/41_db/` — the column set and single-column `PRIMARY KEY` are unchanged (plan Out-of-Scope).

## Compatibility considerations
- N/A: documentation-only change.

## Security considerations
- N/A: documentation-only change.

## Rollback considerations
- Revert this document with `git checkout -- docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` (plus the `135741_03` landing if reverting together).

## Validation plan
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` per `routing.md` Tools.

## Completion criteria
- Both edited passages describe the composed key; the doc no longer claims the lifecycle key is byte-identical to the dispatcher store key; docs checkers report no findings.

## Out of Scope
- `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` — it describes the transport-side pending/audit stores, whose keys are unchanged.
- Any statement about pruning/retention of finished `tool_call_state` rows (`UNK-02`, follow-up issue candidate).

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the key-conflation paragraph (L72) and the `tool_call_state` table row (L78) | Completed | 20261109-070023 | 20261109-070023 | composed-key prose in both locations |
| 2 | Run docs checkers | Completed | 20261109-070023 | 20261109-070023 | quality/structure/consistency --domain agent all exit 0 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `wfaudit002` (via the source plan)
- **Source requirement**: see the plan's Requirements (`REQ-005`)
- **Source plan**: `plans/20261108-084005_wfaudit002_tool-state-key-collisions.md`
- **Generated at**: 20261108-141525
- **Related target files**: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-141525 -->