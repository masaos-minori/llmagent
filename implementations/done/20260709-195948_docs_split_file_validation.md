# Implementation: docs — verify no stale split-file references remain

## Goal

Verify no stale references to split config files remain across all docs.

## Scope

- All files under `docs/`

## Implementation

### Procedure

1. Search for split-file references:
   ```bash
   rg "common\.toml\|llm\.toml\|tools\.toml\|memory\.toml\|otel\.toml\|security\.toml" docs/
   ```
2. If any matches found, fix them.
3. Run format check:
   ```bash
   uv run ruff check docs/ --fix
   ```

### Details

- Only historical/transitional references should remain.
- Allow intentional historical notes (e.g., "previously split into common.toml...").

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| No stale split-file refs | `rg "common\.toml\|llm\.toml\|tools\.toml" docs/` | Only historical refs remain |
