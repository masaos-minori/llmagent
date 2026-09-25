## Goal

Add duplicate link detection to `check_related_links()` and `check_links()` in `tools/check_docs_structure.py`, enforce GV-007 from the Governance Verification Matrix.

## Scope

- Extend `check_related_links()` (line 199) to detect duplicate entries in both `related` and `source` front-matter fields
- Extend `check_links()` (line 163) to detect duplicate Markdown links within body text
- Add `--check-duplicates` CLI flag to enable duplicate detection
- Wire `--check-duplicates` into `validate_file()` function

## Assumptions

- Duplicate detection should be opt-in via `--check-duplicates` flag (per plan's Assumptions section)
- Error message format follows existing pattern: `{filename}: duplicate related link -> '{target}' (appears {n} times)` for front-matter and `{filename}: duplicate link -> '{target}' (appears {n} times)` for body-text
- `Path.resolve()` normalization is sufficient for cross-format duplicate detection (bare filename vs full path)
- Using `collections.Counter` for counting occurrences (per plan's Design section)

## Design decisions

- Use `collections.Counter` to count occurrences of each resolved path/basename in both functions
- Resolve each entry via `Path.resolve()` if it contains `/`, otherwise look up via `basename_index`
- Both functions return findings in the format: `{filename}: duplicate {'related link'/'link'} -> '{target}' (appears {n} times)` where `n` is the occurrence count
- The CLI adds an optional `--check-duplicates` flag — when absent, duplicate detection is skipped entirely (preserving backward compatibility)
- When present, duplicate findings are reported alongside existing existence findings

## Alternatives considered

- Making duplicate detection default-on: rejected per plan's Risk mitigation — would cause widespread CI failures due to pre-existing violations across the corpus
- Adding a separate tool for duplicate detection: unnecessary since the existing functions already iterate over entries and can be extended inline

## Implementation

### Target file

`tools/check_docs_structure.py`

### Procedure

1. Add `--check-duplicates` CLI argument to `main()` in `tools/check_docs_structure.py`
2. Extend `check_related_links()` to count occurrences of each resolved path/basename and report duplicates when count > 1
3. Extend `check_links()` to count occurrences of each resolved path/basename and report duplicates when count > 1
4. Wire `--check-duplicates` flag to enable duplicate detection in `validate_file()`

### Method

Use Edit tool to modify each function sequentially.

### Details

**Step 1: Add `--check-duplicates` CLI argument**

In `main()` (line 247), add argparse argument:
```python
parser.add_argument("--check-duplicates", action="store_true", help="Check for duplicate links")
```

**Step 2: Extend `check_related_links()` (line 199)**

After line 211 (`issues = []`), add duplicate detection logic:
```python
if args.check_duplicates:
    seen: dict[str, int] = {}
    for field in ("related", "source"):
        for entry in data.get(field) or []:
            if "/" in entry:
                resolved = str((path.parent / entry).resolve())
            else:
                resolved = entry
            seen[resolved] = seen.get(resolved, 0) + 1
    for resolved, count in seen.items():
        if count > 1:
            issues.append(f"{path.name}: duplicate related link -> '{resolved}' (appears {count} times)")
```

**Step 3: Extend `check_links()` (line 163)**

After line 164 (`issues = []`), add duplicate detection logic:
```python
if args.check_duplicates:
    seen: dict[str, int] = {}
    for _text, target in LINK_RE.findall(body):
        if target.startswith(("http://", "https://")):
            continue
        if "/" in target:
            resolved = str((path.parent / target).resolve())
        else:
            resolved = target
        seen[resolved] = seen.get(resolved, 0) + 1
    for resolved, count in seen.items():
        if count > 1:
            issues.append(f"{path.name}: duplicate link -> '{resolved}' (appears {count} times)")
```

**Step 4: Wire `--check-duplicates` flag in `validate_file()`**

Pass `args.check_duplicates` through the call chain so both functions receive the flag.

## Compatibility considerations

- The `--check-duplicates` flag is opt-in, preserving backward compatibility — existing CI runs without the flag will not break
- Error message format follows the existing pattern used by broken-link detection, ensuring consistency
- No changes to existing error messages for missing files

## Security considerations

N/A: No security-relevant changes. This is a documentation validation enhancement.

## Rollback considerations

Revert the four Edit operations to restore the original functions. No data loss risk. The `--check-duplicates` flag can also be removed without affecting existing functionality.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/check_docs_structure.py | Unit tests for duplicate detection in `related` field | `uv run pytest tests/tools/test_check_docs_structure.py::test_duplicate_related_links` | All new and existing tests pass |
| tools/check_docs_structure.py | Unit tests for duplicate detection in `source` field | `uv run pytest tests/tools/test_check_docs_structure.py::test_duplicate_source_links` | All new and existing tests pass |
| tools/check_docs_structure.py | Unit tests for duplicate detection in body-text links | `uv run pytest tests/tools/test_check_docs_structure.py::test_duplicate_body_links` | All new and existing tests pass |
| tools/check_docs_structure.py | Regression test confirming existing broken-link detection still works | `uv run pytest tests/tools/test_check_docs_structure.py` | All existing tests pass |
| tools/check_docs_structure.py | Verify unique links pass validation (no false positives) | `uv run pytest tests/tools/test_check_docs_structure.py::test_unique_links_pass` | All new and existing tests pass |
| tools/check_docs_structure.py | Verify duplicate detection with mixed path formats | `uv run pytest tests/tools/test_check_docs_structure.py::test_mixed_path_formats` | All new and existing tests pass |
| .github/workflows/governance-docs-consistency.yml | Integration: verify CI step includes `--check-duplicates` | Manual review of YAML | Flag present in CI step |
| docs/00_governance/governance_04_documentation-checks.md | Verify GV-007 row shows "Existing" | Manual review of markdown table | Status = "Existing", Follow-up = "None" |

## Completion criteria

- `check_related_links()` detects duplicate entries in both `related` and `source` front-matter fields and reports the count
- `check_links()` detects duplicate Markdown links to the same target within a document and reports the count
- Documents with unique links pass validation (no false positives)
- Existing broken-link detection continues to work correctly alongside duplicate detection
- Duplicate detection works with both bare filenames and full paths as link targets
- Bare-filename and full-path references to the same file are treated as duplicates using `Path.resolve()` normalization
- The check is wired into CI pipeline as a Warning-level finding
- GV-007 status updated to "Existing" in the Governance Verification Matrix

## Out of scope

- Detecting duplicate links across multiple documents
- Auto-fixing duplicate links
- Validating duplicate links in non-Markdown files
- Modifying any files outside `Implementation Target Files` (additional target file discovery must be reported separately)

## Execution Status

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
- **Requirement ID**: REQ-001 — `check_related_links()` detects duplicate entries in the `related` front-matter field; REQ-002 — `check_related_links()` detects duplicate entries in the `source` front-matter field; REQ-003 — `check_links()` detects duplicate Markdown links to the same target within a document
- **Source issue**: issues/20260925-220411_gv007_duplicate_related_link_prohibition_check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-052849_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260926-060506
- **Related target files**: tools/check_docs_structure.py
