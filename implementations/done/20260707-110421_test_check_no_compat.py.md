## Goal
Add per-pattern detection tests and allowlist pass-through tests to `tests/test_check_no_compat.py` for the 12 new workflow enforcement patterns.

## Scope
**In**: `tests/test_check_no_compat.py` — add tests for each new pattern; add allowlist test; add `WorkflowExecutionPolicy` import test.
**Out**: Existing tests for other patterns; `check_no_compat.py` implementation (see its doc).

## Assumptions
- `tests/test_check_no_compat.py` exists (confirmed by UNK-01 in Plan 14).
- A `check_compat_patterns(content: str, path: Path, allowlist: set[Path]) -> list[str]` function is importable from `tools.check_no_compat`.
- Each new pattern name matches exactly what is added to `COMPAT_PATTERNS` (see check_no_compat.py doc).

## Implementation

**Target file**: `tests/test_check_no_compat.py`

**Test additions**:
```python
from pathlib import Path
from tools.check_no_compat import check_compat_patterns

def _check(content: str) -> list[str]:
    return check_compat_patterns(content, Path("scripts/test.py"), set())

# One test per new pattern
def test_detects_workflow_mode_field_reference():
    assert any("workflow_mode field reference" in i for i in _check("workflow_mode: str = 'auto'"))

def test_detects_allow_startup_fallback():
    assert any("allow_startup_fallback" in i for i in _check("if self.allow_startup_fallback():"))

def test_detects_is_workflow_enabled():
    assert any("is_workflow_enabled" in i for i in _check("if not policy.is_workflow_enabled():"))

def test_detects_requires_startup_definition():
    assert any("requires_startup_definition" in i for i in _check("policy.requires_startup_definition()"))

def test_detects_allow_turn_fallback():
    assert any("allow_turn_fallback" in i for i in _check("if policy.allow_turn_fallback():"))

def test_detects_workflow_mode_disabled_string():
    assert any("workflow_mode=disabled" in i for i in _check('workflow_mode="disabled"'))

def test_detects_workflow_mode_auto_string():
    assert any("workflow_mode=auto" in i for i in _check('workflow_mode="auto"'))

def test_detects_workflow_mode_disabled_log():
    assert any("Workflow mode=disabled" in i for i in _check('logger.info("Workflow mode=disabled")'))

def test_detects_direct_llm_path_phrase():
    assert any("direct LLM path" in i for i in _check("# direct LLM path fallback"))

def test_detects_direct_execution_fallback_phrase():
    assert any("direct-execution fallback" in i for i in _check("# direct-execution fallback"))

def test_detects_workflow_execution_policy_import():
    assert any("WorkflowExecutionPolicy import" in i for i in _check(
        "from agent.workflow_execution_policy import WorkflowExecutionPolicy"
    ))

def test_detects_workflow_execution_policy_module_import():
    assert any("workflow_execution_policy module import" in i for i in _check(
        "import workflow_execution_policy"
    ))

# Allowlist test
def test_allowlisted_file_not_flagged():
    content = "workflow_mode: str = 'auto'"
    issues = check_compat_patterns(content, Path("scripts/test.py"), {Path("scripts/test.py")})
    assert issues == []

# No false positive for unrelated "mode="
def test_unrelated_mode_assignment_not_flagged():
    content = 'display_mode = "compact"'
    issues = _check(content)
    # "display_mode" should not match "workflow_mode" pattern
    assert not any("workflow_mode field reference" in i for i in issues)
```

**Method**: Unit test addition — direct function call, no subprocess.

**Details**:
- If `check_compat_patterns` is not a public function, expose it or test via the module's `__main__` entry point.
- The `test_unrelated_mode_assignment_not_flagged` test verifies the regex is not overly broad.

## Validation plan
- `uv run pytest tests/test_check_no_compat.py -x -q -v`

---
*Plan: 20260707-105310 (req14) Phase 4*
