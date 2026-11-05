# Plan: cliview002 — single shared StdinReader so a line typed after a multiline timeout reaches the next read

## Goal
- Make post-timeout stdin hand-off deterministic: after `CLIView.read_multiline` times out on a continuation read, a line typed at the next prompt is delivered to the next pending stdin read instead of being swallowed and discarded by the stale reader thread, by wiring every interactive stdin call site to one process-shared `StdinReader` instance.

## Priority
Medium

## Scope
- **In-Scope**: one process-shared `StdinReader` instance (module-level accessor in `scripts/agent/stdin_reader.py`), wired at the three call sites that currently own separate instances (`scripts/agent/cli_view.py`, `scripts/agent/repl_input_loop.py`, `scripts/agent/tool_approval.py`); regression tests for the timeout-then-fresh-read path; documentation of the post-timeout hand-off guarantee in the REPL-IO chapter; deployment hand-off.
- **Out-of-Scope**: the `cliview001` timeout-return change itself (already implemented); changing `_INPUT_TIMEOUT_S` (30s) or the EOF/KeyboardInterrupt branch; any change to `scripts/agent/startup.py`, `scripts/agent/repl.py`, `scripts/agent/resource_shutdown_coordinator.py`, `scripts/agent/context.py` (Explicit in issue).
- **Dependencies**: follow-up to `issues/20261003-180327_cliview001_multiline-input-timeout-crashes-repl.md` (archived in `issues/done/`) / Plan `plans/done/20261101-142849_cliview001_multiline-input-timeout-crashes-repl.md` (archived, `Completed`). The dependency is closed: its UNK-01 resolution path ("file a separate Issue ... and amend this Plan only if it must change a target file") is satisfied by this follow-up Plan without amending the archived Plan (verified in Step 2/6).
  - No `Depends on` line: no active Plan or open Issue gates this Plan's phases.

## Background
`CLIView.read_multiline` wraps each continuation read in `asyncio.wait_for(..., timeout=_INPUT_TIMEOUT_S)` (confirmed: `scripts/agent/cli_view.py` L286-288; timeout branch logs and `break`s at L290-291, the `cliview001` change). Each of `CLIView` (prompt `... `, L115), `ReplInputLoop` (prompt `> `, L70) and `tool_approval` (lazy default, L130) owns a **separate** `StdinReader` daemon-thread instance. `cliview001`'s Unknown UNK-01 asked whether a line typed after the timeout reaches the next read; its pty-based resolution (Plan `Execution Status` step 3, `20261104-165630`) confirmed it does not — the stale `... ` worker, still blocked in C-level `input()`, consumes the keypress, finds its own instance's waiter cleared, discards the line, and cliview002 was filed.

## Problem
`asyncio.wait_for` cancellation cannot interrupt the blocking `input()` running on the worker thread (confirmed by repository evidence: `StdinReader` docstring in `scripts/agent/stdin_reader.py` — "The worker never reads ahead ... A line that arrives after its request was cancelled goes to the newest pending request, and is discarded when none exists" — and `tests/agent/test_stdin_reader.py::TestCancelledRequestDelivery`). Within one instance this hand-off is already correct and tested; across instances the stale thread swallows the tty line for the other instance's next read, so every multiline timeout silently drops the user's next line (pty smoke test recorded in the source Issue: supplied `z` never reached the second read).

## Reason for Change
`cliview001` made timeouts return partial text instead of ending the process, so the post-timeout stdin path is now a normal, recurring user flow; the confirmed line-loss must be fixed rather than left as a Known Issue.

## Implementation Intent
Eliminate cross-instance tty competition instead of trying to cancel an uncancellable `input()`: expose one process-shared `StdinReader` (module-level accessor with a test reset hook) in `scripts/agent/stdin_reader.py`, and have all three call sites read through that single instance with per-call `read(prompt=...)`. The instance-internal cancellation semantics (stale blocked `input()` delivers to the newest waiter) then guarantee the hand-off without changing `StdinReader.read`'s contract.

## Requirements
- `REQ-001`: After a mid-continuation `read_multiline` timeout, a line supplied at the next prompt completes the next pending read (joined text returned); no second timeout and no discarded line.
- `REQ-002`: At most one `StdinReader` worker thread in the REPL process can be blocked in `input()` at any time — `CLIView`, `ReplInputLoop`, and `tool_approval` all read through one shared instance; `StdinReader.read()`'s contract (one read per worker, "already pending" refusal while a request is outstanding, daemon-thread process-exit guarantee, no thread leaks, no read-ahead) is unchanged.
- `REQ-003`: `read_multiline`'s public signature and return contract are unchanged; `_INPUT_TIMEOUT_S` (30s) and the EOF/KeyboardInterrupt branch are unchanged.
- `REQ-004`: Regression tests cover the timeout-then-fresh-read path (mirroring the pty scenario with a fake `input`) and shared-instance identity across the three call sites; `tests/agent/test_stdin_reader.py` and `tests/test_cli_view.py` existing tests pass unchanged.
- `REQ-005`: The REPL-IO chapter documents the post-timeout hand-off guarantee (replacing the Issue's "Known Issue" placeholder intent, since this Plan fixes the behavior).
- `REQ-006`: Deployment hand-off per `skills/deploy/SKILL.md` after the change is committed and pushed (user's decision; approval gate).

## Implementation Target Files
**Freeze status**: Frozen (validated by `issue-to-plan` Step 8's Implementation Target
Files Validation — all rows `Verified` against current source, checked in Step 2/3/8b;
see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/stdin_reader.py | Add a module-level shared-`StdinReader` accessor plus a test reset hook; class semantics unchanged | The three call sites own separate instances; one shared instance is the fix carrier | REQ-002 | Class `StdinReader` in this file: docstring states one daemon thread, one read per request, cancelled-request delivery to the newest request or discard; no module-level accessor exists today (checked in Step 2/3) | `tests/agent/test_stdin_reader.py` | Verified |
| scripts/agent/cli_view.py | Replace the instance-owned `StdinReader(prompt="... ")` (L115) with the shared instance; `read_multiline` continuation read (L286-288) calls `read(prompt="... ")` on it | Stale `... ` worker swallowing the next tty line is the confirmed loss mechanism | REQ-001, REQ-002, REQ-003 | Import at L20; `self._stdin_reader = StdinReader(prompt="... ")` at L115; `wait_for`/timeout `break` at L286-291; `_stdin_reader` referenced only by `read_multiline` (checked in Step 3) | `tests/test_cli_view.py` | Verified |
| scripts/agent/repl_input_loop.py | Replace `StdinReader(prompt="> ")` (L70) with the shared instance; pass `prompt="> "` at the read call sites (L145, L192) | Second competing reader instance in the REPL flow | REQ-001, REQ-002 | Import at L16; reader created at L70; `read()` at L145 and L192; `read_multiline` called at L198 (checked in Step 3) | `tests/agent/test_repl.py` | Verified |
| scripts/agent/tool_approval.py | Replace the lazy `_approval_reader = StdinReader()` (L130) with the shared instance | Third competing reader instance; same loss class for approval answers | REQ-002 | `from agent.stdin_reader import StdinReader`; `_approval_read` lazily creates a module-global reader at L130 and always passes a per-call prompt (checked in Step 3) | tests/agent/test_tool_approval_paths.py | Verified |
| tests/agent/test_stdin_reader.py | Add tests: shared accessor returns the same instance across call sites; reset hook restores isolation | New accessor surface needs direct coverage (REQ-002) | REQ-002, REQ-004 | Existing classes `TestRequestDrivenRead`, `TestCancelledRequestDelivery` (L43-136) prove the same-instance delivery semantics the shared instance relies on (checked in Step 2/3) | itself | Verified |
| tests/test_cli_view.py | Add the timeout-then-fresh-read regression test mirroring the pty scenario (patched `builtins.input`, shortened timeout) | Confirms REQ-001 end-to-end at the `read_multiline` surface | REQ-001, REQ-004 | File exists; `TestReadMultiline` (L99-136) already drives `read_multiline` through patched `builtins.input` (checked in Step 3); adversarial re-check (this cycle): a `TestReadMultilineTimeout` class (same file) already covers the timeout→partial-return path with patched `builtins.input` + `release.wait` synchronization — the new test reuses that synchronization pattern and targets only the not-yet-covered next-read delivery path | itself | Verified |
| docs/23_agent/agent_07_05_cli-and-commands-repl-io.md | Add one paragraph stating the post-timeout hand-off guarantee (next pending read receives the next line via the single shared reader) | Issue Documentation Impact: the agent reference chapter for this behavior exists | REQ-005 | File exists (57 lines); L52 already documents the `> ` prompt and `... ` continuation prompt; resolved via `docs/00_index.md` "CLI view / readline" row (checked in Step 3) | N/A: docs checker in Validation plan | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/repl.py | Constructs `CLIView` (L79) and the input loop; confirms the shared-accessor design needs no construction-site change (file is out-of-scope per Issue) | REQ-002 (design justification) |
| tests/agent/test_repl.py | testmon records 4 tests executing `scripts/agent/stdin_reader.py`; regression surface for the input-loop rewiring | REQ-001, REQ-004 |
| tests/agent/test_repl_error_handling.py | testmon records 1 test executing `scripts/agent/stdin_reader.py`; regression surface | REQ-004 |
| tests/agent/test_tool_approval_paths.py | Mocks `agent.tool_approval._approval_read` at function level (L123, L148), so the shared-instance rewiring needs no test edit; must be read to confirm this | REQ-002, REQ-004 |
| docs/23_agent/agent_12_reference-api.md | CLIView API-index block (L164-173) — `read_multiline` signature is unchanged by REQ-003, so no edit is required; read to confirm | REQ-003 |
| plans/done/20261101-142849_cliview001_multiline-input-timeout-crashes-repl.md | UNK-01 record, its pty resolution, and the same-instance delivery design note (L88) | Background, REQ-001 |

## Acceptance Criteria
- AC-1 (`REQ-001`): With a shortened timeout, a `read_multiline` continuation times out and returns the partial text; a line then supplied reaches the next pending read and completes it (no second timeout, no discarded line).
- AC-2 (`REQ-002`): `CLIView`, `ReplInputLoop` and `tool_approval` read through one shared `StdinReader` instance (asserted identity in `tests/agent/test_stdin_reader.py`); no second reader instance is constructed by these modules.
- AC-3 (`REQ-003`): `read_multiline` and `StdinReader.read` signatures/contracts unchanged; `_INPUT_TIMEOUT_S` still 30s (code inspection + existing tests green).
- AC-4 (`REQ-004`): new tests pass; full `tests/agent/test_stdin_reader.py` and `tests/test_cli_view.py` pass unchanged; `tests/agent/test_repl.py` and the tool-approval suites pass.
- AC-5 (`REQ-005`): the REPL-IO chapter states the hand-off guarantee; docs checkers report no findings.

## Tests
- `REQ-001`/`REQ-004`: new `tests/test_cli_view.py` regression — patch `builtins.input` with a scripted sequence, monkeypatch `_INPUT_TIMEOUT_S` to a sub-second value, time out a `read_multiline` continuation, then start a fresh `read_multiline` and assert the supplied line is returned in its joined text (mirrors the pty scenario without a real tty).
- `REQ-002`: new `tests/agent/test_stdin_reader.py` tests — shared accessor identity, and reset-hook isolation so module state cannot leak across tests.
- `REQ-004`: regression — `uv run pytest tests/agent/test_stdin_reader.py tests/test_cli_view.py tests/agent/test_repl.py tests/agent/test_repl_error_handling.py tests/agent/test_tool_approval_paths.py tests/agent/test_tool_approval_concurrency.py` all green.
- Static gates per `rules/toolchain.md` (ruff, mypy, lint-imports, bandit, radon, module-size, diff-cover ≥90%).

## Documentation Impact
Yes — `REQ-005` drives one paragraph in the chapter resolved via `docs/00_index.md` "Document References by Task" row "CLI view / readline": `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` (the same row also lists `agent_07_02_cli-and-commands-cliview.md`; that chapter documents no stdin-timeout behavior today and is left unchanged). The Issue's "record as Known Issue until fixed" note is superseded because this Plan fixes the behavior; the chapter states the guarantee instead. `agent_12_reference-api.md` needs no change (API surface unchanged, confirmed in Step 3).

## Assumptions
- The archived `cliview001` Plan is not amended: it is `Completed` (all target rows implemented, step 5 deploy step excluded no deploy), and its UNK-01 resolution path explicitly prescribes filing this follow-up Issue instead of an amendment. The Issue's "requires amending the `cliview001` Plan" wording is corrected to: amendment is only needed if the fix landed in that Plan's target files, which it does not (this Plan carries the change).
- REPL stdin reads are sequential (no two genuinely concurrent stdin requests): `ReplInputLoop` awaits every read in order, and tool-approval prompts occur while no stdin read is pending; so routing all sites through one reader does not newly trip the "already pending" refusal.
- Patching `builtins.input` reaches the worker because `StdinReader` looks the default read function up at call time (`tests/agent/test_stdin_reader.py::test_default_read_function_is_looked_up_at_call_time`), so the regression tests need no fake-reader injection.
- Module-singleton test isolation is handled by the reset hook (Phase 1), not by fixture ordering. Extended by this cycle's Step 3a re-check: after the wiring lands, existing `CLIView`-constructing suites (`tests/test_cli_view.py`) share the module-level reader across tests, so their fixtures/setup must call the reset hook to keep cases isolated; the pre-existing `TestReadMultilineTimeout` class already covers timeout→partial-return and is left unchanged.
- `git-fame` produced no author rows for the target files on this host, so `Bus Factor` is `N/A` in `Affected areas`.
- No conflict with the active Plans under `plans/` was observed at Step 3 (their targets are session/compression/counter files); the Frozen overlap check runs at Step 8b.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Prompt visibility after a timeout: the shared worker's still-blocked `input()` printed the old `... ` prompt, so the next `> ` prompt is not re-echoed while the worker waits for the next keypress | No pty evidence for the shared-reader variant specifically | During implementation, re-run the cliview001 pty smoke scenario with the shared reader and confirm the existing "Multiline input timed out" warning makes the state clear to the user; if unclear, add one console warning line (within `cli_view.py`, already a target row) | False |
| UNK-02 | Issue open question "abandon (drop partial text) or retry on the next line": resolved by design as neither — partial text is still returned (unchanged `cliview001` behavior) and the abandoned read's next line is delivered to the next pending read | — | Resolved by repository evidence (`TestCancelledRequestDelivery`, `StdinReader` docstring) and recorded in Design; no further action | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/stdin_reader.py | Modify | Low (one new module-level accessor; class unchanged) | 1 | N/A | not applicable (rsynced) |
| scripts/agent/cli_view.py | Modify | Medium (all REPL turns pass through `read_multiline`; 1 construction site in repl.py untouched) | 3 | N/A | not applicable (rsynced) |
| scripts/agent/repl_input_loop.py | Modify | Medium (drives every REPL read; highest 30d churn of the three) | 5 | N/A | not applicable (rsynced) |
| scripts/agent/tool_approval.py | Modify | Low (approval path only; its tests mock at function level) | 5 | N/A | not applicable (rsynced) |
| tests/agent/test_stdin_reader.py | Modify | Low | N/A (test file) | N/A | not applicable (rsynced) |
| tests/test_cli_view.py | Modify | Low | 3 | N/A | not applicable (rsynced) |
| docs/23_agent/agent_07_05_cli-and-commands-repl-io.md | Modify | Low (docs only; high 30d docs churn raises merge-noise risk only) | 7 | N/A | not applicable (rsynced) |

## Design
- **Decision 1 — single process-shared `StdinReader` via module-level accessor** (chosen). Verified constraint: cancellation cannot interrupt the blocked C-level `input()` (`StdinReader` docstring; `TestCancelledRequestDelivery`; `cliview001` Plan design note L88). Therefore no worker-lifetime trick inside a *cancelled* request can free the tty; the only reliable invariant is that a single reader thread ever holds the blocking `input()`, after which the already-tested same-instance hand-off (stale blocked read delivers to the newest waiter, no second read started) fixes the loss. The accessor is created lazily in `scripts/agent/stdin_reader.py`, with a `reset` hook so unit tests can restore isolation between cases.
- **Alternatives considered**: (a) constructor-injection of one reader from the composition root — rejected: the composition site is `scripts/agent/repl.py` (L79), out-of-scope per the Issue; (b) per-request reader teardown/recreation — rejected: the abandoned thread stays blocked in `input()` and still swallows the next tty line; (c) masking in `cli_view.py` (e.g., draining) — rejected by the Issue's own preference and because it cannot make the swallowed line re-appear; (d) leaving `tool_approval.py` on its own instance — rejected: it is a third tty competitor found by Step 3's consumer scan (`rg "from agent.stdin_reader import"`, instantiation grep), and excluding it would leave the same loss class for approval answers.
- Consumer scan (`tools/scan_change_consumers.py --seed StdinReader`) candidates and their disposition: `scripts/agent/cli_view.py`, `scripts/agent/repl_input_loop.py`, `scripts/agent/tool_approval.py` — target rows; `tests/agent/test_stdin_reader.py`, `tests/test_cli_view.py` — target rows; `tests/agent/test_repl.py`, `tests/agent/test_repl_error_handling.py` (testmon candidates) — reference rows, read-only regression (no construction-site change in their fixtures); mock-level consumers in the tool-approval suites — reference row `tests/agent/test_tool_approval_paths.py` with confirmation that function-level mocks make them `not affected` by the instance change.
- Validation quality baseline (Step 5): `radon cc` on the three production targets — all functions A (1-1 complexity range, none above A shown at `-s` tail); `vulture scripts/ --min-confidence 80` — 2 findings, both in unrelated files (`scripts/rag/ingestion/document_manager.py`, `scripts/shared/runtime_paths.py`), none in the targets; `bandit -r scripts/ -c pyproject.toml` — exit 0 under the repo config (severity report is the pre-existing repo-wide baseline, run 20261104 in this session); `lint-imports` — 6 contracts kept, 0 broken (20261104, post-rebase tree). diff-cover baseline: working tree equals `master` at Plan generation (no changed lines yet), so no baseline percentage is meaningful at Plan time; the implementation phase MUST run `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master` without `--fail-under` to record the baseline and then at the `rules/toolchain.md` ≥90 threshold on the changed lines.
- Operational dependency inspection: not applicable — no MCP-server port or database file is touched (no `ss`/lock check needed); no dependency upgrades, so no `pip-audit`. Persisted-schema check: not applicable (no DDL/migration).

## Implementation steps
1. **Phase 1: Shared reader accessor**
   - [ ] Add the module-level shared-`StdinReader` accessor and test reset hook (REQ-002; scripts/agent/stdin_reader.py)
   - [ ] Add identity/isolation tests for the accessor (REQ-002, REQ-004; tests/agent/test_stdin_reader.py)
2. **Phase 2: Single-reader wiring and the regression test** (release unit with itself — the wiring and its test land together)
   - [ ] Rewire `CLIView` to the shared instance with per-call prompt (REQ-001, REQ-002, REQ-003; scripts/agent/cli_view.py)
   - [ ] Rewire `ReplInputLoop` to the shared instance with `prompt="> "` at its read call sites (REQ-001, REQ-002; scripts/agent/repl_input_loop.py)
   - [ ] Add the timeout-then-fresh-read regression test (REQ-001, REQ-004; tests/test_cli_view.py)
3. **Phase 3: Approval-path wiring**
   - [ ] Rewire `tool_approval` to the shared instance (REQ-002; scripts/agent/tool_approval.py); run the tool-approval suites as regression
4. **Phase 4: Documentation**
   - [ ] Add the hand-off guarantee paragraph to the REPL-IO chapter (REQ-005; docs/23_agent/agent_07_05_cli-and-commands-repl-io.md) and run the docs checkers per `routing.md`
5. **Phase 5: Deployment hand-off**
   - [ ] Hand off to `skills/deploy/SKILL.md` for the `scripts/` changes (REQ-006; scripts/agent/stdin_reader.py, scripts/agent/cli_view.py, scripts/agent/repl_input_loop.py, scripts/agent/tool_approval.py). Prerequisite: the change is committed and pushed first; deploying is the user's decision (approval gate).

### Release units
N/A: no release unit — each phase leaves the full existing suite green (Phase 2 carries its regression test in the same phase; the wiring and test cannot be split without an untested behavior change).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/stdin_reader.py | Unit (accessor identity, reset isolation) | `uv run pytest tests/agent/test_stdin_reader.py -v` | all tests pass |
| scripts/agent/cli_view.py | Unit (timeout-then-fresh-read regression, existing `TestReadMultiline` unchanged) | `uv run pytest tests/test_cli_view.py -v` | all tests pass, new regression included |
| scripts/agent/repl_input_loop.py | Integration regression via REPL tests | `uv run pytest tests/agent/test_repl.py tests/agent/test_repl_error_handling.py -q` | pass unchanged |
| scripts/agent/tool_approval.py | Regression (function-level mocks unaffected) | `uv run pytest tests/agent/test_tool_approval_paths.py tests/agent/test_tool_approval_concurrency.py -q` | pass unchanged |
| docs/23_agent/agent_07_05_cli-and-commands-repl-io.md | Docs gate | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent`, `generate_reference_table.py --check` | no findings; reference-table drift-free |
| all Python targets | Static gates | `uv run ruff format`, `uv run ruff check scripts/ tests/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | clean |
| all changed lines | Coverage gate | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master` (baseline, then `--fail-under=90`) | baseline recorded; ≥90% on changed lines |

## Risks
- **Risk**: routing all call sites through one reader newly trips the "already pending" refusal if any flow ever awaits two stdin reads at once → **Mitigation**: verified sequential flow (Step 3 inspection of `repl_input_loop.py` read sites and approval path); regression suites in the Validation plan cover the REPL and approval paths; refusal semantics themselves are unchanged per REQ-002.
- **Risk**: module-level singleton leaks blocked state across unit tests → **Mitigation**: the Phase 1 reset hook plus identity/isolation tests in `tests/agent/test_stdin_reader.py`.
- **Risk**: after a timeout the user sees no fresh prompt while the shared worker is still blocked in `input()` (UNK-01) → **Mitigation**: the existing `Multiline input timed out` warning line; pty confirmation during implementation (UNK-01 resolution path).
- **Risk**: `scripts/agent/repl_input_loop.py` is the highest-churn production target (5 commits/30d) → **Mitigation**: rewiring is a two-line change (construction + two prompt arguments) validated by its own regression suite in the same phase.
- **Risk**: `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` has high 30d docs churn (7 commits) → **Mitigation**: append-only single paragraph; docs checkers gate the edit.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: shared reader accessor in scripts/agent/stdin_reader.py + accessor tests in tests/agent/test_stdin_reader.py | In Progress | — | — |  |
| 2 | Phase 2: wiring of scripts/agent/cli_view.py and scripts/agent/repl_input_loop.py + regression test in tests/test_cli_view.py | In Progress | — | — |  |
| 3 | Phase 3: wiring of scripts/agent/tool_approval.py | In Progress | — | — |  |
| 4 | Phase 4: docs/23_agent/agent_07_05_cli-and-commands-repl-io.md paragraph + docs checkers | In Progress | — | — |  |
| 5 | Phase 5: deployment hand-off (skills/deploy/SKILL.md) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-090427_01_scripts_agent_stdin_reader.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261105-090427_02_scripts_agent_cli_view.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261105-090427_03_scripts_agent_repl_input_loop.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261105-090427_04_scripts_agent_tool_approval.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261105-090427_07_docs_23_agent_agent_07_05_cli-and-commands-repl-io.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261104-112115_cliview002_stdin-line-lost-after-multiline-timeout.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261104-223334
- **Related target files**: scripts/agent/stdin_reader.py, scripts/agent/cli_view.py, scripts/agent/repl_input_loop.py, scripts/agent/tool_approval.py, tests/agent/test_stdin_reader.py, tests/test_cli_view.py, docs/23_agent/agent_07_05_cli-and-commands-repl-io.md

### Requirement Traceability
| Requirement ID | Source (Issue section / evidence) | Target File | Implementation Step | Acceptance Criterion | Test / Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem + Acceptance Criteria (pty smoke evidence, confirmed by `TestCancelledRequestDelivery` and `StdinReader` docstring in Step 2) | scripts/agent/cli_view.py, scripts/agent/repl_input_loop.py | 2 | AC-1 | new timeout-then-fresh-read test in tests/test_cli_view.py | Confirmed by repository evidence |
| REQ-002 | Implementation Intent + consumer scan finding (Step 3: three instance owners incl. tool_approval.py) | scripts/agent/stdin_reader.py, scripts/agent/tool_approval.py | 1, 3 | AC-2 | accessor identity/isolation tests in tests/agent/test_stdin_reader.py | Confirmed by repository evidence |
| REQ-003 | Constraints (backward compatibility, `_INPUT_TIMEOUT_S`) — verified against cli_view.py L286-291 in Step 2 | scripts/agent/cli_view.py | 2 | AC-3 | existing `TestReadMultiline` tests unchanged | Explicit in issue |
| REQ-004 | Required Changes + Testing Expectations | tests/test_cli_view.py, tests/agent/test_stdin_reader.py | 1, 2 | AC-4 | Validation plan rows for both test files + regression suites | Explicit in issue |
| REQ-005 | Documentation Impact (chapter resolved via docs/00_index.md CLI-view row) | docs/23_agent/agent_07_05_cli-and-commands-repl-io.md | 4 | AC-5 | docs checkers row in the Validation plan | Confirmed by repository evidence |
| REQ-006 | Issue Dependencies/scope handling + `scripts/` change (rules/env.md Architecture) | scripts/agent/stdin_reader.py, scripts/agent/cli_view.py, scripts/agent/repl_input_loop.py, scripts/agent/tool_approval.py | 5 | N/A: deploy has its own approval gate in skills/deploy/SKILL.md | deploy hand-off (Phase 5) | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261105-090427 -->