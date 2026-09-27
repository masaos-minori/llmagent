# Refactor repository_state.py to separate pipeline orchestration from the RepositoryState snapshot value object

## Priority
Medium

## Summary
Split the single large `repository_state.py` module so that `RepositoryState` is a pure frozen snapshot and the write-protection pipeline's orchestration logic lives in `WriteProtectionPipeline` (and its supporting dataclasses), not as methods on the snapshot. Remove the thin backward-compat delegation methods that merely re-expose snapshot fields. Behavior-preserving: no change to rejection messages, stage ordering, or the public contract.

## Background
The module docstring describes it as a frozen `RepositoryState` dataclass plus a multi-stage `WriteProtectionPipeline` orchestrator that unifies scattered `git.Repo` queries into a single snapshot per request, backing the process-local per-path write-serialization locks (REQ-005 / REQ-006). Over time, pipeline stage logic was added as methods on `RepositoryState` alongside the snapshot data. Current consumers: `git_service.py` builds the snapshot and runs the pipeline; `git_security.py` holds a repo-state reference; `git_models.py` exposes it through a Pydantic mixin; `format_output.py` reads the snapshot and remote-URL helpers; `git_server.py` serializes state. Tests live in `tests/mcp_servers/git/test_repository_state.py`.

## Problem
`RepositoryState` mixes two responsibilities in one frozen dataclass:

1. Immutable snapshot data (path, is_dirty, head_type, active_branch, ...) — its declared purpose.
2. Pipeline orchestration behavior (`verify_authorization`, `verify_preconditions`, `verify_postcondition`, `audit`, `structured_result`) — these are orchestration concerns that belong to the write-protection pipeline, not to the snapshot.

Consequences:

- The orchestrator `WriteProtectionPipeline.run()` reaches back into `self._state.verify_*()` instead of owning the stage logic, so the pipeline's control flow is split across two classes.
- The backward-compat delegation methods (`check_dirty_worktree`, `check_detached_head`, `validate_protected`, `validate_ref`) duplicate logic already available as properties/fields (`is_dirty`, `is_detached_head`, `protected_branch`, `ref_valid`) and return the same `(bool, str)` shape. Grep across `scripts/` and `tests/` shows they are invoked only by `tests/mcp_servers/git/test_repository_state.py`, never by production code under `scripts/`.
- Module-level helpers are not grouped by concern: the ref-validation family (`_normalize_branch_name`, `_is_safe_ref`, `_validate_ref`, `_is_protected_branch`) sits near the remote-URL family (`_resolve_remote_url`, `_redact_remote_url`).

## Reason for Change
Maintainability and testability. A reader must understand two concerns before trusting the snapshot, and the pipeline's control flow is divided between the snapshot and the orchestrator. The dead delegation surface adds a second place whose behavior must mirror the properties it duplicates. This is Medium priority: it affects maintainability and type-safety, not behavior, because the refactor preserves behavior.

## Implementation Intent
High level only.

- Make `RepositoryState` a pure frozen snapshot holding only captured data plus the transient `_repo` handle. Move the pipeline stage methods (`verify_authorization`, `verify_preconditions`, `verify_postcondition`, `audit`, `structured_result`) out of the snapshot and into `WriteProtectionPipeline` as methods or small private helpers owned by the pipeline, so the pipeline owns all stage logic in one class.
- Preserve exact rejection messages, stage names, and stage indices — these form the security contract.
- Investigate the backward-compat delegation methods; if confirmed unused outside tests, remove them and their dedicated tests, keeping the underlying properties intact. Retain any method that a missed non-test consumer still relies on.
- Group the module-level helpers by concern (ref-validation vs. remote-URL) without changing signatures.
- Do not change `snapshot()`, the Pydantic core schema, the frozen-dataclass field set, or the lock registry semantics.

## Target Files or Areas
- `scripts/mcp_servers/git/repository_state.py` — primary refactor target
- `tests/mcp_servers/git/test_repository_state.py` — update or remove tests for moved/removed members
- Reference/read only: `scripts/mcp_servers/git/git_service.py`, `git_security.py`, `git_models.py`, `format_output.py`, `git_server.py`

## Required Changes
- Move pipeline stage methods off `RepositoryState` into `WriteProtectionPipeline` (or pipeline-owned helpers); update `run()` to call them locally.
- Preserve every rejection message, stage name, and stage index exactly.
- Confirm via cross-module grep that the backward-compat delegation methods have zero non-test callers, then remove them and their dedicated tests.
- Co-locate ref-validation helpers and remote-URL helpers by concern.
- Keep `RepositoryState` frozen; keep `snapshot()`, `__get_pydantic_core_schema__`, `is_detached_head`, `repo`, `audit`, `structured_result` behavior identical (moved, not rewritten).

## Constraints
- Behavior-preserving: rejection messages, stage ordering/names, and pipeline result shape (`PipelineResult` / `PipelineStage`) must be unchanged.
- No change to the frozen dataclass fields, `snapshot()` inputs/outputs, or the Pydantic opaque-type schema.
- Do not alter the process-local per-path lock registry (`_repo_locks`, `_registry_guard`, `_get_repo_lock`) or the REQ-005 / REQ-006 serialization semantics.
- `_redact_remote_url` (credential redaction, REQ-003) and `_resolve_remote_url` behavior must stay identical — used by `format_output.py`.
- No new circular imports (callers import from `mcp_servers.git.repository_state`).
- Public symbols listed in `__all__` stay unchanged unless a removed member is explicitly approved.

## Acceptance Criteria
- [ ] `RepositoryState` retains no pipeline stage methods (the `verify_*` / `audit` / `structured_result` logic now lives in the pipeline)
- [ ] All existing rejection messages and stage names are byte-for-byte unchanged (diff against current strings)
- [ ] `PipelineResult` / `PipelineStage` shapes and the `reject` / `ok_result` factory outputs are unchanged
- [ ] Backward-compat delegation methods removed only if grep confirms zero non-test callers (otherwise retained)
- [ ] Module-level helpers grouped by concern with unchanged signatures
- [ ] `RepositoryState` remains frozen; `snapshot()`, `__get_pydantic_core_schema__`, `is_detached_head`, `repo` behave identically
- [ ] Existing test suite passes (see Testing Expectations)

## Testing Expectations
- Run the existing git MCP tests: `uv run pytest tests/mcp_servers/git/ -q --ignore=tests/integration/`
- `mypy` and `ruff` pass on all modified files
- Add regression tests covering the moved pipeline stage methods' rejection paths after relocation, so relocation cannot silently change behavior

## Documentation Impact
Update the module docstring and the `WriteProtectionPipeline` docstring to reflect that orchestration now lives in the pipeline rather than the snapshot. No external documentation updates required — the public API surface is unchanged.

## Out of Scope
- Changing write-protection policy, adding/removing pipeline stages, or branch/remote configuration
- Changing `snapshot()` semantics, dataclass fields, or the Pydantic schema
- Altering the lock registry or REQ-005 / REQ-006 serialization
- Renaming public symbols (`RepositoryState`, `WriteProtectionPipeline`, `PipelineResult`, `PipelineStage`)
- Fixing unrelated findings in sibling modules

## Dependencies
N/A: none

## Unresolved Questions
- Are the backward-compat delegation methods (`check_dirty_worktree`, `check_detached_head`, `validate_protected`, `validate_ref`) referenced by any generated or dynamic caller (reflection, dispatch tables) beyond what static grep finds? Verify before removal.
- Should `audit()` / `structured_result()` move into `WriteProtectionPipeline` as methods, or become standalone module functions? Both preserve behavior; this is a design choice.

## AI Implementation Instruction
Behavior-preserving only. Keep rejection messages, stage names, stage indices, and `PipelineResult` / `PipelineStage` shapes identical — diff the strings, do not paraphrase them. After moving each method, rerun `tests/mcp_servers/git/test_repository_state.py` before moving the next. If a non-test caller of a delegation method appears during the move, stop and report rather than removing it. Do not touch the lock registry or `snapshot()`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-185308
- **Related target files**: scripts/mcp_servers/git/repository_state.py, tests/mcp_servers/git/test_repository_state.py
