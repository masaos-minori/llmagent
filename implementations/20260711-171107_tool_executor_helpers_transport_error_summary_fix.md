# Implementation: Fix `format_transport_error()` summary + expand `is_side_effect()` docstring

## Goal

Fix `format_transport_error()`'s `summary` string in
`scripts/shared/tool_executor_helpers.py` so it includes `status_code` and `partial`
(currently it omits both, including only `source`/`kind`/`phase`/`retryable`). Also
expand `is_side_effect()`'s docstring to name all 5 tool categories it actually checks
against (`_SIDE_EFFECT_TOOLS`), since the current docstring only mentions
"write, delete, shell" and omits Git/GitHub tools.

## Scope

**In-Scope:**
- `scripts/shared/tool_executor_helpers.py::format_transport_error()` — extend the
  `summary` string to include `status_code` and `partial`.
- `scripts/shared/tool_executor_helpers.py::is_side_effect()` — expand the docstring
  to name all 5 tool categories covered by `_SIDE_EFFECT_TOOLS`.

**Out-of-Scope:**
- `format_transport_error()`'s `detail` construction — already complete (all 6 fields:
  `source`, `phase`, `kind`, `status_code`, `url`, `retryable`, `partial`); do not touch.
- `tool_hash_key()` — confirmed already correct and already tested; not touched.
- `is_side_effect()`'s implementation/logic (`return tool_name in _SIDE_EFFECT_TOOLS`) —
  unchanged; only the docstring text changes.
- Test file changes — handled in a separate document
  (`tests/test_tool_executor_helpers.py` additions, Phase 2).

## Assumptions

1. `format_transport_error()` (confirmed by direct read, lines 33-56) already builds
   `detail` as a complete JSON dict with all 6 fields. Only `summary` is incomplete.
2. Current `summary`:
   `f"[{source.upper()} {kind}] {phase} failure (retryable={retryable})"`
   — omits `status_code` and `partial`.
3. `summary` is documented as "one-line user-facing" text and is not parsed
   programmatically anywhere in `scripts/` (confirmed via `grep -rn "\.summary"` finding
   no pattern-matching consumer) — so extending its content is a low-risk string change.
4. `_SIDE_EFFECT_TOOLS` (confirmed by direct read, lines 18-25) already is a union that
   includes `WRITE_TOOLS`, `DELETE_TOOLS`, `"shell_run"`, `GIT_WRITE_TOOLS`,
   `GITHUB_WRITE_TOOLS`, and `GITHUB_DANGEROUS_TOOLS` — 5 categories total (write,
   delete, shell, git-write, github-write/dangerous) that the docstring should name.

## Implementation

### Target file

`scripts/shared/tool_executor_helpers.py` (existing file — two localized edits, no
structural/signature changes)

### Procedure

1. Locate `format_transport_error()`'s `summary` assignment (currently a single
   f-string using `source`, `kind`, `phase`, `retryable`).
2. Replace the `summary` f-string with a version that also interpolates
   `status_code` and `partial`, keeping the existing fields and format style
   (`key=value` inside parentheses).
3. Locate `is_side_effect()`'s docstring (currently:
   `"Return True when the tool modifies state (write, delete, shell)."`).
4. Replace the docstring with one that names all 5 categories represented in
   `_SIDE_EFFECT_TOOLS`: write, delete, shell, Git write operations, GitHub
   write/dangerous operations.
5. Do not change `is_side_effect()`'s return statement or `_SIDE_EFFECT_TOOLS`
   itself.

### Method

```python
# format_transport_error() — summary fix
summary = (
    f"[{source.upper()} {kind}] {phase} failure "
    f"(status_code={status_code}, retryable={retryable}, partial={partial})"
)
```

```python
# is_side_effect() — docstring expansion
def is_side_effect(tool_name: str) -> bool:
    """Return True when the tool modifies state: file write/delete, shell,
    Git write operations, or GitHub write/dangerous operations."""
    return tool_name in _SIDE_EFFECT_TOOLS
```

### Details

- Keep the `f"[{source.upper()} {kind}] {phase} failure (...)"` prefix structure
  unchanged — only the parenthesized key=value portion gains two more fields, in the
  order `status_code`, `retryable`, `partial` (status_code first since it commonly
  reads best right after "failure", but any consistent ordering satisfying the
  validation plan's substring assertions is acceptable — the design section of the
  plan places `status_code` before `retryable`).
- `status_code` may be `None` (per `detail`'s type contract) — an f-string will render
  it as the literal text `None`, which is acceptable for a human-readable summary and
  does not need special-casing.
- No change to function signature, return type (`TransportErrorInfo`), or the
  `detail` field construction.
- No change to imports.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/shared/tool_executor_helpers.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/tool_executor_helpers.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no import changes) |
| Tests | `uv run pytest tests/test_tool_executor_helpers.py -v` | All pass, including new `TransportErrorInfo`/`summary` tests added in the companion Phase 2 document |
| Regression | `grep -rn "format_transport_error(" scripts/` then re-run each caller's own test file | No new failures — confirms no caller parses `summary` programmatically |
