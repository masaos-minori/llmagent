# Python Refactoring — Detailed Workflow

See `skills/DESIGN.md`, section "Safety-over-speed priority".

## Workflow position

This is a standalone, reactive workflow, not a phase of the
issue → plan → implementation-procedure → code pipeline. It is invoked directly on
named source files (`prompts/04_refactor.md`), or composed into another skill's
follow-up work (see `SKILL.md` Composes with / Called by).

- Input: target source file path(s), passed as arguments.
- Output: refactored source files, plus the Step 10 report (`report-template.md`); no
  standalone generated document.
- Workflow phase: `python-refactoring`

## Allowed file operations

- Modify only the target file(s) — see `AGENTS.md` Global Rule 5, the canonical
  statement of this scope-discipline restriction.
- Scoped exceptions (nothing else widens the scope):
  - characterization tests Step 4 requires, in the existing test file for the target
    under `tests/` (or a new one mirroring the target's path);
  - for a rename or move that Path B/C approved, the call sites and imports listed in
    the approved affected-file scope.
- Config, deploy, routing, and documentation changes the refactor may imply (see Special
  Cases) are recorded as Proposals unless the user explicitly instructs them.
- MUST NOT change external behavior, public APIs, or visible output.
- MUST NOT edit documentation unless explicitly instructed (one scoped exception: see
  `path-c.md` ADR Requirement — the ADR draft is presented inline, before
  implementation and again in the Step 10 report; only writing it under `docs/10_adr/`
  requires explicit instruction).

## Out of Scope

Apply `rules/ai-execution.md` Global Safety Restrictions (Base) — this already covers
not moving existing documentation files and not changing the workflow directory
structure. Additionally for this workflow, MUST NOT perform any of the following:
- refactoring code without explicit instruction — see `SKILL.md`, section "Core rules"
- implementing a behavior change discovered mid-refactor (record it as a proposal
  instead — see Step 2)

## Multi-file processing

Apply `rules/ai-execution.md` Sequential Target Processing (Base): each cycle covers
Steps 1-10 for one target file before starting Step 1 for the next file.

The one-file-at-a-time rule is the default for Path A and Path B, and for ordering
independent Path C target files outside the same atomic migration group. An approved
Path C atomic migration group is the one exception — see `path-c.md` Architectural
Refactoring Requirements for how a group is processed as a single logical unit.

Apply `rules/ai-execution.md` Progress Reporting (Base) for the per-step report
cadence.

---

## Step 0: Load Required Instructions

If not already loaded, read the following before starting:
- `routing.md`
- `rules/coding.md`
- `rules/toolchain.md`
- `rules/ai-execution.md`
- `skills/DESIGN.md`
- `SKILL.md` (this skill)
- this file
- `validation.md`
- `report-template.md`

MUST NOT eagerly load `discovery.md` or `path-a.md` / `path-b.md` / `path-c.md` — Step 2
loads `discovery.md` and only the one `path-*.md` matching the Path classification
decided there. This list is the one authoritative load list; `AGENTS.md` Global Rule 1
(selective loading) is satisfied by deferring those files.

---

## Step 1: Identify Target Files

- The target files are passed as arguments, e.g. a list of file paths. The user may
  specify one file or a list of multiple files.
- If no arguments are given, stop and ask which files to refactor.
- If any specified file does not exist, stop immediately and report which file(s) are
  missing. MUST NOT start processing any file until all specified paths are confirmed to
  exist.
- Files MUST be refactored one at a time, in the order given (see Multi-file
  processing above for the atomic-migration-group exception).
- Record the working-tree baseline once per cycle: `git status --short`. Changes already
  present (another session's edits, earlier work) are not this cycle's; Step 8 and the
  Completion Gate's "No unrelated files are modified" compare against this baseline. If
  the target file itself already has uncommitted changes, stop and ask: its diff cannot be
  attributed to this refactor. A `pre-commit` run in another session can stash unstaged
  files for a short time (`skills/git-commit-and-sync/workflow.md` Phase 6), so re-check
  before concluding that a file changed or vanished.

---

## Step 2: Refactoring Intent Declaration

Before making any edit to the target file, report the following in Markdown:

- Target file
- Refactoring goal
- Responsibility being improved
- Expected behavior change
- Public API impact
- Behavior preservation strategy
- Expected files to change
- Expected validation commands
- Path classification (A, B, or C) — see `SKILL.md` Routing

Before classifying, run the preliminary search needed by the Routing criteria:

```bash
rg -n "<target module or symbol>" scripts/ tests/    # callers
rg -ln "<target module or symbol>" deploy/ conf.d/ init.d/    # deploy references
```

Use the results for the "more than one caller" and "referenced in deploy scripts"
criteria; confirm each `rg` searched the intended paths (a zero-match result from a wrong
path is not evidence of absence).

Counting callers: a caller is a distinct non-test source file, other than the target, that
imports or calls a symbol this refactor will change in signature, location, or body. A
symbol used only inside the target, or one the refactor leaves untouched, adds no caller.

If `Expected behavior change` is anything other than `none`, stop. MUST NOT implement it.
Record it under `report-template.md`'s `Proposals not implemented` format instead, and
MUST NOT proceed to Step 3 for this idea. Only continue transforming the parts of the
file that involve no behavior change.

Classify the refactoring as Path A, Path B, or Path C now, per `SKILL.md` Routing, then
load the one matching file (`path-a.md`, `path-b.md`, or `path-c.md`). This gates how
much tooling depth Steps 3 and 4 apply — it does not skip Steps 3, 4, or 7 themselves,
nor reduce Step 7's Required validation (`validation.md`), nor skip the Completion gate
(`report-template.md`).

Record the Path A/B/C decision and its rationale in Step 10's report.

Load `discovery.md` now (unconditionally) — its Discovery Vocabulary defines the six
states (Finding / Candidate / Proposal / Approved Change / Blocked / Not Applicable)
used from this point through Step 10 to record what is observed without expanding the
approved change scope.

---

## Step 3: Preparation

Depth depends on the Path classification from Step 2 — see `path-a.md` or `path-b.md`
(Path C applies at least Path B's depth per `path-c.md`) for the exact tool list.

Record the impact scope in a table with the columns `Check | Command | Result | Status`
(`Status` is `Done`, `N/A: Path A`, or `Not run: <reason>`), one row per tool — the row
MUST NOT be omitted when a tool is skipped.

If this mapping shows the change meets a higher Path's criteria than the Step 2
classification (e.g. more callers, a deploy reference, or an import-boundary change),
re-classify upward, load the matching `path-*.md`, and re-issue the Step 2 declaration
for the new Path before continuing. Never downgrade a Path during a cycle.

In addition, regardless of Path, perform `discovery.md`'s Technical Debt Discovery,
Responsibility Analysis, and Documentation Drift Detection (the latter scaled to the Path
as `discovery.md` defines) while reading the target file.

---

## Step 4: Behavior Lock

- Record baseline coverage with `pytest-cov`, scoped to the target:
  `uv run pytest <tests mirroring the target> --cov=<target module> --cov-report=term-missing`
  (confirm the run collected tests and measured the target; see `validation.md`).
  - Tests mirroring the target: `tests/<path below scripts/>/test_<name>.py` when it
    exists, plus the files `rg -l "<target module>" tests/` finds.
  - `<target module>` is the dotted module name below `scripts/` (for example
    `shared.route_resolver`). A file path in `--cov=` ran the tests here but printed no
    coverage table, so it measured nothing; confirm the table lists the target.
- If coverage is below 80%, add characterization tests.
  - Note: 80% is a judgment threshold specific to this procedure, not a project-wide
    standard. The project's own gate is diff-cover at 90% on changed lines (Step 9).
- Record the complexity baseline: `uv run radon cc <target file> -s` (no `-n`, so every
  function is listed). Keep the grade of each function Step 6 may touch; Step 7 compares
  against it (`validation.md` Complexity check).
- Mutation-testing depth depends on the Path classification — see `path-a.md` or
  `path-b.md` (Path C applies at least Path B's depth per `path-c.md`).
- Produce a behavior lock manifest covering:
  - Public functions/classes covered
  - Important branches covered
  - Error paths covered
  - Boundary conditions covered
  - Visible output covered
  - Side effects covered
  - Existing tests used
  - Characterization tests added
  - Complexity baseline (`radon cc` grade per function Step 6 may touch)
  - Known uncovered behavior
- MUST NOT proceed to Step 6 (Transformation) if important behavior is uncovered and no
  characterization test or explicit exception is recorded for it in `Known uncovered
  behavior`.

Path C additionally requires `path-c.md`'s Architecture Baseline before any Path C
transformation begins (Step 6).

---

## Step 5: Side-Effect Inventory

Follow `validation.md` Side-Effect Inventory (Step 5 baseline) in full before
transformation. If any side effect changes during transformation, stop and record it
as a proposal unless explicitly approved.

---

## Step 6: Transformation

### Deletion-First Evaluation

Applies only when the planned transformation would introduce a new class, protocol,
adapter, facade, manager, service, or registry — not for every Step 6 transformation. A
pure rename, an extraction into an existing module, or a type-annotation change does not
require this evaluation. This evaluation and its justification requirement apply
identically to Path A, Path B, and Path C — unlike Steps 3/4's Path-gated tooling-depth
rules, this is not Path-gated, because the design question (does this change need a new
abstraction) is independent of blast radius.

Before introducing such an abstraction, evaluate the following seven steps in order and
stop at the first step that resolves the change; MUST NOT separately justify skipping the
later steps once an earlier one applies:

1. Can the responsibility be removed?
2. Can the state or side effect be removed?
3. Can duplicate paths be consolidated?
4. Can the code be simplified?
5. Can responsibility move to an existing boundary?
6. Can logic be extracted?
7. Is a new abstraction required?

If step 7 is reached, the new abstraction requires a justification with exactly these
seven fields, recorded in the Step 10 report (see `path-c.md` ADR Requirement for when an
ADR is also required):
- The problem being solved
- Why removal or simplification is insufficient
- Ownership
- Lifecycle
- Dependency direction
- Callers
- Test boundary

A new abstraction with an incomplete justification MUST NOT be transformed in this
Step — record it as a Proposal (`discovery.md` Discovery Vocabulary) instead, as in
Step 2's behavior-change stop rule.

### Transforming

- Use `libcst` for symbol-level renames/structural edits that must preserve comments,
  formatting, or docstrings (never regex text replacement). Constraints:
  - Pass one explicit target file path per run, never a directory glob.
  - A `CSTTransformer` matching a bare `Name` also rewrites keyword arguments, attributes,
    and same-named locals. Match the definition (`leave_ClassDef`/`leave_FunctionDef`), its
    imports, and its reference sites selectively (`ScopeProvider` or parent-node checks).
  - Afterwards `git diff` the file: every changed hunk must be the intended symbol.

- Run `ruff format` and `ruff check --fix` after each transformation.
- Ensure no legacy symbol names remain — verify with `rg "OldName" <scope>`.
- If `ruff check --fix` leaves violations or `rg` still finds a legacy symbol name, fix that
  item and re-run only that check. At most 3 attempts per file (`AGENTS.md` Loop Prevention
  > Attempt Limit); then stop and report `Blocked: {file} still has {violation/legacy
  reference} after 3 attempts` — MUST NOT proceed to Step 7 with a known-unresolved item.

---

## Step 7: Validation

Follow `validation.md` Required Validation and Conditional Validation in full. Path C
additionally requires `path-c.md`'s Architecture Comparison Validation in the same
pass.

---

## Step 8: Incremental Migration

- By default, MUST NOT stage or commit anything. Classify changes directly from
  non-interactive `git diff` output, hunk by hunk, without invoking `git add`. Hunks in
  files that were already modified in the Step 1 baseline are not this cycle's changes;
  do not classify them.
- Classify every hunk as one of: rename only, extraction only, simplification, type
  annotation, guard clause, test characterization, validation fix, import cleanup,
  formatting, lint autofix (a change `ruff check --fix` made that the refactor did not
  intend), metadata update. Explain any hunk that fits none.
- Run tests, `ruff`, and `mypy` once per logical group identified via `git diff` (see
  Refactoring-Specific Guidance for scoping) — MUST NOT require staging hunks
  individually to run these checks.
- Ensure every logical group identified via `git diff` is rollback-safe on its own (it
  could be committed or reverted independently without breaking the others).
  - Independence can only be shown by applying a group alone. When the diff has more than
    one group and the user asked for per-group commits, verify each group in a throwaway
    worktree: `git worktree add <scratchpad dir>/rb HEAD`, `git apply` a patch holding
    only that group's hunks (copied verbatim from `git diff`), run the scoped tests,
    `ruff`, and `mypy` there, then `git worktree remove <scratchpad dir>/rb`.
  - Without that request, report the suggested boundaries in Step 10 labelled
    `independence not verified`; do not present them as verified.
  - After a Step 9 failure and its Step 6 fix, redo this classification for the changed
    hunks.
- Staging and committing are both opt-in, never default:
  - If the user has not requested staging or committing: leave the working tree
    unstaged, organize the logical diff groups above, and report the suggested commit
    boundaries in Step 10.
  - If the user explicitly requests staging: `git add -p` (interactive) or `lazygit`
    may be used to stage per-hunk at that point — this is an opt-in action, not a
    required step of this workflow.
  - If the user explicitly requests committing or pushing: hand off to the
    `git-commit-and-sync` skill, one rollback-safe commit per logical unit, and ensure
    each commit passes the Step 10 completion gate (`report-template.md`) before it is
    committed. Interactive or history-rewriting commands (`git rebase -i`, `--amend`)
    are forbidden by that skill and MUST NOT be used.

---

## Step 9: CI Gate

Refer to `rules/toolchain.md` for the full validation sequence (and run it as a whole via
`uv run python tools/run_validation_gates.py`, with `--full` for the complete run, which
selects the gates the changed files need). At minimum:
- Run `pre-commit run --files <changed files>`; use `--all-files` only when the change
  touches shared configuration or the user asks for a full-repo run.
- Run `PYTHONPATH=scripts uv run lint-imports` (the exact form in `rules/toolchain.md`).
- Generate `coverage.xml` the way `rules/toolchain.md` section 7 does
  (`uv run coverage run -m pytest tests/`, then `uv run coverage xml`), then run
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`. It passes
  only at 90% on changed lines, and only when every changed source file appears in the
  diff-cover report. A `coverage.xml` from a scoped run may under-report or omit changed
  lines (not verified here), so do not report it as this gate's result; when the full run
  is impractical, report `Not run: {reason}` (`validation.md` Conditional Validation).
- When a module was split, merged, or grew: `uv run python tools/check_module_size.py`
  (`routing.md` Tools). When the code under a generated-reference domain changed:
  `uv run python tools/generate_reference_table.py --check`.
- When the target is under `tools/` rather than `scripts/`, use `routing.md` "Adding a new
  tool" validation (pass the file path explicitly to `mypy`) instead of the `scripts/`
  scoped commands above.
- Review changes with `git log` and `git diff`.
- Ensure no legacy symbol names remain.

**On a failure**: fix the reported violation in Step 6 (MUST NOT re-derive the Step 2 intent
or Step 4 behavior lock), then re-run Step 7's Required validation (the fix may have changed
behavior or the public API) and this gate. At most 3 Step 6/Step 9 round-trips per file (or
atomic migration group); after the third, stop, roll back (`AGENTS.md` Loop Prevention >
Rollback Directive), MUST NOT start a fourth attempt, and report `Blocked: {file} still fails the CI gate after 3 attempts —
{summary of each attempt}`.

---

## Step 10: Report Results

Follow `report-template.md` in full: the report structure for each file (or approved
atomic migration group), and the Completion Gate that decides whether the cycle may be
reported complete. Path C additionally requires `path-c.md`'s ADR Requirement and Path
C Completion Requirements.

Proposals and Findings live only in this report. When it lists any, offer to file them with
`issue-creator` ("Input from review findings"); this skill writes no issue files itself
(Allowed file operations).

---

## Refactoring-Specific Guidance

- Apply `rules/ai-execution.md` Tool Usage's idempotent-command rule: MUST NOT re-run a
  check (`mypy`/`pyright`/`ruff`/`pydeps`/`import-linter`/`mutmut`/`rg`) against an unchanged
  target expecting a different result; re-run only after the fix it depends on.
- Step 3 runs sequentially. `rg` and the deploy-reference search run every time; `pydeps`/
  `import-linter`/`ast-grep` only for Path B or C (`path-a.md`/`path-b.md`). Keep only the
  impact scope table, not raw tool output.
- Capture only error/summary lines from `mypy`, `pyright`, `ruff`, and test runs, scoped to
  the target file or module wherever possible.
- `mutmut` (3.x here) takes its mutation scope from `[tool.mutmut]` `source_paths` in
  `pyproject.toml`; it has no `--paths-to-mutate`. Run `uv run mutmut run`, optionally
  naming specific mutants (`mutmut run <MUTANT_NAMES>`) and `--max-children`, then read
  `uv run mutmut results` and filter the report to the refactored module's mutants. If
  a run cannot be limited to the target in reasonable time, report `Not run` with the
  reason rather than running an unbounded whole-repo mutation.
- In Step 8, run the full mypy/test/ruff check once per logical diff group identified
  via `git diff` rather than after every single hunk; use a lighter check (e.g. `ruff`
  only) when inspecting individual hunks.
- Keep progress reports and Step 10 results concise; MUST NOT restate full diffs or raw
  tool output. Evidence tables (manifest, inventory, mutation report) MUST still list
  every required field even when kept concise.

---

## Special Cases

- If refactoring `tool_executor.py`, `route_resolver.py`, or `runtime_tool_registry.py`,
  perform extra verification for MCP routing: `rg -ln "RuntimeToolRegistry|ToolRouteResolver" scripts/`
  — check that how tools are registered and resolved is unchanged (this is the exact
  command `path-c.md` Architecture Baseline's "Routing or registration" field reuses).
  `ToolRouteResolver` takes `RuntimeToolRegistry` (populated from live `/v1/tools`
  discovery) as its sole routing authority (`scripts/shared/route_resolver.py`), so the
  `tool_names` config key is not routing evidence.
- If `config/agent.toml` would need to change, or modules are added or removed such that
  `deploy/deploy.sh` (and the other `deploy/*.sh` scripts), `routing.md`, or `AGENTS.md`
  would need updates, do not edit them (see Allowed file operations): record each as a
  Proposal in the Step 10 report, or make the edit only when the user explicitly
  instructs it.
- When `scripts/` files were added, removed, or renamed, the change reaches production
  only through `git-commit-and-sync` (a pushed HEAD) and then `deploy` (Phases 1-4,
  including Phase 1b when an MCP server binary is affected). This skill never starts
  `deploy` itself; mention it in the Step 10 report. Renaming or moving an MCP server
  module also changes `ENTRIES` (`deploy/build_binaries.sh`), `BINARY_NAMES`
  (`deploy/deploy.sh`), `BINARY_SOURCES` (`tools/manage_binaries.py`), and `cmd` in
  `config/agent.toml`; record each as a Proposal.
