## Goal

Precheck step for the `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` documentation
plan (source: `plans/20260717-180307_plan.md`, requirement 19: "Document MCP runtime
availability metadata and disabled tool behavior"). Confirm, before any file is edited, the
exact current entry format used in `docs/04_mcp_90_inconsistencies_and_known_issues.md` and the
exact behavior of `tests/test_check_mcp_docs_consistency.py`, so that Implementation step 7 (add
a "known gap" entry) and the plan's Validation plan (run the pytest file) are both grounded in
the real current structure rather than an assumed one. This is a read-only investigation step —
it produces no file edits itself, only facts consumed by later steps.

## Scope

**In scope**: read `docs/04_mcp_90_inconsistencies_and_known_issues.md` in full and
`tests/test_check_mcp_docs_consistency.py` in full; record findings for reuse by the
`04_mcp_90` known-gap-entry doc and by the validation-plan doc.

**Out of scope**: editing either file (this is Implementation step 1 of the plan, a
precondition check only — the actual edit is step 7, covered by a separate procedure doc).

## Assumptions

- The plan's own Affected-areas note says `04_mcp_90_inconsistencies_and_known_issues.md`
  "exists per the document guide's File Index; not yet read in full at authorship time — read
  before editing." This step performs that read.
- The plan's Validation plan assumes `uv run pytest tests/test_check_mcp_docs_consistency.py -v`
  "must pass after the File Index edits" — this assumption needs verifying, since the test file
  might not actually exercise the File Index at all (see Details below; this affects how the
  validation-plan doc for this feature should describe that test run).

## Implementation

### Target file

- `docs/04_mcp_90_inconsistencies_and_known_issues.md` (read only)
- `tests/test_check_mcp_docs_consistency.py` (read only)

### Procedure

1. Read `docs/04_mcp_90_inconsistencies_and_known_issues.md` in full (49 lines).
2. Read `tests/test_check_mcp_docs_consistency.py` in full (506 lines).
3. Record the exact entry format found in (1) as the template for Implementation step 7's new
   entry.
4. Record what (2) actually checks, so the plan's Validation plan step ("this pytest file must
   pass") is described accurately rather than assumed.
5. No file is modified in this step.

### Method

Plain read (no code changes). Facts below were gathered via a read-only investigation pass.

### Details

**`docs/04_mcp_90_inconsistencies_and_known_issues.md` (49 lines)** — current structure:

- L13: `# MCPにおける不整合と既知の問題` (title)
- L28: `## MDQ ハイブリッド検索はstub（未実装）` — the only current entry, an H2 heading (not a
  table row, not a numbered `MCP-NN` entry)
- L39: `## Related Documents`
- L43: `## Keywords`

The declared entry template (L18-24) lists these bullet fields:
`**Type:**`, `**Impact scope:**`, `**Statement A / B:**`, `**Current safe interpretation:**`,
`**Recommended action:**`, `**Notes for AI reference:**`.

The one real existing entry (L28-36) deviates slightly — it uses `**Current behavior:**` and
`**Affected config:**` instead of some declared fields — so the declared list is a guideline,
not a strictly enforced schema. Each entry is wrapped in `---` rules before/after (L26, L37).

**Append point**: a new entry belongs after L37 (closing `---` of the MDQ entry) and before L39
(`## Related Documents`) — i.e., insert at line 38, following `## <title>` + bullets + trailing
`---`.

**Important discrepancy to flag**: `tests/test_check_mcp_docs_consistency.py` and its
`_ACTIVE_ISSUE_ALLOWLIST` reference a `### MCP-NN: <title>` heading scheme under an
`## Active Issues` section (IDs `MCP-01`...`MCP-08`) — but the real
`04_mcp_90_inconsistencies_and_known_issues.md` file has **no such section and no `MCP-NN`
numbering** at all; it has exactly one untitled/unnumbered `##` entry. This is a genuine
discrepancy between the test's assumed structure and the real file. The new known-gap entry
(step 7) should follow the **real current file's format** (plain `## <title>` heading + bullet
fields), not the `MCP-NN` scheme the test file expects, since retrofitting `MCP-NN` numbering is
out of this plan's scope (out-of-scope: "Implementing or changing behavior of ... those are
requirements 14/15/16/17").

**`tests/test_check_mcp_docs_consistency.py` (506 lines)** — per its own docstring (L1-5), this
file is **"Unit tests for scripts/check_mcp_docs_consistency.py — synthetic doc content, not
references to real doc files."** All `DocFile` objects under test are constructed in-memory via
`_mk_file()` (L30-31) with fabricated line lists. **It does not read any real file under
`docs/`, does not check the File Index table, and does not verify that every `docs/04_mcp_*.md`
file appears in the index.** It unit-tests these checker functions (imported from
`tools/check_mcp_docs_consistency.py`, which lives at
`/home/sugimoto/llmagent/tools/check_mcp_docs_consistency.py`, not under `scripts/`):
`check_startup_modes` (L49-103), `check_fail_open_workflow_allowlist` (L108-130),
`check_routing_authority` (L136-158), `check_active_inconsistencies` (L164-225, the one that
assumes the `MCP-NN`/`## Active Issues` scheme), `_ACTIVE_ISSUE_ALLOWLIST` (L231-245),
`check_live_discovery_routing` (L251-275), `check_routing_authority_v1tools` (L281-307),
`check_tool_names_routing_input` (L313-355), `check_audit_log_single_format` (L361-385),
`check_transport_error_is_error` (L391-443), `check_stdio_active_transport` (L449-482),
`check_strict_validation_skips_unreachable` (L488-506).

**Consequence for the plan's Validation plan**: running
`uv run pytest tests/test_check_mcp_docs_consistency.py -v` will pass or fail independent of
this plan's doc edits (it is a self-contained unit test suite over synthetic fixtures) — it is
NOT evidence that the File Index edit (step 4) or the new known-gap entry (step 7) are correct.
The real end-to-end check against actual `docs/` content is the separately installed CLI entry
point `uv run check-mcp-docs` (registered in `pyproject.toml`, documented in
`rules/toolchain.md` under "MCP documentation consistency"), which runs
`tools/check_mcp_docs_consistency.py`'s checks against the real files. The validation-plan doc
for this feature should run `uv run check-mcp-docs` (real-file check) in addition to — not
instead of — the plan's stated pytest command, and should note the pytest command alone does
not validate the File Index or the new known-gap entry's format.

## Validation plan

- No file changed in this step; nothing to validate directly.
- Downstream: Implementation step 7's procedure doc must model its new entry on the real format
  recorded here (H2 heading + bullet fields, `---` before/after), not the test file's `MCP-NN`
  scheme.
- Downstream: the validation-plan doc for this feature must run `uv run check-mcp-docs` (real
  files) alongside `uv run pytest tests/test_check_mcp_docs_consistency.py -v` (synthetic-only),
  and should not claim the pytest run alone proves the File Index/known-gap edits are correct.
