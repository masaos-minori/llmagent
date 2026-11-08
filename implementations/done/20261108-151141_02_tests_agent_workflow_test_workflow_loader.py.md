# Implementation procedure: tests/agent/workflow/test_workflow_loader.py

## Goal
Extend the existing loader test file with regression coverage that fails on HEAD and passes after the loader fix:
malformed `stages` element shapes, non-dict `retry_policy`, non-bool stage `retryable` values, the dict-container
regression pin, an entry-point test proving the startup preflight wraps loader shape errors (`__cause__` is
`WorkflowLoadError`, not `AttributeError`), and shipped-definition value pins.

## Scope
**Release unit**: wfaudit004-full
**Phases:** 1 (loader tests) and 2 (entry-point consistency test, `REQ-005`)
**Covers Plan target file row**: `tests/agent/workflow/test_workflow_loader.py` (`Modify`, `REQ-005`)
- All new tests live in the existing file `tests/agent/workflow/test_workflow_loader.py` (374 lines at HEAD
  `ad48bfa28`). No new test file is created; the file already owns the loader's numeric-validation, retry_on, and
  preflight test classes.
- Source-side work is covered by `implementations/20261108-151141_01_scripts_agent_workflow_workflow_loader.py.md`
  (Plan row `scripts/agent/workflow/workflow_loader.py`); this document adds only tests.

## Assumptions
- The file's fixtures and idioms at HEAD: module-level `_VALID` definition dict (L21, stages carry `id`,
  `timeout_sec`, `retryable`; stages are `plan`/`execute`/`verify`; `retry_policy` carries `max_attempts`,
  `backoff_sec`); `_write_json(tmp_path, "default", data)` helper; loader call idiom
  `WorkflowLoader(workflows_dir=tmp_path)` then `load()`; `WorkflowLoader` and `WorkflowLoadError` imported at L12.
  Verified by reading the file at `ad48bfa28`.
- Exact-message pins that must not change: `TestWorkflowLoaderNumericValidation` (class at L233) parametrized
  decorators at L236 (timeout_sec bad values `True`, `"120"`, `2.5`, `None`) and L254 (policy field x bad values);
  retry_on message tests (L270-336); `test_preflight_validate_path_loads_shipped_retry_on` (L341) which locally
  imports `validate_path` from `agent.workflow.validate`. Plan Risks row.
- Entry point under test: `check_workflow_definition` in `agent.services.workflow_schema` (L22) takes an optional
  `workflows_dir` argument and re-raises loader failures as `RuntimeError` from the caught exception (L38-39); on
  HEAD a string stage reaches it as `AttributeError`. Plan Reference Files (`workflow_schema.py` row, `Verified`).
- The entry-point test lives in this file (not in `tests/agent/services/`): it tests loader contract propagation and
  this file already contains the sibling preflight test at L341. Plan target row `Related Tests` cell `self`.

## Design decisions
- New test classes mirror the file's established structure: class docstring naming the requirement,
  `@pytest.mark.parametrize` value matrices, `pytest.raises(WorkflowLoadError, match=...)` with message substrings.
  New-case assertions match on substrings (`must be a dict`, `retryable must be a bool`) because exact wording is
  defined by the loader procedure (151141_01); pinned existing messages stay exact-match tests. Plan Acceptance
  Criteria `REQ-001`-`REQ-004`.
- Malformed stage element tests append the bad element to a full valid `_VALID` stage list (index 3), so the
  element-type refusal is the first failure and each case isolates one defect.
- Entry-point test asserts `pytest.raises(RuntimeError)` plus `isinstance(exc.__cause__, WorkflowLoadError)` —
  wrapping behavior `check_workflow_definition` already performs (L38-39); the change under test is the cause type.
  Plan Requirement Traceability (`REQ-005` row) and live repro.

## Alternatives considered
- Separate file `tests/agent/workflow/test_workflow_loader_shapes.py` — rejected: the Plan target row names the
  existing file, and related loader-contract tests already group here; a split file would scatter fixtures.
- Testing malformed shapes only through `validate_path` — rejected: the Plan repro list targets `_validate`
  directly; entry-point coverage is one additional test, not a replacement.
- Snapshot/golden comparison of the shipped `WorkflowDef` — rejected: shipped-file tests already exist (L336, L341);
  extending the same idiom with explicit `retryable is True/False` assertions is lighter.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_loader.py`

**Fix notes (20261108-151141, revised 20261108-151141 after checker feedback): the loader entry points are class
`WorkflowLoader` method `load` (imported at L12) and `validate_path` / `check_workflow_definition`; all fixture
references below were verified against the file at HEAD `ad48bfa28`.**

### Procedure
Add new test classes at the end of the file (after `TestWorkflowsDirResolver`). No existing test, fixture, helper, or
parametrized message string is modified.

### Method

**Step 1 — `TestWorkflowLoaderStageShapeValidation` (new), a class mirroring the numeric-validation class style:**
Parametrized bad stage element (append as the fourth stage of `copy.deepcopy(_VALID)` so required stages stay
valid), written with `_write_json` and loaded with the standard loader idiom (label → bad element → expected):

| Case id | Bad stage element | Expect after the loader fix | Fails on HEAD as |
|---|---|---|---|
| `string-stage` | `"analyze"` | `WorkflowLoadError`, message contains `stage 3` and `must be a dict` | raw `AttributeError` |
| `int-stage` | `42` | `WorkflowLoadError`, `stage 3 must be a dict...` | raw `AttributeError` |
| `none-stage` | `None` | `WorkflowLoadError`, `stage 3 must be a dict, got NoneType: None` | raw `AttributeError` |
| `dict-container-pin` | `stages={"id": "analyze", ...}` (whole container) | `WorkflowLoadError` matching the existing `'stages' must be a non-empty list` | already passes (regression pin) |

**Step 2 — `retry_policy` shape cases (same class):**
- `retry_policy="default"` (string) → `WorkflowLoadError`, message `retry_policy must be a dict, got str: 'default'`
  substring match; on HEAD: raw `AttributeError` from the `.keys()` read.
- `retry_policy=3` → same refusal shape; on HEAD: raw `AttributeError`.
- Regression pin: `retry_policy={"max_attempts": 3, "backoff_sec": 1, "retry_on": ["bogus"]}` → existing unknown-kind
  message stays byte-identical (pattern already pinned near L300; keep the existing test, add nothing here).

**Step 3 — `TestWorkflowLoaderRetryableStrictBool` (new), a class:**
Parametrize `stages[1]["retryable"]` (deep-copied `_VALID`) through `load()`:

| `retryable` value | Expect after the loader fix | Fails on HEAD as |
|---|---|---|
| `"false"` | `WorkflowLoadError`, message contains `retryable must be a bool` | loads; becomes `True` |
| `0` | `WorkflowLoadError`, same message shape | loads silently; becomes `False` |
| `None` | `WorkflowLoadError`, same message shape | loads silently; becomes `False` |
| `True` / `False` | load unchanged; assert `stage.retryable is True` / `is False` | already passes |

**Step 4 — entry-point consistency test (Phase 2, `REQ-005`):**
Add `test_check_workflow_definition_wraps_stage_shape_error` (new), a test function in a new class
`TestPreflightCauseWiring` (new), placed near the existing preflight test area: write a malformed definition (string stage element)
as `default.json` into `tmp_path`; locally import `check_workflow_definition` from `agent.services.workflow_schema`
(same local-import idiom as the test at L341); call it with `workflows_dir=tmp_path`; assert
`pytest.raises(RuntimeError)` and that the caught exception's `__cause__` is an instance of `WorkflowLoadError`. On
HEAD this fails: the cause is `AttributeError` (issue repro).

**Step 5 — shipped-definition value pin:**
Add `test_shipped_default_stage_retryable_values_are_bool` (new): load shipped `config/workflows/default.json` with the
module-level `WorkflowLoader()` idiom used at L336 and assert every `StageDefinition.retryable` is exactly `True` or
`False` (`type(...) is bool`), pinning the shipped file against the new strictness.

### Details
- No new module-level imports beyond L12: `check_workflow_definition` and `validate_path` are imported inside test
  bodies, following the existing L341-347 idiom.
- Parametrize `ids=` lists human-readable case ids (`"string-stage"`, ...) so failures name the case.
- Class docstrings state the requirement ids they cover (`REQ-001`-`REQ-005`) so the file's stated coverage matches
  its content.

## Compatibility considerations
- Tests are additive: existing tests, fixtures, helpers, and the pinned parametrized messages (L236, L254 and the
  retry_on tests) are not edited.
- New tests in Steps 1-4 fail on HEAD by design (raw `AttributeError`, or silent `True` for `retryable: "false"`) and
  pass only after the 151141_01 loader change; Plan Validation plan sequences loader and tests in one Phase 1/2 batch.
- The dict-container pin row (Step 1) and the shipped-file pins (Step 5) pass before and after unchanged.
- No changes to shared fixtures, so unrelated test classes in the file are unaffected.

## Security considerations
- Test fixtures contain only synthetic definition dicts; no secrets, no network, no DB side effects beyond the
  existing in-memory and `tmp_path` patterns of this file.

## Rollback considerations
- Single-file change: `git checkout -- tests/agent/workflow/test_workflow_loader.py` restores HEAD `ad48bfa28`. The
  added tests are pure additions; removing them cannot affect other test modules.

## Validation plan
```bash
uv run pytest tests/agent/workflow/test_workflow_loader.py -q          # targeted
uv run pytest tests/agent/workflow/ -q                                  # neighboring files
uv run pytest tests/agent/services/ -q                                  # entry-point side
uv run pytest tests/ -q                                                 # full suite at completion
```
- Red/green gate: Steps 1-4 new cases must fail on HEAD (raw `AttributeError` / silent load) and pass with the
  151141_01 loader change; pins (dict-container row, existing messages, shipped-file rows) pass before and after.
- Full `uv run pytest tests/ -q` green before completion (Plan Validation plan).

## Completion criteria
1. Each Plan repro case has a named test asserting `WorkflowLoadError` with a field-naming message substring.
2. `retryable: "false"` no longer loads; the test asserts refusal (on HEAD it asserted a silent `True` load).
3. Dict-container case and existing-message pins (L236/L254 patterns, unknown-kind `retry_on` message) pass unchanged.
4. Entry-point test asserts `RuntimeError.__cause__` is a `WorkflowLoadError`.
5. Shipped `config/workflows/default.json` values asserted unchanged, with strict-bool `retryable` pins.
6. Full suite green.

## Out of Scope
- Source loader changes (own procedure document, Plan row `scripts/agent/workflow/workflow_loader.py`).
- `tests/agent/services/` test files (no Plan target row; entry-point coverage lives here per Assumptions).
- `WorkflowLoader` name/dir resolution behavior (`TestWorkflowsDirResolver` already covers it; no new requirement).

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add shape-validation and strict-bool test classes (Steps 1-3) | Completed | — | 20261109-005342 |  |
| 2 | Add entry-point `__cause__` test and shipped-definition pin (Steps 4-5) | Completed | — | 20261109-005342 |  |
| 3 | Run pytest per Validation plan; confirm red-on-HEAD for new cases | Completed | — | 20261109-005342 |  |
| 4 | Run the validation sequence (rules/toolchain.md) | Completed | — | 20261109-005342 |  |

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
- **Requirement ID**: `REQ-005` (entry-point test); regression coverage for `REQ-001`-`REQ-004`
- **Source issue**: `issues/20261107-203217_wfaudit004_loader-validation-gaps.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084007_wfaudit004_loader-validation-gaps.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-151141
- **Related target files**: `tests/agent/workflow/test_workflow_loader.py`

<!-- tools/generate_workitem.py implementation-procedure 20261108-151141_02 from plans/20261108-084007_wfaudit004_loader-validation-gaps.md -->