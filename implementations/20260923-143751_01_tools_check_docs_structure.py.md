## Goal

Implement REQ-001 through REQ-005 (`plans/20260923-142045_plan.md`) in
`tools/check_docs_structure.py`: make `check_related_links()`/`check_links()` resolve
bare-filename cross-references via a repository-wide basename index instead of
directory-relative resolution, fail loudly on a future duplicate basename, and make
the default file-discovery glob recursive.

## Scope

Modify only `tools/check_docs_structure.py` to:
1. Add a module-level `_build_basename_index()` helper (REQ-001).
2. Change `check_related_links()` to resolve via the index, with a fallback for
   already-directory-qualified entries (REQ-002).
3. Change `check_links()` the same way (REQ-003).
4. Fail loudly (non-zero exit, explicit message) if the index finds a duplicate
   basename (REQ-004).
5. Change `main()`'s default glob from `docs/*.md` to `docs/**/*.md`, build the index
   once, and thread it through `validate_file()` into both check functions (REQ-001,
   REQ-005).

## Assumptions

- Every filename under `docs/**/*.md` is currently globally unique (confirmed by the
  Plan: 0 duplicate basenames across 188 files) — REQ-004 exists precisely so this
  stops being a silent assumption going forward.
- `validate_file()` has exactly one production call site (`main()`, this same file,
  line 253) and two test call sites (`tests/tools/test_check_docs_structure.py`, lines
  170 and 179) — confirmed via `rg "validate_file\("`. Adding a new required parameter
  to `validate_file()`'s signature will make those two existing test calls raise
  `TypeError` until updated — that update is the responsibility of this Plan's other
  implementation procedure document (`tests/tools/test_check_docs_structure.py`, seq
  02), not this one. This document's own "Completion criteria" therefore does not
  require the full test suite to pass in isolation — see Out of scope.
- No other tool in the repository parses the exact "references missing file" / "broken
  link" issue message strings (confirmed via `rg "references missing file|broken link ->" --type py -l`
  — only this file itself matches) — the message format can be preserved as-is without
  a hidden cross-tool dependency.

## Design decisions

- Build the basename index by scanning `(ROOT_DIR / "docs").rglob("*.md")` once,
  inside `main()`, before the existing file-discovery glob loop — not inside
  `check_related_links()`/`check_links()` themselves, since those are called once per
  file and must not each rescan the whole tree.
- Resolution order per reference, applied in both `check_related_links()` and
  `check_links()`: if the entry contains a path separator (`/`) — an
  already-directory-qualified reference such as `adr/ADR-010-rag-fallback.md` or
  `../00_governance_01_documentation-policy.md`, both confirmed in use today — resolve
  it via the existing `(path.parent / entry).resolve()` check first. Otherwise (a bare
  filename), look it up as `basename_index.get(entry)`. This preserves every reference
  style already in use in the repository today rather than replacing the old check
  outright.
- Detect a duplicate basename during index construction, not lazily during individual
  file checks — a duplicate is a repository-wide integrity problem, not a per-file one,
  and should be reported once, clearly, rather than surfacing as confusing per-file
  noise.
- Thread the index through as an explicit parameter (`basename_index: dict[str, Path]`)
  rather than a module-level global or a class — keeps the existing free-function
  structure and signatures with one added parameter each, matching this file's current
  style (plain functions, no classes).

## Alternatives considered

- Rewriting every existing cross-reference in `docs/*.md` to use an explicit relative
  path instead of a bare filename: rejected — this is exactly the manual, large-blast-
  radius rewrite this Plan exists to avoid (298 references across the tree), and is
  explicitly out of scope per the source Issue and Plan.
- Re-scanning `docs/**/*.md` on demand inside each call to `check_related_links()`/
  `check_links()` instead of building the index once in `main()`: rejected — `O(files²)`
  in the worst case (one full rescan per file being validated) instead of `O(files)`,
  and would need its own separate duplicate-detection pass anyway, duplicating REQ-004's
  logic across many call sites instead of once.
- Silently keeping the first match found when two files share a basename: rejected per
  REQ-004 — an unnoticed regression given the whole reorg's cross-reference safety
  depends on basename uniqueness continuing to hold.

## Implementation

### Target file

`tools/check_docs_structure.py`

### Procedure

1. Add `_build_basename_index(docs_dir: Path) -> dict[str, Path]` near the top of the
   file (after the `LINK_RE` definition, before `strip_fenced_code`): iterate
   `docs_dir.rglob("*.md")`, and for each file, check whether `path.name` is already a
   key in the index; if so, raise a `ValueError` naming both conflicting paths;
   otherwise add it.
2. Change `check_related_links(path, content)` to `check_related_links(path, content, basename_index)`:
   for each `related`/`source` entry, if `"/" in entry`, resolve via the existing
   `(path.parent / entry).resolve()` check (unchanged); otherwise look up
   `basename_index.get(entry)` and report "references missing file" if it is `None`.
3. Change `check_links(path, content)` to `check_links(path, content, basename_index)`
   with the same resolution-order change as step 2, reporting "broken link" on a miss.
4. Change `validate_file(path, expected_area, schema=None)` to
   `validate_file(path, expected_area, schema=None, *, basename_index)` (keyword-only,
   required — no default, since every real caller must supply it): pass
   `basename_index` through to the two updated calls at the end of the function.
5. In `main()`: change `patterns = args.globs or ["docs/*.md"]` to
   `patterns = args.globs or ["docs/**/*.md"]`; call
   `basename_index = _build_basename_index(DOCS_DIR)` once, wrapped so a `ValueError`
   from step 1 is caught, printed to stderr, and causes `main()` to return `1`
   immediately (before any file validation runs); pass `basename_index=basename_index`
   into the existing `validate_file(path, args.area, schema)` call.

### Method

Direct source edit via targeted `Edit` calls to the five locations above; no external
migration script needed, no other file touched.

### Details

Current (`check_related_links`, lines 176-194):
```python
def check_related_links(path: Path, content: str) -> list[str]:
    ...
    for field in ("related", "source"):
        for entry in data.get(field) or []:
            resolved = (path.parent / entry).resolve()
            if not resolved.is_file():
                issues.append(
                    f"{path.name}: front matter references missing file '{entry}' (field: {field})"
                )
    return issues
```

After modification (illustrative; `check_links` follows the same pattern):
```python
def check_related_links(
    path: Path, content: str, basename_index: dict[str, Path]
) -> list[str]:
    ...
    for field in ("related", "source"):
        for entry in data.get(field) or []:
            if "/" in entry:
                resolved = (path.parent / entry).resolve()
                found = resolved.is_file()
            else:
                found = entry in basename_index
            if not found:
                issues.append(
                    f"{path.name}: front matter references missing file '{entry}' (field: {field})"
                )
    return issues
```

New helper, added before `strip_fenced_code`:
```python
def _build_basename_index(docs_dir: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for path in docs_dir.rglob("*.md"):
        if path.name in index:
            raise ValueError(
                f"duplicate basename '{path.name}' found at both "
                f"{index[path.name]} and {path}"
            )
        index[path.name] = path
    return index
```

`main()`, current:
```python
    patterns = args.globs or ["docs/*.md"]
    files: set[Path] = set()
    for pattern in patterns:
        files.update(ROOT_DIR.glob(pattern))
    ...
    for path in sorted(files):
        issues = validate_file(path, args.area, schema)
```

After modification:
```python
    patterns = args.globs or ["docs/**/*.md"]
    files: set[Path] = set()
    for pattern in patterns:
        files.update(ROOT_DIR.glob(pattern))

    try:
        basename_index = _build_basename_index(DOCS_DIR)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    ...
    for path in sorted(files):
        issues = validate_file(path, args.area, schema, basename_index=basename_index)
```

## Compatibility considerations

- `validate_file()`'s signature gains a required keyword-only parameter
  (`basename_index`). This breaks the two existing calls in
  `tests/tools/test_check_docs_structure.py` (lines 170, 179) with a `TypeError` until
  that file's own implementation procedure (seq 02, same Plan) updates them — this is
  expected and coordinated, not an unintended regression; see Assumptions.
- CLI-visible behavior: the default glob (no arguments passed) now covers
  `docs/adr/`, `docs/eventbus/`, `docs/databases/`, and any future subfolder;
  callers that already pass explicit glob arguments (all current pre-commit hooks and
  CI workflows do) are unaffected either way.
- Every reference style already in use in the repository today (bare filename,
  `subdir/file.md`, `../file.md`) continues to resolve exactly as before — confirmed
  via the Plan's Reference Files evidence (`docs/adr/ADR-015-...md`,
  `docs/03_rag_91_design_notes.md`).
- The exact "references missing file" / "broken link" message text is unchanged —
  confirmed no other tool parses it.

## Security considerations

No security impact — this is a documentation-structure-validation tool with no
network, subprocess, or file-write behavior; the change only alters which files it
reads to build its in-memory index.

## Rollback considerations

1. Revert the five edited locations to their pre-change form (straightforward, since
   each is a small, localized diff within this one file).
2. No data migration or state to unwind — this tool has no persistent state; a rollback
   only requires the source file to return to its prior content.

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
against the current `docs/` tree and diff its output against the pre-change baseline
recorded in the Plan's Problem section (645 front-matter entries / 58 cross-folder, 811
body links / 240 cross-folder, 0 pre-existing broken front-matter refs, 5 pre-existing
broken body links from `ADR-008`/`ADR-010`) — expect the same findings, since this
change alone does not move any file. Full test-suite validation (including the two
now-updated call sites) is this Plan's seq-02 document's responsibility, run together
per the Plan's own Validation plan once both documents are implemented.

## Completion criteria

- `_build_basename_index()` exists and raises on a duplicate basename, naming both
  conflicting paths.
- `check_related_links()` and `check_links()` both resolve a bare-filename
  cross-directory reference successfully, and both preserve resolution for
  already-directory-qualified references.
- `main()`'s default glob is `docs/**/*.md`.
- `validate_file()`'s signature includes the new required `basename_index` parameter,
  and `main()`'s only production call site supplies it.
- Running `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
  against the unmodified `docs/` tree reports the same findings as the pre-change
  baseline in this Plan.

## Out of scope

- Updating `tests/tools/test_check_docs_structure.py`'s two existing call sites or
  adding the four new test cases — tracked by this Plan's seq-02 implementation
  procedure document for that file.
- Any change to `docs/*.md` content, `tools/_docs_consistency_lib.py`,
  `.github/workflows/*.yml`, or any other tool.
- Any physical `docs/` file move.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_build_basename_index()` and duplicate-detection handling in `main()` | Completed | 20260923-144938 | 20260923-144938 | Step3 stale_detector false-positive (36 findings, all net-new symbols this procedure introduces) confirmed by user; bypassed per user direction. |
| 2 | Update `check_related_links()` and `check_links()` to resolve via the index with the directory-qualified fallback | Completed | 20260923-144938 | 20260923-144938 | check_related_links/check_links updated to resolve via basename_index with directory-qualified fallback. |
| 3 | Update `validate_file()`'s signature and `main()`'s default glob + index wiring | Completed | 20260923-144938 | 20260923-144938 | validate_file()/main() updated; default glob now docs/**/*.md. |
| 4 | Run the validation sequence (`rules/toolchain.md`) — full-suite pass deferred until seq-02 also lands | Completed | 20260923-144938 | 20260923-144938 | ruff format/check, mypy, bandit: pass. lint-imports: 1 pre-existing unrelated violation (scripts/shared/production_config_validator.py -> agent.*, untouched by this change). pytest tests/tools/test_check_docs_structure.py: 14 passed, 2 failed with TypeError on missing basename_index (expected, coupled to seq-02; full-suite green deferred until seq-02 lands per this document's own Validation plan). |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: issues/done/20260923-140511_docsreorg01_make-docs-cross-reference-resolution-folder-independent.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-142045_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-143751
- **Related target files**: tools/check_docs_structure.py