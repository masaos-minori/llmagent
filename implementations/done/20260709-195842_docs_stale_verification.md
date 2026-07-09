# Implementation: docs — verify no stale wording remains

## Goal

Verify that no stale `"deprecated"` or `"no longer enforced"` wording remains in any doc file after the fix.

## Scope

- All files under `docs/`

## Assumptions

1. Phase 1 and Phase 2 edits are complete.

## Implementation

### Procedure

1. Run search for stale patterns:
   ```bash
   rg "tool_results.*deprecated\|no longer enforced" docs/
   ```
2. If any matches found, fix them.
3. Run format check:
   ```bash
   uv run ruff check docs/ --fix
   ```

### Details

- No file creation or modification needed if zero matches.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| No stale wording | `rg "tool_results.*deprecated\|no longer enforced" docs/` | 0 matches |
| Format | `uv run ruff check docs/` | 0 errors |
