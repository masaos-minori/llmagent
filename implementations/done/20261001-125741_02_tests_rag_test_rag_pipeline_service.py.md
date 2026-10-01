## Goal

Add a marker-lock guard to `tests/rag/test_rag_pipeline_service.py` that fails when the ADR-010 fallback markers (`ResultSource.FALLBACK` and the `scripts/rag/http_augment.py::in_process_fallback` literal) are produced outside their sanctioned production modules (REQ-005; resolves UNK-01).

## Scope

- **In-Scope**: Add one new test class to `tests/rag/test_rag_pipeline_service.py` that statically scans production sources under `scripts/` for the two markers.
- **Out-of-Scope**: Changing any fallback behavior; modifying other test files or any source file; judging whether the current 401/403 handling is correct (UNK-03).

## Assumptions

- `ResultSource.FALLBACK` is defined in `scripts/rag/models_result.py` and is currently referenced as an attribute only inside `AugmentRefiner.run_http_augment()` in `scripts/rag/augment.py` (verified with a repo-wide search over `scripts/` in this pass).
- The `scripts/rag/http_augment.py::in_process_fallback` literal currently appears only in `scripts/rag/http_augment.py`.
- The test module imports production code as top-level `rag.*` (scripts/ is on the import path), so the `scripts/` directory can be located from `rag.__file__`.
- Existing tests `test_401_no_fallback` / `test_403_no_fallback` / `test_json_parse_error_does_not_call_set_fallback_reason` pin only `call_rag_service()`'s return/reason contract (401/403: one request, `http_auth_error:` reason, `None`; parse error: `""`, no reason). They do not exercise the markers and must not be edited.

## Design decisions

- Use a static AST scan rather than runtime patching: the marker is an enum member referenced in one production statement, so "produced only in the sanctioned module" is a property of the source tree, and a scan fails deterministically when a new reference appears elsewhere.
- Two assertions, one per marker: the set of files (relative to `scripts/`) containing an `ast.Attribute` node `ResultSource.FALLBACK` must equal the sanctioned set; the set of files containing the string constant `scripts/rag/http_augment.py::in_process_fallback` must equal its sanctioned set.
- The sanctioned sets are module-level constants in the test class so a future ADR-approved relocation is a one-line, reviewable change.

## Alternatives considered

- **Patching `ResultSource.__new__` / enum members**: not feasible; enum members cannot be intercepted at assignment.
- **Callback tracking through `call_rag_service()` with HTTP 500/401**: rejected; it never touches `ResultSource.FALLBACK`, so it cannot detect relocation of the marker (and the 401/403 reason behavior is already pinned by existing tests).
- **Runtime test through `AugmentRefiner.run_http_augment()`**: deferred; it verifies marker values, not uniqueness of the production site, and needs a RagConfig fixture not present in this module.

## Implementation

### Target file

`tests/rag/test_rag_pipeline_service.py`

### Procedure

1. Re-confirm with `rg -n "ResultSource\.FALLBACK" scripts/` and `rg -n "in_process_fallback" scripts/` that the sanctioned sets are `{rag/augment.py}` and `{rag/http_augment.py}`.
2. Add `import ast` and `from pathlib import Path` at the top of the module (alongside the existing imports) and `import rag` for locating `scripts/`.
3. Append `class TestFallbackMarkerLockGuard` at the end of the module, following the existing class-per-concern layout.
4. Run the new class, then the whole module.

### Method

Add at module end (adapt names to the module's existing import style; keep type annotations, as `mypy` covers tests per `rules/toolchain.md`):

```python
class TestFallbackMarkerLockGuard:
    """ADR-010 markers must stay inside their sanctioned production modules."""

    _SCRIPTS_ROOT = Path(rag.__file__).resolve().parent.parent
    _FALLBACK_SOURCE_FILES = {"rag/augment.py"}
    _IN_PROCESS_FALLBACK_FILES = {"rag/http_augment.py"}

    def _production_trees(self) -> dict[str, ast.Module]:
        return {
            path.relative_to(self._SCRIPTS_ROOT).as_posix(): ast.parse(
                path.read_text(encoding="utf-8")
            )
            for path in self._SCRIPTS_ROOT.rglob("*.py")
            if "__pycache__" not in path.parts
        }

    def test_result_source_fallback_only_in_sanctioned_module(self) -> None:
        found = {
            name
            for name, tree in self._production_trees().items()
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute)
            and node.attr == "FALLBACK"
            and isinstance(node.value, ast.Name)
            and node.value.id == "ResultSource"
        }
        assert found == self._FALLBACK_SOURCE_FILES

    def test_in_process_fallback_literal_only_in_sanctioned_module(self) -> None:
        found = {
            name
            for name, tree in self._production_trees().items()
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and node.value == "in_process_fallback"
        }
        assert found == self._IN_PROCESS_FALLBACK_FILES
```

Verify before finalizing: that `rag.__file__` resolves to `scripts/rag/__init__.py` in the test environment (if `rag` is a namespace package, derive the root from `rag.pipeline_service.__file__` instead), and that every file under `scripts/` parses with `ast.parse`.

### Details

- A failure message should list the unexpected files (use `found - sanctioned` in the assert message) so a reviewer sees where the marker leaked.
- Do not add runtime mocks; the existing contract-pin tests stay untouched.
- If `ruff`/`mypy` flag the class-level `Path(...)` constant, move it into a module-level private constant.

## Compatibility considerations

- Test-only change; no production behavior change.
- The scan reads every `.py` file under `scripts/` once per test; runtime is small relative to the module's async tests.

## Security considerations

- None: read-only parsing of repository sources.

## Rollback considerations

- Revert the single commit that adds `tests/rag/test_rag_pipeline_service.py::TestFallbackMarkerLockGuard`; no other file is affected.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/rag/test_rag_pipeline_service.py` | Unit: new guard class | `uv run pytest tests/rag/test_rag_pipeline_service.py::TestFallbackMarkerLockGuard -q` | Both new tests pass |
| `tests/rag/test_rag_pipeline_service.py` | Regression: whole module (incl. `test_401_no_fallback`, `test_403_no_fallback`) | `uv run pytest tests/rag/test_rag_pipeline_service.py -q` | All pass |
| `tests/rag/test_rag_pipeline_service.py` | Negative check (manual, then revert): temporarily add `ResultSource.FALLBACK` reference in another `scripts/` module | `uv run pytest tests/rag/test_rag_pipeline_service.py::TestFallbackMarkerLockGuard -q` | The matching test fails (AC-5); revert the temporary edit |
| `tests/rag/test_rag_pipeline_service.py` | Lint/type | `uv run ruff check tests/rag/test_rag_pipeline_service.py` and `uv run mypy tests/rag/test_rag_pipeline_service.py` | Clean |

## Completion criteria

- `tests/rag/test_rag_pipeline_service.py::TestFallbackMarkerLockGuard` exists in `tests/rag/test_rag_pipeline_service.py` with one test per marker (REQ-005).
- The guard fails when either marker appears in an unsanctioned `scripts/` module (verified by the negative check; AC-5).
- All pre-existing tests in the module still pass.
- No file other than `tests/rag/test_rag_pipeline_service.py` is modified.

## Out of scope

- Changing or judging 401/403 fallback behavior (tracked as UNK-03 in the Plan).
- Editing any `scripts/` source file.
- Editing the ADR-004 document (separate procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261001-172654 | 20261001-172654 | stale check: clean after wording fix; changed: tests/rag/test_rag_pipeline_service.py |
| 2 | Add or update tests per Validation plan | Completed | 20261001-172654 | 20261001-172654 | new class: 2 tests pass; negative check fails as expected and was reverted; module 18 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261001-172654 | 20261001-172654 | ruff format/check pass; mypy 16 pre-existing errors, none in new lines; bandit Low only (assert); full suite 8006 passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261001-172654 | 20261001-172654 | N/A: no docs/00_index.md task-scope mapping for tests file |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | N/A: no blockers | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005
- **Source issue**: `issues/20260930-134926_adr004inv15_adr-004-inv-15-and-inv-16-cross-cutting-fallback-audit-not-re-verified.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260930-212727_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-132025
- **Related target files**: tests/rag/test_rag_pipeline_service.py