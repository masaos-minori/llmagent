# Implementation Procedure: Remove Obsolete web_search_url from Agent Configuration (Dataclass)

## Goal

Remove `web_search_url` field from AgentConfig dataclass if present.

## Scope

- `scripts/agent/config_dataclasses.py` only
- Field removal; no new content creation

## Assumptions

1. The requirement `requires/20260714_06_require.md` is the canonical specification for this task.
2. `web_search_url` may exist as a field in the AgentConfig dataclass.
3. No source code changes beyond removing the field definition.

## Implementation

### Target file

`scripts/agent/config_dataclasses.py`

### Procedure

1. **Check for `web_search_url` field**: Inspect `config_dataclasses.py` for `web_search_url` field definition.
2. **Remove if present**: Delete the field definition if found.

### Method

- Pattern-based search followed by targeted text deletion via file edit.

### Details

- Search for `web_search_url` pattern in `config_dataclasses.py`
- Delete the entire field definition line(s)
- Preserve surrounding context and formatting
- Ensure no orphaned commas or syntax errors remain

## Validation plan

1. Verify `web_search_url` no longer appears in `config_dataclasses.py`.
2. Confirm Python syntax is valid after removal.
3. Verify no broken cross-references from removed section.
4. Run `pre-commit run --all-files` if linting is configured.
