## Goal

Remove the now-unused partial-completion counter from the LLM client so the counter
has a single owner (`RuntimeStats`).

## Scope
**Release unit**: partial-counter-owner (plan Release units: Phases 2, 3 — validated and released together)

## Assumptions

- The client attribute was initialized once and incremented only by the two writers
  (the runner at `scripts/agent/llm_turn_runner.py` and the deleted module).
- `LLMClient.stream` never reads or writes the attribute.

## Design decisions

- Delete the single attribute initialization line from the constructor.

## Alternatives considered

- Leaving the attribute as dead state: rejected; `vulture` flags it and it is a
  second owner of the counter.

## Implementation
### Target file
`scripts/shared/llm_client.py`

### Procedure

- Remove `self.stat_partial_completions: int = 0` from the client constructor
  (the cumulative session-statistics block, between `stat_parse_errors` and
  `apply_config`).

### Method

- One-line removal; no other reference to the attribute remains after the runner
  change and the module deletion.

### Details

- `vulture scripts/ --min-confidence 80` reports no dangling reference after this
  change.

## Compatibility considerations

- No public contract change; the attribute was internal bookkeeping.

## Security considerations

- N/A: no auth, secret, or input-handling change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run vulture scripts/ --min-confidence 80` is clean for this attribute.
- Full test suite passes.

## Completion criteria

- `llm_client.py` no longer defines `stat_partial_completions`; no reference remains.

## Out of Scope

- Any change to client retry, stream, or heartbeat behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-05T14:55 | 2026-11-05T15:00 | Step 3b verification 2026-11-05: clean (attribute at llm_client.py L82 in the stats block confirmed; stale_detector: not stale). Correction: unit line added. Removed self.stat_partial_completions init line from LLMClient constructor (between stat_parse_errors and apply_config). |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-05T15:00 | 2026-11-05T15:05 | Targeted: tests/shared 1225 passed; plan-listed integration run (test_rag_llm_integration.py + test_orchestrator_integration.py) 47 passed; runner-path re-run 181 passed. Step 3e: ruff clean; mypy clean (490 files); vulture: 0 findings for stat_partial_completions (pre-existing unrelated findings unchanged). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-05 | 2026-11-05 | End-of-unit full-suite run 1: 11565 passed / 2 failed (mdq flaky per Failure Log + manifest-drift test). Allowed re-run 2: 11566 passed / 1 failed = test_live_docs_have_no_drift = allowed-red manifest drift (Failure Log), cleared by companion 08. diff-cover: scripts/agent/llm_turn_runner.py 100% (Total 1 line, Missing 0); coverage.xml written. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-05 | 2026-11-05 | Matching row 'LLM client (streaming/retry)' -> agent_05_llm-and-streaming.md exists, but no doc content references the removed attribute (grep: only agent_03_02/03_03 mention stat_partial_completions, all via ctx.stats, prose unchanged); no edit made. Stale references in agent_10_05/agent_13 are companions 07/08 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-084444_03_scripts_shared_llm_client.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002 — remove the unused client counter
- **Source issue**: issues/20261031-180511_partialcount001_partial-completion-counter-dead.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115736_partialcount001_partial-completion-counter-dead.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-084444
- **Related target files**: scripts/shared/llm_client.py
