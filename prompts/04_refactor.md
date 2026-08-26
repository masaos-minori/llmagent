You are a senior software engineer and refactoring specialist.

Read the target source files passed as arguments, then refactor them based on the rules below.

This workflow intentionally prioritizes safety, evidence, and correctness over speed. Do not
skip a step because it seems slow.

- Do not modify files outside the scope of the target files.
- Do not change external behavior, public APIs, or visible output.
- Do not edit documentation unless explicitly instructed.
- Do not touch files under `__pycache__/`.
- Use Markdown for all progress reports and per-file results. Be concrete and implementation-oriented.

### Core Rules

- Change only one feature or one responsibility at a time.
- Keep every change small.
- If a change may alter behavior, do not implement it — record it as a proposal instead (see
  Step 10, `Proposal Format`).
- Minimize changes to exception handling, state, side effects, I/O, and concurrency.
- Do not refactor code unless explicitly instructed via a target file or issue. This workflow is reactive, not proactive.

### Refactoring Rules

- Give each function one responsibility.
- Do not mix fetching, transformation, decision logic, and persistence in one function.
- Reduce nesting, branching, and long functions.
- Prefer early returns and small helper functions when they improve clarity.
- Use clear and explicit names.
- Extract shared logic only when it should evolve together later.
- Avoid unnecessary abstraction.

### Type Safety Rules

- Add explicit type annotations where needed.
- Add boundary checks where types are unclear.
- Do not use `Any`, unnecessary casts, or unsafe assertions.
- Prevent invalid `None` flow.
- Keep input validation separate from internal logic.

## Shared Rules

- Execution rules: see `rules/ai-execution.md` (context reading, tool usage, reasoning, output, progress reporting, command results, sequential target processing).
- Global safety restrictions: see `rules/ai-execution.md` (do not modify files outside scope, do not process `__pycache__/`, do not perform unrelated refactoring, do not perform broad formatting-only rewrites, do not process target-file cycles in parallel).

### Tasks

Report progress at the start and end of each step.

If multiple target files are specified, treat Steps 1-10 as one complete cycle per file:
finish every step for the current file before starting Step 1 for the next file. Do not
batch-read multiple target files up front, and do not interleave steps across files.

#### Step 0: Load required files

If not already loaded, read the following before starting:
- `routing.md`
- `rules/coding.md`
- `rules/toolchain.md`
- `skills/python-refactoring/SKILL.md`
- `rules/ai-execution.md`

#### Step 1: Identify target files

- The target files are passed as arguments, e.g. a list of file paths. The user may specify one file or a list of multiple files.
- If no arguments are given, stop and ask which files to refactor.
- If any specified file does not exist, stop immediately and report which file(s) are missing. Do not start processing any file until all specified paths are confirmed to exist.
- Refactor strictly one file at a time, in the order given. Do not read or inspect files that will be processed in a later cycle.

#### Step 2: Refactoring intent declaration

Before making any edit to the target file, report the following in Markdown:

- Target file
- Refactoring goal
- Responsibility being improved
- Expected behavior change
- Public API impact
- Behavior preservation strategy
- Expected files to change
- Expected validation commands
- Path classification (A or B) — see "Path classification" below

If `Expected behavior change` is anything other than `none`, stop. Do not implement it.
Record it under `Proposals not implemented` (Step 10 format) instead, and do not proceed to
Step 3 for this idea. Only continue transforming the parts of the file that involve no
behavior change.

##### Path classification

Classify the refactoring as Path A, Path B, or Path C before Step 3. This gates how much tooling
depth Steps 3 and 4 apply — it does not skip Steps 3, 4, or 7 themselves, nor reduce
Step 7's Required validation, nor skip the Completion gate.

**[Path A] Minor change** — must satisfy ALL:
- Affects a single target file
- No import boundary changes (no new cross-layer imports)
- `Expected behavior change: none` (per the declaration above)
- Not referenced in `deploy.sh`

**[Path B] Higher-impact change** — satisfies ANY:
- Affects more than one file
- Changes an import boundary or module layer
- Referenced in `deploy.sh`
- Touches shared/extracted logic used by more than one caller

**[Path C] Architectural refactoring** — satisfies ANY:
- Module relocation
- Module merge or split
- Responsibility or ownership transfer
- Dependency-direction change
- Architectural boundary change

If a change satisfies any Path C criterion, classify it as Path C even if it also
satisfies a Path B criterion (e.g. an import-boundary change that is a byproduct of a
relocation, merge, split, ownership transfer, or boundary change is Path C, not Path B); a
narrower import-direction fix that is not part of such a structural change remains Path B.

Record the Path A/B/C decision and its rationale in Step 10's report.

##### Path C: Architectural Refactoring

A Path C change requires all of the following before implementation begins:

1. Explicit approval
2. Affected-file scope
3. Current and proposed boundaries
4. Migration strategy
5. Rollback strategy
6. Documentation impact
7. ADR requirement — an ADR must exist or be referenced before implementation; this
   requirement does not define the ADR template or process itself (reserved for a later
   issue in this sequence)

An unapproved Path C idea is a Proposal only, per the Proposal state defined in the
`##### Discovery Vocabulary` subsection of this Step (added per
`implementations/20260826-155803_01_prompts_04_refactor.md.md` `REQ-001`); it must not be
transformed in Step 6 until it becomes an Approved Change per that same subsection's rule
that only an Approved Change may be transformed in Step 6, with all seven items above
satisfied and explicit approval given.

**Atomic migration group**: the explicit, enumerated set of files whose changes must be
applied and validated together, because no proper subset of them can independently pass
Step 7 validation while the remaining members are unchanged (e.g. relocating a module and
updating every one of its callers). Group membership must be declared and included in the
approval above (item 2, affected-file scope) before Step 3 begins for any member of the
group.

The one-file-at-a-time rule (Step 1) remains the default for Path A and Path B, and for
ordering independent Path C target files that do not belong to the same atomic migration
group. For an approved atomic migration group, the rule applies to the group as a single
logical unit rather than to each member file individually — one Path classification, one
Step 3-7 preparation/validation/gating pass, and one Completion gate cover the whole group
— while member files are still read and transformed one at a time in a fixed, declared
order and never in parallel (Step 6 Transformation and the Global Safety Restriction
against parallel target-file processing still apply within the group).

Silent expansion of an approved atomic migration group is prohibited. If executing the
group reveals that an additional file must change for the group to remain valid, stop; the
additional file is a new Proposal requiring a new approval cycle for the amended group
before any further transformation. The originally approved group's membership is frozen at
approval time.

##### Discovery Vocabulary

While investigating the target file (Steps 2-10), use these six states to record what is
observed without expanding the approved change scope:

- **Finding**: an evidence-based observation of a concrete problem (e.g. duplicate logic,
  unclear ownership) recorded per the Finding record schema (see Step 3, Technical Debt
  Discovery). Requires a populated `evidence` field.
- **Candidate**: a Finding assessed as potentially actionable, not yet evaluated for
  approval.
- **Proposal**: a behavior-changing idea surfaced during work on the target file. This is
  the same concept as, and must use, the existing "Proposals not implemented" format defined
  in Step 10 (Title / Reason / Behavior risk / Affected files / Suggested follow-up issue /
  Recommended validation) — this section does not define a second Proposal format.
- **Approved Change**: a change explicitly authorized for this refactoring cycle; only an
  Approved Change may be transformed in Step 6.
- **Blocked**: a Finding, Candidate, or Proposal that cannot be evaluated further without
  additional evidence or a decision outside this workflow's scope.
- **Not Applicable**: a Finding, Candidate, or Proposal determined, after evaluation, not to
  apply to the current target file or refactoring cycle.

Discovery (Finding, Candidate, Proposal) does not authorize implementation — only an
Approved Change may be transformed in Step 6. This does not weaken or replace the Step 2 rule
that any `Expected behavior change` other than `none` must stop work and be recorded under
`Proposals not implemented`; that rule continues to apply unchanged.

#### Step 3: Preparation

Depth depends on the Path classification above.

- Use `rg` to find symbol usages (always run, not conditional).
- Check whether the target files are referenced in `deploy.sh` (always run).
- **Path A**: skip `pydeps`, `import-linter`, and `ast-grep`; record `N/A: Path A` for
  each in the impact scope table.
- **Path B**: run `pydeps` to inspect the import graph, `import-linter` to verify module
  boundaries, and `ast-grep` for structural usage search — each subject to the
  Conditional tool handling defined in Step 7 (report why unavailable, use an
  alternative if one exists, never report a skipped check as passed).
- **Path C**: apply at least Path B's depth (Path C's criteria entail the
  import-boundary/dependency-direction conditions Path B already tests for).
- Record the impact scope in a table, marking any tool skipped for either reason
  (Path A or unavailability) as `N/A` or `Not run` respectively — never omit the row.

##### Technical Debt Discovery

Applies regardless of Path A/B classification (lightweight and report-only; not subject to
the `pydeps`/`import-linter`/`ast-grep` tooling-depth rule above).

While reading the target file, record a Finding (see Discovery Vocabulary) for observations
in these six categories only:
- Duplicate logic
- Duplicate validation
- Unclear ownership
- Excessive indirection
- Responsibility concentration
- Testability concerns

Every Finding must record all six fields:
- **ID**: a short unique identifier for this Finding within the cycle
- **Category**: one of the six categories above
- **Severity**: `Critical` / `High` / `Medium` / `Low` / `Informational`, per
  `skills/python-code-review/SKILL.md` Severity
- **Evidence**: a concrete repository location — file path and line range, or a command and
  its output. A Finding with no populated evidence field must not be recorded.
- **Impact**: the concrete consequence if left unaddressed
- **Recommendation**: what a future Approved Change could do about it — recording the
  recommendation does not authorize acting on it now

Recording a Finding here never authorizes implementing it in this cycle.

##### Responsibility Analysis

Applies regardless of Path A/B classification, for the same reason as Technical Debt
Discovery above.

For each function/class in the target file, record:
- **Responsibilities**: what it is accountable for
- **Dependencies**: what it relies on
- **Side effects**: what it does beyond its return value (see Step 5 for the full inventory)
- **State ownership**: what state it owns or mutates
- **Branching**: its decision points

When this analysis identifies a split candidate (a function/class whose responsibilities
should be divided), report it using the Proposal format (Discovery Vocabulary) — do not
implement the split automatically. This is the same "discovery does not authorize
implementation" rule applied specifically to split candidates.

##### Documentation Drift Detection

Applies regardless of Path A/B classification (uniform across all paths; does not
reference Path classification).

While investigating the target file (Steps 2-10), compare relevant implementation
details against these seven document sources: `routing.md`, `AGENTS.md`, README,
design documents, coding and toolchain rules, configuration specifications, deployment
definitions. For "design documents," use `docs/00_index.md`'s "Document References by
Task" table to locate the documents actually governing the target file's behavior,
rather than scanning all of `docs/*.md`.

Record each discovered discrepancy as a Drift Finding with exactly six fields — a
Drift Finding with any field unpopulated must not be recorded:
- **Document**: the document source compared against (one of the seven above)
- **Implementation evidence**: a concrete repository location — file path and line
  range, or a command and its output
- **Drift description**: what the document says versus what the implementation
  actually does
- **Confidence**: `Unverified`, `Ambiguous Source of Truth`, or one of
  `rules/coding.md`'s five "Current behavior" categories (see below)
- **Possible source of truth**: which of the document or the implementation is likely
  authoritative, once confidence supports a choice
- **Suggested follow-up**: what a future Approved Change or documentation update could
  do about it — recording it here does not authorize acting on it now

When evidence is sufficient to decide, populate "possible source of truth" and
"suggested follow-up" using `rules/coding.md`'s existing five-category "Current
behavior" classification (Accepted current specification / Implementation fix required
/ Documentation fix required / Issue already tracked / Obsolete and removable) directly
— this subsection does not define a second, parallel classification.

When evidence is not yet sufficient to select one of the five categories, classify the
Drift Finding's confidence as one of two pre-classification states instead. These two
states are additions to, not replacements for, the five-category system:
- **Unverified**: the drift claim itself cannot yet be confirmed from available
  evidence.
- **Ambiguous Source of Truth**: evidence confirms a discrepancy but does not indicate
  which of the document or the implementation is authoritative.

A Drift Finding classified `Ambiguous Source of Truth` must NOT be auto-resolved via
`rules/coding.md`'s "ambiguous cases default to Implementation fix required" rule —
that default is calibrated for authoring a single `docs/*.md` note about an
already-known gap, not for a drift-detection process spanning a wider, more
consequential document set (deployment definitions, toolchain rules, routing, etc.). An
`Ambiguous Source of Truth` finding requires explicit maintainer confirmation — via the
sign-off channel defined in `rules/coding.md` "Explicit sign-off gates," or the unified
Proposal mechanism below — before it is routed into one of the five categories. This is
a documented, deliberate divergence from `rules/coding.md`'s default-ambiguous
behavior, scoped only to this Documentation Drift Detection subsection;
`rules/coding.md`'s own default continues to apply unchanged everywhere else.

Documentation Drift Detection does not modify any document: no automatic edit to
`docs/*.md`, `routing.md`, `AGENTS.md`, README, design documents, coding/toolchain
rules, configuration specifications, or deployment definitions. Any suggested
documentation change is recorded using the existing Step 10 "Proposals not
implemented" format (Title / Reason / Behavior risk / Affected files / Suggested
follow-up issue / Recommended validation) — the same format this workflow already uses
for behavior-changing ideas — never applied directly during this Step.

If a listed comparison target has no corresponding file in the repository (e.g. no
repository-root `README.md` as of this writing), skip that target for the current
cycle — do not fabricate a comparison, and do not record a Drift Finding for the
target's mere absence. A missing document is a documentation-completeness question
outside this subsection's scope (comparing an existing document's claims against the
implementation), not a drift between the two.

#### Step 4: Behavior lock

- Record baseline coverage with `pytest-cov`.
- If coverage is below 80%, add characterization tests.
  - Note: 80% is a judgment threshold specific to this procedure, not a project-wide standard.
- **Path A**: skip `mutmut`; record `Not run: Path A` in the manifest and rely on the
  characterization tests and coverage above.
- **Path B**: run `mutmut` when the repository configures and supports it (per the
  Conditional tool handling in Step 7). When run, ensure there are no surviving
  mutations in the refactored paths, or that every surviving mutation is documented as
  equivalent (Step 10 format). When unavailable, report `Not run` — never treat
  mutation coverage as satisfied in that case.
- **Path C**: apply at least Path B's depth (Path C's criteria entail the
  import-boundary/dependency-direction conditions Path B already tests for).
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
- Do not proceed to Step 6 (Transformation) if important behavior is uncovered and no
  characterization test or explicit exception is recorded for it in `Known uncovered behavior`.

##### Architecture Baseline (Path C)

Applies only when the change is classified Path C (see `##### Path C: Architectural
Refactoring`). Path A and Path B proceed through this Step exactly as today, unaffected.

Before any Path C transformation begins (Step 6), capture all eight of the following
fields:

- **Module ownership**: no established repository command exists for this field
  (verified: no `CODEOWNERS` file, no ownership-registry document, no documented
  ownership-check command anywhere in `rules/`, `routing.md`, or `skills/`). Capture
  manually by direct code inspection, using `rules/env.md` Architecture's six-layer
  diagram (`scripts/{agent,db,eventbus,mcp_servers,rag,shared}/`) as the default
  ownership unit (the owning layer/module directory).
- **Dependency direction**: run `pydeps` (import graph) and `import-linter`/
  `lint-imports` against `.importlinter`'s contracts — the same tools this Step already
  runs at Path B/C depth — cross-checked against `rules/env.md` Architecture's layer
  diagram.
- **Entry points**: no single established repository command covers all entry-point
  types. Capture manually via `rg "if __name__ == .__main__.":` plus direct inspection
  of `config/agent.toml` service definitions and the relevant MCP server class's
  `http_port` class variable (`scripts/mcp_servers/server.py`-derived modules).
- **Lifecycle ownership**: no established repository command exists for this field
  beyond module-naming convention. Capture manually via `rg` for class names containing
  `Lifecycle` and for `start`/`stop`/`shutdown` method definitions in the affected
  module.
- **State ownership**: reuse this Step's sibling Step 5's existing side-effect
  inventory "Global mutable state" item as the baseline record for this field; do not
  define a second, separate capture method.
- **Configuration dependencies**: `rg` against `config/*.toml` and
  `shared/config_loader.py` usages, consistent with `rules/env.md`'s statement that
  `config/agent.toml` is the configuration SSOT.
- **Routing or registration**: `rg "ToolRouteResolver\|tool_names" scripts/shared/` —
  the exact command already named in `skills/python-refactoring/workflow.md` Special
  Cases and cross-referenced by this file's own Special Cases section.
- **Deployment references**: reuse Step 3's existing "referenced in `deploy.sh`" check
  verbatim; do not define a second deploy-reference check.

Module ownership, entry points, and lifecycle ownership are manual-capture fields with
no established repository tooling — record them explicitly as such rather than
applying an inconsistent ad hoc method across runs.

Do not start a Path C transformation (Step 6) if any required Architecture Baseline
field is missing or its capture is incomplete.

#### Step 5: Side-effect inventory

Before transformation, list current side effects in the target file:

- File I/O
- Network I/O
- Subprocess execution
- Database access
- Environment variable access
- Global mutable state
- Logging
- Caching
- Concurrency
- Time-dependent behavior
- Randomness

This inventory is the baseline that Step 7 must reconfirm as unchanged after transformation.
If any side effect changes, stop and record it as a proposal unless explicitly approved.

#### Step 6: Transformation

##### Deletion-First Evaluation

Applies only when the planned transformation would introduce a new class, protocol,
adapter, facade, manager, service, or registry — not for every Step 6 transformation. A
pure rename, an extraction into an existing module, or a type-annotation change does not
require this evaluation. This evaluation and its justification requirement apply
identically to Path A, Path B, and Path C — unlike Step 3/4's existing Path-gated
tooling-depth clauses, this is not Path-gated, because the underlying design question
(does this change need a new abstraction) is independent of blast radius.

Before introducing a new class, protocol, adapter, facade, manager, service, or
registry, evaluate the following seven steps in order and stop at the first step that
resolves the change — the first step that applies settles the question; do not
separately justify skipping the later steps once an earlier one applies:

1. Can the responsibility be removed?
2. Can the state or side effect be removed?
3. Can duplicate paths be consolidated?
4. Can the code be simplified?
5. Can responsibility move to an existing boundary?
6. Can logic be extracted?
7. Is a new abstraction required?

If step 7 is reached, the new abstraction requires a justification with exactly these
seven fields, recorded in the Step 10 report (see `##### ADR Requirement` for when the
new abstraction also requires an ADR):
- The problem being solved
- Why removal or simplification is insufficient
- Ownership
- Lifecycle
- Dependency direction
- Callers
- Test boundary

A new abstraction with an incomplete justification must not be transformed in this
Step — record it as a Proposal (`##### Discovery Vocabulary`) instead, consistent with
Step 2's existing "if behavior change is anything other than none, stop, record as
proposal" pattern.

- Use `libcst` for symbol-level refactoring when needed.
- Run `ruff` after each transformation.
- Ensure no legacy symbol names remain.

#### Step 7: Validation

##### Required validation

Run repository-defined validation for:
- formatting
- linting
- type checking
- affected tests
- public API stability
- exception behavior
- side effects
- import boundaries when imports change

At minimum:
- Run `mypy`.
- Cross-check with `pyright`.
- Run `ruff`.
- Run characterization tests.

In addition, perform and record the following checks:

- **Public API stability check** — verify before/after equality of:
  - Public class names
  - Public function names
  - Public method names
  - Function signatures
  - Return types
  - Exceptions relied upon by callers
  - CLI-visible behavior
  - Tool or server route names
  - Configuration keys

  If any public API change is required, stop and record it as a proposal unless explicitly
  approved.

- **Exception behavior freeze** — do not change exception behavior unless explicitly approved.
  Preserve:
  - Exception types
  - Exception messages where visible or tested
  - Retry behavior
  - Fallback behavior
  - Error logging behavior
  - Error return values
  - Failure ordering

  If exception handling appears incorrect, do not fix it during refactoring. Record it as a
  proposal.

- **Side-effect inventory recheck** — confirm the Step 5 inventory is unchanged.

- **Import boundary evidence** — when imports are changed, record:
  - Imports added
  - Imports removed
  - Imports moved
  - Layer boundary impact (see the import layer contract in `AGENTS.md`)
  - `import-linter` result
  - Circular import risk
  - Runtime import side-effect risk

  Do not introduce a new import from a lower layer to a higher layer unless explicitly
  approved.

##### Conditional validation

Run these tools only when the repository configures and supports them:
- `mutmut`
- `diff-cover`
- `import-linter`
- `pydeps`
- `ast-grep`
- `pyright`
- `pre-commit`
- `libcst`

If a conditional tool is unavailable:
- Report why it was not run.
- Use a repository-defined alternative when available.
- Do not report the skipped check as passed.
- Report `Blocked` only if the missing check is required to prove behavior preservation.
- Otherwise, continue and record the check as `Not run`.

Do not require interactive Git commands. Use non-interactive `git diff` commands. Do not stage or commit unless the user explicitly requests it. Report suggested commit boundaries in the final report.

If mutation testing is not configured, report `Not run`. Do not invent mutation results.

##### Path C: Architecture Comparison Validation

Applies only when the change is classified Path C. These eight items are mandatory
checks for Path C — not optional the way the Conditional validation list above is; only
their evidence availability, not their requiredness, may be `Not run`/`Blocked`.

For each item, re-run the same capture method recorded in the Architecture Baseline
(Step 4) after Step 6 Transformation, and compare the result against the baseline
recorded before transformation:

- **Before-and-after dependency comparison** — compares the dependency direction field.
- **Architecture-boundary comparison** — compares the dependency direction field,
  cross-checked against `.importlinter` contracts and `rules/env.md`'s layer diagram.
- **Ownership validation** — compares the module ownership and state ownership fields.
- **Migration validation** — verifies every declared atomic migration group member (see
  `##### Path C: Architectural Refactoring`) was transformed and no partial-migration
  state remains.
- **Rollback validation** — verifies the rollback strategy declared in that same
  subsection's pre-implementation checklist is actually exercisable, not merely stated.
- **Route, tool, or plugin registration comparison** — compares the routing or
  registration field.
- **Configuration and deployment comparison** — compares the configuration
  dependencies and deployment references fields.
- **Removed-symbol reference check** — a repository-wide (not target-file-scoped) `rg`
  search for old symbol names, extending Step 6's "no legacy symbol names remain" rule
  and Step 9's equivalent check beyond the target file or migration group to the whole
  repository.

Report each item as one of `Pass`, `Fail`, `Not run`, or `Blocked`, reusing the
Conditional validation reporting rule above verbatim in spirit: report why an item was
not run, use a repository-defined alternative when available, do not report a skipped
item as passed, report `Blocked` only if the missing check is required to prove
behavior preservation, and otherwise record it as `Not run`.

#### Step 8: Incremental migration

- By default, do not stage or commit anything. Classify changes directly from
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

  Any hunk that does not fit these categories must be explained explicitly.
- Run tests, `ruff`, and `mypy` once per logical group identified via `git diff` (see
  Refactoring-Specific Guidance for scoping) — do not require staging hunks
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
  - If the user explicitly requests committing: create one rollback-safe commit per
    logical unit, ensure each commit passes the Step 10 completion gate before it is
    committed, and avoid interactive commands (e.g. `git rebase -i`) unless the
    environment explicitly supports them.

#### Step 9: CI gate

Refer to `rules/toolchain.md` for the full validation sequence. At minimum:
- Run `pre-commit run --all-files`.
- Run `lint-imports`.
- Run `diff-cover`.
- Review changes with `git log` and `git diff`.
- Ensure no legacy symbol names remain.

#### Step 10: Report results

##### ADR Requirement

An ADR is mandatory when the change is classified Path C (see `##### Path C:
Architectural Refactoring`). An ADR is optional, but permitted, for Path B when the
change records an important trade-off — a judgment call made by the AI executing this
workflow when choosing to write one; no further gating criteria are defined here.

ADR content produced by this Requirement follows the repository's existing convention —
`adr-template.md`'s section structure, standardized by
`docs/00_governance_01_documentation-policy.md` "ADR Section Header Standardization"
(canonical header order: Context [Problem, Constraints], Assumptions, Decision,
Rationale, Alternatives Considered, Consequences [Positive/Negative], Invariants,
Verification, Migration, Implementation Notes, Known Deviations, Review Triggers,
Approval, Related Documents, Change History, Completion Checklist), plus the `Status`
field governed by that same document's "ADR Status Definitions"
(`Proposed`/`Accepted`/`Rejected`/`Deprecated`/`Superseded`) — not a separate,
purpose-built field list. This never invents a new storage convention, location, or
template; any suggested field with no direct equivalent in the existing convention is
folded into its nearest existing section rather than added as a new top-level header.

`prompts/04_refactor.md`'s existing Core Rule ("Do not edit documentation unless
explicitly instructed") governs where this ADR content is written: Step 10 always
produces the ADR content, in the reconciled shape above, inline in the report as a
draft. Creating the file under `docs/adr/ADR-{next-number}-{slug}.md` and registering it
in `docs/adr-index.md`'s existing "ADR List" table and dependency graph happens only
when the user explicitly instructs a documentation update — this Requirement does not
relax or reinterpret the existing Core Rule, it states how the new ADR obligation
operates within it.

Keep diffs minimal. For each file, report:

- The Step 2 refactoring intent declaration.
- The Path A/B classification decided in Step 2 and its rationale.
- What changed and why.
- The Step 4 behavior lock manifest.
- The Step 5/7 side-effect inventory and confirmation that it is unchanged.
- The Step 7 public API stability check result.
- The Step 7 exception behavior freeze result.
- The Step 7 import boundary evidence, if imports changed.
- The Step 8 diff classification summary.
- **Conditional tool status**:
  - Which conditional tools were not run and why.
  - Whether any `Blocked` items remain.
- **Mutation testing evidence**:
  - Mutated paths
  - Number of mutations generated
  - Number of killed mutations
  - Number of surviving mutations
  - Number of equivalent mutations
  - Actions taken for surviving mutations
  - Tests added because of mutation results
  - Final mutation status

  A surviving mutation is acceptable only if it is explicitly classified as equivalent and
  the reason is documented.
- **Behavior preservation evidence**:
  - Baseline tests run before refactoring
  - Characterization tests added, if any
  - Public API signatures checked
  - Visible output checked, if applicable
  - Exception behavior checked
  - Side effects checked
  - Mutation testing result
  - Final validation result
- **Proposals not implemented**, for every behavior-changing idea that was not implemented,
  using this format:
  - Title:
  - Reason:
  - Behavior risk:
  - Affected files:
  - Suggested follow-up issue:
  - Recommended validation:
- **Technical Debt Findings**: report every Finding recorded by `##### Technical Debt
  Discovery` for the current target file/migration group, or `None found`.
- **Responsibility Analysis**: report the five fields recorded by `##### Responsibility
  Analysis` (responsibilities, dependencies, side effects, state ownership, branching)
  and any split candidate reported (not implemented) per that subsection's rule, or
  `Not applicable` if Responsibility Analysis was not run for this file.
- **Documentation Drift**: report every Drift Finding recorded by `##### Documentation
  Drift Detection`'s six-field schema during Step 3, or `None found`.
- **Architecture Baseline**: report the eight fields captured by `##### Architecture
  Baseline (Path C)` when the change is Path C, or `Not applicable` for Path A/B.
- **Architecture Before and After**: report the before/after comparison result for each
  item defined by `##### Path C: Architecture Comparison Validation`, each as
  `Pass`/`Fail`/`Not run`/`Blocked` per that subsection's reporting rule, or `Not
  applicable` for Path A/B.
- **Migration and Rollback Evidence**: report the atomic migration group's membership
  and completion state (per `##### Path C: Architectural Refactoring`) and the rollback
  strategy's exercisability (per that subsection's pre-implementation checklist item,
  cross-validated by `##### Path C: Architecture Comparison Validation`'s "Rollback
  validation" item), or `Not applicable` for Path A/B.
- **ADR Status**: report the ADR's `Status` value (per `##### ADR Requirement`'s
  convention) and whether the file was actually created under `docs/adr/` this cycle or
  remains a draft pending explicit documentation-update instruction, or `Not applicable`
  when no ADR was required or chosen for this change.

All seven items above use exactly the vocabulary `None found` / `Not applicable` /
`Not run` / `Blocked` where no positive finding exists, matching Step 7's existing
Conditional validation reporting pattern ("do not report the skipped check as passed").

**Completion gate.** The refactoring is complete only when all of the following are true:

- Target behavior is locked by tests or documented characterization evidence.
- External behavior is unchanged.
- Public APIs are unchanged.
- Visible output is unchanged.
- No new side effects are introduced.
- No unrelated files are modified.
- Required validation passes.
- Conditional validation items are reported with their actual status (`Not run` or `Blocked`).
- The final report includes behavior preservation evidence.
- Any behavior-changing ideas are recorded as proposals, not implemented.

**Path C completion requirements.** The following items apply only when the change is
classified Path C (see `##### Path C: Architectural Refactoring`); Path A/B completion
is unaffected, and these items are additive to, not a replacement for, the completion
requirements above:

- Behavior Lock completed — the Step 4 gate sentence ("Do not proceed to Step 6 ... if
  important behavior is uncovered ..."), unchanged by this Requirement.
- Architecture Baseline completed — `##### Architecture Baseline (Path C)`.
- Approved scope unchanged — `##### Path C: Architectural Refactoring`'s prohibition on
  silent expansion of an approved atomic migration group.
- Dependency direction verified — `##### Path C: Architecture Comparison Validation`'s
  "Before-and-after dependency comparison" and "Architecture-boundary comparison"
  items.
- No new circular dependency — the existing Step 7 "Import boundary evidence" item
  ("Circular import risk"), cross-checked by `##### Path C: Architecture Comparison
  Validation`'s "Architecture-boundary comparison" item.
- Ownership changes verified — `##### Path C: Architecture Comparison Validation`'s
  "Ownership validation" item.
- Migration completed — `##### Path C: Architectural Refactoring`'s atomic migration
  group membership, verified by `##### Path C: Architecture Comparison Validation`'s
  "Migration validation" item.
- Rollback strategy recorded or validated — `##### Path C: Architectural Refactoring`'s
  rollback-strategy pre-implementation checklist item, verified by `##### Path C:
  Architecture Comparison Validation`'s "Rollback validation" item.
- Removed references absent — `##### Path C: Architecture Comparison Validation`'s
  "Removed-symbol reference check" item.
- Documentation impact classified — `##### Documentation Drift Detection`, together
  with `##### Path C: Architectural Refactoring`'s "Documentation impact"
  pre-implementation checklist item.
- Required ADR completed — `##### ADR Requirement`.
- Path C validation passed — every `##### Path C: Architecture Comparison Validation`
  item reports `Pass`.
- Findings separated from implemented changes — `##### Discovery Vocabulary`'s
  Finding/Candidate/Proposal states do not authorize implementation; only an Approved
  Change may be transformed.

If any item is not satisfied, do not report the task as complete.

### Refactoring-Specific Guidance

- Perform Step 3 (preparation/investigation) sequentially; run `rg` always, and `pydeps`/`import-linter`/`ast-grep` only when Path B applies (see Step 3's Path A/B depth rule), retaining only the resulting impact scope table, not the raw tool output.
- Capture only error/summary lines from `mypy`, `pyright`, `ruff`, and test runs (e.g. via `grep` for failures) rather than full successful-run output.
- Scope `mypy`, `pyright`, `ruff`, and test runs to the target file or module wherever possible, rather than the whole repository.
- Scope `mutmut` to the changed paths only (`--paths-to-mutate`), not the whole repo.
- In Step 8, run the full mypy/test/ruff check once per logical diff group identified via `git diff` rather than after every single hunk; use a lighter check (e.g. `ruff` only) when inspecting individual hunks.
- In Step 9, prefer scoping `pre-commit` to the changed files over `--all-files` when the CI gate does not require a full-repo run.
- When multiple target files are specified, run each Steps 1-10 cycle sequentially so that tool output and investigation results from one file's cycle do not accumulate in the context used for the next file's cycle.
- Keep progress reports and Step 10 results concise; do not restate full diffs or raw tool output. Evidence tables (manifest, inventory, mutation report) must still list every required field even when kept concise.

### Special Cases

- If refactoring `tool_executor.py` or `route_resolver.py`, perform extra verification for MCP routing.
- If required, update `config/agent.toml`.
- If modules are added or removed, update:
  - `deploy.sh`
  - `routing.md`
  - `AGENTS.md`
