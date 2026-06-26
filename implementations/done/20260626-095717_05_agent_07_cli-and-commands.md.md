# Implementation: Add /db alias migration note to cli-and-commands.md

Steps covered: Plan 20260626-095717 — All steps (docs-only)

---

## Goal

Add a brief migration note to `docs/05_agent_07_cli-and-commands.md` documenting that `/db` flat aliases have been removed and what the canonical replacements are.

---

## Scope

- **In scope**: `docs/05_agent_07_cli-and-commands.md` — migration note section
- **Out of scope**: runtime code changes

---

## Implementation

### Target file
`docs/05_agent_07_cli-and-commands.md`

### Procedure
1. Add a "Migration Notes" section (or append to existing one):
   ```
   ## Migration Notes

   ### /db alias commands (removed)

   The following flat alias commands have been removed. Use the canonical sub-command
   syntax instead:

   | Removed | Replacement |
   |---------|------------|
   | `/db-list` | `/db list` |
   | `/db-query <sql>` | `/db query <sql>` |
   | `/db recover` | See `/db help` for the canonical recovery command |

   These aliases were provided for backward compatibility and are no longer supported.
   ```

### Method
Documentation-only change.

---

## Validation plan

- Pre-commit: `pre-commit run --all-files` — markdown lint must pass.
- Confirm: `grep -n "Migration Notes\|Removed.*alias" docs/05_agent_07_cli-and-commands.md` shows the section.
