## Goal
- Make the two `tools/TOOL_DESCRIPTIONS.md` rows for `tools/run_validation_gates.py` match the runner: no `--fast` option, no stop-at-first-failure claim across gates, and every other claim of both rows confirmed against the code.

## Priority
Low

## Scope
- **In-Scope**: the two rows of `tools/TOOL_DESCRIPTIONS.md` that describe `run_validation_gates.py`, and the recorded confirmation of each claim they keep.
- **Out-of-Scope**: changing the runner's behavior or options (no `--fast`, no stop-at-first-failure mode); other rows of the descriptions file; the same status wording in `routing.md`, the runner's module docstring, and its `--help` text (UNK-02).
- **Dependencies**: the gate-output Plan also rewrites these two rows (its documentation phase), so this Plan lands after that phase and verifies the final text once (structured line below).
  - **Depends on**: plans/20261117-125737_wftool006_gate-output-noise.md | phase 4 | rewrites the same two runner rows for the new default output and the `--verbose` flag

## Background
Filed as a follow-up of the gate-output Plan (its UNK-02). The same drift was noted on 2026-11-02 in an archived procedure for this file ("not changed here") and was never tracked as an issue.

## Problem
`uv run python tools/run_validation_gates.py --help` lists `--base`, `--full`, `--jobs`, `--verbose`, and the `drift` subcommand; there is no `--fast` (`Explicit in code`, `Operationally observed` in this cycle; `--verbose` was added by the prerequisite Plan, re-verified 20261118). The default mode is fast, selected by the absence of `--full`. The rows state `--fast`/`--full` and "stops non-zero on the first `Fail`" (`Explicit in code`, lines 147 and 260 of `tools/TOOL_DESCRIPTIONS.md` after the prerequisite Plan's documentation phase, re-verified 20261118).

Checked against the code in this cycle, the stop claim is partly true and the issue's replacement wording has to keep that:
- Across gates the runner runs every selected gate and returns `1` when any result is `Fail`, else `0` (`_run_gates`, `Explicit in code`).
- Within one gate, `run_gate` runs its commands in order and stops at the first non-zero exit (`Explicit in code`, its docstring).

Further claims of the rows that do not match the code (found while verifying "every other claim", beyond the issue's text):
- The rows say changed files come "from `git diff <base>`". The runner diffs staged changes against the base and unstaged changes against the index, keeps only added, modified, renamed, and copied paths (`--diff-filter=AMRC`), and so never sees untracked or deleted files (`_changed_files`, `Explicit in code`).
- The rows say the runner prints one `Pass`/`Fail`/`Partial`/`Not available`/`Blocked` summary. `classify` can return only `Pass`, `Fail`, and `Not available`; `Partial` and `Blocked` are in the vocabulary tuple but no code path produces them (`Explicit in code`).
- The second row says it prints "the failing command". The summary prints every gate's command with its status, and a `Fail` row carries the exit code as its detail (the renderer is `tools/_validation_gate_report.py` since the prerequisite Plan landed, and the runner builds the `exit code` detail in `run_gate`; re-verified 20261118 in place of the `_print_summary` this Plan first cited).

## Reason for Change
- A reader who copies `--fast` from the description gets an argument error, and one who relies on stop-at-first-failure misreads a run that reports every failure. A reader who expects untracked files to be validated gets no gate for a new file.
- The drift has stood since 2026-11-02, so it does not correct itself. The severity is low.

## Implementation Intent
- The rows describe the options, the discovery, the statuses, and the failure behavior that the code has, and nothing they state about the runner is left unverified.
- Documentation follows the code; the other copies of the status wording are reported, not edited here (UNK-02).

## Requirements
- `REQ-001`: Neither row mentions `--fast`; they state that fast mode is the default and `--full` adds the `rules/toolchain.md` sequence.
- `REQ-002`: Both rows state that the runner runs every selected gate, reports each result, and exits `1` when any gate is `Fail` (otherwise `0`), and that within one gate the commands stop at the first non-zero exit.
- `REQ-003`: Both rows state how changed files are discovered (staged against the base, unstaged against the index, added, modified, renamed, and copied paths only) and which statuses the runner produces (`Pass`, `Fail`, `Not available`).
- `REQ-004`: Each remaining claim of both rows is confirmed against `--help` or the code, and the confirmation is recorded in the commit message body or the review; `tools/check_tool_descriptions_sync.py` passes.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Correct the two `run_validation_gates.py` rows | The rows name `--fast`, claim a stop at the first `Fail`, describe discovery as `git diff <base>`, and list five statuses | REQ-001, REQ-002, REQ-003, REQ-004 / AC-1, AC-2, AC-3, AC-4 | Lines 147 and 260 (re-verified 20261118 after the prerequisite Plan's documentation phase); `--help` lists `--base`, `--full`, `--jobs`, `--verbose`, `drift`; `_changed_files` (`--diff-filter=AMRC`, staged against the base and unstaged against the index), `classify` (produces only `Pass`, `Fail`, `Not available`), `run_gate` (stops at the first non-zero exit within a gate), and `_run_gates` (runs every gate, exits 1 when any is `Fail`) in `tools/run_validation_gates.py` (re-verified 20261118) | `tools/check_tool_descriptions_sync.py` | Verified |

Revalidation (20261118, plan-to-implementation-procedure Step 3a): every claim of the target-row
evidence was re-checked against the current code and `--help` output; only the two line numbers
and the `--help` flag list changed (the prerequisite Plan's documentation phase landed, all its
steps `Completed`). The dependency on that Plan is satisfied.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/run_validation_gates.py` | The behavior every claim is checked against (`_changed_files`, `run_gate`, `run_gates`, `classify`, `_run_gates`, the parser) | `tools/TOOL_DESCRIPTIONS.md` / REQ-001 to REQ-004 |
| `tools/_validation_gate_defs.py` | The `Gate` type (`exclusive`, `requires_context`) and the routing gate table the rows summarize | `tools/TOOL_DESCRIPTIONS.md` / REQ-004 |
| `rules/toolchain.md` | The canonical sequence that full mode adds | `tools/TOOL_DESCRIPTIONS.md` / REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001): `rg -n -- "--fast" tools/TOOL_DESCRIPTIONS.md` reports nothing for the runner rows, and the rows name fast mode as the default.
- AC-2 (REQ-002): Neither row says the runner stops at the first failure across gates; both state the all-gates run, the exit code rule, and the per-gate stop (review against `run_gates` and `run_gate`).
- AC-3 (REQ-003): The rows' discovery and status statements equal what `_changed_files` and `classify` do (review).
- AC-4 (REQ-004): Each remaining claim is listed with its confirming source in the commit message body or the review, and `tools/check_tool_descriptions_sync.py` passes.

## Tests
N/A: documentation-only. The sync checker and the claim-by-claim review replace tests (REQ-004).

## Documentation Impact
N/A for `docs/*.md`: no file under `docs/` changes. The two rows of `tools/TOOL_DESCRIPTIONS.md` are the change (REQ-001 to REQ-004).

## Assumptions
- The rows are re-read after the gate-output Plan's documentation phase, because that Plan changes the default output and adds a flag; this Plan's text is final only after it.
- Stop-at-first-failure was never a runner mode: the code and `rules/toolchain.md` describe a run of all selected gates, so the documentation changes and the code does not.
- Overlap with the gate-output Plan on the two rows is a sequencing dependency, declared above. Overlap on the file with the other tooling Plans is row-level.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether stop-at-first-failure was ever intended | No design record found; the code and `rules/toolchain.md` describe all selected gates | None needed: documentation follows the code | False |
| UNK-02 | The same five-status wording appears in `routing.md` (the runner row), the runner's module docstring, and its `--help` description, although only three statuses are produced | Whether the vocabulary is kept deliberately for the canonical set of `rules/ai-execution.md` | Report it to the owner after this Plan lands; a separate issue covers any change outside the two rows | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low: two documentation rows read by the sync checker | N/A: Path A | N/A: Path A | not applicable (rsynced) |

## Design
**Classification**: Path A (one target row, documentation only). Step 3's direct verification ran once; the validation baseline is `N/A: no Python target`.
- **Direct verification**: the claims above were checked against `tools/run_validation_gates.py` and its `--help` output; nothing imports the descriptions file except the sync checker.
- **Decision, wording**: state the observable behavior (all gates run, exit rule, per-gate stop, discovery, produced statuses) instead of removing the sentences, so a reader keeps the information the old rows tried to give.
- **Baseline**: N/A: no Python target.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Verify the claims**
   - [ ] Re-read the two rows after the gate-output Plan's documentation phase and list each claim with its source in `--help` or the code (REQ-004; `tools/TOOL_DESCRIPTIONS.md`)
2. **Phase 2: Correct the rows**
   - [ ] Remove `--fast`, state the default mode and `--full`, the all-gates run and exit rule, the per-gate stop, the discovery, and the produced statuses (REQ-001, REQ-002, REQ-003; `tools/TOOL_DESCRIPTIONS.md`)
3. **Phase 3: Verification** (no deploy step: no `scripts/` or `config/` file changes)
   - [ ] Run `tools/check_tool_descriptions_sync.py`, record the confirmation list in the commit message body, and report UNK-02 (REQ-004; `tools/TOOL_DESCRIPTIONS.md`)

### Release units
N/A: no release unit; each phase passes validation alone when applied in order.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Claim-by-claim review; doc consistency | `uv run python tools/run_validation_gates.py --help`; `uv run python tools/check_tool_descriptions_sync.py`; `rg -n -- "--fast" tools/TOOL_DESCRIPTIONS.md` | Rows match `--help` and the code; no finding; no runner row names `--fast` |

## Risks
- **Risk**: The gate-output Plan changes the runner output after this text is final → **Mitigation**: the Plan depends on that Plan's documentation phase and re-reads the rows in Phase 1.
- **Risk**: Newly written claims are wrong in turn → **Mitigation**: each claim gets a recorded source before it is kept (REQ-004).
- **Risk**: `tools/TOOL_DESCRIPTIONS.md` has very high churn → **Mitigation**: change only the two rows and rebase through the commit skill.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify each claim of the two rows against `--help` and the code | In Progress | — | — |  |
| 2 | Correct the two rows | In Progress | — | — |  |
| 3 | Verification: sync check, confirmation record, report the other copies | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261118-072236_01_tools_TOOL_DESCRIPTIONS.md.md | 1, 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-132203_wftoolfu003_runner-description-drift.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261117-134238
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (remove `--fast`, state the default mode) | `tools/TOOL_DESCRIPTIONS.md` | Phase 2 | AC-1 | `rg` for `--fast`; `--help` | Explicit in issue |
| REQ-002 | Required Changes (state the all-gates run and exit rule); `run_gate` evidence | `tools/TOOL_DESCRIPTIONS.md` | Phase 2 | AC-2 | review against `run_gates` and `run_gate` | Derived from confirmed evidence |
| REQ-003 | Required Changes (verify every other claim); `_changed_files` and `classify` evidence | `tools/TOOL_DESCRIPTIONS.md` | Phase 2 | AC-3 | review against `_changed_files` and `classify` | Derived from confirmed evidence |
| REQ-004 | Required Changes (verify and run the sync check); Acceptance Criteria | `tools/TOOL_DESCRIPTIONS.md` | Phase 1, Phase 3 | AC-4 | `tools/check_tool_descriptions_sync.py`; confirmation record | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261118-072236 -->