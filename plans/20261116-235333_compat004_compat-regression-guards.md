## Goal
Convert the workflow-definition and attempt-lease cleanup decisions made by the sibling issues into repository invariants in `tools/check_compat_shims.py` so that removed defaults (`RetryPolicy.retry_on`, `WorkflowDef.stages`, `WorkflowDef.retry_policy`), an optional/`lease_duration_sec`, nullable lease columns, and reintroduced current-tense "legacy age threshold" wording cannot silently return. The guards fail locally and in CI with a specific diagnostic. The existing `db.store` / `eventbus.db` name prohibitions stay unchanged.

## Priority
Medium

## Scope
- **In-Scope**: Add `ast`-based rules that fail when `RetryPolicy.retry_on`, `WorkflowDef.stages`, or `WorkflowDef.retry_policy` has a default or default factory; when the attempt writer or its `StateStore` facade accepts an optional or defaulted `lease_duration_sec`; and a source check that the canonical `attempts` DDL does not declare `owner_id` or `lease_expires_at` nullable; add a documentation check for current-tense `legacy age threshold` wording with an allowance for text marked `removed`/`historical`/`withdrawn`; add positive/negative/allowed-historical tests for every new rule; wire the new rules into `.pre-commit-config.yaml` and `.github/workflows/backward-compat-check.yml` if their file filters do not already cover the inspected files; update `tools/TOOL_DESCRIPTIONS.md` if the described behavior changes; keep the existing `db.store` / `eventbus.db` prohibitions unchanged; add no permanent production exception.
- **Out-of-Scope**: Changing the workflow definition, lease writer, schema, or documentation (sibling issues own those); re-adding or altering the `db.store` / `eventbus.db` rules; the EventBus facade question (`scripts/eventbus/db.py` is already deleted and guarded); broad refactoring of `tools/check_compat_shims.py`; any change that would make the checker fail on the current (pre-migration) source.
- **Dependencies**: The Issue depends on `issues/20261116-114753_compat001_workflow-definition-strict-contract.md` and `issues/20261116-114834_compat002_mandatory-attempt-leases.md` (the rules enforce the end state those issues create; the new rules would fail on the current source otherwise). Both have frozen Plans but neither is implemented yet (source still shows `retry_on` optional, `WorkflowDef.stages` with `default_factory=list`, and nullable lease columns).
  - **Depends on**: `plans/20261116-214100_compat001_workflow-definition-strict-contract.md` | phase 3 (implementation) | the loader/model contract that makes `retry_on` required and `stages`/`retry_policy` default-free pins which signal the AST rule must detect; sequencing-only, the guard enforces compat001's end state.
  - **Depends on**: `plans/20261116-221315_compat002_mandatory-attempt-leases.md` | phase 3 (implementation) | the schema-level `NOT NULL` lease columns and the always-stamped `lease_duration_sec` pin the DDL and writer/facade signals the guard must detect; sequencing-only, the guard enforces compat002's end state.

## Background
Explicit in code: `tools/check_compat_shims.py` already forbids `from db.store import`, `from eventbus.db import`, `import eventbus.db`, and `from eventbus import db` (the `compatrm003` pattern group, lines 123-127), and both `scripts/db/store.py` and `scripts/eventbus/db.py` are absent (confirmed in Step 2). The checker is wired into `.pre-commit-config.yaml` (`check-compat-shims`, running `--check-removed-names --check-doc-symbols`, filter `^(scripts/.*\.py|docs/.*\.md|tests/.*\.py|tools/(check_compat_shims\.py|_compat_leftover_phrases\.py|compat_exceptions\.toml))$`) and into `.github/workflows/backward-compat-check.yml` with the same flags. It uses regex pattern tables plus a few `ast`-based checks (`check_mcp_health_reexport_import`, `check_gateless_discovery_construction`, `check_removed_name_reintroduction` with `_is_historical_context` support); it has no check for dataclass field defaults, function-parameter defaults, or nullable DDL columns. The helper module `tools/_compat_leftover_phrases.py` already owns `LEFTOVER_PHRASES`, `check_leftover_phrases`, and a shared `python_nodes` AST parse, skips its own source, and was added the same way in `d0da368a7` (plan 20261112-122408, rmcompat008) — the established precedent for adding a rule. Current source is pre-migration: `workflow_loader.py:27` documents `retry_on` as optional, `models.py:89` gives `WorkflowDef.stages` a `default_factory=list`, and `schema_sql.py` keeps `owner_id` / `lease_expires_at` nullable — so every new rule would fail on the current committed source until the sibling issues land. Tests for the checker live in `tests/tools/test_check_compat_shims.py`, `tests/tools/test_compat_checker_precompiled.py`, and `tests/tools/test_no_compatibility_policy_gate.py`. The `tools/check_module_size_tools_baseline.txt` records `check_compat_shims.py` at 36235 B, near the 24576 B... (baseline is a separate gate; growth past a recorded size fails), so a new helper module may be required.

## Problem
The checker detects removed names, not removed behavior. Optional `retry_on`, a default `WorkflowDef.stages`/`retry_policy`, an optional `lease_duration_sec`, and nullable lease columns can all come back while every symbol name stays unchanged, so no current rule would fail. The "legacy age threshold" wording can also reappear in current-tense documentation without a rule to flag it. Without enforcement, the one-time cleanup in the sibling issues relies on manual review to stay in place.

## Reason for Change
Maintainability and regression-prevention. The one-time cleanup relies on manual review; converting it to a repository invariant that fails locally and in CI removes that reliance. The guards add value only after the sibling issues land, so this is not time-sensitive on its own — but freezing the plan now lets implementation start immediately once their source lands, without re-planning.

## Implementation Intent
Prefer small `ast`-based rules over regexes for signature and default checks, and a source check for the canonical DDL. Express each rule so it passes on the strict end state and fails on the reintroduced pattern, using the same issue-string shape as `check_compat_patterns` / `check_leftover_phrases`. Put new phrase/pattern tables in `tools/_compat_leftover_phrases.py` (mirroring the rmcompat008 precedent) rather than growing `check_compat_shims.py` past its baseline; add the DDL and parameter-default checks where they belong. Keep historical references legal when clearly marked `removed`/`historical`/`withdrawn`. Use the existing exception mechanism sparingly; add no permanent production exception. Wire the new rules into the pre-commit hook and CI, add positive/negative/allowed-historical tests, and run the full tool validation sequence.

## Requirements
- `REQ-001`: Add an `ast`-based rule that fails when `RetryPolicy.retry_on`, `WorkflowDef.stages`, or `WorkflowDef.retry_policy` has a default or default factory in the model/loader definitions. Passes on the strict end state created by `compat001`; fails on the current `default_factory=list` / optional source. (`tools/check_compat_shims.py`, `tools/_compat_leftover_phrases.py`)
- `REQ-002`: Add an `ast`-based rule that fails when the attempt writer or its `StateStore` facade accepts an optional or defaulted `lease_duration_sec`. Passes on the strict end state created by `compat002`; fails on the current optional source. (`tools/check_compat_shims.py`)
- `REQ-003`: Add a source check that the canonical `attempts` DDL (`scripts/db/schema_sql.py`) does not declare `owner_id` or `lease_expires_at` nullable. Passes on the strict end state created by `compat002`; fails on the current nullable DDL. (`tools/check_compat_shims.py`)
- `REQ-004`: Add a documentation check for current-tense `legacy age threshold` wording under `docs/`, with an allowance for text marked `removed`, `historical`, or `withdrawn`. (`tools/_compat_leftover_phrases.py`)
- `REQ-005`: Keep the existing `db.store` and `eventbus.db` prohibitions unchanged; they still fail on a reintroduced import. (`tools/check_compat_shims.py`)
- `REQ-006`: Add tests for every new rule: a positive case (reintroduction fails), a negative case (current/strict source passes), and an allowed historical reference. (`tests/tools/test_check_compat_shims.py`)
- `REQ-007`: Confirm the pre-commit hook's file filter and the CI path filter cover every file the new rules inspect; extend them if not. (`.pre-commit-config.yaml`, `.github/workflows/backward-compat-check.yml`)
- `REQ-008`: Update `tools/TOOL_DESCRIPTIONS.md` if the described behavior changes, in the same change, per `routing.md` "When to run which tool". (`tools/TOOL_DESCRIPTIONS.md`)

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/_compat_leftover_phrases.py` | Add the canonical `attempts` DDL nullability source check, the `ast`-based default/`lease_duration_sec` parameter rule, and the current-tense `legacy age threshold` doc phrase table; expose them via the shared `python_nodes` parse. Retains ~18 KB headroom under the 24576 B tools gate. | REQ-001, REQ-002, REQ-003, REQ-004; AC: reintroducing a default / optional lease param / nullable column / current-tense age wording fails. | Owns `LEFTOVER_PHRASES`, `check_leftover_phrases`, `python_nodes`; 5829 B today (Step 2). | `tests/tools/test_check_compat_shims.py` | Verified |
| `tools/check_compat_shims.py` | Wire the new checks into `check_all`; keep the file at or below its 36235 B baseline ceiling via net-size-neutral wiring or a controlled shrink. | REQ-001–REQ-005; AC: new rules run under `--check-removed-names --check-doc-symbols` and exit non-zero on reintroduction. | `check_all` wiring point confirmed; file is exactly at the 36235 B ceiling (Step 2). | None | Verified |
| `tests/tools/test_check_compat_shims.py` | Add a positive case (reintroduction fails), a negative case (strict source passes), and an allowed-historical case for every new rule. | REQ-006; AC: each new rule has positive/negative/allowed-historical cases. | Existing checker test file (Step 2). | `tests/tools/test_check_compat_shims.py` | Verified |

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
| `scripts/db/schema_sql.py` | Canonical `attempts` DDL for the `REQ-003` nullability check; confirm `owner_id` / `lease_expires_at` are nullable now and become `NOT NULL` after `compat002`. | `tools/_compat_leftover_phrases.py` (`REQ-003`) |
| `scripts/agent/workflow/models.py` | `WorkflowDef.stages` / `retry_policy` and `RetryPolicy.retry_on` definitions for the `REQ-001` default check; confirm the current `default_factory=list` and optional fields. | `tools/_compat_leftover_phrases.py` (`REQ-001`) |
| `scripts/agent/workflow/workflow_loader.py` | Current `retry_on`-optional contract (`_REQUIRED_POLICY_KEYS`) that the `REQ-001` guard enforces against once `compat001` makes it required. | `tools/_compat_leftover_phrases.py` (`REQ-001`) |
| Attempt writer and its `StateStore` facade | `REQ-002` signal for an optional/defaulted `lease_duration_sec`; path pinned by `compat002`'s implemented contract. | `tools/_compat_leftover_phrases.py` (`REQ-002`) |
| `tools/compat_exceptions.toml` | Confirm no permanent production exception is added for any removed behavior; exceptions stay fixture-only. | `tools/check_compat_shims.py` (`REQ-005`) |
| `tools/check_module_size_tools_baseline.txt` | Size gate ceiling: `check_compat_shims.py` frozen at 36235 B (cannot grow); `_compat_leftover_phrases.py` not baselined (under 24576 B). | `tools/check_compat_shims.py`, `tools/_compat_leftover_phrases.py` |
| `.pre-commit-config.yaml` | Confirm the `check-compat-shims` `files` filter already covers `scripts/**`, `docs/**`, `tests/**`, and both tool modules; Step 2 confirms it does, so no change is required. | `tools/check_compat_shims.py` (`REQ-007`) |
| `.github/workflows/backward-compat-check.yml` | Confirm the CI `paths` filter already covers every file the new rules inspect; Step 2 confirms it does, so no change is required. | `tools/check_compat_shims.py` (`REQ-007`) |
| `docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md` | Confirm the facade-prohibition description stays consistent with the unchanged `db.store` / `eventbus.db` rules; whether it needs any change is `Needs confirmation`. | `tools/check_compat_shims.py` (`REQ-005`) |
| `plans/20261116-214100_compat001_workflow-definition-strict-contract.md` | Frozen contract pinning the `retry_on`-required / default-free end state the `REQ-001` guard enforces. | `tools/_compat_leftover_phrases.py` (`REQ-001`) |
| `plans/20261116-221315_compat002_mandatory-attempt-leases.md` | Frozen contract pinning the `NOT NULL` lease columns and always-stamped `lease_duration_sec` end state the `REQ-002`/`REQ-003` guards enforce. | `tools/_compat_leftover_phrases.py` (`REQ-002`, `REQ-003`) |
| `tools/TOOL_DESCRIPTIONS.md` | Read to determine whether the expanded rule set changes the described behavior; update in the same change if so. | `tools/check_compat_shims.py` (`REQ-008`) |

## Acceptance Criteria
- [ ] Reintroducing a default on `RetryPolicy.retry_on`, `WorkflowDef.stages`, or `WorkflowDef.retry_policy` fails the checker with a specific diagnostic. (`REQ-001`, AC line 53)
- [ ] Making `lease_duration_sec` optional or defaulted in the attempt writer or facade fails the checker. (`REQ-002`, AC line 55)
- [ ] Making either canonical lease column nullable fails the checker or a schema test. (`REQ-003`, AC line 55)
- [ ] Current-tense `legacy age threshold` wording in `docs/` fails the checker; text marked historical does not. (`REQ-004`, AC line 56)
- [ ] The existing `db.store` and `eventbus.db` prohibitions still fail on a reintroduced import. (`REQ-005`, AC line 57)
- [ ] Each new rule has positive, negative, and allowed-historical test cases. (`REQ-006`, AC line 58)
- [ ] The pre-commit hook and the CI job run the checker mode that includes the new rules. (`REQ-007`, AC line 59)
- [ ] The checker stays under its size gates: `check_compat_shims.py` at or below 36235 B, `_compat_leftover_phrases.py` under 24576 B. (`REQ-001`–`REQ-003`)
- [ ] No permanent production exception is added for any removed behavior. (`Implementation Intent`)

## Tests
- Unit tests in `tests/tools/test_check_compat_shims.py`: for each new rule, a positive case (isolated fixture reintroduces the prohibited default / optional param / nullable column / current-tense wording and fails), a negative case (current/strict source passes), and an allowed-historical case (text marked `removed`/`historical`/`withdrawn` passes). (`REQ-001`–`REQ-004`)
- A regression case confirming the unchanged `db.store` / `eventbus.db` prohibitions still fail on a reintroduced import. (`REQ-005`)
- Run `uv run pytest tests/tools -v` and `uv run pytest -m repo_scan -v`. (`Testing Expectations`)
- Run `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` against the live repository and confirm it passes (zero findings) after the sibling issues land. (`Testing Expectations`)
- Run `uv run python tools/check_tool_descriptions_sync.py`, `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`, and `uv run ruff format` / `ruff check` / `mypy` / `bandit` on the changed tool. (`Testing Expectations`, `routing.md` "Adding a new tool")
- Confirm by inspection that `.pre-commit-config.yaml` and `.github/workflows/backward-compat-check.yml` invoke the checker with the new rules enabled. (`REQ-007`, `Testing Expectations`)

## Documentation Impact
`tools/TOOL_DESCRIPTIONS.md` only: if the expanded rule set changes the checker's described behavior, update its row in the same change per `routing.md` "When to run which tool" (`check_tool_descriptions_sync.py` fails when a tool's description refers to behavior that no longer matches). No `docs/*.md` is modified by this Plan — the workflow/lease documentation is owned by the sibling issues. Whether `docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md` needs a consistency edit is `Needs confirmation` (Reference Files).

## Assumptions
- The default / optional-parameter checks can be expressed robustly with `ast`: the checker already runs two always-on `ast` rules (`check_mcp_health_reexport_import`, `check_gateless_discovery_construction`) and the helper exposes a shared `python_nodes` parse, so AST-based detection is proven-feasible in this codebase. This resolves `UNK-01` as non-blocking.
- New rule logic belongs in `tools/_compat_leftover_phrases.py` (the rmcompat008 precedent), not in `check_compat_shims.py`, because the latter is exactly at its 36235 B baseline ceiling and cannot grow. This resolves `UNK-02` as non-blocking and makes module-size a design constraint, not a blocker.
- The `legacy age threshold` doc check belongs in `_compat_leftover_phrases.py` alongside the other path-scoped phrase tables, using the existing `_is_historical_context` allowance for `removed`/`historical`/`withdrawn` markers. This resolves `UNK-03`.
- The `.pre-commit-config.yaml` and `.github/workflows/backward-compat-check.yml` filters already cover every file the new rules read (`scripts/**`, `docs/**`, `tests/**`, both tool modules); Step 2 confirmed both filters include these paths, so REQ-007's "extend if not" resolves to "no change needed."
- Freezing this plan now is correct even though all implementation is gated on `compat001`/`compat002`: the plan documents the design and the gating; it does not implement. This matches the established queue pattern (each issue → plan → archive → commit).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Can the default and optional-parameter checks be expressed robustly with `ast` against the model and writer definitions, or is a narrow pattern rule enough? | None — two `ast` rules already run in the checker and `python_nodes` is shared. | Resolved: prefer `ast`; finalize exact node predicates against the implemented `compat001`/`compat002` contract at implementation. | False |
| UNK-02 | Does the checker's file-size baseline force a new module? | None — `_compat_leftover_phrases.py` exists at 5829 B with ~18 KB headroom. | Resolved: add rules to the existing helper; keep it under 24576 B. | False |
| UNK-03 | Where does the `legacy age threshold` doc check belong — `_compat_leftover_phrases.py` or a separate checker? | None — the helper owns path-scoped phrase tables and the historical-marker allowance. | Resolved: put it in `_compat_leftover_phrases.py` (`REQ-004`). | False |
| UNK-04 | How to wire the new checks into `check_all` without growing `check_compat_shims.py` past 36235 B? | None yet — the net-size-neutral wiring approach is not pinned. | Resolve at implementation: extract an existing check into the helper or apply a controlled shrink to create room; the baseline permits shrinking. | False |

No item from Step 2 remains `Needs confirmation`; nothing is `BLOCKING`.

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/_compat_leftover_phrases.py` | Modify | Low — tooling only; a failing rule fails locally and in CI, not runtime | Multiple contributors | not applicable (rsynced) |
| `tools/check_compat_shims.py` | Modify | Low — tooling only; gated by the 36235 B size ceiling | Multiple contributors | not applicable (rsynced) |
| `tests/tools/test_check_compat_shims.py` | Modify | Low — test-only | Multiple contributors | not applicable (rsynced) |

## Design
Three design decisions the Issue left open are resolved below with rationale and compatibility impact.

### Decision 1 — Where the new rules live: the helper module, not `check_compat_shims.py`
- **Choice**: put the DDL nullability check, the default/`lease_duration_sec` AST rule, and the `legacy age threshold` doc phrase table in `tools/_compat_leftover_phrases.py`; wire them into `check_all` from `check_compat_shims.py`.
- **Alternatives considered**: adding the rules directly to `check_compat_shims.py`. That file is exactly at its 36235 B baseline ceiling and cannot grow, so any addition fails `check_module_size.py`.
- **Rationale for the choice**: `_compat_leftover_phrases.py` owns the shared `python_nodes` AST parse and path-scoped phrase tables, sits at 5829 B (~18 KB headroom under the 24576 B tools gate), and was added the same way in the rmcompat008 precedent (`d0da368a7`). This resolves `UNK-02` and keeps both modules within their gates.
- **Compatibility impact**: `check_compat_shims.py` must stay ≤ 36235 B; wiring is net-size-neutral or a controlled shrink (`UNK-04`).

### Decision 2 — `ast` over regex for defaults and parameters
- **Choice**: express the `retry_on` / `stages` / `retry_policy` default check and the `lease_duration_sec` optional-parameter check as `ast` rules (walk the dataclass fields / function signatures), and a source-text check for the canonical `attempts` DDL nullability.
- **Alternatives considered**: a narrow regex on the source. A regex cannot reliably distinguish a real default from a coincidental token and would need exceptions to pass on current code.
- **Rationale for the choice**: the checker already runs two always-on `ast` rules; `ast` distinguishes a genuine `default`/`default_factory` / optional parameter from incidental text, so the rule passes on the strict end state and fails on reintroduction without exceptions. Finalize the exact node predicates against the implemented `compat001`/`compat002` contract (`UNK-01`).
- **Compatibility impact**: the rule must be pinned to the signal each sibling issue actually removes (loader-required vs dataclass-default-free); verify which signal disappears once they land.

### Decision 3 — Gated implementation, frozen plan now
- **Choice**: freeze the plan now with all implementation gated behind `compat001` and `compat002` implementing; Phase 1 is verification/wiring prep, Phases 2-3 add the rules once the strict source exists.
- **Alternatives considered**: do not create a plan until the siblings land. That stalls the single-issue queue and loses the design review benefit.
- **Rationale for the choice**: the rules would fail on the current (pre-migration) source, so implementation is correctly deferred; freezing the plan now lets implementation start immediately once their source lands, matching the queue's per-issue plan-then-archive pattern.
- **Compatibility impact**: no code changes in this phase; the plan is document-only.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`.

1. **Phase 1: Verify signals and prepare wiring (source still pre-migration)**
   - [ ] REQ-007; confirm `.pre-commit-config.yaml` and `.github/workflows/backward-compat-check.yml` already cover every file the new rules inspect; record "no change needed".
   - [ ] REQ-001–REQ-003; pin the exact `ast` node predicates and the DDL column names against the current source and the frozen `compat001`/`compat002` contracts; record which signal each rule detects.
   - [ ] REQ-005; confirm `tools/compat_exceptions.toml` needs no new entry and `docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md` stays consistent.
   - [ ] Determine the net-size-neutral wiring into `check_all` that keeps `check_compat_shims.py` ≤ 36235 B (`UNK-04`).
2. **Phase 2: Add the rules (gated on `compat001`/`compat002` implementing)**
   - [ ] REQ-001; `tools/_compat_leftover_phrases.py` — add the `RetryPolicy.retry_on` / `WorkflowDef.stages` / `WorkflowDef.retry_policy` default + default-factory AST rule.
   - [ ] REQ-002; `tools/_compat_leftover_phrases.py` — add the attempt writer / `StateStore` facade optional-or-defaulted `lease_duration_sec` AST rule.
   - [ ] REQ-003; `tools/_compat_leftover_phrases.py` — add the canonical `attempts` DDL `owner_id` / `lease_expires_at` non-nullability source check.
   - [ ] REQ-004; `tools/_compat_leftover_phrases.py` — add the current-tense `legacy age threshold` doc phrase table with the `removed`/`historical`/`withdrawn` allowance.
   - [ ] REQ-001–REQ-005; `tools/check_compat_shims.py` — wire the new checks into `check_all` net-size-neutrally (≤ 36235 B).
3. **Phase 3: Tests, gates, and tool-description sync**
   - [ ] REQ-006; `tests/tools/test_check_compat_shims.py` — positive/negative/allowed-historical tests for each new rule plus the unchanged `db.store`/`eventbus.db` regression case.
   - [ ] REQ-008; `tools/TOOL_DESCRIPTIONS.md` — update the checker's row if the expanded rule set changes its described behavior, in the same change.
   - [ ] Run ruff format/check, mypy, bandit, `check_tool_descriptions_sync.py`, `check_module_size.py --scripts-dir tools`, and `pytest -m repo_scan`; confirm the live `--check-removed-names --check-doc-symbols` run passes.

### Release units
N/A: no release unit. The rules are additive guards; they fail on reintroduced patterns, they do not break existing callers or tests before another phase lands.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/_compat_leftover_phrases.py` | New rules pass on strict source, fail on reintroduced default/optional-param/nullable/current-tense wording; historical-marked text allowed. | `uv run pytest tests/tools -v`, `uv run pytest -m repo_scan -v` | All pass; each rule has positive/negative/allowed-historical cases. |
| `tools/check_compat_shims.py` | New rules wired into `check_all`; live run passes; size ≤ 36235 B. | `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols`; `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Live run exits 0; module-size gate passes. |
| `tools/check_compat_shims.py`, `tools/_compat_leftover_phrases.py` | Lint / type / security gates. | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit` | Clean. |
| `tools/TOOL_DESCRIPTIONS.md` | Tool-description sync after behavior change. | `uv run python tools/check_tool_descriptions_sync.py` | Passes; row updated in same change. |
| `.pre-commit-config.yaml`, `.github/workflows/backward-compat-check.yml` | Confirm filters cover inspected files. | Manual inspection | Confirmed covered (no change). |

## Risks
- **Risk**: Adding rules to `check_compat_shims.py` grows it past the 36235 B baseline ceiling and fails `check_module_size.py`. → **Mitigation**: route all new logic through `_compat_leftover_phrases.py` (18 KB headroom); keep `check_compat_shims.py` net-size-neutral via a controlled shrink or by extracting an existing check into the helper (Decision 1, `UNK-04`).
- **Risk**: An `ast` default/parameter rule that is too broad fails on the current pre-migration source (which still has the optional/default fields), blocking implementation. → **Mitigation**: implement only after `compat001`/`compat002` land; pin the exact node predicate to the signal each issue removes (Decision 2).
- **Risk**: The nullable-column DDL check or the doc-phrase check over-deletes legitimate historical context. → **Mitigation**: the doc check allows `removed`/`historical`/`withdrawn` markers; the DDL check targets the canonical `attempts` table only.
- **Risk**: Naming a runbook/command or schema symbol that does not exist. → **Mitigation**: confirm `owner_id` / `lease_expires_at` column names and the canonical DDL location against `scripts/db/schema_sql.py` at implementation.
- **Risk**: A permanent production exception is added to keep a rule passing. → **Mitigation**: the Issue forbids permanent exceptions; a rule that cannot pass without one must be made precise or dropped (`AI Implementation Instruction`).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify signals and prepare net-size-neutral wiring | Pending | — | — | Source still pre-migration; prepare now |
| 2 | Add the four rules to `_compat_leftover_phrases.py` and wire into `check_all` | Pending | — | — | Gated on `compat001`/`compat002` implementing |
| 3 | Tests, size/lint/type/security gates, tool-description sync | Pending | — | — | After rules land |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261116-114953_compat004_compat-regression-guards.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261116-235333
- **Related target files**: `tools/_compat_leftover_phrases.py`, `tools/check_compat_shims.py`, `tests/tools/test_check_compat_shims.py` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (default rule); AC line 53 | `tools/_compat_leftover_phrases.py`, `tools/check_compat_shims.py` | Step 2 | Reintroducing a default fails with a specific diagnostic | `pytest tests/tools -v`; `pytest -m repo_scan` | Derived from confirmed evidence |
| REQ-002 | Required Changes (lease param rule); AC line 55 | `tools/_compat_leftover_phrases.py` | Step 2 | Optional/defaulted `lease_duration_sec` fails | `pytest tests/tools -v` | Derived from confirmed evidence |
| REQ-003 | Required Changes (DDL nullability); AC line 55 | `tools/_compat_leftover_phrases.py` | Step 2 | Nullable lease column fails the checker or a schema test | `pytest tests/tools -v` | Confirmed: columns nullable now (`schema_sql.py`) |
| REQ-004 | Required Changes (doc phrase rule); AC line 56 | `tools/_compat_leftover_phrases.py` | Step 2 | Current-tense age wording fails; historical does not | `pytest tests/tools -v` | Derived from confirmed evidence |
| REQ-005 | Required Changes (keep prohibitions); AC line 57 | `tools/check_compat_shims.py` | Step 2 | Existing `db.store`/`eventbus.db` prohibitions still fail | regression test | Confirmed: patterns present (`check_compat_shims.py:123-127`) |
| REQ-006 | Required Changes (tests); AC line 58 | `tests/tools/test_check_compat_shims.py` | Step 3 | Each rule has positive/negative/allowed-historical cases | `pytest tests/tools -v` | Derived |
| REQ-007 | Required Changes (hook/CI filter); AC line 59 | `.pre-commit-config.yaml`, `.github/workflows/backward-compat-check.yml` | Step 1 | Hook and CI run the mode with new rules enabled | manual inspection | Confirmed: filters already cover inspected paths |
| REQ-008 | Required Changes (tool description); Testing Expectations | `tools/TOOL_DESCRIPTIONS.md` | Step 3 | Description reflects expanded behavior if changed | `check_tool_descriptions_sync.py` | Needs confirmation at implementation |
