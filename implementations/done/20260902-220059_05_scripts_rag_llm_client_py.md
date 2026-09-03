## Goal

Update the two `load_all()` call sites in `scripts/rag/llm_client.py` to invoke the fail-closed path.

## Scope

Modify `scripts/rag/llm_client.py` only. Update the `load_all()` calls at lines 68 and 81 to pass `strict=True` if REQ-001's fix does not make the default strict.

## Assumptions

- REQ-001's fix determines whether this file needs a separate change. If REQ-001 changes the default to `True`, no change is needed here.
- Both `cfg = ConfigLoader().load_all()` calls at lines 68 and 81 currently omit `strict`.

## Design decisions

- Conditional approach: only modify this file if REQ-001 requires explicit `strict=True` arguments at callers.
- If REQ-001 changes the default, this file is left unchanged.

## Alternatives considered

- Always adding `strict=True` regardless of REQ-001's approach. Rejected because it would be redundant if REQ-001 changes the default.

## Implementation

### Target file

`scripts/rag/llm_client.py`

### Procedure

After applying REQ-001's fix, determine whether this file needs modification:
- If REQ-001 changed the default to `True`: no change needed.
- If REQ-001 added explicit `strict=True` to callers: update lines 68 and 81 to pass `strict=True`.

### Method

1. After REQ-001 is applied, read `scripts/rag/llm_client.py` lines 65-85 to confirm both call sites.
2. Determine if the `load_all()` calls still omit `strict`.
3. If yes, add `strict=True` argument to both calls.

### Details

1. Read `scripts/rag/llm_client.py` around lines 68 and 81 to confirm current state.
2. Apply conditional change based on REQ-001's outcome.

## Compatibility considerations

- RAG LLM client startup: if the client previously relied on silent-continue for a missing `agent.toml`, this change will now cause it to raise `ConfigMissingError`.

## Security considerations

- Medium blast radius: RAG LLM client startup. Making it fail-closed aligns with ADR-004 INV-01/INV-02's Fail-Fast requirements.

## Rollback considerations

- Revert the `strict=True` additions if any were made. No other rollback needed.

## Validation plan

Run `uv run pytest tests/shared/test_config_loader.py -v` and `uv run pytest tests/agent/test_startup.py -v` to confirm no regressions.

## Completion criteria

- Either confirmed no change needed (if REQ-001 changes the default), or `strict=True` added to both lines 68 and 81
- All existing tests pass

## Out of scope

- Changes to other `load_all()` call sites (handled by their respective documents)
- Unknown-key rejection (REQ-004, handled separately)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | No change needed; REQ-001 made load_all() default to strict=True |
| 2 | Add or update tests per Validation plan | Skipped | — | — | No code change required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Skipped | — | — | No code change required |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | No code change required |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260902-101452_h02_config_loader_fail_closed_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-191443_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-220059
- **Related target files**: scripts/rag/llm_client.py
