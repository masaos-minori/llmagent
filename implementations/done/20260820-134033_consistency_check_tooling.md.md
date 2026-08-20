# Implementation Procedure: Add Model Reference Consistency Check to Doc Consistency Checker

## Goal
Add a new check function to `tools/check_docs_consistency.py` / `tools/_docs_consistency_lib.py` that extracts `.gguf` filenames and `embedding_dims` values across the three canonical docs, groups them by role (chat LLM vs. embedding model), and fails when a role resolves to more than one distinct filename/dimension.

## Scope
- Target files:
  - `tools/check_docs_consistency.py` — wire new check into `overview`/`deployment`/`rag` domain blocks
  - `tools/_docs_consistency_lib.py` (or directly in `check_docs_consistency.py`) — add extraction/grouping function
  - `.github/workflows/overview-docs-consistency.yml`, `deployment-docs-consistency.yml`, `rag-docs-consistency.yml` — fix invocation to use consolidated script
  - `tests/tools/test_check_docs_consistency.py` (new or extend) — unit tests for new check

## Assumptions
- Domain-specific checks live in `check_docs_consistency.py` itself (not in `_docs_consistency_lib.py`) — add new function there
- Three target files are fixed paths: `docs/01_overview-files-01-build.md`, `docs/02_deployment.md`, `docs/03_rag_05_1-configuration-reference.md`
- Role classification heuristic: `.gguf` hit classified as `embedding` if nearby context contains "embed"/"埋込"/"埋め込み", else `chat_llm`
- Check is best-effort: returns `[]` if none of the three target files exist rather than hard-failing

## Design decisions
- Add `"modelrefs"` skip option to `ALL_SKIP_OPTIONS`
- Call new function inside `overview`/`deployment`/`rag` domain branches of `main()`
- Fix three CI workflow YAMLs to invoke `python tools/check_docs_consistency.py --domain <domain>` instead of deleted per-domain scripts
- Role classification heuristic documented as limitation (best-effort)

## Implementation
### Target files
1. `tools/check_docs_consistency.py` — add check function, skip option, wire into domain dispatch
2. `tools/_docs_consistency_lib.py` — if domain checks live here, add extraction function there
3. `.github/workflows/overview-docs-consistency.yml` — fix invocation
4. `.github/workflows/deployment-docs-consistency.yml` — fix invocation
5. `.github/workflows/rag-docs-consistency.yml` — fix invocation
6. `tests/tools/test_check_docs_consistency.py` (new or extend) — unit tests

### Procedure
1. Examine `tools/check_docs_consistency.py` structure to determine where to add the new check
2. Add `check_model_reference_consistency()` function with role-tagged extraction
3. Add `"modelrefs"` to `ALL_SKIP_OPTIONS`
4. Wire into `overview`/`deployment`/`rag` branches in `main()`
6. Fix three CI workflow YAMLs
7. Add unit tests (pass case + deliberately-mismatched fail case)

### Method
Direct Python code modifications with exact line matching

### Details
**New check function signature (add to `check_docs_consistency.py` or `_docs_consistency_lib.py`):**
```python
def check_model_reference_consistency(docs_dir: Path, repo_root: Path) -> list[Issue]:
    """Extract .gguf filenames and embedding_dims from the three canonical docs.
    
    Groups by role (chat_llm vs embedding) and flags conflicts.
    Returns list of Issues (ERROR severity) per conflicting file/line pair.
    """
    target_files = [
        repo_root / "docs" / "01_overview-files-01-build.md",
        repo_root / "docs" / "02_deployment.md",
        repo_root / "docs" / "03_rag_05_1-configuration-reference.md",
    ]
    # If none exist, return empty (best-effort)
    if not all(f.exists() for f in target_files):
        return []
    
    # Extract .gguf filenames and embedding_dims with role classification
    # Group by role across all three files
    # Emit ERROR Issue per conflicting file/line pair
    ...
```

**Role classification heuristic:**
```python
def _classify_gguf_role(line: str, context_lines: list[str]) -> str:
    """Classify .gguf hit as 'embedding' if nearby context contains embed keywords."""
    embed_keywords = ["embed", "埋込", "埋め込み", "embedding", "embedding_dims"]
    context = " ".join(context_lines + [line]).lower()
    if any(kw in context for kw in embed_keywords):
        return "embedding"
    return "chat_llm"
```

**Integration into `main()` (after line ~720):**
```python
# Domain-specific checks
if args.domain == "overview":
    if "modelrefs" not in skip:
        all_issues.extend(check_model_reference_consistency(docs_dir, repo_root))
    # ... existing checks
elif args.domain == "deployment":
    if "modelrefs" not in skip:
        all_issues.extend(check_model_reference_consistency(docs_dir, repo_root))
    # ... existing checks
elif args.domain == "rag":
    if "modelrefs" not in skip:
        all_issues.extend(check_model_reference_consistency(docs_dir, repo_root))
    # ... existing checks
```

**Add to `ALL_SKIP_OPTIONS` (around line 92):**
```python
ALL_SKIP_OPTIONS: frozenset[str] = frozenset(
    {
        "links",
        "removedfiles",
        "commanddrift",
        "filerefs",
        "funcrefs",
        "schemadrift",
        "diagnostics",
        "portdrift",
        "tooldrift",
        "crawlerconfig",
        "debugoutput",
        "dbcount",
        "dbtable",
        "configkey",
        "portrange",
        "conflisting",
        "modelrefs",  # NEW
    }
)
```

**CI Workflow Fixes (three files):**

`.github/workflows/overview-docs-consistency.yml`:
```yaml
# OLD: runs: python tools/check_overview_docs_consistency.py
# NEW:
runs: python tools/check_docs_consistency.py --domain overview
```

`.github/workflows/deployment-docs-consistency.yml`:
```yaml
runs: python tools/check_docs_consistency.py --domain deployment
```

`.github/workflows/rag-docs-consistency.yml`:
```yaml
runs: python tools/check_docs_consistency.py --domain rag
```

**Unit Tests (`tests/tools/test_check_docs_consistency.py`):**
```python
def test_model_reference_consistency_pass(tmp_path):
    # Create three temp docs with matching .gguf/embedding_dims
    # Run check_model_reference_consistency
    # Assert no issues returned

def test_model_reference_consistency_fail(tmp_path):
    # Create three temp docs with mismatched .gguf filename for chat_llm
    # Run check_model_reference_consistency
    # Assert Issue reported with correct file/line
```

## Compatibility considerations
- New check is additive; existing checks unchanged
- Skip option allows selective disable
- Best-effort: no hard-fail if target files missing

## Security considerations
- None — static analysis only

## Rollback considerations
- Git revert of modified files

## Validation plan
- `uv run pytest tests/tools/test_check_docs_consistency.py -v` — pass + fail cases
- `uv run python tools/check_docs_consistency.py --domain overview` (x3 domains) — exit 0 on reconciled docs
- CI workflows execute new command correctly

## Out of scope
- Fixing `agent-docs-consistency.yml` and `mcp-docs-consistency.yml` (out of scope per plan)

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-221506_require.md
- Source plan: plans/20260819-174858_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-134033
- Related target files: tools/check_docs_consistency.py, tools/_docs_consistency_lib.py, .github/workflows/overview-docs-consistency.yml, .github/workflows/deployment-docs-consistency.yml, .github/workflows/rag-docs-consistency.yml, tests/tools/test_check_docs_consistency.py