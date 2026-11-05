## Goal

Remove the now-unused partial-completion counter from the LLM client so the counter
has a single owner (`RuntimeStats`).

## Scope
**Release unit**: N/A: not part of a release unit

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
