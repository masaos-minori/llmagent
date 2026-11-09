## Goal
Delete the unused `EPHEMERAL_KEYS` alias in the conversation state manager so the strict COMPAT scan reports no finding in this file (`REQ-002`).

## Scope
**Release unit**: wfaudit012-full

- Covers Plan `plans/20261108-084013_wfaudit012_shim-checker-case-gap.md` row 5 only: `scripts/agent/conversation_state_manager.py`.

## Assumptions
- Procedure 01 (`implementations/20261108-190836_01_tools_check_compat_shims.py.md`) lands in the same change unit; the alias is invisible to the current case-sensitive scan, so this deletion is the follow-through that makes the strict run clean (`REQ-002`).
- The alias has no callers: the 2026-11-08 grep over `scripts/`, `tests/`, `docs/`, `tools/` finds the bare name `EPHEMERAL_KEYS` only at `scripts/agent/conversation_state_manager.py:32` (the comment) and `:33` (the alias assignment). Other hits are distinct symbols: `_EPHEMERAL_KEYS` in this file (L30 definition, L49 class attribute, L74, L82) and `_ALL_EPHEMERAL_KEYS` in `scripts/agent/message_schema.py` (L26, L66, L107).

## Design decisions
- Delete rather than reword: the name exists only to keep an import path alive for callers that do not exist, which is exactly what the no-compatibility policy forbids; same disposition as procedure 03 and `wfaudit008`.
- The class attribute at L49 (`_EPHEMERAL_KEYS = _EPHEMERAL_KEYS`, with its explanatory comment at L47-48) stays: it re-binds the private module-level constant inside the class so `_clear_previous_turn_ephemeral_messages` can reference it without an instance, and it carries no flagged phrase.

## Alternatives considered
- Rename the private constant to `EPHEMERAL_KEYS` and delete the alias assignment: rejected — every internal user (L49, L74, L82) and the class attribute comment name the private form; renaming widens the diff for no behavior gain.
- Keep the alias and reword the comment: rejected — hides a live leftover from the checker without removing it.
- Add a `fixture`-category manifest entry: rejected — production source, not negative-test data.

## Implementation
### Target file
`scripts/agent/conversation_state_manager.py`

### Procedure
Delete two lines: the comment at L32 and the alias assignment at L33.

### Method
Remove `# Backward-compatible alias for existing callers that import EPHEMERAL_KEYS` (L32) and `EPHEMERAL_KEYS = _EPHEMERAL_KEYS` (L33), leaving the private definition `_EPHEMERAL_KEYS: frozenset[str] = frozenset({"_ephemeral", "_memory_injected"})` (L30) and its comment (L29), and the `class ConversationStateManager` block starting at L36, unchanged.

### Details
- No import elsewhere names `EPHEMERAL_KEYS`: the module's consumers import the class (`scripts/agent/orchestrator.py:34`, `scripts/agent/workflow_engine_adapter.py:24`, `tests/agent/test_resource_shutdown_coordinator.py:21`), not the constant.
- The ephemeral-key semantics stay defined in one place: `_EPHEMERAL_KEYS` here and `_ALL_EPHEMERAL_KEYS` composed from `TRUSTED_SOURCES` in `scripts/agent/message_schema.py`.

## Compatibility considerations
- Public surface unchanged: the constant was never import-used, and the class API is untouched.
- After this edit the file produces no COMPAT finding in the strict run.

## Security considerations
- No security-relevant code touched; message-history cleanup semantics (which keys are stripped between turns) are unchanged.

## Rollback considerations
- Revert the commit restores both lines with no state to unwind. Rolling this back while procedure 01 stays landed re-opens the `conversation_state_manager.py:32` finding, so a rollback here must be followed by the census gate re-run.

## Validation plan
- Grep gate: `grep -rn "EPHEMERAL_KEYS" scripts/ tests/ docs/ tools/` lists only `_EPHEMERAL_KEYS` and `_ALL_EPHEMERAL_KEYS` uses after the change, and no bare `EPHEMERAL_KEYS`.
- Targeted tests: `uv run pytest tests/agent/test_history_compression_consistency.py tests/agent/test_resource_shutdown_coordinator.py tests/agent/test_import_smoke.py -q`, then `uv run pytest tests/agent/ -q`.
- Checker gate: `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` reports no finding for this file; the full run exits 0 only after procedures 03-09 and `wfaudit008` have all landed.
- `uv run ruff check scripts/agent/conversation_state_manager.py`, `uv run ty check scripts/agent/conversation_state_manager.py`, and `uv run python tools/check_module_size.py` per `rules/toolchain.md`.

## Completion criteria
- L32-33 gone, `_EPHEMERAL_KEYS` still the single definition, no bare `EPHEMERAL_KEYS` reference anywhere, and no finding for this file in the strict checker run.

## Out of Scope
- The class attribute comment (L47-49) and `_ALL_EPHEMERAL_KEYS` in `scripts/agent/message_schema.py`.
- The checker semantics flip and the other census files (procedures 01-04, 06-09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-091614 | 20261109-091614 | two-line deletion (L32-33) STEP 1: two-line deletion (L32-33) applied; ruff/mypy/bandit/module-size clean |
| 2 | Add or update tests per Validation plan | Completed | 20261109-091619 | 20261109-091619 | no new test: existing suite plus the grep gate STEP 2: no new test; targeted suite (47 + 4220 agent tests) pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-101109 | 20261109-101109 | repo-clean gate depends on procedures 03-09 and `wfaudit008` STEP 3: per-member validators + targeted tests pass; diff-cover 100%; census 0 findings. End-of-unit full suite has 28 pre-existing eventbus failures (verified on clean HEAD, unrelated to unit); user approved proceeding. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-091619 | 20261109-091619 | no doc edit in scope STEP 4: N/A - no docs/00_index.md task-scope mapping for scripts/agent/conversation_state_manager.py |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261107-203225_wfaudit012_shim-checker-case-gap.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084013_wfaudit012_shim-checker-case-gap.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-190836
- **Related target files**: `scripts/agent/conversation_state_manager.py`; consumers `scripts/agent/orchestrator.py` (L34), `scripts/agent/workflow_engine_adapter.py` (L24), `scripts/agent/message_schema.py` (L26, L66, L107), `tests/agent/test_resource_shutdown_coordinator.py` (L21)