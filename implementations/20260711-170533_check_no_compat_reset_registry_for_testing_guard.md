# Implementation Procedure: `tools/check_no_compat.py` — guard `_reset_registry_for_testing` against production use

## Goal

Add a `COMPAT_PATTERNS` entry to `tools/check_no_compat.py` that flags any use of
`_reset_registry_for_testing` (from `shared/tool_registry.py`) outside `tests/`, so a future
production file cannot accidentally import/call this test-only reset helper without CI
catching it.

## Scope

**In-Scope:**
- `tools/check_no_compat.py`: add one new pattern to the existing `COMPAT_PATTERNS` dict
  matching the literal identifier `_reset_registry_for_testing`.
- Rely on the file's existing `ALLOWLIST`/allowlist mechanism (already used to exempt
  `tests/*.py` for other test-referencing patterns) to exempt `tests/` from this new pattern
  — do not invent a new allowlist mechanism.

**Out-of-Scope:**
- Any change to `shared/tool_registry.py`'s `_reset_registry_for_testing()` implementation
  itself (no runtime guard, no `RuntimeError` inside the function).
- Any change to `tests/test_tool_registry_reset_protection.py` (pre-existing file; read it
  first at implementation time to avoid duplicating coverage it may already provide).
- Broader refactors of `COMPAT_PATTERNS` or `ALLOWLIST` structure.

## Assumptions

1. `_reset_registry_for_testing()` (`shared/tool_registry.py`, confirmed near lines 148-151)
   is currently called only from within `tests/` (confirmed by `grep -rn
   "_reset_registry_for_testing" scripts/`).
2. No existing pattern in `tools/check_no_compat.py`'s `COMPAT_PATTERNS` currently references
   `_reset_registry_for_testing` (confirmed by `grep -n "_reset_registry_for_testing"
   tools/check_no_compat.py` returning no matches) — this is a net-new, additive pattern.
3. `COMPAT_PATTERNS` is a `dict[str, str]` mapping a human-readable name to a regex pattern
   string (confirmed from existing entries in the file).
4. The file's scan already applies an allowlist mechanism that exempts `tests/*.py` for
   similar test-referencing patterns (confirmed by reading existing entries near lines 94 and
   126 of `tools/check_no_compat.py`) — this plan reuses that same mechanism rather than
   adding new exemption logic.

## Implementation

### Target file

`tools/check_no_compat.py`

### Procedure

1. Read the existing `COMPAT_PATTERNS` dict and note the exact style used for keys (short,
   descriptive names) and values (raw regex strings).
2. Add one new entry: key describing the pattern's intent (e.g. `"test-only registry reset
   used outside tests"`), value a regex matching the identifier `_reset_registry_for_testing`
   (plain literal match is sufficient — no need for import-statement-specific regex unless
   the existing patterns in this file follow that convention; match the established style).
3. Confirm the file's existing allowlist/exemption logic already exempts paths under `tests/`
   for this class of pattern. If the mechanism requires per-pattern registration (rather than
   a blanket `tests/` exemption), follow whatever the nearest existing analogous entry (lines
   ~94, ~126) does — do not introduce a new, differently-shaped exemption path.
4. Do not add file-specific allowlist entries (e.g. for `shared/tool_registry.py` itself,
   where the function is *defined*, not *misused*) unless testing in Step 5 below reveals the
   scanner also flags the definition site itself — if so, confirm whether the existing scanner
   already distinguishes "definition" from "usage" (e.g. via regex anchoring on `import` or
   call-site syntax) before adding any allowlist entry for the definition file.

### Method

Single additive dict-entry edit to `tools/check_no_compat.py`. No changes to the scanning
logic, CLI, or output format.

### Details

Reference pseudocode (illustrative — adapt exact regex syntax to match the file's existing
pattern style, e.g. whether other entries anchor on `import` statements or match bare
identifiers):

```python
COMPAT_PATTERNS = {
    # ... existing entries ...
    "test-only registry reset used outside tests": r"_reset_registry_for_testing",
}
```

with the existing `ALLOWLIST` (or equivalent) mechanism exempting `tests/*.py`, mirroring how
other test-referencing patterns already in this file are handled (per the existing entries
noted in Assumption 4).

Before finalizing, read `tests/test_tool_registry_reset_protection.py` in full — per the
plan's Out-of-Scope note, it likely already covers part of this "test-only API" concern from
a different angle (e.g. asserting the function raises or warns in some context), and this new
CI pattern should complement, not duplicate, that existing test's intent.

## Validation plan

Filtered to checks relevant to this file, from the plan's Validation plan table:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tools/check_no_compat.py` | 0 errors |
| CI guard | `uv run python tools/check_no_compat.py` | Passes; confirms the new pattern correctly allowlists `tests/` while catching any hypothetical production usage |
