## Goal

Implementation step 8 and the "Validation plan" section of `plans/20260717-180307_plan.md`
(requirement 19: "Document MCP runtime availability metadata and disabled tool behavior"): the
final cross-file validation pass for this documentation-only plan — confirm no new doc content
introduced by this plan describes `requires_config` as active, confirm the new
`04_mcp_03_06` file actually documents the new terms, confirm the new file is discoverable via
the documented navigation path, and confirm no code/test changes were made.

This doc is deliberately named to disambiguate it from other, unrelated `*full_validation_pass*`
docs already present under `implementations/` for other plans in this batch (e.g.
`20260718-090322_full_validation_pass_config_dependent_rename.md` for requirement 14,
`20260718-090830_full_validation_pass_tools_enabled_disabled_reason.md` and
`20260718-091922_full_validation_pass_call_tool_disabled_gate.md` for requirement 16,
`20260718-095511_full_validation_pass_availability_metadata_schema_tests.md` for requirement 18)
— none of those docs' Goals name this plan's specific documentation-only scope (requirement 19,
`plans/20260717-180307_plan.md`), so none of them cover this plan's validation step; confirmed by
reading each of their Goal lines directly.

## Scope

**In scope**: cross-file grep/consistency checks across the doc files this plan touches
(`docs/04_mcp_03_06_tool-runtime-availability-metadata.md` [new],
`docs/04_mcp_00_document-guide.md`, the 4 catalog docs, `docs/05_agent_08_04_configuration-mcp-approval-obs.md`,
`docs/04_mcp_90_inconsistencies_and_known_issues.md`), plus confirming no `scripts/`/`tests/`/
`config/` file was touched (this plan's Out-of-scope guarantee).

**Out of scope**: running the standard code-oriented toolchain (`ruff`, `mypy`, `lint-imports`,
`bandit`, `pytest` full suite, `diff-cover`, `pre-commit run --all-files`) as a blanket
requirement — this plan's own Validation plan section explicitly states: "No code/test changes
are made, so the repo's standard ruff/mypy/lint-imports/pytest/diff-cover toolchain sequence is
not applicable to this plan beyond the one doc-consistency test ... Markdown files are outside
ruff/mypy scope; verified `.importlinter` and `bandit` configs do not scan `docs/`." This
validation doc follows that explicit scoping rather than blanket-applying `rules/toolchain.md`'s
full code-oriented sequence.

## Assumptions

- Per the format-precheck procedure doc
  (`20260718-101327_mcp90_and_consistency_test_format_precheck.md`),
  `uv run pytest tests/test_check_mcp_docs_consistency.py -v` exercises only synthetic in-memory
  fixtures and does not read any real file under `docs/` — so it will pass/fail independent of
  this plan's edits and must NOT be treated as proof the File Index edit or the new known-gap
  entry are correct. The real end-to-end check against actual `docs/` content is
  `uv run check-mcp-docs` (CLI entry point registered in `pyproject.toml`, documented in
  `rules/toolchain.md`).
- This plan's Out-of-scope section guarantees zero changes to `scripts/mcp_servers/**`,
  `scripts/shared/**`, `scripts/agent/**`, or any test file — this must be confirmed by
  `git diff --stat`, not merely assumed.

## Implementation

### Target file

None (cross-cutting validation step; no file is edited by this doc — it validates the outputs of
Implementation steps 3-7, each covered by its own procedure doc).

### Procedure

1. `grep -rn "requires_config" docs/` (repo-wide, after all steps 1-7 have been applied) →
   confirm every remaining match is one of the 4 catalog docs' **pre-existing, untouched** lines
   (the ones this plan deliberately left alone per the sequencing-check doc), not a new mention
   introduced by this plan's own additions.
2. `grep -n "requires_config" docs/04_mcp_03_06_tool-runtime-availability-metadata.md` → expect 0
   matches, or matches only inside the explicit "removed/obsolete" sentence in that file's
   section 1 (never presented as currently active) — per the step-3 procedure doc's own
   Validation plan.
3. `grep -c "config_dependent\|disabled_reason\|enabled_for_llm"
   docs/04_mcp_03_06_tool-runtime-availability-metadata.md` → expect > 0 (confirms the new terms
   are actually documented, per this plan's own stated Validation plan).
4. Manual read-through of `docs/04_mcp_00_document-guide.md`'s Reading Order and File Index →
   confirm the new file is discoverable via the documented `01 → 02 → 03 → 04 → 05 → 06 → 90`
   navigation path (the File Index row edit from Implementation step 4 makes `04_mcp_03_06`
   reachable under the `03` block).
5. `uv run check-mcp-docs` — run the real CLI consistency checker against actual `docs/` content.
   This is the check that actually exercises the real files this plan edited; it must be
   included even though the plan's own Validation plan section only names the pytest command,
   because that pytest command alone does not validate real-file correctness (see Assumptions).
6. `uv run pytest tests/test_check_mcp_docs_consistency.py -v` — run as stated in the plan's
   Validation plan, understanding it as a synthetic-fixture regression check on the checker
   functions themselves, not a check of this plan's specific doc edits.
7. `git diff --stat docs/` — confirm only the intended files changed:
   `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` (new),
   `docs/04_mcp_00_document-guide.md`, the 4 catalog docs, `docs/05_agent_08_04_configuration-mcp-approval-obs.md`,
   `docs/04_mcp_90_inconsistencies_and_known_issues.md`.
8. `git diff --stat` (repo-wide, no path filter) → confirm zero changes outside `docs/` — no
   `scripts/`, `tests/`, or `config/` file touched, per this plan's Out-of-scope guarantee.

### Method

Shell-based grep/diff checks plus two test/CLI invocations (`check-mcp-docs`, `pytest` on the one
named test file). No code is written or modified by this validation step itself.

### Details

This validation step depends on Implementation steps 3-7 having already been applied (each has
its own procedure doc: `20260718-101441_04_mcp_03_06_tool-runtime-availability-metadata.md`,
`20260718-101528_04_mcp_00_document-guide.md`,
`20260718-101558_04_mcp_04_catalog_docs_availability_notes.md`,
`20260718-101641_05_agent_08_04_configuration-mcp-approval-obs.md`,
`20260718-101707_04_mcp_90_inconsistencies_and_known_issues.md`). It should be run once, after
all five are applied, as the final gate before this plan is considered complete — matching
Implementation step 8's position as the last step in the plan.

Baseline note carried over from the sequencing-check doc: the repo-wide `requires_config` count
under `scripts/` was 51 (not the plan's stated 47) across the same 10 files as of this
investigation — this is a `scripts/` baseline, unaffected by and not in scope for this
documentation-only plan's validation, but recorded here for consistency with the other
procedure docs in this batch.

## Validation plan

- All 8 procedure steps above ARE this doc's own validation plan (this is itself the plan's
  validation step). Success criteria: step 1 shows no leakage, step 3 shows >0 matches, step 5
  and step 6 both pass, step 7/8 show only the expected `docs/` files changed and nothing under
  `scripts/`/`tests/`/`config/`.
- If `uv run check-mcp-docs` (step 5) reports a new WARNING/ERROR attributable to this plan's
  edits (e.g. the new `04_mcp_90` entry interacting unexpectedly with
  `check_active_inconsistencies`'s `## Active Issues` scan), treat that as a blocking finding to
  resolve before considering this plan's documentation work complete, rather than silently
  ignoring it.
