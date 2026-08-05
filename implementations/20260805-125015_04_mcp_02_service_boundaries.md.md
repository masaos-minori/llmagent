# Implementation Procedure: docs/04_mcp_02_service_boundaries.md

## Goal

- Align `docs/04_mcp_02_service_boundaries.md` with `config/agent.toml` (port source of truth)
  and with `docs/04_mcp_01_tool_ownership_matrix.md` (file-mcp split, no redundant
  allow/forbid tables), per `plans/20260802-152611_plan.md`.

## Scope

- In scope: `docs/04_mcp_02_service_boundaries.md` content review and, if needed, correction of
  port numbers, `file-mcp` split sections, and removal of any redundant
  allowed/forbidden-operation tables in favor of a reference link.
- Out of scope: `config/agent.toml` changes; any other `docs/*.md` file; automated Mermaid
  diagram generation (tracked separately for `04_mcp_01_tool_ownership_matrix.md`, already
  covered by `implementations/done/20260723-172114_docs_04_mcp_01_tool_ownership_matrix.md.md`).

## Assumptions

- `config/agent.toml` `[mcp_servers.*]` blocks are the authoritative port source.
- Fact (verified during this investigation): the current
  `docs/04_mcp_02_service_boundaries.md` (194 lines) already shows, for every server, a port
  number matching `config/agent.toml`:
  `file-read-mcp` 8005, `file-write-mcp` 8007, `file-delete-mcp` 8008, `rag-pipeline-mcp` 8010,
  `cicd-mcp` 8012, `mdq-mcp` 8013, `git-mcp` 8014, `shell-mcp` 8009, `web-search-mcp` 8004,
  `github-mcp` 8006 — all match `config/agent.toml` lines 290-384.
- Fact: the `file-mcp` split into `file-read-mcp` / `file-write-mcp` / `file-delete-mcp` is
  already present as three separate `###` sections (lines 19, 32, 45), each with its own
  Responsibilities / Explicit Non-responsibilities / Ownership rationale.
- Fact: no standalone "Allowed/Forbidden operation types" table exists in the file; each
  server section already uses "Explicit Non-responsibilities" prose, and the file already
  references `04_mcp_01_tool_ownership_matrix.md` twice (line 161, line 187) as the
  authoritative tool-to-server mapping.
- Conclusion: the plan's described defect (stale ports, unsplit `file-mcp`, redundant
  allow/forbid sections) does not currently exist in this file. The remaining action is a
  verification-only pass, not a content rewrite. This procedure is written to cover both the
  verification pass and the corrective edit, in case a discrepancy is found at execution time.

## Design decisions

- Treat `config/agent.toml` as the single source of truth for ports (per
  `skills/python-design` evidence-labeling: mark doc content as "Needs confirmation" until
  cross-checked against the config, then reclassify as fact once verified — see rules/coding.md
  "Documentation notes" classification table).
- Per `rules/coding.md` classification table: since the current file content already matches
  the desired end state, this is an "Accepted current specification" case, not a
  "Documentation fix required" case — no edit should be forced solely to satisfy the plan if
  the content is already correct.
- Keep the fix (if any is found necessary at execution time) minimal and localized to the
  specific stale line(s); do not restructure sections that are already correct.

## Alternatives considered

- Rewriting the whole file unconditionally to match the plan's literal steps, regardless of
  current content — rejected, since it risks introducing formatting-only churn on sections
  already correct (out of scope per the workflow's "no broad formatting-only rewrites" rule).
- Deferring this file's procedure entirely because "no change is currently needed" — rejected,
  since the workflow's already-implemented check is filename-based only (against
  `implementations/` and `implementations/done/`), and no matching file exists there for this
  target; the procedure document is still required.

## Implementation

### Target file

- `docs/04_mcp_02_service_boundaries.md`

### Procedure

1. Re-verify port numbers in `docs/04_mcp_02_service_boundaries.md` against the current
   `config/agent.toml` `[mcp_servers.*]` blocks (lines 290-384 as of this investigation) —
   confirm no drift has been introduced since this procedure was written.
2. Re-verify the three `file-*-mcp` sections (read/write/delete) are present with distinct
   responsibilities.
3. Re-verify no standalone "Allowed operations" / "Forbidden operations" table exists outside
   of the "Explicit Non-responsibilities" prose bullets, and that a reference link to
   `04_mcp_01_tool_ownership_matrix.md` is present.
4. If any discrepancy is found in steps 1-3, apply the minimal targeted edit (corrected port
   number, added missing split section, or replacement of a redundant table with a reference
   link) and re-run the checks below.
5. If no discrepancy is found, record the verification as complete with no content change
   required.

### Method

- Use `grep -n` for `port`, `8[0-9][0-9][0-9]`, `file-mcp|file-read|file-write|file-delete`,
  and `allowed|forbidden` against the target file, and `grep -n '\[mcp_servers\.' -A2
  config/agent.toml` for the authoritative port list, then diff manually — do not paste full
  file contents into review notes.
- Use `uv run check-mcp-docs` (registered in `pyproject.toml`; see `rules/toolchain.md`
  "MCP documentation consistency") to run the automated `check_port_drift` (ERROR-level) check,
  which compares doc-mentioned ports next to `<name>-mcp` tokens against
  `config/agent.toml`.

### Details

- Current per-server port lines in the target file (verified in this investigation):
  line 19 `file-read-mcp (port 8005)`, line 32 `file-write-mcp (port 8007)`,
  line 45 `file-delete-mcp (port 8008)`, line 58 `rag-pipeline-mcp (port 8010)`,
  line 73 `cicd-mcp (port 8012)`, line 88 `mdq-mcp (port 8013)`,
  line 103 `git-mcp (port 8014)`, line 118 `shell-mcp (port 8009)`,
  line 131 `web-search-mcp (port 8004)`, line 145 `github-mcp (port 8006)`.
- Cross-server rules already reference the split at line 172:
  `` `file-*`: Direct file I/O within allowed_dirs (split into read, write, delete) ``.
- Reference links to the ownership matrix already exist at line 161 (inline, end of
  per-server section) and line 187 (Related Documents section).

## Compatibility considerations

- Documentation-only; no runtime/API compatibility impact.
- Internal Markdown links (`04_mcp_01_tool_ownership_matrix.md`, `04_mcp_00_document-guide.md`,
  `00_governance_07_needs-confirmation-inventory.md#nc-004`) must remain valid after any edit —
  verify with the `check-mcp-docs` link-check pass (see `rules/toolchain.md`).

## Security considerations

- N/A — no code, secrets, or access-control content is touched; the file only documents
  existing MCP server boundaries.

## Rollback considerations

- Low risk: a single Markdown file. Revert via `git checkout -- docs/04_mcp_02_service_boundaries.md`
  or `git revert <commit>` if a future edit under this procedure needs to be undone.

## Validation plan

- `uv run check-mcp-docs` — confirms no `check_port_drift` (ERROR) and no broken internal
  Markdown links (per `rules/toolchain.md` "MCP documentation consistency").
- Manual diff review: `git diff docs/04_mcp_02_service_boundaries.md` before staging, per
  `rules/toolchain.md` "Diff review" step.
- Manual cross-check: every port number in the file against `config/agent.toml`
  `[mcp_servers.*]` blocks.

## Out of scope

- Modifying `config/agent.toml`.
- Modifying `docs/04_mcp_01_tool_ownership_matrix.md` (already covered by
  `implementations/done/20260723-172114_docs_04_mcp_01_tool_ownership_matrix.md.md`).
- Implementing automated Mermaid diagram generation (explicitly deferred by the source plan).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260802-152611_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-125015
- Related target files: 04_mcp_02_service_boundaries.md
