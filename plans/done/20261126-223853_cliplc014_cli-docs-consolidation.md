## Goal
- Make the CLI (chapter 07) and MCP lifecycle documentation set state one authoritative claim per concept, by correcting the confirmed stale or contradictory statements so that every written claim is provable against current source and a named test.

## Priority
Low

## Scope
- **In-Scope**: the six documentation rows in `Implementation Target Files`; a verification pass over all ten chapter-07 documents and the MCP lifecycle document; running the repository docs checkers on the changed files.
- **Out-of-Scope**: new checkers (Markdown lint, duplicate-usage) — the existing checkers already cover broken links and command-reference consistency, and the Issue's AI Implementation Instruction restricts this phase to documentation edits (user decision, 2026-11-26); renaming files whose names do not match their content, because a rename requires updating `tests/docs/test_command_docs_sync.py` hardcoded paths plus `docs/00_index.md`, `docs/01_overview/overview_01_03-arch-features.md`, `routing.md`, and `.claude/commands/mcp-server-add.md` and needs a maintainer approval record per `docs/00_governance/governance_01_documentation-policy.md` (user decision, 2026-11-26); behavior changes owned by the other issues of this backlog; any ADR content change.
- **Dependencies**: the backlog issues cliplc001 through cliplc013 are closed (`issues/done/`), so no dependency blocks this Plan.
  - **Depends on**: N/A: no open dependency. cliplc011 already owns the `/stats` canonical specification row in `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`; this Plan does not modify that file (see Assumptions).

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 14), filed as `issues/20261119-145312_cliplc014_cli-docs-consolidation.md`. The chapter-07 documents exist under `docs/23_agent/` as `agent_07_01` through `agent_07_10`; the backlog's paths without the `23_agent/` directory do not exist. The backlog's defect list (duplicate command definitions, misleading filenames, empty sections, punctuation errors, contradictory shutdown guarantees, obsolete delayed-input behavior) was `Needs confirmation` at filing time. Step 2 resolved that list against current source: three of the six claims do not reproduce, and the MCP lifecycle document was identified as `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md`.

## Problem
Six statements in the documentation set contradict current source or each other:

- `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md:73` documents `/config show`; `/config` has no subcommand in `scripts/agent/commands/command_defs_list.py:40-45`.
- `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md:57` states that Ctrl-C never ends the REPL by itself, which contradicts line 39 of the same file and `scripts/agent/signal_handler.py:102-138` (force-exit path when `shutdown_force_exit_on_second_sigint` is true).
- `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md:21` states that shutdown removes the process entry before signalling; `scripts/agent/http_lifecycle_shutdown_coordinator.py` (lines 9 and 109) and `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md:101` state that nothing is removed before the termination attempt and a record is released only on a confirmed exit. `tests/agent/test_http_lifecycle_shutdown_coordinator.py::test_no_removal_before_termination` proves the code behavior.
- `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md:106` enumerates `RAG hits` in the `/stats` output; no RAG hits counter exists in the stats model (`scripts/agent/commands/models.py:30-47`; `rag_db_configured` only gates a hint line at `scripts/agent/commands/cmd_config_stats.py:141-143`). The `not yet implemented, SHARED-003` parenthetical is accurate for the aggregate-state clause: `cmd_config_stats.py:130-136` prints memory aggregate counters but no Repository Context aggregate state, and SHARED-003 is still `open` in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`. The stale part of the row is the `RAG hits` enumeration, not the parenthetical.
- `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md:57` has an empty `## Known Limitations` section, the only genuinely empty section in the chapter.
- `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md:30-40` lists the chapter files in a non-numeric order (04, 05, 02, 03, 07, 08, 09, 10, 06).

Claims that do not reproduce against current source: duplicate authoritative command specifications (`agent_07_03` is an index that explicitly delegates subcommand and argument detail to the per-command chapters, line 42); punctuation, spacing, and indentation errors (none found in the chapter); obsolete delayed-input behavior (`agent_07_05` already documents the current input-handoff behavior implemented by cliplc001). `## Design Intent` headings followed directly by `###` subsections are not empty-content defects.

## Reason for Change
Documentation follows the settled contracts: the dependency issues are closed, so the behavior the documents describe is final. A contradictory shutdown guarantee or an unregistered command usage can make an operator take a wrong action; the Issue keeps Low priority because no such incident is cited.

## Implementation Intent
One authoritative statement per command and lifecycle concept, verified against source and a test before it is written. Navigation and section completeness are normalized inside the existing files; filenames are not changed. No new checker is introduced — the existing docs gates are the enforcement mechanism.

## Requirements
- `REQ-001`: Every documented command usage must exist in the registered command surface; remove the unregistered `/config show` usage from the pending-restart display text.
- `REQ-002`: The REPL interrupt contract must be stated without internal contradiction: the absolute Ctrl-C claim must be qualified by the configured force-exit opt-in that the same document already states.
- `REQ-003`: The MCP lifecycle document must state process-record ownership during shutdown the way the coordinator implements it (record released only on a confirmed exit).
- `REQ-004`: A stale claim must be removed where the implementation contradicts it: the unprovable `RAG hits` enumeration in the `/stats` row is removed, while the `not yet implemented, SHARED-003` parenthetical stays because the aggregate-state reporting it names is still unimplemented. The privacy scope of the `/stats` aggregate reporting stays.
- `REQ-005`: An empty section must be completed — either with the actual limitation or with the `Not applicable.` convention used by the sibling chapter documents.
- `REQ-006`: The chapter index navigation must list the chapter files in the chapter's own numbering order.
- `REQ-007`: Every statement written must be verified against current source and a test before writing; a statement no test proves is reported, not written (the Issue's AI Implementation Instruction).
- `REQ-008`: The changed documents must pass the repository docs checkers.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed — see this Plan's Step 8 report in the workflow run).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md` | Modify: replace the unregistered `/config show` usage with the registered `/config` form | Documented command does not exist in the registered surface | REQ-001; AC-1 | `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md:73` vs `scripts/agent/commands/command_defs_list.py:40-45` (`/config`, no subcommands) (checked in Step 2) | `tests/tools/test_check_command_contracts.py` (usage-line contract), docs gate `uv run python tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` | Modify: qualify the absolute Ctrl-C statement so it matches the force-exit opt-in stated earlier in the same file | Internally contradictory shutdown guarantee | REQ-002; AC-2 | `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md:57` vs line 39 of the same file and `scripts/agent/signal_handler.py:102-138` (checked in Step 2) | `tests/agent/test_signal_handler.py` (`TestInterruptByState`, `test_configured_force_exit_is_read_once_at_construction`) | Verified |
| `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md` | Modify: restate process-record removal during shutdown to match the coordinator's record-ownership rule | Contradicts the coordinator and the sibling lifecycle document | REQ-003; AC-2 | `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md:21` vs `scripts/agent/http_lifecycle_shutdown_coordinator.py:9,109` and `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md:101` (checked in Step 2) | `tests/agent/test_http_lifecycle_shutdown_coordinator.py::test_no_removal_before_termination` | Verified |
| `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` | Modify: remove the unprovable `RAG hits` enumeration from the `/stats` row; keep the `not yet implemented, SHARED-003` parenthetical (verified accurate) | The documented output line has no implementing counter | REQ-004; AC-2 | `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md:106` vs `scripts/agent/commands/models.py:30-47` and `scripts/agent/commands/cmd_config_stats.py:141-143` (checked in Step 3a) | `tests/agent/commands/test_agent_cmd_config.py` (`_cmd_stats`) | Verified |
| `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md` | Modify: complete the empty `## Known Limitations` section | Empty section | REQ-005; AC-3 | `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md:57` empty; convention `Not applicable.` at `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md:91` (checked in Step 3a) | docs gate `uv run python tools/check_docs_quality.py` | Verified |
| `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md` | Modify: order the chapter index table by chapter file number | Navigation order does not match the chapter numbering | REQ-006; AC-3 | `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md:30-40` table order 04, 05, 02, 03, 07, 08, 09, 10, 06 (checked in Step 2) | `tests/docs/test_command_docs_sync.py` (reads the chapter-07 file set) | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.
- Write every `File Path` cell, every `tests/...py` path in `Related Tests`, and every path in
  `Implementation steps` in backticks: `tools/close_procedures_batch.py` and the companion check read
  only backticked paths. `uv run python tools/backtick_plan_related_tests.py plans/{filename}.md`
  normalizes a Plan, and `tools/check_workitem_structure.py` reports a plain path
  (`plain-path-citation`).

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/23_agent/agent_07_02_cli-and-commands-cliview.md` | Verification pass: no defect found; confirms the presentation-layer boundary is stated consistently with the input controller | REQ-007 |
| `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` | Canonical command index and the `Not applicable.` convention for `## Known Limitations`; its `/stats` row is owned by cliplc011 | REQ-004, REQ-005, REQ-007 |
| `docs/23_agent/agent_07_04_cli-and-commands-purpose.md` | Verification pass: no defect found | REQ-007 |
| `docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md` | Verification pass: no punctuation or navigation defect found | REQ-007 |
| `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md` | Read for the `/debug verbose` claim, which is verified accurate (`scripts/agent/commands/cmd_debug.py:34-52` reports no source/section diagnostics) | REQ-005, REQ-007 |
| `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md` | Verification pass: no defect found; confirms retired `/memory` usage forms are listed as retired, not as an authoritative specification | REQ-007 |
| `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` | The sibling lifecycle document that already states the record-ownership rule correctly; its stderr-log path row is owned by cliplc009 | REQ-003 |
| `scripts/agent/commands/command_defs_list.py` | Canonical registered command surface for REQ-001 | REQ-001 |
| `scripts/agent/signal_handler.py` | Interrupt and force-exit behavior for REQ-002 | REQ-002 |
| `scripts/agent/http_lifecycle_shutdown_coordinator.py` | Record-ownership behavior for REQ-003 | REQ-003 |
| `scripts/agent/commands/cmd_config_stats.py` | Implemented `/stats` aggregate reporting for REQ-004 | REQ-004 |
| `tests/docs/test_command_docs_sync.py` | Hardcodes the chapter-07 filenames; confirms a rename is out of scope and that the index change does not break it | REQ-006 |
| `tools/check_docs_consistency.py` | Existing command-reference and broken-link checks; shows the coverage gap recorded as UNK-01 | REQ-001, REQ-008 |

Step 3a findings (2026-11-26, adversarial verification): all Problem claims reconfirmed against current source —
`/config show` at `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md:73` against the registered `/config`
with no subcommands (`scripts/agent/commands/command_defs_list.py:40-45`); the Ctrl-C contradiction between
`docs/23_agent/agent_07_05_cli-and-commands-repl-io.md:57` and line 39 of the same file with the force-exit path at
`scripts/agent/signal_handler.py:102-138`; the shutdown record-ownership contradiction at
`docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md:21` against `scripts/agent/http_lifecycle_shutdown_coordinator.py:9,109`
and `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md:101`; the empty `## Known Limitations` section; the
non-numeric chapter index order at `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md:30-40`; and the
`Not applicable.` convention at `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md:91`. Two corrections:
the empty section heading is at line 57, not 51 (line 51 is the RAG-search paragraph), and the Problem section's
statement count is six, not seven. REQ-004's premise is narrowed: the `not yet implemented, SHARED-003` parenthetical
is accurate, so the actionable change is the unprovable `RAG hits` enumeration. Statements no test proves are
reported, not written: the memory aggregate lines (`scripts/agent/commands/cmd_config_stats.py:130-136`) and the
`Debug mode` line have no asserting test, so no new statement about them is written; the existing wording that is
accurate against source is left unchanged. UNK-02 is resolved by the maintainer's confirmation of the chapter-numbering
convention (2026-11-26).

## Acceptance Criteria
- AC-1 (REQ-001): no documented command or subcommand usage in the changed files that is absent from `scripts/agent/commands/command_defs_list.py`.
- AC-2 (REQ-002, REQ-003, REQ-004): each corrected statement matches the implementation and is provable by the test named in its target row.
- AC-3 (REQ-005, REQ-006): no empty section remains in the chapter, and the chapter index lists files in chapter numbering order.
- AC-4 (REQ-008): the docs checkers pass on the changed files.
- AC-5 (REQ-007): the verification record for each changed statement is reported; any statement no test proves is reported rather than written.

## Tests
- REQ-001: `uv run python tools/check_docs_consistency.py --domain agent` plus `uv run pytest tests/tools/test_check_command_contracts.py`.
- REQ-002: `uv run pytest tests/agent/test_signal_handler.py`.
- REQ-003: `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py`.
- REQ-004: `uv run pytest tests/agent/commands/test_agent_cmd_config.py`.
- REQ-005, REQ-006: `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py 'docs/23_agent/agent_07_*.md'`.
- REQ-007: manual verification against the Reference Files before writing; no automated test proves a documentation sentence by itself, so the verification record is the evidence.
- REQ-008: the docs gate set in the Validation plan.

## Documentation Impact
This Plan is the documentation change itself. Per `docs/00_index.md`'s "Document References by Task" table, the affected documents are the Agent domain spec chapter 07 files and the MCP domain spec lifecycle file listed in `Implementation Target Files`; the intent, boundaries, failure behavior, and Known Issues are written into those files. No ADR content is changed (out of scope).

## Assumptions
- cliplc011 owns the `/stats` canonical specification row in `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`; this Plan changes only the same claim's copy in `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`. Compatible overlap, no sequencing dependency.
- cliplc009 owns `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`; this Plan changes only `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md`. Compatible overlap.
- Existing checkers satisfy the Issue's broken-link and command-reference consistency requirements; only Markdown lint and duplicate-usage checks are absent, and they are out of scope per the user decision recorded in Scope.
- Completing an empty section with `Not applicable.` follows the convention already used in the same chapter; it is not a claim about behavior.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | `tools/check_docs_consistency.py`'s command-contract check scans only `agent_07_07` to `agent_07_10` (`_COMMAND_CHAPTER_DOCS`, line 222), so the unregistered `/config show` usage in `agent_07_06` is not caught by any automated check; the fix cannot be validated by the existing checker | No rule or test covers usage lines outside the four command chapters | Maintainer decides whether to extend the checker's chapter set; out of scope for this Plan per the user decision, so REQ-001 is validated by manual comparison against `scripts/agent/commands/command_defs_list.py` | False |
| UNK-02 | No governance rule states the ordering convention for a chapter index table; REQ-006 is a navigation normalization, not a rule violation | `docs/00_governance/governance_00_document-guide.md` and `governance_01_documentation-policy.md` contain no index-ordering rule | Resolved: the maintainer confirmed the chapter-numbering convention on 2026-11-26, so Phase 6 proceeds | False (resolved) |
| UNK-03 | Whether the SHARED-003 registry entry in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` needs a scope note once the `/stats` aggregate claim is corrected | The registry entry covers the memory model, not the `/stats` reporting scope | Report to the maintainer; `governance_03` is out of scope for this Plan | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md` | Modify | Low | 1 | High (100% single author) | not applicable (rsynced) |
| `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` | Modify | Low | 3 | High (100% single author) | not applicable (rsynced) |
| `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md` | Modify | Low | 2 | High (100% single author) | not applicable (rsynced) |
| `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` | Modify | Low | 5 | High (100% single author) | not applicable (rsynced) |
| `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md` | Modify | Low | 1 | High (100% single author) | not applicable (rsynced) |
| `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md` | Modify | Medium | 0 | High (100% single author) | not applicable (rsynced) |

## Design
Path B classification: six modification targets, all documentation, so the four Path B
analyses were run at the documentation scale.

- Architecture analysis: `rg "^from|^import"` does not apply to Markdown targets. Instead, `rg -n "agent_07_" .` shows the chapter is referenced by `tests/docs/test_command_docs_sync.py` (hardcoded filenames), `docs/00_index.md`, `docs/01_overview/overview_01_03-arch-features.md`, and the chapter's own front-matter `related:` lists. `mcp_03_05` is referenced by `routing.md`, `.claude/commands/mcp-server-add.md`, `docs/00_governance`-linked MCP guide files, and `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`. These references are why renames are out of scope; content-only edits do not break them.
- Dependency graphing: no Python module imports a documentation file. The only code coupling is the test that enumerates the chapter-07 filenames and the docs checkers that scan the domain directories.
- Historical analysis: `git log --name-only --pretty=format: --since=30.days` gives the per-file churn in the Affected areas table; none of the six files is in the 30-day top 15 for `docs/23_agent` or `docs/22_mcp`. Bus factor is high across the chapter (49 commits, one author).
- Operational dependency inspection: not applicable — no DB file, port, or running process is involved; the check was not run because no target is a runtime resource.
- Validation quality baseline: `N/A: no Python target` (all rows are documentation).
- Design decision: the corrected statements are written only where a named test proves the implementation behavior; statements that no test proves are reported, not written (REQ-007). No new abstraction, no new checker, no filename change.
- Release units: each step is a single-file documentation edit that passes the docs gates on its own, so no release unit is required.

## Implementation steps

1. **Phase 1: Command-surface correction**
   - [ ] Replace the unregistered `/config show` usage with the registered `/config` form in the Pending Restart Display section (REQ-001; `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`)
2. **Phase 2: Interrupt contract consistency**
   - [ ] Qualify the absolute Ctrl-C statement so it matches the configured force-exit opt-in already stated in the same document (REQ-002; `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`)
3. **Phase 3: MCP lifecycle record ownership**
   - [ ] Restate process-record removal during shutdown to match the coordinator's confirmed-exit rule (REQ-003; `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md`)
4. **Phase 4: Stale implementation-status claim**
   - [ ] Remove the unprovable `RAG hits` enumeration from the `/stats` row; keep the `not yet implemented, SHARED-003` parenthetical and the aggregate-state privacy scope (REQ-004; `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`)
5. **Phase 5: Section completeness**
   - [ ] Complete the empty `## Known Limitations` section with the chapter convention (REQ-005; `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md`)
6. **Phase 6: Navigation normalization**
   - [ ] Reorder the chapter index table by chapter file number (REQ-006; `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md`) — conditional on UNK-02
7. **Phase 7: Validation and reporting**
   - [ ] Run the docs gates on the changed files and the targeted tests named in the target rows (REQ-007, REQ-008; all six target files)
   - [ ] Report any statement that no test proves instead of writing it, and report UNK-01's coverage gap to the maintainer (REQ-007; no file change)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md` | Docs gate + manual contract check against the registered surface | `uv run python tools/check_docs_consistency.py --domain agent`; compare with `scripts/agent/commands/command_defs_list.py` | No finding; the file contains no usage absent from the registry |
| `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` | Unit test proving the force-exit opt-in | `uv run pytest tests/agent/test_signal_handler.py` | Pass; the document's statement matches `TestInterruptByState` |
| `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md` | Unit test proving record ownership | `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py` | Pass, including `test_no_removal_before_termination` |
| `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` | Unit test for the implemented aggregate reporting | `uv run pytest tests/agent/commands/test_agent_cmd_config.py` | Pass; no `not yet implemented` claim remains for implemented behavior |
| `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md` | Docs structural gate | `uv run python tools/check_docs_quality.py` | No issues found |
| `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md` | Docs structural gate + link reachability | `uv run python tools/check_docs_structure.py 'docs/23_agent/agent_07_*.md'` | All checks passed |
| All changed docs | Content policy and language gates | `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_japanese.py` | No warnings; no Japanese text |
| This Plan | Workitem structure and traceability gates | `uv run python tools/backtick_plan_related_tests.py plans/20261126-223853_cliplc014_cli-docs-consolidation.md`; `uv run python tools/check_workitem_structure.py --file plans/20261126-223853_cliplc014_cli-docs-consolidation.md` | No findings |

## Risks
- **Risk**: the corrected statements drift again when the behavior changes → **Mitigation**: the existing docs gates run in CI for the agent and mcp domains; the coverage gap for usage lines outside the four command chapters is recorded as UNK-01 for a maintainer decision.
- **Risk**: the excluded renames leave the filename/content mismatch in place (`agent_07_01` is a chapter index, `agent_07_09` covers Debug and Compact only) → **Mitigation**: recorded in Scope as out-of-scope; a rename needs a maintainer approval record per `docs/00_governance/governance_01_documentation-policy.md` and a coordinated update of `tests/docs/test_command_docs_sync.py` and the referencing documents.
- **Risk**: removing the `/stats` SHARED-003 parenthetical could be read as closing a registry entry → **Mitigation**: only the implementation-status wording is changed in the chapter; `docs/00_governance/governance_03_issue-and-uncertainty-management.md` is not modified (UNK-03).
- **Risk**: overlap with cliplc011 and cliplc009 on files this Plan does not modify → **Mitigation**: this Plan's rows are limited to files those Plans do not target; the overlap is recorded as compatible in Assumptions.
- **Risk**: REQ-006 is a normalization without a governing rule, so it could be seen as unrelated cleanup → **Mitigation**: it is requested by the Issue's Required Changes; conditional on UNK-02, and skipped if the maintainer does not confirm the convention.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Command-surface correction in `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md` | In Progress | — | — |  |
| 2 | Interrupt contract consistency in `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` | In Progress | — | — |  |
| 3 | MCP lifecycle record ownership in `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md` | In Progress | — | — |  |
| 4 | Unprovable `RAG hits` enumeration in the `/stats` row of `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` | In Progress | — | — | Parenthetical kept (Step 3a) |
| 5 | Section completeness in `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md` | In Progress | — | — |  |
| 6 | Navigation normalization in `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md` | In Progress | — | — | UNK-02 resolved (convention confirmed 2026-11-26) |
| 7 | Validation and reporting across the six target files | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261127-001124_01_docs_23_agent_agent_07_06_cli-and-commands-hot-reload.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261127-001124_02_docs_23_agent_agent_07_05_cli-and-commands-repl-io.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261127-001124_03_docs_22_mcp_mcp_03_05_lifecycle-and-new-server.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261127-001124_04_docs_23_agent_agent_07_07_cli-and-commands-slash-commands-session-mcp.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261127-001124_05_docs_23_agent_agent_07_09_cli-and-commands-slash-commands-workflow-debug.md.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261127-001124_06_docs_23_agent_agent_07_01_cli-and-commands-cli-reference.md.md` | 6 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-145312_cliplc014_cli-docs-consolidation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-223853
- **Evidence revision**: a817eab7c6d6d5d42c541c03c3caa20e893f3da8
- **Related target files**: `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md`, `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`, `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`, `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`, `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md`, `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes + `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md:73` vs `scripts/agent/commands/command_defs_list.py:40-45` | `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md` | 1 | AC-1 | `uv run python tools/check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-002 | Required Changes (contradictory shutdown guarantees) + `agent_07_05:57` vs line 39 and `scripts/agent/signal_handler.py:102-138` | `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` | 2 | AC-2 | `tests/agent/test_signal_handler.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes (contradictory shutdown guarantees) + `mcp_03_05:21` vs `scripts/agent/http_lifecycle_shutdown_coordinator.py:9,109` | `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md` | 3 | AC-2 | `tests/agent/test_http_lifecycle_shutdown_coordinator.py::test_no_removal_before_termination` | Confirmed by repository evidence |
| REQ-004 | Required Changes + `agent_07_07:106` vs `scripts/agent/commands/models.py:30-47` and `scripts/agent/commands/cmd_config_stats.py:141-143` | `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` | 4 | AC-2 | `tests/agent/commands/test_agent_cmd_config.py` | Confirmed by repository evidence (scope narrowed in Step 3a: `RAG hits` only) |
| REQ-005 | Required Changes (empty sections) + `agent_07_09:57` | `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md` | 5 | AC-3 | `uv run python tools/check_docs_quality.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes (navigation) + `agent_07_01:30-40` | `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md` | 6 | AC-3 | `uv run python tools/check_docs_structure.py 'docs/23_agent/agent_07_*.md'` | Confirmed (convention confirmed by the maintainer, 2026-11-26) |
| REQ-007 | AI Implementation Instruction | N/A: no single target file — applies to all six rows | 7 | AC-5 | Verification record against the Reference Files | Explicit in issue |
| REQ-008 | Constraints + Testing Expectations | N/A: no single target file — applies to all six rows | 7 | AC-4 | Docs gate set in the Validation plan | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261127-001124 -->