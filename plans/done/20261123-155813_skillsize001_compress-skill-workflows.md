## Goal
- Add a size-budget gate for the files that every pipeline cycle loads (skills, rules, prompts, templates, routing, AGENTS) so they cannot grow past a recorded ceiling, and shrink what the `issue-to-plan` and `plan-to-implementation-procedure` cycles load by moving the runtime sections of `skills/DESIGN.md` into a small runtime rule file (Stages 1 and 2 of the staged compression; Stages 3 to 7 are tracked in a follow-up issue).

## Priority
Medium

## Scope
- **In-Scope**: Stage 1: a baseline-gated size check for the pipeline instruction files, its tests, its registration in the validation gates, the tool inventory, the tool-gate table, and CI, and the recorded baseline. Stage 2: a runtime rule file holding the `skills/DESIGN.md` sections that the workflows load at Step 0 (Output language, Out-of-scope paths, Change-impact table, Tool availability guard, Analysis-only phase constraint), `skills/DESIGN.md` keeping each heading as a one-line pointer, and the Step 0 and reference updates of the two skills that load it (`issue-to-plan`, `plan-to-implementation-procedure`) and their two prompts.
- **Out-of-Scope**: Stages 3 to 7 of the Issue (thinner `SKILL.md` files, preflight and postflight tools, the main-path and edge-case split of each workflow, condensed manual-fallback prose, the section index of `rules/ai-execution.md`); changing the meaning of any rule; skills outside `issue-to-plan` and `plan-to-implementation-procedure` (their references to `skills/DESIGN.md` sections stay valid through the pointers); renaming or removing `skills/DESIGN.md`; `docs/*.md`; code under `scripts/`.
- **Dependencies**: None open. The Issue's remaining stages are filed as a separate follow-up Issue and wait for this Plan's measured numbers; no other open Plan or Issue targets these files (sibling check, 2026-11-23).

## Background
Source Issue: `skillsize001`. Re-measured in this cycle (sizes in bytes; tokens are bytes divided by four, an estimate):
- One `plan-to-implementation-procedure` cycle loads about 167 KB, of which `skills/DESIGN.md` is 18.9 KB; one `issue-to-plan` cycle loads about 146 KB, of which `skills/DESIGN.md` is 18.9 KB. Both workflows load it only for named sections: `plan-to-implementation-procedure` Step 0 cites "Output language, Out-of-scope paths", `issue-to-plan` Step 0 cites "Output language, Change-impact table, Out-of-scope paths, Tool availability guard", and their Allowed file operations cite "Analysis-only phase constraint". Those five sections total about 3.8 KB (Output language 1142 B, Analysis-only phase constraint 908 B, Change-impact table 777 B, Tool availability guard 668 B, Out-of-scope paths 220 B); the rest of the file is per-skill guidance and the skill catalog.
- The 71 files that pipeline cycles load (`skills/**/*.md`, `rules/*.md`, `prompts/*.md`, `templates/*.md`, `routing.md`, `AGENTS.md`, `CLAUDE.md`) total 827,660 B; 18 of them are over 16,384 B and 7 over 24,576 B. No size check covers them (`tools/check_module_size.py` covers `scripts/` and `tools/` Python modules only).
- The model for the new check exists: `tools/check_module_size.py` measures bytes, takes a baseline file of `<relpath>\t<size>` ceilings, fails on growth past a ceiling and on a stale entry, and reports a shrunk file so the baseline can be tightened. The latest example of wiring a new check is the config comment lint (`tools/check_config_comment_length.py`): the tool, its tests, a `tools/_validation_gate_defs.py` gate with path patterns, a CI step, and rows in `tools/TOOL_DESCRIPTIONS.md` (two tables) and `rules/tool-gates.md`.
- `skills/DESIGN.md` is cited by section name from about 115 places across skills, prompts, rules, and tools, so its headings must stay (as pointers). `tools/check_skills_references.py` checks that referenced paths exist and `tools/check_skills_heading_cycles.py` checks reference cycles between documents; both report no issues today.
- Growth history (git): the pipeline workflows plus the main rules and `skills/DESIGN.md` went from 92.6 KB (2026-09-01) to 232 KB (2026-11-23); about 100 commits touched them since 2026-10-01.
- Path B (13 target files across tools, tests, gates, CI, rules, skills, and prompts). Architecture: the new tool is a leaf script importing only the sibling `check_module_size` helpers; `lint-imports` is unaffected (tools are outside the contracts). Historical churn (30 days): `tools/TOOL_DESCRIPTIONS.md` 73 commits, `skills/issue-to-plan/workflow.md` 15, `skills/plan-to-implementation-procedure/workflow.md` 11, `.github/workflows/ci.yml` 10, `tools/_validation_gate_defs.py` 9, `skills/DESIGN.md` 2, `rules/tool-gates.md` 2, `prompts/01_issue-to-plan.md` 1, `prompts/02_plan-to-implementation-procedure.md` 0. Operational dependency: none (no ports, no database).
- Validation quality baseline (Step 5): `radon cc tools/check_module_size.py`: `main` is D (30), `load_baseline` B (8), the rest A; the new tool must keep `main` small by extracting helpers. `vulture scripts/ --min-confidence 80` reports two unused variables in files this Plan does not touch; `bandit -r scripts/` reports 7 medium and 41 high findings in `scripts/` unrelated to this Plan (baseline, not touched). diff-cover: the new tool's changed lines need at least 90 percent coverage from its own tests.

## Problem
Nothing stops the pipeline instruction files from growing again, and two of the three largest pipeline cycles load the whole 18.9 KB design document to read about 3.8 KB of runtime sections.

## Reason for Change
The per-invocation load grew 2.5 times in three months; a budget gate is the cheapest way to keep the later stages from being undone, and the runtime split is the largest mechanical saving that needs no rule rewording.

## Implementation Intent
Build the size check first by mirroring the module size gate, wire it everywhere the previous new check was wired, then create the runtime rule file by moving the five cited sections out of `skills/DESIGN.md` (leaving each heading with a one-line pointer so no citation breaks), point the two skills at the new file, and record the baseline last so that it holds the final sizes. Move text without rewording it.

## Requirements
- `REQ-001`: A tool `tools/check_skill_size.py` measures the covered instruction files in bytes and reports a violation for a file over the default limit of 16,384 B that is not in the baseline, for a baselined file that grew past its recorded size, and for a stale baseline entry (file gone or back under the limit); a shrunk file is reported as advisory; `--update-baseline` and `--no-baseline` behave as in `tools/check_module_size.py`.
- `REQ-002`: The check is registered like the previous new check: a validation gate with path patterns, a CI step, the `tools/TOOL_DESCRIPTIONS.md` rows, and the `rules/tool-gates.md` row, and the existing drift checks for gates and tool descriptions pass.
- `REQ-003`: `rules/skill-runtime.md` holds the five runtime sections moved verbatim from `skills/DESIGN.md`; `skills/DESIGN.md` keeps each of those headings with a one-line pointer; `issue-to-plan` and `plan-to-implementation-procedure` (workflows and prompts) load `rules/skill-runtime.md` instead of `skills/DESIGN.md`; no other skill's citation of a moved section breaks.
- `REQ-004`: The baseline file records the final sizes of the covered files after Stage 2, with a header comment stating the measurement (file count, total bytes, and the per-invocation load of the three measured skills), and the measured reduction for `plan-to-implementation-procedure` and `issue-to-plan` is at least 12 KB each.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tools/check_skill_size.py | create: new tool that collects the covered instruction files, applies the default limit and the baseline, and reports violations, stale entries, and shrunk files; reuses `load_baseline` and `write_baseline` from `tools/check_module_size.py` | No size check covers the pipeline instruction files | REQ-001; AC-1 | `tools/check_module_size.py` (baseline model: `collect_sizes`, `load_baseline`, `write_baseline`, `main`; checked in Step 3) | `tests/tools/test_check_skill_size.py` | Verified |
| tests/tools/test_check_skill_size.py | create: unit tests for the new tool (over-limit, within baseline, growth, stale entry, shrunk file, update and no-baseline modes, malformed baseline line, exit codes) | The new tool needs tests, including the failure cases | REQ-001; AC-1 | `tests/tools/test_check_config_comment_length.py` (sibling convention for a baseline-gated tool test; checked in Step 3) | itself | Verified |
| tools/TOOL_DESCRIPTIONS.md | modify: add the tool row to the summary table and to the per-tool table | `check_tool_descriptions_sync.py` requires a row for every tool | REQ-002; AC-2 | `TOOL_DESCRIPTIONS.md:120` and `:282` (rows of `check_config_comment_length.py`; checked in Step 3) | N/A: documentation (`tools/check_tool_descriptions_sync.py`) | Verified |
| tools/_validation_gate_defs.py | modify: add a gate `check_skill_size` with path patterns for the covered files and the tool | Every CI lint command needs a gate | REQ-002; AC-2 | `_validation_gate_defs.py:413-419` (`check_config_comment_length` gate with `patterns`; checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| rules/tool-gates.md | modify: add the "when to run" row | The table is the single source for when to run which tool | REQ-002; AC-2 | `tool-gates.md:42` (config comment row; checked in Step 3) | N/A: documentation (`run_validation_gates.py drift`) | Verified |
| .github/workflows/ci.yml | modify: add the CI step next to the module size checks | CI mirrors the gate | REQ-002; AC-2 | `ci.yml:46-51` (module size and config comment steps; checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| rules/skill-runtime.md | create: the five runtime sections moved verbatim from `skills/DESIGN.md` | The workflows load the whole design document for these sections only | REQ-003; AC-3 | `skills/DESIGN.md` sections `Output language` (1142 B), `Analysis-only phase constraint` (908 B), `Change-impact table` (777 B), `Tool availability guard` (668 B), `Out-of-scope paths` (220 B); `issue-to-plan/workflow.md:78` and `plan-to-implementation-procedure/workflow.md:82` Step 0 lists (checked in Step 3) | N/A: documentation (`tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`) | Verified |
| skills/DESIGN.md | modify: replace the body of each moved section with a one-line pointer to `rules/skill-runtime.md`, keeping the heading | About 115 citations name these sections; the headings must stay | REQ-003; AC-3 | `rg -l "skills/DESIGN.md"` finds 54 files citing it; heading list at `DESIGN.md:113-270` (checked in Step 3) | N/A: documentation (`tools/check_skills_references.py`) | Verified |
| skills/issue-to-plan/workflow.md | modify: Step 0 loads `rules/skill-runtime.md` instead of `skills/DESIGN.md`; the four inline citations of moved sections name the new file | One of the two skills that load the document at Step 0 | REQ-003; AC-3 | `issue-to-plan/workflow.md:25,78,353,408,728` (checked in Step 3) | N/A: documentation (`tools/check_skills_references.py`) | Verified |
| skills/plan-to-implementation-procedure/workflow.md | modify: Step 0 loads `rules/skill-runtime.md` instead of `skills/DESIGN.md`; the Allowed file operations citation names the new file | The second skill that loads the document at Step 0 | REQ-003; AC-3 | `plan-to-implementation-procedure/workflow.md:37,82` (checked in Step 3) | N/A: documentation (`tools/check_skills_references.py`) | Verified |
| prompts/01_issue-to-plan.md | modify: the Output language reference names `rules/skill-runtime.md` | The prompt cites the moved section | REQ-003; AC-3 | `prompts/01_issue-to-plan.md:33` (checked in Step 3) | N/A: documentation | Verified |
| prompts/02_plan-to-implementation-procedure.md | modify: the Output language reference names `rules/skill-runtime.md` | The prompt cites the moved section | REQ-003; AC-3 | `prompts/02_plan-to-implementation-procedure.md:27` (checked in Step 3) | N/A: documentation | Verified |
| tools/check_skill_size_baseline.txt | create: the recorded per-file ceilings and the measurement header, written last by `--update-baseline` | The check needs its baseline, recorded after Stage 2 so it holds the final sizes | REQ-004; AC-4 | `tools/check_module_size_baseline.txt` (baseline file model; checked in Step 3) | `tests/tools/test_check_skill_size.py` | Verified |

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

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| tools/check_module_size.py | The baseline model to mirror and the helpers to reuse; its `main` is complexity D (30), so the new tool extracts helpers instead | tools/check_skill_size.py, REQ-001 |
| tools/check_module_size_baseline.txt | The baseline file format (`<relpath>\t<size>`, `#` comments) | tools/check_skill_size_baseline.txt, REQ-004 |
| tools/check_config_comment_length.py | The latest example of a tool wired into a gate and CI | REQ-002 |
| tools/check_skills_references.py | Verifies that every referenced path resolves; must stay green after the moves | REQ-003 |
| tools/check_skills_heading_cycles.py | Verifies reference cycles between documents; the pointers in `DESIGN.md` and the new rule file must not form one | REQ-003 |
| tools/check_tool_descriptions_sync.py | Requires a `TOOL_DESCRIPTIONS.md` row for every tool | REQ-002 |
| skills/issue-creator/SKILL.md | Loads the whole `skills/DESIGN.md` for other sections (Evidence labels and similar), which stay there | REQ-003 |
| skills/code-implementation/SKILL.md | Cites `skills/DESIGN.md` Out-of-scope paths; valid through the pointer | REQ-003 |

## Acceptance Criteria
- `AC-1` (REQ-001): `uv run python tools/check_skill_size.py` passes on the final tree; its tests cover an over-limit file, growth past a baseline entry, a stale entry, a shrunk file, `--update-baseline`, `--no-baseline`, and a malformed baseline line.
- `AC-2` (REQ-002): `uv run python tools/run_validation_gates.py drift`, `uv run python tools/check_tool_descriptions_sync.py`, and `tests/tools/test_run_validation_gates.py` pass with the gate, CI step, and table rows added.
- `AC-3` (REQ-003): `rules/skill-runtime.md` contains the five sections verbatim; each moved heading in `skills/DESIGN.md` remains with a one-line pointer; `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` report no issues; the Step 0 lists of the two skills name `rules/skill-runtime.md`.
- `AC-4` (REQ-004): The baseline file holds the final sizes and the measurement header; the measured per-invocation load of `plan-to-implementation-procedure` and of `issue-to-plan` is at least 12 KB lower than the 2026-11-23 figures in Background.

## Tests
- Unit: `uv run pytest tests/tools/test_check_skill_size.py -q` for the failure cases (REQ-001).
- Gate wiring: `uv run pytest tests/tools/test_run_validation_gates.py -q` and `uv run python tools/run_validation_gates.py drift` (REQ-002).
- Reference checks: `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` (REQ-003).
- Measurement: the per-invocation load before and after, computed from the Step 0 file lists with the same method as Background (REQ-004).
- `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, and the full test suite, per `rules/toolchain.md`.

## Documentation Impact
N/A: no `docs/*.md` change; the changed documents are the tool inventory (`tools/TOOL_DESCRIPTIONS.md`), the gate table (`rules/tool-gates.md`), the skills and prompts named in the rows, and the new runtime rule file.

## Assumptions
- The default limit of 16,384 B is a judgment: it is two thirds of the module size gate and leaves the 18 files over it to the baseline; it is recorded as UNK-01 and can be changed by one constant.
- The check covers `skills/**/*.md`, `rules/*.md`, `prompts/*.md`, `templates/*.md`, `routing.md`, `AGENTS.md`, and `CLAUDE.md`; implementation-procedure and plan documents are work items, not instructions, and are excluded.
- Moving the five sections is a move, not a rewording: the new file carries the text verbatim and the pointers in `skills/DESIGN.md` only name the new file.
- The per-invocation estimates divide bytes by four; the 12 KB target is stated in bytes so it does not depend on a tokenizer.
- The other skills that cite the moved sections (about 30 files) are not edited; their citations stay valid through the pointers.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Is 16,384 B the right default limit for an instruction file | Only the current size distribution (18 of 71 files over it) was inspected | One constant in the tool; the maintainer can change it without changing the design | False |
| UNK-02 | Whether `check_skills_heading_cycles.py` reports a cycle between the `DESIGN.md` pointer lines and the new rule file | The tool reports no issue today, but the pointers add new cross references | Run the tool after the move; if it reports a cycle, make the pointers plain text without a path link | False |
| UNK-03 | The real token count of one invocation (the estimate divides bytes by four) | No tokenizer count | Out of scope here; the byte target does not depend on it | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tools/check_skill_size.py | Create | Low | N/A: new file | High (single maintainer >70%) | none (tools/ is not deployed) |
| tests/tools/test_check_skill_size.py | Create | Low | N/A: new file | High (single maintainer >70%) | none (tests) |
| tools/TOOL_DESCRIPTIONS.md | Modify | Low | 73 | High (single maintainer >70%) | none (documentation) |
| tools/_validation_gate_defs.py | Modify | Medium | 9 | High (single maintainer >70%) | none (tools/ is not deployed) |
| rules/tool-gates.md | Modify | Low | 2 | High (single maintainer >70%) | none (documentation) |
| .github/workflows/ci.yml | Modify | Medium | 10 | High (single maintainer >70%) | none (CI only) |
| rules/skill-runtime.md | Create | Medium | N/A: new file | High (single maintainer >70%) | none (documentation) |
| skills/DESIGN.md | Modify | Medium | 2 | High (single maintainer >70%) | none (documentation) |
| skills/issue-to-plan/workflow.md | Modify | Medium | 15 | High (single maintainer >70%) | none (documentation) |
| skills/plan-to-implementation-procedure/workflow.md | Modify | Medium | 11 | High (single maintainer >70%) | none (documentation) |
| prompts/01_issue-to-plan.md | Modify | Low | 1 | High (single maintainer >70%) | none (documentation) |
| prompts/02_plan-to-implementation-procedure.md | Modify | Low | 0 | High (single maintainer >70%) | none (documentation) |
| tools/check_skill_size_baseline.txt | Create | Low | N/A: new file | High (single maintainer >70%) | none (tools/ is not deployed) |

## Design
- **New tool**: `tools/check_skill_size.py` collects the covered files with a small `collect_covered(root)` helper, compares them with the limit and the baseline in a `evaluate(sizes, baseline, limit)` helper that returns violations, stale entries, and shrunk files, and keeps `main` thin (the model's `main` is complexity D (30)). `load_baseline` and `write_baseline` come from `tools/check_module_size.py` (a sibling import, as `tools/generate_reference_table.py` imports `_agent_config_migration`). Exit codes follow the model: 0 clean, 1 violation or stale entry. Messages name the file, its size, the limit or ceiling, and the remedy (move the branch to an edge-case file, or lower via `--update-baseline`).
- **Baseline semantics**: a ceiling, not a license (same as the module gate): growth fails, shrink is reported, a stale entry fails, `--update-baseline` rewrites from the current violations; the header comment lines carry the measurement. The baseline is recorded after Stage 2 (last row) so it holds the final sizes; the earlier rows pass without it because the gate row and the CI row form a release unit with the baseline row.
- **Runtime split**: copy the five sections verbatim into `rules/skill-runtime.md` under their original headings; in `skills/DESIGN.md` replace each moved body with one line `Moved to rules/skill-runtime.md (section: <name>).` and keep the heading. Update only the two skills' Step 0 lists and their inline citations of moved sections, plus the two prompts' Output language lines. The `Analysis-only phase constraint` citation in `skills/issue-creator/SKILL.md` and other skills stays valid through the pointer.
- **Alternatives**: a section-reading tool instead of a new rule file (rejected: more code and the same indirection); moving all of `skills/DESIGN.md` to `rules/` (rejected: it is cited as a design document from many places and a rename breaks them); one baseline entry per covered file (rejected: a file just under the limit can grow to it, which the limit bounds, and the file would be noisy).
- **Consumer scan** (Step 3): no symbol, schema, or public API changes; the moved sections are cited by name from 54 files, which the pointers keep valid. Predictable fallout: module size (`tools/check_skill_size.py` stays far below 24,576 B), pinned counts (no test pins the gate count; `tests/tools/test_run_validation_gates.py` checks that every CI lint command has a gate, which row 6 and row 4 satisfy together), tool inventory (row 3), generated blocks (none: the changed files are outside the generated-reference domains).
- **Persisted schema check**: not applicable.

## Implementation steps
1. **Phase 1: Size-check tool**
   - [ ] Create the tool with its helpers (REQ-001; tools/check_skill_size.py)
   - [ ] Create its unit tests, including the failure cases (REQ-001; tests/tools/test_check_skill_size.py)
2. **Phase 2: Wiring**
   - [ ] Add the tool rows to the inventory (REQ-002; tools/TOOL_DESCRIPTIONS.md)
   - [ ] Add the gate (REQ-002; tools/_validation_gate_defs.py), the tool-gate row (REQ-002; rules/tool-gates.md), and the CI step (REQ-002; .github/workflows/ci.yml)
3. **Phase 3: Runtime split**
   - [ ] Create the runtime rule file and add the pointers in the design document (REQ-003; rules/skill-runtime.md, skills/DESIGN.md)
   - [ ] Point the two skills and their prompts at the new file (REQ-003; skills/issue-to-plan/workflow.md, skills/plan-to-implementation-procedure/workflow.md, prompts/01_issue-to-plan.md, prompts/02_plan-to-implementation-procedure.md)
4. **Phase 4: Baseline and verification**
   - [ ] Record the baseline with `--update-baseline` and the measurement header (REQ-004; tools/check_skill_size_baseline.txt)
   - [ ] Run the validation sequence in `rules/toolchain.md`, the reference checkers, and the gates; compute the per-invocation load before and after (REQ-001 to REQ-004). No deploy step: no `scripts/` or `config/` change.

### Release units
**Unit**: skill-size-gate | **Phases**: 2, 4 | **Reason**: the gate and the CI step fail until the baseline file exists, and the baseline records the sizes after Phase 3, so the wiring and the baseline cannot be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/check_skill_size.py, tests/tools/test_check_skill_size.py | Unit | `uv run pytest tests/tools/test_check_skill_size.py -q`; `uv run ruff check tools/check_skill_size.py`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | Pass; coverage of the new tool at least 90 percent on changed lines |
| Gate, CI, inventory, tool-gate row | Drift | `uv run python tools/run_validation_gates.py drift`; `uv run python tools/check_tool_descriptions_sync.py`; `uv run pytest tests/tools/test_run_validation_gates.py -q` | Pass |
| rules/skill-runtime.md, skills/DESIGN.md, workflows, prompts | Reference | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | No issues |
| Baseline | Gate | `uv run python tools/check_skill_size.py`; `uv run python tools/run_validation_gates.py` | Pass |
| Whole repository | Full | `uv run pytest tests/ -n logical -m "not integration and not production_paths_allowed and not repo_scan"`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | Pass |

## Risks
- **Risk**: A moved section is reworded or lost → **Mitigation**: copy verbatim; a before and after diff of the five section texts is part of the verification, and the pointers keep every citation resolvable.
- **Risk**: The pointer lines and the new file form a reference cycle that `check_skills_heading_cycles.py` rejects → **Mitigation**: UNK-02; plain-text pointers without a path link if needed.
- **Risk**: The CI step lands before the baseline and turns CI red → **Mitigation**: the release unit `skill-size-gate` orders the baseline row last and the commit carries all rows together.
- **Risk**: Other sessions edit `skills/` or `rules/` while this runs and the recorded sizes go stale → **Mitigation**: record the baseline last, from the final tree, and rerun `--update-baseline` once before the commit.
- **Risk**: High churn on `tools/TOOL_DESCRIPTIONS.md` (73 commits) conflicts with parallel work → **Mitigation**: the edit is two added rows; land it with the rest in one commit.
- **Risk**: The new tool's `main` grows complex like the model's (D (30)) → **Mitigation**: helpers for collection and evaluation; `radon cc` is part of the validation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Size-check tool | In Progress | — | — |  |
| 2 | Phase 2: Wiring | In Progress | — | — |  |
| 3 | Phase 3: Runtime split | In Progress | — | — |  |
| 4 | Phase 4: Baseline and verification | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261123-160210_01_tools_check_skill_size.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261123-160210_02_tests_tools_test_check_skill_size.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261123-160210_03_tools_TOOL_DESCRIPTIONS.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261123-160210_04_tools__validation_gate_defs.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261123-160210_05_rules_tool-gates.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261123-160210_06_.github_workflows_ci.yml.md | 2 | Procedure | Pending | — | — |
| implementations/20261123-160210_07_rules_skill-runtime.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261123-160210_08_skills_DESIGN.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261123-160210_09_skills_issue-to-plan_workflow.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261123-160210_10_skills_plan-to-implementation-procedure_workflow.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261123-160210_11_prompts_01_issue-to-plan.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261123-160210_12_prompts_02_plan-to-implementation-procedure.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261123-160210_13_tools_check_skill_size_baseline.txt.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261123-155457_skillsize001_compress-skill-workflows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261123-155813
- **Related target files**: tools/check_skill_size.py, tests/tools/test_check_skill_size.py, tools/TOOL_DESCRIPTIONS.md, tools/_validation_gate_defs.py, rules/tool-gates.md, .github/workflows/ci.yml, rules/skill-runtime.md, skills/DESIGN.md, skills/issue-to-plan/workflow.md, skills/plan-to-implementation-procedure/workflow.md, prompts/01_issue-to-plan.md, prompts/02_plan-to-implementation-procedure.md, tools/check_skill_size_baseline.txt

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (Stage 1); `check_module_size.py` model | tools/check_skill_size.py | 1 | AC-1 | `test_check_skill_size.py` | Confirmed by repository evidence |
| REQ-001 | Issue Testing Expectations (unit tests incl. failure cases) | tests/tools/test_check_skill_size.py | 1 | AC-1 | itself | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (Stage 1 gate wiring); config comment lint precedent | tools/TOOL_DESCRIPTIONS.md | 2 | AC-2 | `check_tool_descriptions_sync.py` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (Stage 1 gate wiring) | tools/_validation_gate_defs.py | 2 | AC-2 | `test_run_validation_gates.py` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (Stage 1 gate wiring) | rules/tool-gates.md | 2 | AC-2 | `run_validation_gates.py drift` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (Stage 1 CI) | .github/workflows/ci.yml | 2 | AC-2 | `test_run_validation_gates.py` | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes (Stage 2); measured section sizes | rules/skill-runtime.md | 3 | AC-3 | `check_skills_references.py` | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes (Stage 2); 115 section citations | skills/DESIGN.md | 3 | AC-3 | `check_skills_references.py` | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes (Stage 2); Step 0 list | skills/issue-to-plan/workflow.md | 3 | AC-3 | `check_skills_references.py` | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes (Stage 2); Step 0 list | skills/plan-to-implementation-procedure/workflow.md | 3 | AC-3 | `check_skills_references.py` | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes (Stage 2); prompt citation | prompts/01_issue-to-plan.md | 3 | AC-3 | `check_skills_references.py` | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes (Stage 2); prompt citation | prompts/02_plan-to-implementation-procedure.md | 3 | AC-3 | `check_skills_references.py` | Confirmed by repository evidence |
| REQ-004 | Issue Acceptance Criteria (size-budget check passes; reduction measured) | tools/check_skill_size_baseline.txt | 4 | AC-4 | `check_skill_size.py` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261123-160210 -->