# Implementation Procedure: `tests/shared/test_runtime_tool_registry.py`

## Goal

Migrate this file's 19 `RuntimeToolRegistry(` constructions to explicit allowlists and convert the `allowed_servers=None` case into a `TypeError` regression (REQ-006: migration without changing assertion meaning; REQ-001 `None`-rejection regression per the plan's Tests section).

## Scope

- `tests/shared/test_runtime_tool_registry.py`: 19 constructions at lines 23, 260, 276, 291, 311, 327, 341, 349, 448, 462, 504, 518, 531, 537, 550, 560, 574, 588, 597 (measured at HEAD); 9 already pass `allowed_servers` explicitly and stay semantically identical.
- No production-code edits here (row 3 owns the constructor change).

## Assumptions

- Row 3 lands first (constructor already requires the argument); this file is expected red between row 3 and this migration — run `uv run pytest tests/shared/test_runtime_tool_registry.py` immediately after editing (plan Phase 2 per-file rule).
- Helper `_registry_with` (:22-23) builds `{tool.name: tool}` from the tools under test; its server keys are reachable from the `RuntimeTool` inputs the test constructs.

## Design decisions

- Migration rule (applies to all 12 migration rows): an explicit allowlist computed from the tools under test — `allowed_servers=frozenset(tool.server_key for tool in tools)` (or the literal set matching the test's scenario, mirroring the existing explicit sites like :318 `frozenset(["healthy"])`); deny-all scenarios already use `frozenset()` (:518, :563) and stay.
- The `allowed_servers=None` site (:531) becomes `test_allowed_servers_none_raises_type_error` (new): `pytest.raises(TypeError)`; the previous behavior assertion ("None keeps today's behavior") is deleted because that behavior no longer exists — this is the only intentional meaning change the plan sanctions (REQ-001's regression replaces it).

## Alternatives considered

- Passing `frozenset()` everywhere for brevity — rejected: deny-all would silently exclude tools and flip most assertions' meaning (violates REQ-006).

## Implementation

### Target file

`tests/shared/test_runtime_tool_registry.py`

### Procedure

1. `_registry_with` (:23): add `allowed_servers=frozenset({tool.server_key for tool in tools})` (computes from the varargs) so the ~8 constructions routed through it need no per-site change.
2. Sites :260-:341, :448, :462 (no allowlist today): add `allowed_servers=frozenset([...])` listing exactly the server keys of the tools built in that test.
3. Sites already explicit (:349, :504, :518, :537, :550, :560, :574, :588, :597): keep values byte-identical (characterization locks), except :518 stays `frozenset()` deny-all.
4. Site :531: replace the whole test body with the `TypeError` regression named above.

### Method

Per-construction diff review: after editing, `git diff` must show only added `allowed_servers=` kwargs (or the sanctioned :531 replacement); no assertion line may change (REQ-006 "assertion meaning unchanged").

### Details

- This file is the behavior spec for the constructor: keep its structure (helper + class grouping) intact; the new regression test joins the class covering the posture gate (:499-597 region).

## Compatibility considerations

- Run this file green before migrating the next test file (plan Phase 2 incremental rule); full-suite green is the Phase 2 gate (row 3 lists the coupling).

## Security considerations

- N/A: test migration; the deny-all and posture-exclusion assertions stay as fail-closed locks.

## Rollback considerations

- Revert with row 3 as one commit group.

## Validation plan

- `uv run pytest tests/shared/test_runtime_tool_registry.py`, then `uv run pytest tests/shared tests/agent` (plan Phase 2 "Done when").
- Gates: `uv run ruff check tests`, mypy test conventions per `rules/toolchain.md`.

## Completion criteria

- All 19 constructions explicit; the only behavior-flavored edit is the sanctioned `None` → `TypeError` regression; every other assertion byte-identical and green (plan AC-6).

## Out of Scope

- The 11 other test files (rows 12-22); the constructor change (row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate 19 constructions per Procedure 1-3 | Pending | — | — | Needs row 3 |
| 2 | Replace :531 test with `None`-rejection regression | Pending | — | — | REQ-001 lock |
| 3 | Run this file, then `tests/shared tests/agent` | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Row 3 (constructor) must land first | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (`None`-rejection regression), REQ-006 (19-construction migration, meaning preserved)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `tests/shared/test_runtime_tool_registry.py`
