## Goal

Replace explicit per-file listings for the `web_search/` and `github/` MCP server
subdirectories in `docs/01_overview-files-03-scripts-part4.md` with descriptive prose, so
future service-prefixed file renames inside those directories do not require doc edits.

## Scope

- In scope: the `web_search/` and `github/` bullet blocks in
  `docs/01_overview-files-03-scripts-part4.md` (tree diagram section).
- Out of scope: any other subdirectory block in the same file (e.g. `file/`), any other
  `docs/01_overview-files-03-scripts-part*.md` file, and any source file under
  `scripts/mcp_servers/`.

## Assumptions

- Fact (verified by direct read of `docs/01_overview-files-03-scripts-part4.md` lines
  28-43): the `web_search/` block (lines 35-38) and `github/` block (lines 39-42) already
  contain prose descriptions pointing to `scripts/mcp_servers/web_search/` and
  `scripts/mcp_servers/github/` respectively, with no enumerated per-file bullets. The
  drift this plan targets does not currently reproduce in the file as read.
- Assumption: the plan (`plans/done/20260802-093000_plan.md` after Step 4 of this cycle)
  was written against an earlier state of the doc, or the fix was already applied by a
  prior, untracked edit outside this workflow's `implementations/` records.
- This procedure is written as instructed regardless of the above, since this workflow's
  "already implemented" check is filename-based only (see Traceability / Out of scope).

## Design decisions

- Per `skills/DESIGN.md` §Documentation notes classification (referenced via
  `rules/coding.md`): if, at execution time, the doc still shows drift, treat it as
  "Documentation fix required" — fix the doc directly, no issue filing needed, since this
  is a pure prose/listing correction with no behavior change.
- If, at execution time, the doc already matches the desired prose form (as currently
  observed), classify per `rules/coding.md` as "Obsolete and removable" for the purposes
  of this specific plan item — re-verify against current code/doc before treating the
  plan item as a no-op, per that rule's requirement not to delete/skip a note without
  verification.
- Keep the fix additive/prose-only: no restructuring of the surrounding tree-diagram
  formatting (indentation, box-drawing characters) used elsewhere in the file.

## Alternatives considered

- Auto-generate the subdirectory listing from `ls scripts/mcp_servers/<name>/` at doc-build
  time — rejected: this doc set has no build/generation pipeline (plain Markdown,
  hand-maintained); introducing one is out of scope for a single-file wording fix.
- Leave enumerated file lists but add a "may drift" disclaimer — rejected: does not solve
  the root cause (drift itself), only annotates it.

## Implementation

### Target file

- `docs/01_overview-files-03-scripts-part4.md`

### Procedure

1. Re-verify current directory contents before editing:
   - `ls scripts/mcp_servers/web_search/`
   - `ls scripts/mcp_servers/github/`
2. Re-read `docs/01_overview-files-03-scripts-part4.md` lines ~28-43 to confirm current
   state (prose vs. enumerated list) immediately before editing, since state may have
   changed since this procedure was written.
3. If enumerated per-file bullets are present under either `web_search/` or `github/`,
   replace them with prose in the same style as the other block (short service
   description + pointer sentence to the `scripts/mcp_servers/<name>/` path), matching
   the existing bilingual (English comment / Japanese prose) convention used in the
   surrounding file.
4. If both blocks already contain only prose (current observed state), do not edit the
   file; record the item as a no-op in the validation step.

### Method

- Use `Read` with a bounded `offset`/`limit` around the `web_search/`/`github/` lines
  (located via `grep -n "web_search\|github" docs/01_overview-files-03-scripts-part4.md`)
  rather than reading the full file.
- Use `Edit` (exact string replacement) scoped to the identified line range; do not use a
  full-file rewrite.

### Details

- Evidence (grep, this session):
  `docs/01_overview-files-03-scripts-part4.md:35` `web_search/` bullet,
  `docs/01_overview-files-03-scripts-part4.md:39` `github/` bullet.
- Evidence (direct read, this session): lines 36-38 and 40-42 already carry prose
  ("各サービス固有のファイル...", "各ドメイン...") pointing at the source directories, not
  file-name lists.
- `scripts/mcp_servers/web_search/` currently contains 9 files (e.g.
  `web_search_server.py`, `web_search_models.py`, ...); `scripts/mcp_servers/github/`
  currently contains 27 files (e.g. `github_server.py`, `service_dispatch.py`, ...) — both
  consistent with "many files, prose is cheaper than an enumerated list."

## Compatibility considerations

- Documentation-only; no API, schema, or runtime behavior change.
- No impact on `deploy/deploy.sh` copy list or `config/agent.toml` (per `rules/coding.md`
  module-addition rule) since no module is added or removed.

## Security considerations

- N/A — prose-only documentation edit, no code or config execution path touched.

## Rollback considerations

- Single-file Markdown edit; revert via `git checkout -- docs/01_overview-files-03-scripts-part4.md`
  or a follow-up commit reverting the specific hunk if the prose wording needs
  adjustment.

## Validation plan

- Manual inspection: `git diff docs/01_overview-files-03-scripts-part4.md` shows only the
  intended block(s) changed (or no diff, if the no-op branch applies).
- `grep -n "web_search_server.py\|github_server.py" docs/01_overview-files-03-scripts-part4.md`
  returns no match (confirms no leftover explicit filenames in the edited blocks).
- `ls scripts/mcp_servers/web_search/` and `ls scripts/mcp_servers/github/` re-run to
  confirm the prose's "many prefixed files" framing still holds.
- No automated test suite applies (doc-only change); no `rules/toolchain.md` code
  validation steps (ruff/mypy/pytest/etc.) apply here.

## Out of scope

- Any other subdirectory block (`file/`) in the same doc.
- Any other `docs/01_overview-files-03-scripts-part*.md` file.
- Any source code under `scripts/mcp_servers/`.
- Determining, as part of this document-only workflow phase, whether the doc fix was
  already separately applied — that determination is deferred to whoever executes this
  procedure (see Assumptions).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260802-093000_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-105913
- Related target files: 01_overview-files-03-scripts-part4.md
