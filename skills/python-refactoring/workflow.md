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
- If coverage is below 80%, add characterization tests.
  - Note: 80% is a judgment threshold specific to this procedure, not a project-wide
    standard.
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

- Use `libcst` for symbol-level refactoring when needed. When a change MUST preserve
  comments, formatting, or docstrings during a rename/structural edit, use a
  CST-preserving transform, not regex-based text replacement. Apply it only to the
  explicit file path(s) in the approved scope (never a directory glob), and restrict the
  rename to the intended symbol: a bare `Name` match also rewrites unrelated
  identifiers (keyword arguments, attributes, same-named locals), so match the
  definition, its imports, and its references selectively, e.g. for a top-level class:

  ```python
  import sys
  from pathlib import Path

  import libcst as cst

  class RenameClass(cst.CSTTransformer):
      def leave_ClassDef(
          self, original_node: cst.ClassDef, updated_node: cst.ClassDef
      ) -> cst.ClassDef:
          if updated_node.name.value == "OldName":
              return updated_node.with_changes(name=cst.Name("NewName"))
          return updated_node

      def leave_Name(
          self, original_node: cst.Name, updated_node: cst.Name
      ) -> cst.Name:
          # Reference sites only: add checks (ScopeProvider / parent node) so attributes,
          # keyword arguments, and shadowing locals named "OldName" are left alone.
          return updated_node

  path = Path(sys.argv[1])  # one explicit target file
  source = path.read_text(encoding="utf-8")
  new_code = cst.parse_module(source).visit(RenameClass()).code
  if new_code != source:
      path.write_text(new_code, encoding="utf-8")
  ```

  After the edit, review `git diff` for the file: every changed hunk must be the intended
  symbol.

- Run `ruff format` and `ruff check --fix` after each transformation.
- Ensure no legacy symbol names remain — verify with `rg "OldName" <scope>`.
- If `ruff check --fix` leaves unfixed violations, or `rg` still finds a legacy symbol
  name, fix the specific remaining item and re-run only that check (not the whole
  Transformation step). Per `AGENTS.md` Loop Prevention > Attempt Limit, at most 3
  fix-and-recheck attempts per file in this step; if violations or legacy references
  remain after 3 attempts, stop and report `Blocked: {file} still has {violation/legacy
  reference} after 3 attempts` — MUST NOT proceed to Step 7 with a known-unresolved item.

---

## Step 7: Validation

Follow `validation.md` Required Validation and Conditional Validation in full. Path C
additionally requires `path-c.md`'s Architecture Comparison Validation in the same
pass.

---

## Step 8: Incremental Migration

- By default, MUST NOT stage or commit anything. Classify changes directly from
  non-interactive `git diff` output, hunk by hunk, without invoking `git add`.
- Classify every hunk as one of:
  - rename only
  - extraction only
  - simplification
  - type annotation
  - guard clause
  - test characterization
  - validation fix
  - import cleanup
  - formatting
  - metadata update

  Any hunk that does not fit these categories MUST be explained explicitly.
- Run tests, `ruff`, and `mypy` once per logical group identified via `git diff` (see
  Refactoring-Specific Guidance for scoping) — MUST NOT require staging hunks
  individually to run these checks.
- Ensure every logical group identified via `git diff` is rollback-safe on its own (it
  could be committed or reverted independently without breaking the others).
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
- Generate `coverage.xml` with the scoped test run (`--cov-report=xml`), then run
  `uv run diff-cover coverage.xml --compare-branch=master`.
- When a module was split, merged, or grew: `uv run python tools/check_module_size.py`
  (`routing.md` Tools). When the code under a generated-reference domain changed:
  `uv run python tools/generate_reference_table.py --check`.
- When the target is under `tools/` rather than `scripts/`, use `routing.md` "Adding a new
  tool" validation (pass the file path explicitly to `mypy`) instead of the `scripts/`
  scoped commands above.
- Review changes with `git log` and `git diff`.
- Ensure no legacy symbol names remain.

**On a failure**: return to Step 6 (Transformation) to fix the specific violation
reported — MUST NOT re-derive the Step 2 intent or Step 4 behavior lock — then re-run
Step 7's Required validation (the fix may have changed behavior or the public API) and
this Step 9 CI gate, not Steps 1-6. Per `AGENTS.md` Loop Prevention > Attempt
Limit, at most 3 Step 6/Step 9 round-trips for the same file (or atomic migration
group); if the gate still fails after 3 attempts, stop, apply Rollback (see `AGENTS.md`
Loop Prevention > Rollback Directive), and report `Blocked: {file} still fails the CI
gate after 3 attempts — {summary of each attempt}` — MUST NOT start a fourth attempt.

---

## Step 10: Report Results

Follow `report-template.md` in full: the report structure for each file (or approved
atomic migration group), and the Completion Gate that decides whether the cycle may be
reported complete. Path C additionally requires `path-c.md`'s ADR Requirement and Path
C Completion Requirements.

---

## Refactoring-Specific Guidance

- Apply `rules/ai-execution.md` Tool Usage's idempotent-command rule throughout: MUST NOT
  re-run `mypy`/`pyright`/`ruff`/`pydeps`/`import-linter`/`mutmut`/`rg` against an
  unchanged target expecting a different result — only re-run a check after the
  specific fix it depends on (see Step 6/Step 9 fix-and-recheck rules).
- Perform Step 3 (preparation/investigation) sequentially; `rg` and the deploy-reference
  search MUST run every time regardless of Path, and `pydeps`/`import-linter`/
  `ast-grep` only when Path B or C applies (see `path-a.md`/`path-b.md`), retaining only
  the resulting impact scope table, not the raw tool output. The deploy-reference check
  is the `rg -ln ... deploy/ conf.d/ init.d/` search from Step 2.
- Capture only error/summary lines from `mypy`, `pyright`, `ruff`, and test runs (e.g.
  via `grep` for failures) rather than full successful-run output.
- Scope `mypy`, `pyright`, `ruff`, and test runs to the target file or module wherever
  possible, rather than the whole repository.
- `mutmut` (3.x here) takes its mutation scope from `[tool.mutmut]` `source_paths` in
  `pyproject.toml`; it has no `--paths-to-mutate`. Run `uv run mutmut run`, optionally
  naming specific mutants (`mutmut run <MUTANT_NAMES>`) and `--max-children`, then read
  `uv run mutmut results` and filter the report to the refactored module's mutants. If
  a run cannot be limited to the target in reasonable time, report `Not run` with the
  reason rather than running an unbounded whole-repo mutation.
- In Step 8, run the full mypy/test/ruff check once per logical diff group identified
  via `git diff` rather than after every single hunk; use a lighter check (e.g. `ruff`
  only) when inspecting individual hunks.
- When multiple target files are specified, run each Steps 1-10 cycle sequentially so
  one file's tool output and investigation results do not accumulate in the next file's
  context.
- Keep progress reports and Step 10 results concise; MUST NOT restate full diffs or raw
  tool output. Evidence tables (manifest, inventory, mutation report) MUST still list
  every required field even when kept concise.

---

## Special Cases

- If refactoring `tool_executor.py` or `route_resolver.py`, perform extra verification
  for MCP routing: `rg "ToolRouteResolver|tool_names" scripts/shared/` — check if
  `ToolRouteResolver` prefix mappings or `tool_names` config keys change (this is the
  exact command `path-c.md` Architecture Baseline's "Routing or registration" field
  reuses).
- If `config/agent.toml` would need to change, or modules are added or removed such that
  `deploy/deploy.sh` (and the other `deploy/*.sh` scripts), `routing.md`, or `AGENTS.md`
  would need updates, do not edit them (see Allowed file operations): record each as a
  Proposal in the Step 10 report, or make the edit only when the user explicitly
  instructs it. Run `deploy`'s Phase 2-3 afterwards when `scripts/` files were added,
  removed, or renamed (`SKILL.md` Composes with).

## Output format

See `report-template.md` for the exact final-report structure; output is code changes
plus the Step 10 report.
