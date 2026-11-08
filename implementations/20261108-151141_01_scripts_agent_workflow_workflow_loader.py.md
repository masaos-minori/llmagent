# Implementation procedure: scripts/agent/workflow/workflow_loader.py

## Goal
Make the workflow loader reject malformed definition shapes with `WorkflowLoadError` at every field it reads:
- Add a `_require_dict` (new) helper next to `_require_int`, mirroring its field-naming message style.
- Validate the `stages` elements and the `retry_policy` value as dicts before the code paths index them (closes the
  raw `AttributeError` escapes: string stage at L108, non-dict `retry_policy` at L127).
- Enforce a strict bool for `retryable` in `_validate` (a stage `retryable` of `"false"` no longer loads as `True`;
  `0`/`None` no longer load silently).

## Scope
**Release unit**: wfaudit004-full
**Phases:** 1 (loader validation, `REQ-001`-`REQ-004`)
**Covers Plan target file row**: `scripts/agent/workflow/workflow_loader.py` (`Modify`, `REQ-001`-`REQ-004`)
- Only `scripts/agent/workflow/workflow_loader.py` (187 lines at HEAD `ad48bfa28`) is edited here.
- New symbol in this document: `_require_dict` (new). Existing symbols change behavior only, never signatures:
  `_validate` (L100), `WorkflowLoader` (L141).
- Test work is covered by its own procedure document
  `implementations/20261108-151141_02_tests_agent_workflow_test_workflow_loader.py.md` (Plan row
  `tests/agent/workflow/test_workflow_loader.py`); this document's Validation plan lists its pytest commands because
  they validate this file.

## Assumptions
- `scripts/agent/workflow/workflow_loader.py` at HEAD contains `_require_int` (L84-97), `_validate` (L100-138), and
  class `WorkflowLoader` with `load` (L141-187); `WorkflowLoadError` is defined in the same file (L57) and is the
  loader's established refusal exception. Verified by reading the file at `ad48bfa28`.
- The refusal message style is established by `_require_int`: `f"{label} must be an integer, got ..."` (L93).
  `WorkflowLoadError`-based refusals already exist for stages container (L106-107), stage keys (L124), numeric
  fields (L125, L131-132), `retry_on` (L74, L77-80), and `require_approval` (L134-138).
- Callers handle `WorkflowLoadError` as a refusal: `scripts/agent/workflow/validate.py` `validate_path` (L22) and its
  CLI `main` catch (L44); `scripts/agent/services/workflow_schema.py` `check_workflow_definition` (L22) catches
  `(WorkflowLoadError, ValueError, TypeError, AttributeError)` (L38) and re-raises as `RuntimeError` (L39);
  `scripts/agent/orchestrator.py` startup catches `(WorkflowLoadError, FileNotFoundError)` (L130). Verified at HEAD;
  raising `WorkflowLoadError` instead of letting `AttributeError` reach these handlers keeps startup refusal unchanged.
- `config/workflows/default.json` ships valid shapes (stage `id`/`timeout_sec`/`retryable`, `retry_policy` with
  `max_attempts`/`backoff_sec`/`retry_on`); the new checks are no-ops for it (existing shipped-file tests green).

## Design decisions
- Reuse the loader's existing refusal pattern: `_require_dict` (new) mirrors `_require_int`'s `type(value) is not dict`
  strictness and `f"{label} must be a dict, got {type(value).__name__}: {value!r}"` message shape.
- Validate before use: check each stage element is a dict immediately after the container check (before the `stage_ids`
  comprehension at L108), and check `retry_policy_data` is a dict immediately after L126 (before `.keys()` at L127), so
  a raw `AttributeError` can never precede a typed refusal.
- Enforce `type(stage["retryable"]) is bool` inside the per-stage loop of `_validate` (L121-125 region), not inside the
  `StageDefinition` construction at L161-168: validation stays in `_validate` (the established validation point) and
  the existing `bool(s["retryable"])` at L165 becomes a no-op for validated bools (left in place to keep the
  construction line unchanged).
- Stage `retryable` strictness mirrors `_require_int`'s bool rejection (`type(value) is not int` at L91): JSON bool
  only, no truthy coercion.

## Alternatives considered
- JSON-schema validation library for workflow definitions — rejected: heavy new dependency for a handful of type
  checks; the loader already owns field-by-field validation with typed messages (the `_require_int` pattern). The Plan
  prescribes helpers/checks in the existing style.
- Coercing non-bool `retryable` instead of rejecting — rejected: `retryable: "false"` coercing to `True` is the exact
  silent-behavior bug in the issue's live repro; acceptance criterion `REQ-003` requires rejection.
- Checking stages elements inside the `StageDefinition` comprehension in `load` instead of `_validate` — rejected:
  `_validate` is the single validation point already used for every other refusal; keeping refusals there preserves
  the documented order ("A value that fails this validation stops loading with a workflow load error").
- Replacing `bool(s["retryable"])` at L165 with `s["retryable"]` — rejected as necessary-but-not-sufficient and a
  behavior-visible edit; strict enforcement in `_validate` covers it without touching the construction line.

## Implementation
### Target file
`scripts/agent/workflow/workflow_loader.py`

**Fix notes (20261108-151141, revised 20261108-151141 after checker feedback): the loader's public entry point is
class `WorkflowLoader` with method `load` (L141-187), not a module-level function; `WorkflowLoadError` lives in this
file (L57), not a separate errors module.**

### Procedure
Add one new module-level helper and typed checks inside `_validate`. No signatures, return types, `WorkflowDef`
fields, or existing message texts change.

### Method

**Step 1 — New helper `_require_dict` (new), placed between `_require_int` (ends L97) and `_validate` (starts L100):**
```python
def _require_dict(value: object, label: str) -> dict[str, object]:
    """..."""
    if type(value) is not dict:
        raise WorkflowLoadError(
            f"{label} must be a dict, got {type(value).__name__}: {value!r}"
        )
    return value
```
Docstring in the same style as `_require_int` (state the strictness and that the error names the field).

**Step 2 — `stages` element dict check (inside `_validate`):**
- Keep the existing container refusal (`'stages' must be a non-empty list`, L106-107) byte-identical.
- Immediately after it, before the `stage_ids` comprehension (L108), add:
```python
for index, stage in enumerate(stages_data):
    _require_dict(stage, f"stage {index}")
```
  so string/int/None stage elements raise a named refusal before `s.get("id")` (L108) or `stage.keys()` (L122) run.
  The per-stage loop at L121-125 then needs no signature change (elements are guaranteed dicts).

**Step 3 — `retry_policy` dict guard:**
- After `retry_policy_data = data.get("retry_policy", {})` (L126) and before the `.keys()` difference (L127), insert
  `_require_dict(retry_policy_data, "retry_policy")` so a string/int `retry_policy` raises `retry_policy must be a
  dict, got ...` instead of crashing with `AttributeError` at L127. The required-keys refusal (L128-129) and numeric
  checks (L131-132) are unchanged.

**Step 4 — strict bool for `retryable` (inside the per-stage loop, after the `_require_int` timeout check L125):**
```python
if type(stage["retryable"]) is not bool:
    raise WorkflowLoadError(
        f"stages[{i}].retryable must be a bool, got {type(stage['retryable']).__name__}: {stage['retryable']!r}"
    )
```
Label style matches `stages[{i}].timeout_sec` (L125). The `bool(s["retryable"])` at L165 stays as-is (already-validated
bools pass through unchanged).

**Step 5 — docstring updates.** Module docstring (L2-5) and `_validate`'s docstring (L101) gain "field shapes"
wording (stage objects, `retry_policy` object, strict bool `retryable`) alongside the existing numeric statement, so
the module contract matches the new behavior.

**Step 6 — no other changes.** `_validate_retry_on`, `WorkflowLoader`'s `load` method including its parse and
not-a-dict guards (L153-158), and the `WorkflowDef` construction stay untouched.

### Details
- `bool` is an `int` subclass: `_require_int`'s `type(value) is not int` (L91) already refuses bools for numeric
  fields; the Step 4 `type(...) is bool` check is the mirror-image strictness (only bools).
- `stages` given as a dict container already raises `'stages' must be a non-empty list` (L106-107) — this procedure
  changes nothing there; it is a regression pin for the test procedure.
- Order inside `_validate` after the change: required keys (L102-104) → container list check (L106-107) → element dict
  check (Step 2) → duplicate/required-stage ids (L108-120) → per-stage keys/timeout/retryable (L121-125 + Step 4) →
  `retry_policy` dict guard (Step 3) → policy keys/numerics/`retry_on` (L127-133) → `require_approval` (L134-138).

## Compatibility considerations
- Error-type change for currently-crashing inputs: string/int stages and non-dict `retry_policy` raise
  `WorkflowLoadError` instead of raw `AttributeError`. `check_workflow_definition` already names `AttributeError` in
  its catch tuple (L38) — after the change the cause is `WorkflowLoadError`; the `RuntimeError` wrapper and startup
  refusal are unchanged. `orchestrator.py` L130 already handles `WorkflowLoadError`.
- Exact existing message texts must stay byte-identical (parametrized tests pin them): `'stages' must be a non-empty
  list` (L107), `stage[i] missing keys` (L124), `stages[i].timeout_sec must be ...` (L125 via `_require_int`),
  `retry_policy missing keys` (L129), `retry_policy.max_attempts`/`retry_policy.backoff_sec` messages (L131-132),
  `retry_on` messages (L74, L77-80), `require_approval` message (L134-138).
- `retryable: 0` / `None` / `"false"` previously loaded silently through `bool(...)` (L165); they now refuse. Shipped
  configs use literal JSON bools, so no shipped definition changes.
- `WorkflowDef` output shape, `WorkflowLoader.load`'s signature, and the `WorkflowLoadError` type are unchanged.

## Security considerations
- `{value!r}` in refusal messages reflects definition content into logs/errors; definitions are operator-supplied
  config, consistent with `_require_int`'s existing messages (no new exposure class). No untrusted-input path reaches
  the loader; definitions come from local config files.

## Rollback considerations
- Single-file change: `git checkout -- scripts/agent/workflow/workflow_loader.py` restores HEAD `ad48bfa28`. No DB
  migration, no config migration, no service-state change.

## Validation plan
Targeted tests (the companion test procedure implements them; run them against this file):
```bash
uv run pytest tests/agent/workflow/test_workflow_loader.py -q
uv run pytest tests/agent/workflow/ -q
uv run pytest tests/agent/services/ -q
```
Behavior assertions:
- New: string stage, int stage, `None` stage each raise `WorkflowLoadError` whose message names `stage N` and `must
  be a dict`; string/int `retry_policy` raises `retry_policy must be a dict...`. All fail on HEAD with raw
  `AttributeError` (issue repro, re-verified at `ad48bfa28`).
- New: non-bool `retryable` values (`"false"`, `0`, `None`) raise `WorkflowLoadError` (`retryable must be a bool...`);
  on HEAD `"false"` loads as `True` and `0`/`None` load as `False`.
- Regression pin: `stages` as a dict container still raises the existing `'stages' must be a non-empty list`.
- Regression pin: shipped `config/workflows/default.json` loads with identical `WorkflowDef` values before/after
  (existing shipped-file tests stay green).
- Run the full validation sequence from rules/toolchain.md (ruff, basedpyright, bandit, pip-audit, pytest) at completion.

## Completion criteria
1. Every malformed-shape case from the Plan's repro list raises `WorkflowLoadError` with a field-naming message; no
   raw `AttributeError` escapes `_validate` or `WorkflowLoader` `load` for dict/list/str/int/float/bool/None JSON values.
2. `stages` as a dict container still raises the unchanged existing message.
3. Stage `retryable` accepts only `True`/`False`; `"false"`, `0`, `None` refuse.
4. All pre-existing tests in `tests/agent/workflow/` pass unmodified (parametrized pins at
   `tests/agent/workflow/test_workflow_loader.py` L236 and L254 green).
5. `config/workflows/default.json` (and deployed `config/workflows/*.json` if probed) loads with unchanged values.
6. Lint/type/security gates green per rules/toolchain.md.

## Out of Scope
- New field validations the loader does not perform today (Plan Out of Scope: `retry_on` element values beyond the
  existing list/string/kind checks, `description` validation).
- `scripts/agent/services/workflow_schema.py` (Reference row; its catch tuple at L38 already lists `AttributeError`
  and stays unchanged) and `scripts/agent/orchestrator.py` (Reference; L130 already handles `WorkflowLoadError`).
- `scripts/agent/workflow/validate.py` (no change; `validate_path` already propagates `WorkflowLoadError`).
- Tests (own procedure document, Plan row `tests/agent/workflow/test_workflow_loader.py`); docs (own procedure
  document, Plan row `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`).

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_require_dict` (new) helper and stage/retry_policy/retryable type checks in `_validate` | Pending | — | — | |
| 2 | Run pytest per Validation plan (companion test procedure supplies the new tests; run the full loader test file) | Pending | — | — | |
| 3 | Confirm shipped `config/workflows/default.json` loads with identical `WorkflowDef` values before/after | Pending | — | — | |
| 4 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261107-203217_wfaudit004_loader-validation-gaps.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084007_wfaudit004_loader-validation-gaps.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-151141
- **Related target files**: `scripts/agent/workflow/workflow_loader.py`

<!-- tools/generate_workitem.py implementation-procedure 20261108-151141_01 from plans/20261108-084007_wfaudit004_loader-validation-gaps.md -->
