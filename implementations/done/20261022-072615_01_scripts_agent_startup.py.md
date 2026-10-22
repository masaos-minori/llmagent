## Goal

Delete the dead `StartupOrchestrator._classify_memory_failure` forwarding shim in
`scripts/agent/startup.py` (`REQ-001`, `REQ-002`). It is defined but never called; the
authoritative memory-failure classification lives in `PromptSetup._classify_memory_failure`
(`startup_prompt_setup.py:36`) and is used there.

## Scope

- **In-Scope**:
  - Delete the two-line `_classify_memory_failure` method (current lines 152-153) from
    `StartupOrchestrator` in `scripts/agent/startup.py`, plus the single trailing blank
    line (154) that precedes `_setup_prompt` (preserves method separation).
  - Confirm via repo-wide grep that nothing references
    `StartupOrchestrator._classify_memory_failure` before removal (`REQ-002`).
- **Out-of-Scope**:
  - Any change to `PromptSetup._classify_memory_failure` (`startup_prompt_setup.py:36`)
    or its call site (`startup_prompt_setup.py:82`).
  - Any change to the module-level `_classify_rag_failure` in `startup_validation.py`
    (live), or its docstring reference (`startup_validation.py:34`).
  - Behavior changes; the method is never called, so runtime behavior is unchanged.
  - Governance documentation updates.

## Assumptions

- **ASM-001**: The method is truly dead — verified by repo-wide
  `rg -n '_classify_memory_failure' scripts/ tests/`: the only matches are the dead
  definition (`startup.py:152-153`), the live `PromptSetup` definition+call
  (`startup_prompt_setup.py:36,82`), the `startup_validation.py:34` docstring reference,
  and test references to `PromptSetup._classify_memory_failure` (which target
  `PromptSetup`, not the shim).
- **ASM-002**: No external caller via dynamic attribute access. `rg` for
  `getattr`/`hasattr`/`__getattribute__` near startup shows only
  `startup_reporter.py:123` (`getattr(cfg_entry, "failure_policy", None)`) — unrelated to
  `_classify_memory_failure`. UNK-01 resolved.
- **ASM-003**: Removing the method does not change the class's public surface (private,
  `_`-prefixed).
- **ASM-004**: The plan's cited line numbers (139-140) predate star002's addition of the
  `except StartupInterrupted` branch; the method now sits at lines 152-153. This procedure
  cites the current source-verified lines.

## Design decisions

- Delete exactly the two-line def+return and the single trailing blank line before
  `_setup_prompt`. No call-site update is needed because no caller exists.
- Leave the delegation target (`PromptSetup._classify_memory_failure`) untouched — it
  remains reachable through `PromptSetup.setup_prompt()`.

## Alternatives considered

- Redirecting any future caller to call `self._prompt_setup._classify_memory_failure`
  directly: rejected — nothing calls the shim today, so there is no call site to redirect;
  adding a forwarder would recreate the very dead symbol this removes.

## Implementation

### Target file

`scripts/agent/startup.py`

### Procedure

1. Delete the `_classify_memory_failure` method (lines 152-153) and the trailing blank
   line 154 from `StartupOrchestrator` (`REQ-001`; `scripts/agent/startup.py`).

### Method

Edit the method body between `_report_readiness` and `_setup_prompt`. Remove the `def`
line, its `return` line, and the single blank line that separates the method from
`_setup_prompt`, so `_report_readiness` is immediately followed by `_setup_prompt`.

### Details

Current `StartupOrchestrator` tail (before deletion):

```python
    def _report_readiness(self, pipeline: StartupValidationResult) -> None:
        """Report aggregated readiness status after startup checks complete."""

    def _classify_memory_failure(self, exc: Exception) -> str:
        return self._prompt_setup._classify_memory_failure(exc)

    async def _setup_prompt(self) -> None:
        """Inject semantic memories into the initial system prompt."""
        await self._prompt_setup.setup_prompt()
```

Delete lines 152-154 (the `def`/`return` pair plus the trailing blank line):

```python
    def _report_readiness(self, pipeline: StartupValidationResult) -> None:
        """Report aggregated readiness status after startup checks complete."""

    async def _setup_prompt(self) -> None:
        """Inject semantic memories into the initial system prompt."""
        await self._prompt_setup.setup_prompt()
```

The method delegates to `self._prompt_setup._classify_memory_failure`, whose owner
`PromptSetup` is injected in `__init__` (`startup.py:65`); deleting the shim leaves that
dependency and the live classifier intact.

## Compatibility considerations

No runtime change: the shim was never called. `PromptSetup._classify_memory_failure`
(`startup_prompt_setup.py:36`) and its call site (`:82`) are byte-for-byte unchanged
(`REQ-003`; AC-003). Existing `tests/agent/test_startup_prompt_setup.py` exercises
`PromptSetup._classify_memory_failure(...)`, which is unaffected.

## Security considerations

N/A: no auth, secret, or crypto impact. No suppression added.

## Rollback considerations

Revert the single deletion (`git checkout scripts/agent/startup.py`, or re-insert the two
lines) — a single logical commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/startup.py` | Static: method removed; no dangling reference; method separation preserved | `rg`, `ruff`, `mypy`, `bandit` | AC-001, AC-002, AC-004 |
| Repo-wide `rg _classify_memory_failure` | Static: only `startup_prompt_setup.py` def/call + `startup_validation.py:34` docstring remain | `rg` | AC-002 |
| Startup unit suites | Behavior unchanged (method was uncalled) | `pytest` | AC-004 |

## Completion criteria

- `grep` of `startup.py` shows no `_classify_memory_failure` method on `StartupOrchestrator`
  (AC-001).
- A repo-wide `rg -n '_classify_memory_failure' scripts/ tests/` shows only the
  `startup_prompt_setup.py` definition/call and the `startup_validation.py` docstring
  reference (AC-002).
- `PromptSetup._classify_memory_failure` and its call site are unchanged (AC-003).
- `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/`,
  `uv run bandit scripts/agent/startup.py` pass; startup-related pytest suites pass
  (AC-004).

## Out of Scope

`scripts/agent/startup_prompt_setup.py` (live classifier),
`scripts/agent/startup_validation.py` (docstring + live `_classify_rag_failure`), retry
behavior, any other startup method.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261022-100112 | Deleted dead shim at startup.py:152-154 |
| 2 | Add or update tests per Validation plan | Completed | — | 20261022-100112 | N/A: dead-code removal — no test should cover an uncalled method; existing suite verifies the live PromptSetup classifier |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261022-100112 | ruff/mypy/bandit clean; startup suites green |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261022-100112 | N/A: no docs map to `startup.py` |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: `issues/done/20261021-220515_star004_remove-dead-startuporchestrator._classify_memory_failure-method.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261021-233609_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-072615
- **Related target files**: `scripts/agent/startup.py`
