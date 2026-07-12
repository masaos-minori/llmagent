# Implementation Procedure: tools/validate_docs_structure.py — front-matter reference existence check

Source plan: `plans/20260712-162714_plan.md`, Implementation step 3-5

## Goal

Add a new check to `tools/validate_docs_structure.py` that verifies every filename listed under
a doc's front-matter `related:`/`source:` fields actually exists under `docs/`, closing the gap
that let 58 files accumulate dead references undetected (see
`implementations/20260712-164711_docs_front_matter_dead_reference_cleanup.md` for the cleanup
this check guards against regressing).

## Scope

**In scope:**
- `tools/validate_docs_structure.py`: new function (front-matter reference existence check),
  wired into `validate_file()`.

**Out of scope:**
- `tools/check_docs_consistency.py` / `tools/check_mcp_docs_consistency.py` — not touched.
- Any `docs/*.md` content change (handled by the separate cleanup implementation doc, which must
  land first so this new check doesn't immediately fail against unfixed docs).

## Assumptions

1. `check_links()` (currently lines 86-95) and `check_front_matter()` (currently lines 53-74)
   still exist at approximately these locations — reconfirm with a direct read immediately before
   editing.
2. `main()`'s `total_issues` aggregation (currently lines 111-142) has no WARNING/ERROR severity
   distinction; every issue returned by any check function counts identically toward the single
   failure count and toward exit code 1. The new check follows this same pattern — it does not
   introduce a new severity concept.
3. The front-matter cleanup (`implementations/20260712-164711_...cleanup.md`) has already been
   applied before this check is wired in, so `uv run python tools/validate_docs_structure.py`
   stays clean immediately after this change (no docs should trigger the new check).

## Implementation

### Target file

`tools/validate_docs_structure.py`

### Procedure

1. Read the current file in full and reconfirm the exact line ranges of `check_front_matter()`,
   `check_links()`, and `validate_file()`.
2. Add a new function, e.g. `check_related_links(path: Path, content: str) -> list[str]`, placed
   near `check_front_matter()` and `check_links()` (after `check_links()`, before
   `validate_file()`).
3. Inside the new function:
   - Parse the front matter YAML the same way `check_front_matter()` does (`content[3:end]` via
     `yaml.safe_load`), or — if refactoring `validate_file()` to parse front matter once and pass
     the parsed `dict` to both `check_front_matter()` and the new function — update both call
     sites accordingly. Prefer the minimal-diff option (parse again in the new function) unless
     the refactor is trivial; do not restructure unrelated code.
   - For each of `related` and `source` keys present in the parsed front matter (both are
     optional at the YAML level even though `check_front_matter()` requires `related` to be
     *present*; `source` may be absent), iterate the list values.
   - For each entry, resolve `(path.parent / entry).resolve()` and check `.is_file()`, exactly
     mirroring `check_links()`'s existing resolution logic (do not invent a different path-join
     strategy).
   - If not a file, append an issue string:
     `f"{path.name}: front matter references missing file '{entry}' (field: related|source)"`
     (substitute the actual field name, not the literal `related|source`).
4. Wire the new function into `validate_file()`'s call sequence (after `check_links(path, content)`).
5. Run `uv run ruff format tools/validate_docs_structure.py` and
   `uv run ruff check tools/validate_docs_structure.py` to confirm style compliance.
6. Run `uv run mypy tools/validate_docs_structure.py` to confirm type-checks pass (the function
   signature must match the existing check function pattern: `(path: Path, content: str) ->
   list[str]` or `(path: Path, content: str) -> list[str]` consistent with siblings).

### Method

Pseudocode sketch (illustrative only, not production code):

```python
def check_related_links(path: Path, content: str) -> list[str]:
    if not content.startswith("---"):
        return []
    end = content.find("\n---", 3)
    if end == -1:
        return []
    try:
        data = yaml.safe_load(content[3:end]) or {}
    except yaml.YAMLError:
        return []  # already reported by check_front_matter(); avoid double-reporting
    issues = []
    for field in ("related", "source"):
        for entry in data.get(field) or []:
            resolved = (path.parent / entry).resolve()
            if not resolved.is_file():
                issues.append(
                    f"{path.name}: front matter references missing file '{entry}' (field: {field})"
                )
    return issues
```

### Details

- Do not raise on a YAML parse error inside this new function — `check_front_matter()` already
  reports malformed YAML; this function should silently return `[]` in that case to avoid
  duplicate/confusing error output for the same root cause.
- Keep the function's cyclomatic complexity low (target grade A/B per `radon cc`, consistent
  with sibling check functions in this file, which currently sit at CC 2-9).
- Do not modify `check_front_matter()`'s existing behavior (field-presence check stays as-is).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Structure validation | `uv run python tools/validate_docs_structure.py` | `All checks passed` (assuming the front-matter cleanup already landed) |
| Lint | `uv run ruff check tools/validate_docs_structure.py` | 0 errors |
| Format | `uv run ruff format --check tools/validate_docs_structure.py` | no changes needed |
| Type check | `uv run mypy tools/validate_docs_structure.py` | no new errors |
| Complexity baseline | `uv run radon cc tools/validate_docs_structure.py -s` | new function at grade A/B, consistent with existing functions |
| Regression test (manual, do not commit) | Temporarily add a fake dead reference to a scratch copy of a doc file (outside `docs/`, e.g. in the scratchpad dir) and run the check against it via a small ad-hoc script; confirm it reports the missing file. Revert/discard the scratch file — do not leave test artifacts under `docs/`. | Issue reported |
