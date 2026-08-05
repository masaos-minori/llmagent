# Implementation Procedure: docs/04_mcp_06_10_settings-with-high-operational-impact.md

## Goal
Clarify that "fail-closed" in the settings table is a description of a design policy
(deny-all-on-empty-allowlist), not a literal configuration key, to prevent developers from
mistaking it for a config field name.

## Scope
- In scope: the `allowed_repos` row of the settings table in
  `docs/04_mcp_06_10_settings-with-high-operational-impact.md`.
- Out of scope: any other row in the table, source code, or other documentation files.
- Note (evidence from current file content, `Needs confirmation` on intent): line 19 of the
  target file already reads
  `` | `allowed_repos` = `[]`（fail-closed方針） | すべてのGitHub書き込みが拒否される | ``,
  which matches the plan's suggested revision. This procedure is produced regardless, per the
  plan-to-implementation-procedure workflow's filename-only "already implemented" check
  (no matching file existed under `implementations/` or `implementations/done/`). Whoever
  executes this procedure should verify current file state before editing, and treat the
  edit as a no-op if the wording already matches.

## Assumptions
- The parent plan's investigation (that `fail_closed` is not a literal config key anywhere in
  `scripts/` or `config/`) is accurate and does not need to be re-verified here.
- No other documentation file duplicates this exact table row wording.

## Design decisions
- Prefer inline disambiguation (parenthetical Japanese note `（fail-closed方針）`) over adding a
  new footnote/section, per the plan's "Suggested revision" — keeps the change minimal and
  file-level (YAGNI: don't add a new doc section for one row).
- Keep the two existing backtick-quoted config values (`allowed_repos`, `[]`) as-is; only the
  free-text portion changes, so the change stays consistent with `rules/coding.md`'s intent of
  distinguishing literal identifiers (backticked) from descriptive text.

## Alternatives considered
- Rewriting the row to drop "fail-closed" entirely and only describe the effect: rejected,
  the plan's issue is disambiguation, not removal of the useful, well-known term.
- Adding a footnote linking to `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`:
  optional per the plan ("if necessary"); not required if the parenthetical rewrite alone
  removes the ambiguity — deferred to the executor's judgment at edit time.

## Implementation
### Target file
`docs/04_mcp_06_10_settings-with-high-operational-impact.md`

### Procedure
1. Read the file's settings table (front matter + table, lines ~1-25) to confirm the current
   wording of the `allowed_repos` row.
2. If the row still reads with `fail_closed` presented as a bare backtick-quoted key (e.g.
   `` `fail_closed` `` outside a descriptive phrase), rewrite the first column to
   `` `allowed_repos` = `[]`（fail-closed方針） ``. If the row already matches this wording,
   skip the edit (no-op) and note it in the change log / commit message.
3. Scan the rest of the table (rows for `allowed_dirs`, `command_allowlist`,
   `repo_allowlist`, `allowed_repo_paths`, `read_only`, `tool_definitions_strict`) for any
   similar bare backtick-quoted policy terms that are not literal config keys; only touch
   `allowed_repos` unless another row shows the identical defect (out of scope otherwise —
   flag separately if found).
4. Optionally add a one-line clarification note beneath the table if the parenthetical alone
   is judged insufficient, cross-referencing
   `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`.

### Method
- Direct text edit of the Markdown table cell; no code, no generated content.
- Use `grep -n "fail_closed\|fail-closed" docs/04_mcp_06_10_settings-with-high-operational-impact.md`
  to relocate the row before editing (do not need to load the full file into context beyond
  the table region).

### Details
- Current file (as observed via `grep`/limited read on 2026-08-05): the table lives at lines
  16-24; the row of interest is line 19; front matter (lines 1-12) and `## Related Documents`
  / `## Keywords` sections (lines 29-35) are unrelated and must not change.
- No code identifiers are involved; `fail_closed` does not appear as an actual config key in
  `scripts/` or `config/` per the plan's stated assumption — this is a docs-wording-only
  change.

## Compatibility considerations
- Documentation-only change; no API, schema, or config-key change. No backward-compatibility
  impact on running agents or MCP servers.
- Preserve existing Markdown table structure (column count, header) so other tooling that
  parses this doc (if any) is unaffected.

## Security considerations
- N/A — no code, secrets, or executable content involved; the change only affects prose
  describing an already-existing fail-closed behavior.

## Rollback considerations
- Single-file, single-row Markdown edit; revert via `git checkout -- docs/04_mcp_06_10_settings-with-high-operational-impact.md`
  or a follow-up commit reverting the row text if the rewording is judged unclear later.

## Validation plan
- Manual review only (per `rules/toolchain.md`, this is a docs-only change and does not
  require the code validation sequence — no ruff/mypy/bandit/pytest applicability).
- Confirm the row no longer implies `fail_closed` is a literal configurable key, and that
  meaning is conveyed via descriptive Japanese text instead of a bare backtick term.
- Run `uv run check-mcp-docs` if available, to confirm no broken internal links or drift was
  introduced (this doc has `related`/`source` front-matter links to
  `04_mcp_00_document-guide.md` and `04_mcp_06_02_configuration-file-inventory.md`).

## Out of scope
- Any other row in the settings table.
- Source code changes (none exist for `fail_closed` as a literal key).
- Other documentation files, including `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
  (referenced only, not edited).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-066900_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-131652
- Related target files: docs/04_mcp_06_10_settings-with-high-operational-impact.md
