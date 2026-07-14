# Implementation: Add `tools/` to `check_no_compat.py`'s scanned directories

Source plan: `plans/20260711-171430_plan.md` (Phase 2).

## Goal

Extend `tools/check_no_compat.py`'s `dirs_to_scan` list to include `tools/` itself, so the
one other location in the repository containing Python source (dev/CI tooling scripts) is
covered by the same compatibility/anti-pattern scan already applied to `scripts/`, `docs/`,
and `tests/`.

## Scope

**In-Scope:**
- `tools/check_no_compat.py`: add `ROOT_DIR / "tools"` to the `dirs_to_scan` list in `main()`
  (currently line 192).
- Re-run the scan after the change and confirm it still passes (no new findings surfaced from
  `tools/*.py` itself).

**Out-of-Scope:**
- Any change to `COMPAT_PATTERNS`, `ALLOWLIST`, or the scanning logic itself — this is purely
  a scan-scope (directory list) change.
- Adding any new allowlist entries speculatively; only add one if the re-run in this phase
  actually surfaces a new finding (see Risks in the source plan).

## Assumptions

1. Confirmed by direct read of `tools/check_no_compat.py` line 192: `dirs_to_scan = [ROOT_DIR
   / "scripts", ROOT_DIR / "docs", ROOT_DIR / "tests"]` — `tools/` is not currently included.
2. Confirmed by `find /home/masaos/llmagent/tools -name "*.py"`: `tools/` contains several
   dev/CI scripts (e.g. `check_no_compat.py` itself, `check_docs_consistency.py`,
   `split_oversized_docs.py`) that are Python source not currently scanned by this tool.
3. This is a low-risk, additive change: broadening scan scope can only surface new findings,
   never suppress existing ones.

## Implementation

### Target file

`tools/check_no_compat.py`

### Procedure

1. Open `tools/check_no_compat.py` and locate the `dirs_to_scan` list assignment inside
   `main()` (around line 192).
2. Add `ROOT_DIR / "tools"` as a fourth entry in the list, preserving the existing entries and
   their order (`scripts`, `docs`, `tests`, then `tools`).
3. Run `uv run python tools/check_no_compat.py` and inspect the output.
4. If the scan surfaces any new finding from a file under `tools/` (e.g. `check_no_compat.py`
   self-referencing one of its own pattern strings as data), triage it: if it is a legitimate
   self-referential match (a precedent already established for how `tests/` entries are
   allowlisted), add a narrowly scoped allowlist entry mirroring the existing style; otherwise
   fix the flagged code. Do not add a blanket exemption for all of `tools/`.
5. If the scan passes clean with no new findings, no further action is needed beyond the
   one-line list change.

### Method

Single additive list-entry edit to `tools/check_no_compat.py`'s `dirs_to_scan`. No changes to
`COMPAT_PATTERNS`, `ALLOWLIST`, or the CLI/output format, unless Step 4 above requires a
narrowly scoped allowlist addition.

### Details

Target edit (`tools/check_no_compat.py`, illustrative):

```python
dirs_to_scan = [
    ROOT_DIR / "scripts",
    ROOT_DIR / "docs",
    ROOT_DIR / "tests",
    ROOT_DIR / "tools",
]
```

## Validation plan

Filtered to checks relevant to this file, from the plan's Validation plan table:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tools/check_no_compat.py` | 0 errors |
| CI scan | `uv run python tools/check_no_compat.py` | Passes with `tools/` included in scan scope; no unresolved new findings |
