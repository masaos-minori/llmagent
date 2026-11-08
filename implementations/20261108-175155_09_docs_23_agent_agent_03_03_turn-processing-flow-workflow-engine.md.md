## Goal
Update the Startup Recovery section of `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`: the sentence that says `StateStore.recover_stale_attempts()` "is called with the store's connection" (L165) must state the no-argument facade call, matching the behavior documents 01/03 land.

## Scope
**Release unit**: wfaudit015-full (docs row lands with the unit; the sentence describes the converted call shape).

**Plan row implemented**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md` Implementation Target Files row 9 (`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `REQ-002`/`REQ-003`; plan step 3).

**In scope**:
- The single sentence at the top of the Startup Recovery paragraph (verified verbatim at HEAD `ad48bfa28`, L165).

**Out of scope**:
- The rest of the same sentence and paragraph (the "repairs attempt records only" half belongs to `wfaudit007`'s doc scope — `plans/done/20261108-084004_wfaudit007_task-status-never-reconciled.md` — and is left byte-identical here).
- The Loader Validation Rules section edited by `implementations/20261108-151141_03_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md` (disjoint).
- `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` — confirmed no-change (grep `get_connection` across `docs/` returns zero matches outside this sentence's rewording territory).

**Dependencies (landing order)**: documents 01/03 land before or with this docs edit so the doc never describes a call shape the code does not have.

## Assumptions
| ID | Assumption | Validation |
|---|---|---|
| A-001 | L165 is the only docs sentence describing the recovery call's arguments. | Verified (grep "called with the store" in the file: one match) |
| A-002 | The docs boundary claim ("StateStore is the CRUD facade; `get_connection` is the escape hatch") does not need changing: the method still exists (`UNK-01`). | Verified (plan Scope) |

## Design decisions
| ID | Decision | Rationale |
|---|---|---|
| D-001 | Reword only the call-description clause; keep sentence structure and every other claim intact. | `check_docs_consistency.py` cross-checks claims against `scripts/`; a minimal clause edit keeps all other verified claims stable. |
| D-002 | State both halves explicitly: "no arguments" and "the store uses its own connection internally". | Preserves the explanatory value of the old sentence (why no connection is passed) instead of just deleting the phrase. |

## Alternatives considered
| Alternative | Reason rejected |
|---|---|
| Delete the sentence | It anchors the startup-recovery flow description; deletion would leave readers without the call-shape fact the plan is about. |
| Also document `get_connection()`'s remaining production use (the wfaudit001 purge call) | That call does not exist at HEAD; documenting it here would be a speculative doc claim (AGENTS.md policy 4). |

## Implementation
### Target file
`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` (plan target row 9).

### Procedure
Step 1: reword the Startup Recovery sentence's call clause.

### Method
Single-sentence find-and-replace (HEAD `ad48bfa28` L165 reference).

### Details
Step 1 — current sentence (L165, first sentence of the Startup Recovery paragraph):
```markdown
During `Orchestrator.__init__()`, `StateStore.recover_stale_attempts()` is called with the store's connection.
```
Replace that first sentence with:
```markdown
During `Orchestrator.__init__()`, `StateStore.recover_stale_attempts()` is called with no arguments; the store uses its own connection internally.
```
The remainder of the paragraph ("It classifies every `running` attempt row and repairs attempt records only: ...") stays byte-identical.

## Compatibility considerations
- Docs-only change; no code or test impact in this file.
- If `wfaudit007`'s docs edit has already landed, its rewording of the "repairs attempt records only" half must be preserved — anchor on the call clause, not the whole paragraph.

## Security considerations
N/A (documentation change).

## Rollback considerations
Revert the sentence with the wfaudit015-full unit.

## Validation plan
Runnable as soon as this docs edit lands (independent of the code rows):
| Gate | Command | Expectation |
|---|---|---|
| Docs quality | `uv run python tools/check_docs_quality.py` | clean |
| Docs structure | `uv run python tools/check_docs_structure.py "docs/23_agent/*.md"` | clean |
| Content policy | `uv run python tools/check_docs_content_policy.py` | clean |
| Domain consistency | `uv run python tools/check_docs_consistency.py --domain agent` | clean |
| Language policy | `uv run python tools/check_docs_japanese.py` | clean |
| Stale claim check | `uv run python tools/stale_detector.py implementations/20261108-175155_09_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md` | "Procedure is not stale" |

## Completion criteria
- The Startup Recovery sentence states the no-argument call and internal connection use; no other sentence in the file changed.
- All docs checkers above exit clean.

## Out of Scope
- All production and test edits (documents 01-08).
- `agent_04_03` (confirmed no-change).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the Startup Recovery call clause | Pending | — | — | |
| 2 | Run the docs validation gates | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-003`
- **Source issue**: `issues/20261107-203228_wfaudit015_state-store-facade-bypass.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-175155
- **Related target files**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

<!-- tools/generate_workitem.py implementation-procedure timestamp: 20261108-175155 -->
