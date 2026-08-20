# Implementation Procedure: Add Unit Tests for Model Reference Consistency Check

## Goal
Add unit tests for the new `check_model_reference_consistency()` function in `tests/tools/test_check_docs_consistency.py` (new file or extend):
- Pass case: all three canonical docs agree on model references
- Fail case: inject a mismatched filename, assert correct file/line pairs reported

## Scope
- Target file: `tests/tools/test_check_docs_consistency.py` (new file)
- Add two test functions for the new model reference consistency check

## Assumptions
- The new check function `check_model_reference_consistency()` exists in `tools/check_docs_consistency.py` or `tools/_docs_consistency_lib.py`
- Function signature: `check_model_reference_consistency(docs_dir: Path, repo_root: Path) -> list[Issue]`
- Test uses temporary directory with controlled doc content

## Design decisions
- Create new test file `tests/tools/test_check_docs_consistency.py` (no existing test file for this checker)
- Two test cases: pass (all docs agree) and fail (mismatched filename)
- Use `tmp_path` fixture for isolated temp docs
- Mock repo_root to point to temp directory

## Implementation
### Target file
`tests/tools/test_check_docs_consistency.py` (new file)

### Procedure
1. Create new test file
2. Add imports and fixtures
3. Add `test_model_reference_consistency_pass` test
4. Add `test_model_reference_consistency_fail` test

### Method
New Python test file creation

### Details
**Test file structure:**
```python
"""tests/tools/test_check_docs_consistency.py
Unit tests for tools/check_docs_consistency.py model reference consistency check.
"""

from __future__ import annotations

from pathlib import Path
import pytest
from tools._docs_consistency_lib import DocFile, Issue
from tools.check_docs_consistency import check_model_reference_consistency


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    """Create a temporary repo root with the three canonical docs."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    
    # Write three canonical docs with consistent model references
    (docs_dir / "01_overview-files-01-build.md").write_text("""---
title: "Build and Models File Structure"
category: overview
---
# ファイル構成
## 3. ファイル構成
``` text
/opt/llm/
├─ models/
│   ├─ chat-model-Q4_K_M.gguf
│   └─ embedding-model-Q8_0.gguf
```
""")
    
    (docs_dir / "02_deployment.md").write_text("""---
title: "Deployment Guide"
category: deployment
---
# デプロイ
## 1.4 LLM モデルの取得
| モデル | ファイル名 |
|---|---|
| multilingual-e5-small (埋め込み) | embedding-model-Q8_0.gguf |
| gemma-4-e4b-it (LLM) | chat-model-Q4_K_M.gguf |
""")
    
    (docs_dir / "03_rag_05_1-configuration-reference.md").write_text("""---
title: "RAG Configuration Reference"
category: rag
---
# 設定リファレンス
## 1.3 `config/ingester.toml`
| Parameter | Default | Description |
|---|---|---|
| `embedding_dims` | `384` | 埋め込みベクトルの次元数 (モデルと一致必須: embedding-model-Q8_0.gguf) |
""")
    
    return tmp_path


def test_model_reference_consistency_pass(repo_root: Path) -> None:
    """All three docs agree on model references -> no issues."""
    issues = check_model_reference_consistency(repo_root / "docs", repo_root)
    assert issues == []


def test_model_reference_consistency_fail(repo_root: Path) -> None:
    """Mismatched .gguf filename for chat_llm across docs -> issues reported."""
    # Override overview doc with mismatched chat model filename
    overview = repo_root / "docs" / "01_overview-files-01-build.md"
    overview.write_text("""---
title: "Build and Models File Structure"
category: overview
---
# ファイル構成
## 3. ファイル構成
``` text
/opt/llm/
├─ models/
│   ├─ different-chat-model-Q4_K_M.gguf
│   └─ embedding-model-Q8_0.gguf
```
""")
    
    issues = check_model_reference_consistency(repo_root / "docs", repo_root)
    
    # Should report exactly one conflict for chat_llm role
    assert len(issues) == 1
    issue = issues[0]
    assert issue.severity == "ERROR"
    assert "chat_llm" in issue.message
    assert "01_overview-files-01-build.md" in issue.file
    assert "02_deployment.md" in issue.message  # other file with different value
```

## Compatibility considerations
- New test file only; no existing tests modified
- Uses standard pytest patterns

## Security considerations
- None — test only

## Rollback considerations
- Git revert (delete test file)

## Validation plan
- `uv run pytest tests/tools/test_check_docs_consistency.py -v` — both tests pass
- `uv run pytest tests/tools/test_check_docs_consistency.py -v -k "model_reference"` — targeted run

## Out of scope
- Integration tests for full `check_docs_consistency.py` CLI (separate procedure)

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-221506_require.md
- Source plan: plans/20260819-174858_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-134200
- Related target files: tests/tools/test_check_docs_consistency.py