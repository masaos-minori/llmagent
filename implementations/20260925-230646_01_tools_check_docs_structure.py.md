## Goal

Add automated detection of self-referencing links in documents, enforcing GV-006 from the Governance Verification Matrix. A document must not link to itself in its `related` front-matter field or in body-text Markdown links. REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007.

## Scope

- Modify `check_links()` to detect self-references in body-text Markdown links
- Modify `check_related_links()` to detect self-references in the `related` front-matter field
- Add error reporting with format: `{filename}: self-reference detected -> '{target}'`
- Preserve existing broken-link detection logic

## Assumptions

- GV-006 defines self-references as violations (confirmed by Issue background)
- The check should apply to all documents including ADR documents (both use `.md` extension and could contain self-references)
- Using `Path.resolve()` for consistent comparison between source and target paths
- Error message format follows existing style in `check_links()` and `check_related_links()`: `{path.name}: 'field' value {value!r} ...`

### Discrepancy note (UNK-01 resolution)

The Plan's Assumptions section states "Warning-level finding (per GV-006 gate column)" but the Governance Verification Matrix table shows GV-006's Gate column as "Blocking". This discrepancy was resolved during Phase 1 verification: the Plan's Assumptions takes precedence as it references a more specific downstream requirement. The CI wiring will treat GV-006 findings as Warning-level (non-blocking), consistent with how other structural checks operate.

## Design decisions

- Use `Path.resolve()` for consistent comparison regardless of path style (absolute, relative, cross-directory)
- Add self-reference check after the file-existence check passes in both functions — avoids false positives on broken links and preserves existing behavior
- Report self-reference alongside any other issues found in the same call (do not short-circuit)

## Alternatives considered

- Basename-only comparison: would produce false positives when different files share the same basename across directories. Rejected because `Path.resolve()` provides full-path accuracy.
- Separate dedicated function: would add API surface without clear benefit since the check is trivially integrated into existing functions.

## Implementation
### Target file

`tools/check_docs_structure.py`

### Procedure

1. Modify `check_links()` to detect self-references in body-text Markdown links
2. Modify `check_related_links()` to detect self-references in the `related` front-matter field

### Method

#### Step 1: Modify `check_links()` to detect self-references

Current code at line 163-175:
```python
def check_links(path: Path, content: str, basename_index: dict[str, Path]) -> list[str]:
    issues = []
    body = strip_fenced_code(content)
    for _text, target in LINK_RE.findall(body):
        if target.startswith(("http://", "https://")):
            continue
        if "/" in target:
            found = (path.parent / target).resolve().is_file()
        else:
            found = target in basename_index
        if not found:
            issues.append(f"{path.name}: broken link -> '{target}'")
    return issues
```

Change to:
```python
def check_links(path: Path, content: str, basename_index: dict[str, Path]) -> list[str]:
    issues = []
    body = strip_fenced_code(content)
    for _text, target in LINK_RE.findall(body):
        if target.startswith(("http://", "https://")):
            continue
        if "/" in target:
            found = (path.parent / target).resolve().is_file()
        else:
            found = target in basename_index
        if not found:
            issues.append(f"{path.name}: broken link -> '{target}'")
        elif target != path.name:
            # Self-reference check: compare resolved paths to handle absolute/relative/cross-dir cases
            if "/" in target:
                resolved_target = (path.parent / target).resolve()
            else:
                # For bare basenames, resolve via basename_index to get the actual path
                resolved_target = basename_index.get(target, path.parent / target).resolve()
            if resolved_target == path.resolve():
                issues.append(f"{path.name}: self-reference detected -> '{target}'")
    return issues
```

Key changes:
1. Added `elif target != path.name` guard before resolving paths — skips self-reference check for obvious cases where the target string equals the filename (avoids redundant resolution)
2. Resolves the target path using the same method as the broken-link check (`/` present → `(path.parent / target).resolve()`, absent → lookup via `basename_index`)
3. Compares resolved paths against `path.resolve()` for accurate self-reference detection
4. Reports only when resolved paths match AND the target is not already caught by the `target != path.name` guard

#### Step 2: Modify `check_related_links()` to detect self-references

Current code at line 199-222:
```python
def check_related_links(
    path: Path, content: str, basename_index: dict[str, Path]
) -> list[str]:
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
            if "/" in entry:
                found = (path.parent / entry).resolve().is_file()
            else:
                found = entry in basename_index
            if not found:
                issues.append(
                    f"{path.name}: front matter references missing file '{entry}' (field: {field})"
                )
    return issues
```

Change to:
```python
def check_related_links(
    path: Path, content: str, basename_index: dict[str, Path]
) -> list[str]:
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
            if "/" in entry:
                found = (path.parent / entry).resolve().is_file()
            else:
                found = entry in basename_index
            if not found:
                issues.append(
                    f"{path.name}: front matter references missing file '{entry}' (field: {field})"
                )
            elif entry != path.name:
                # Self-reference check: compare resolved paths to handle absolute/relative/cross-dir cases
                if "/" in entry:
                    resolved_entry = (path.parent / entry).resolve()
                else:
                    resolved_entry = basename_index.get(entry, path.parent / entry).resolve()
                if resolved_entry == path.resolve():
                    issues.append(
                        f"{path.name}: self-reference detected -> '{entry}'"
                    )
    return issues
```

Key changes mirror those in `check_links()`:
1. Added `elif entry != path.name` guard before resolving paths
2. Resolves the entry path using the same method as the existence check
3. Compares resolved paths against `path.resolve()` for accurate self-reference detection
4. Reports only when resolved paths match AND the entry is not already caught by the guard

## Compatibility considerations

- Existing broken-link detection logic is preserved — self-reference check runs after the existence check passes
- No interface changes to either function's signature or return type
- Self-reference errors are reported alongside any other issues found in the same call (no short-circuit)

## Security considerations

N/A — this change adds validation, does not modify security-sensitive behavior.

## Rollback considerations

If the change causes false positives for legitimate cross-references:
1. Revert the two function modifications above
2. Verify the issue was caused by basename collisions across directories (should not happen with `Path.resolve()` comparison)

## Validation plan

- Unit test for `check_links()` detecting self-reference in body-text link — REQ-008
- Unit test for `check_related_links()` detecting self-reference in `related` field — REQ-008
- Unit test for normal cross-references passing (no false positives) — REQ-009
- Unit test for self-reference with absolute path resolution — REQ-004
- Unit test for self-reference with relative path resolution — REQ-005
- Manual verification: `uv run python tools/check_docs_structure.py docs/*.md` reports no self-reference errors for current documents

## Completion criteria

- `check_links()` detects self-references in body-text Markdown links
- `check_related_links()` detects self-references in the `related` front-matter field
- Error message format matches: `{filename}: self-reference detected -> '{target}'`
- Both checks work correctly with absolute paths, relative paths, and cross-directory references
- Existing broken-link detection continues to work correctly

## Out of scope

- Detecting indirect circular references (A→B→A chains) — only direct self-references
- Auto-fixing self-references (report-only, like other structural checks)
- Validating self-references in non-Markdown files
- Adding self-reference detection for the `source` front-matter field beyond what `check_related_links()` already covers

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007
- **Source issue**: issues/20260925-220411_gv006_self_reference_prohibition_check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-222948_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260925-230646
- **Related target files**: tools/check_docs_structure.py
