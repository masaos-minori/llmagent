## Goal

Implementation step 5 of `plans/20260717-180307_plan.md` (requirement 19): add a short one-line
`config_dependent`/`enabled`/`disabled_reason` computation note plus a cross-link to the new
`docs/04_mcp_03_06_tool-runtime-availability-metadata.md` file, in each of the 4 existing MCP
server-catalog docs, next to their existing `requires_config` mentions — without duplicating the
full spec four times and without performing the `requires_config` → `config_dependent` rename
itself (that rename belongs to sibling requirement 14, `plans/20260717-173602_plan.md`).

This single plan step touches 4 files identically; this one procedure doc covers all 4 (matching
the plan's own step granularity — see the sequencing-check procedure doc
(`20260718-101407_requires_config_sequencing_check_for_availability_metadata_docs.md`) for the
per-file `requires_config` grep evidence this doc's notes must sit adjacent to).

## Scope

**In scope**: add one short note + link per file to:
- `docs/04_mcp_04_01_web-search-file-read-github.md` (2 note locations: near L67 and L111)
- `docs/04_mcp_04_02_file-write-file-delete-shell.md` (2 note locations: near L28 and L60)
- `docs/04_mcp_04_03_rag-pipeline-and-cicd.md` (1 note location: near the table at L77-79)
- `docs/04_mcp_04_05_git.md` (1 note location: near L27-31)

**Out of scope**: renaming `requires_config` → `config_dependent` in these 4 files (requirement
14's commit, not this plan's); editing any other file; adding the full spec content (lives only
in `04_mcp_03_06`, linked from here).

## Assumptions

- As confirmed by the sequencing-check investigation (2026-07-18), requirement 14's rename has
  **not yet landed** in any of the 4 files — all still say `requires_config`, none say
  `config_dependent`. Per that doc's branch logic, this step's notes must therefore be added
  **adjacent to**, not replacing, the existing `requires_config` text, referencing
  `config_dependent`/`enabled`/`disabled_reason` as the target/new field names (the new doc file
  `04_mcp_03_06` already states the implementation-status caveat, so these short notes can
  reference the target names directly without re-stating the caveat each time — one link to
  `04_mcp_03_06` covers that).
- If Implementation step 5 is executed after requirement 14's rename has landed (re-check via
  grep first, per the sequencing-check doc), the note text should reference `config_dependent`
  as the already-current field name rather than "replaces `requires_config`" — this is a minor
  wording adjustment only, not a scope change.
- Per-server `enabled`/`disabled_reason` computation basis (from plan Assumption 4 / Design):
  file read/write/delete servers → based on `allowed_dirs`; git → based on `allowed_repo_paths`
  (precedence) / `read_only`; rag-pipeline/cicd → no active computation yet (shell/cicd allowlist
  fields are reserved/forward-looking per requirement 15's plan, not yet implemented) — the
  rag-pipeline-and-cicd catalog doc's note must say so rather than imply an active mechanism.

## Implementation

### Target file

- `docs/04_mcp_04_01_web-search-file-read-github.md`
- `docs/04_mcp_04_02_file-write-file-delete-shell.md`
- `docs/04_mcp_04_03_rag-pipeline-and-cicd.md`
- `docs/04_mcp_04_05_git.md`

### Procedure

For each file, insert one short sentence immediately after the existing `requires_config`
prose/table content, referencing the new canonical doc:

1. `04_mcp_04_01_web-search-file-read-github.md`:
   - After L67 (`全ツールとも config を必要としない（requires_config: false）。` — file-read
     tools): add a line noting these tools have no `allowed_dirs` gate so `enabled` is always
     `true` for them (file-read has no config-dependent gating), linking to `04_mcp_03_06`.
   - After L111 (`全ツールとも config が必須（requires_config: true）。` — github tools): add a
     line noting `enabled`/`disabled_reason` for github tools follow whatever config-presence
     gate github-mcp implements (verify exact gating condition against requirement 15/16's
     implementation once landed; until then, link to `04_mcp_03_06` for the general contract
     without asserting a specific github-mcp gate condition not yet confirmed).
2. `04_mcp_04_02_file-write-file-delete-shell.md`:
   - After L28 (file-write tools) and L60 (file-delete tools): add a line each noting
     `enabled`/`disabled_reason` are computed from `allowed_dirs` (empty → disabled, reason
     `"allowed_dirs is empty"`), linking to `04_mcp_03_06`. Do NOT add an equivalent note to the
     shell-mcp section of this file (shell's own gating is `command_allowlist`, currently
     reserved/not-yet-implemented per requirement 15's plan) — if a shell-specific note is added,
     it must explicitly say "reserved, not yet implemented" per the Design section's rule against
     presenting unimplemented behavior as live.
3. `04_mcp_04_03_rag-pipeline-and-cicd.md`:
   - After the table at L77-79 (`requires_config` column): add a line noting cicd's
     `enabled`/`disabled_reason` computation (`"workflow_allowlist is empty"`) is
     reserved/forward-looking only — requirement 15's plan explicitly scopes cicd/shell
     implementation out — link to `04_mcp_03_06` section 3 (standard `disabled_reason` values
     table) for the reserved-status detail.
4. `04_mcp_04_05_git.md`:
   - After L27 (prose) / near the table at L29-31: add a line noting git's `enabled`/
     `disabled_reason` computation: `allowed_repo_paths` empty takes precedence
     (`"allowed_repo_paths is empty"`), else `read_only=true` disables write tools only
     (`"read_only=true"`), linking to `04_mcp_03_06`.
5. In every inserted note, use the same short phrasing pattern (e.g. "runtime availability
   (`enabled`/`disabled_reason`) for these tools is documented in
   [04_mcp_03_06](04_mcp_03_06_tool-runtime-availability-metadata.md).") so the 4 files stay
   terse and the full spec is single-sourced in the new file, per the plan's Design note: "one
   line ... note per server plus a link to the new `04_mcp_03_06` file, rather than duplicating
   the full spec four times."

### Method

Direct Markdown insertion of one short sentence (with a relative Markdown link) per note
location listed above — 6 insertion points total across the 4 files (2 + 2 + 1 + 1). No table
restructuring, no rename of existing `requires_config` text.

### Details

Exact current anchor text for each insertion point (verified by direct read, 2026-07-18):

- `04_01` L67: `全ツールとも config を必要としない（`requires_config: false`）。`
- `04_01` L111: `全ツールとも config が必須（`requires_config: true`）。`
- `04_02` L28: `全ツールとも config を必要としない（`requires_config: false`）。`
- `04_02` L60: `全ツールとも config を必要としない（`requires_config: false`）。`
- `04_03` L77-79: table header `| ツール | ティア | 入力 | `requires_config` |` then rows (e.g.
  `trigger_workflow` / WRITE_DANGEROUS / yes)
- `04_05` L27: `全ツールとも config が必須（`requires_config: true`）。`; L29-31 table with a
  `requires_config` column.

Frontmatter of each file (unchanged by this step, for reference): `04_01` tags
`mcp, server-catalog, web-search, file-read, github`; `04_02` tags
`mcp, server-catalog, file-write, file-delete, shell`; `04_03` tags
`mcp, server-catalog, rag-pipeline, cicd`; `04_05` tags `mcp, server-catalog, git`. None of the 4
files' `related:` frontmatter lists currently reference `04_mcp_03_06` (it doesn't exist yet
before Implementation step 3 runs) — adding these 4 files to `04_mcp_03_06`'s own `related:` list
was already covered in the step-3 procedure doc; optionally, each of these 4 files' own
`related:` list could gain a `04_mcp_03_06_tool-runtime-availability-metadata.md` entry too, for
bidirectional discoverability, though the plan's Design section does not explicitly require this
frontmatter-level cross-link (only prose + link).

## Validation plan

- `grep -c "04_mcp_03_06" docs/04_mcp_04_01_web-search-file-read-github.md
  docs/04_mcp_04_02_file-write-file-delete-shell.md docs/04_mcp_04_03_rag-pipeline-and-cicd.md
  docs/04_mcp_04_05_git.md` → expect each file to show at least 1 match after this step.
- Re-run `grep -rn "requires_config"` across the 4 files → confirm the existing
  `requires_config` mentions are still present, unchanged, and not replaced (rename remains
  requirement 14's job) — count should match the pre-edit baseline recorded in the
  sequencing-check doc (2 + 2 + table-cols + prose+table-cols respectively).
- Manual read-through: confirm none of the 4 new notes assert `command_allowlist`/
  `workflow_allowlist`-based gating (shell/cicd) as currently active — they must say
  reserved/not-yet-implemented if mentioned at all.
- `uv run check-mcp-docs` — run to confirm no regression against the real-file consistency
  checks (startup modes, fail-open wording, routing authority, active-issue cross-refs,
  toolcount) that this CLI runs over actual `docs/` content.
- `git diff --stat docs/04_mcp_04_01_web-search-file-read-github.md
  docs/04_mcp_04_02_file-write-file-delete-shell.md docs/04_mcp_04_03_rag-pipeline-and-cicd.md
  docs/04_mcp_04_05_git.md` — confirm only small additive insertions, no line replaced/removed.
