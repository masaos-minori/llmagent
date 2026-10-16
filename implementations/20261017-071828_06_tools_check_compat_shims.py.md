## Goal

Extend `GV-017` so the reintroduction of any removed command name (`/diff`, `/system`,
`/audit`, `/workflow`) in a current specification is detected
(`REQ-005`, command-surface reduction).

## Scope

In scope: add four removed-name patterns to `_REMOVED_NAME_PATTERNS` in
`tools/check_compat_shims.py`, command-usage-aware, with the historical-context exemption.
Out of scope: the command/handler/mixin deletions (`REQ-001`–`REQ-004`), the pattern tests
(`test_check_compat_shims.py`, `REQ-005`, separate document), and the `GV-017`
documentation update (`governance_04_documentation-checks.md`, `REQ-007`, separate
document).

## Assumptions

- `_REMOVED_NAME_PATTERNS` is iterated by `check_removed_name_reintroduction()`, which is
  gated behind `--check-removed-names` (off by default).
- The historical-context exemption (`_HISTORICAL_CONTEXT_MARKERS`) must be preserved so
  legitimate release-note / migration-history mentions are not flagged.

## Design decisions

- **Match slash-command usage, not bare words.** Each pattern is anchored to the leading
  `/` (e.g. matches `/diff` but not the ordinary word `diff` in `git diff`), so ordinary
  uses of `workflow`, `audit`, `system`, `diff` do not false-positive.
- **Follow the existing key convention.** New keys are human descriptions that cite this
  plan (`plans/20261016-233542_plan.md`) and a short tag (`diffcmd`/`syscmd`/`auditcmd`/
  `wfcmd`), matching the style of the existing entries.
- **Keep the exemption intact.** Do not touch `_HISTORICAL_CONTEXT_MARKERS`; the new
  patterns inherit it.

## Alternatives considered

`N/A`: the goal requires detecting reintroduction of each name; a non-command-anchored
pattern would over-flag and contradict the "match command usage and not words" requirement.

## Implementation

### Target file

`tools/check_compat_shims.py`

### Procedure

1. Locate `_REMOVED_NAME_PATTERNS` (L203) and `_HISTORICAL_CONTEXT_MARKERS` just above it;
   confirm `check_removed_name_reintroduction()` (L260) iterates the dict and honors the
   markers, and that `--check-removed-names` (L398) opts in.
2. Add four entries to `_REMOVED_NAME_PATTERNS`, one per removed name, each anchored to the
   leading `/` so only slash-command invocations match.
3. Verify the patterns do not match the bare words `workflow`, `audit`, `system`, `diff`.
4. Leave `_HISTORICAL_CONTEXT_MARKERS`, `check_removed_name_reintroduction()`, and the CLI
   wiring untouched.

### Method

Insert the four `{description: re.compile(...)}` entries into the existing dict literal,
preserving dict syntax and ordering.

### Details

- Pattern design: match a `/` immediately followed by the name as a word boundary, e.g.
  `r"/\bdiff\b"`, so `/diff` matches but `file_diff` or `git diff` does not. Apply the same
  shape to `/system`, `/audit`, `/workflow`.
- `/workflow` has no current `CommandDef`; the pattern still guards against future
  registration, consistent with the source directive naming it.
- The corresponding `GV-017` documentation update in
  `docs/00_governance/governance_04_documentation-checks.md` is a separate procedure
  document; update both so docs and code agree.

## Compatibility considerations

The tool stays off by default (`--check-removed-names` required); adding patterns changes
no default behavior. When enabled, it may now flag current-spec docs that reintroduce a
removed name.

## Security considerations

`N/A`: documentation-quality guard; no secret, permission, or data path is introduced.

## Rollback considerations

Revert the commit.

## Validation plan

- `pytest tests/tools/test_check_compat_shims.py` — hit on command use for each name, no hit
  on ordinary words, historical-context exemption honored.
- `python tools/check_compat_shims.py --check-removed-names` — passes on the current corpus.
- `ruff` — clean.

## Completion criteria

`_REMOVED_NAME_PATTERNS` contains four new entries for `/diff`, `/system`, `/audit`,
`/workflow` that match slash-command usage only, the historical-context exemption still
works, and `--check-removed-names` passes.

## Out of scope

`command_defs_list.py` (`REQ-001`), `cmd_context.py` (`REQ-002`), `cmd_audit.py`/`registry.py`
(`REQ-003`), `conversation_service.py` (`REQ-004`), `test_check_compat_shims.py`
(`REQ-005`), documentation (`REQ-007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add GV-017 removed-name patterns to `tools/check_compat_shims.py` (`REQ-005`) | Pending | — | — | |
| 2 | Add GV-017 pattern tests (`tests/tools/test_check_compat_shims.py`) | Pending | — | — | |
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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261016-162117_cli001_remove-diff-system-audit-slash-commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-233542_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-071828
- **Related target files**: `tools/check_compat_shims.py`
