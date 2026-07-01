# Implementation: Add /note removal migration note

## Goal

Add a Migration Notes entry for the removed `/note` command group in `docs/05_agent_07_cli-and-commands.md`, enabling users to understand the migration path to `/memory`.

## Scope

**In-Scope**:
- Add `/note commands (removed)` section to Migration Notes in `docs/05_agent_07_cli-and-commands.md`

**Out-of-Scope**:
- Cleanup of residual `/note` references in `docs/05_agent_13_reference-api.md`
- Cleanup of notes references in other docs
- Backward-compatible alias implementation

## Assumptions

- Migration Notes section currently contains only `/db alias commands` and `/mcp install` entries; no `/note` entry exists (confirmed)
- The `/note` removal is a confirmed change with clear replacement mapping to `/memory` commands
- New entry should be appended after the last existing Migration Notes entry (`/mcp install (removed)`)

## Implementation

### Target file

`docs/05_agent_07_cli-and-commands.md` — Migration Notes section

### Procedure

1. Read `docs/05_agent_07_cli-and-commands.md` to locate the Migration Notes section
2. Identify the position after the last existing Migration Notes entry (`/mcp install (removed)`)
3. Append a new section with the following structure:

#### `/note commands (removed)`

List of removed commands:

| Removed | Replacement |
|---------|------------|
| `/note add` | `/memory list` / `/memory show` |
| `/note list` | `/memory list` |
| `/note delete` | `/memory delete` |
| `/note pin` | `/memory pin` |
| `/note unpin` | `/memory unpin` |
| `/note search` | `/memory search` |

Reason: Persistent notes removed from the Agent command layer; long-term searchable context should use the memory layer.

Statement: No backward-compatible alias is provided.

### Method

Append text after the last line of the existing Migration Notes section. The new section follows the same format as the existing `/db alias commands (removed)` and `/mcp install (removed)` entries:
- Section heading using `###` level
- Brief explanatory paragraph
- Table mapping removed commands to replacements
- Statement about backward compatibility

### Details

The removed `/note` command group includes 6 subcommands:
- `/note add` — replaced by `/memory list` or `/memory show` (viewing)
- `/note list` — replaced by `/memory list`
- `/note delete` — replaced by `/memory delete`
- `/note pin` — replaced by `/memory pin`
- `/note unpin` — replaced by `/memory unpin`
- `/note search` — replaced by `/memory search`

The replacement mapping is not 1-to-1 because some `/note` commands map to multiple `/memory` commands depending on the user's intent (e.g., `/note add` could map to viewing existing memories or showing a specific memory).

## Validation plan

| Check | Method | Target |
|-------|--------|--------|
| Format consistency | Manual review | New section matches existing Migration Notes entries format |
| Completeness | Compare with plan requirements | All 6 removed commands listed with replacements |
| Accuracy | Cross-reference with `/memory` command table in same doc | Replacement commands exist and are accurate |
