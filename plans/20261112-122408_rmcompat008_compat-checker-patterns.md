## Goal
- Make a removed compatibility leftover fail `tools/check_compat_shims.py` when it returns: add path-scoped phrase patterns for the leftover kinds found in the review (each with a positive and a negative test fixture) and trim `_HISTORICAL_CONTEXT_MARKERS` to the markers the live documents still need. The exemption mechanism stays fixture-only and no exemption is widened.

## Priority
Low

## Scope
- **In-Scope**: a new helper module `tools/_compat_leftover_phrases.py` holding eleven path-scoped phrase patterns and their check (including one phrase that spans two lines); its call from `check_all` in `tools/check_compat_shims.py`; the reduction of `_HISTORICAL_CONTEXT_MARKERS` from twelve entries to the two that are needed (`legacy`, `removed`); tests; the `tools/TOOL_DESCRIPTIONS.md` rows; adding the helper to the path filters of the existing pre-commit hook and CI workflow so a change to it still runs the check (fallout, see Background).
- **Out-of-Scope**: removing the current matches (rmcompat007); the documentation forbidden-pattern list and severity (adrrev018); the checker's exemption policy and `tools/compat_exceptions.toml`; the phrase "replaces the" (see UNK-03); any edit to a source that currently matches.
- **Dependencies**: The patterns can be enforced only after the sweep Plan removes the matches they would find in `scripts/`.
  - **Depends on**: plans/20261112-122030_rmcompat007_history-comment-sweep.md | phase all | the patterns match comment and docstring text the sweep rewrites; the checker must pass on the repository when this Plan lands.

## Background
Re-verified 2026-11-12 (Step 2 and Step 3):
- `tools/check_compat_shims.py` runs `COMPAT_PATTERNS` (line-based, case-insensitive, every scanned file), `ADR_PROHIBITED_PATTERNS`, two syntax-tree rules, and (with `--check-removed-names`) `check_removed_name_reintroduction()`, which is the only user of `_HISTORICAL_CONTEXT_MARKERS` (line 494, docs only). `COMPAT_PATTERNS` has no historical-context exemption. The default scan is `scripts/`, `docs/`, `tests/`, and `tools/` (`*.py` and `*.md`; `*.md` under `done/` skipped); `config/*.toml` is not scanned.
- The checker passes today (`All checks passed`, per the Issue).
- Measured on the live repository on 2026-11-12 (case-insensitive, same files as the checker), lines per directory (scripts / docs / tests / tools): "Extracted from" 59 / 6 / 3 / 1; "Refactored:" 2 / 0 / 0 / 0; "Precedent:" 3 / 0 / 3 / 0; "signature stability" 3 / 0 / 0 / 0; "re-exported for" 1 / 0 / 0 / 1; "predates" 0 / 1 / 0 / 0; "user-approved" 0 / 0 / 0 / 0; "pre-migration gate|database" 2 / 0 / 0 / 1; "additive (wire) field" 1 / 2 / 0 / 0; "bypass(es) build_db_config" 3 / 0 / 1 / 0 (the `scripts` matches are `ingester.py:116`, `crawler.py:95`, and the documented current behavior of `SQLiteHelper` at `scripts/db/helper.py:77`); "replaces the old|previous|former|legacy" 1 / 1 / 1 / 2; bare "bypass" 23 / 55 / 82 / 5 and bare "replaces the" 7 / 10 / 50 / 5; "mirror... exactly" 1 / 0 / 1 / 0.
- `tools/check_compat_shims.py` is 36243 bytes; the tools size baseline records 36263 (`tools/check_module_size_tools_baseline.txt:4`) and only shrinks, so new code cannot be added to the module.
- Measured by running `check_removed_name_reintroduction()` over every non-`done` document with each marker removed in turn and with subsets: no findings with only `legacy` and `removed`; the greedy minimal cover is exactly those two; with an empty set there are 9 findings. The Japanese markers are not needed (documents are English only, `tools/check_docs_japanese.py`).
- `tests/tools/test_check_compat_shims.py` is already a `fixture` exemption (`tools/compat_exceptions.toml:169`); the checker's own source is exempt through `[checker_self_reference]`.

Corrections found against the Issue's claims:
- Patterns apply to every scanned file, not only `scripts/` and `docs/`: unscoped phrases would also hit `tests/` (for example three "Extracted from" and three "Precedent:" lines) and `tools/` (including the checker's own pattern text), which the Issue forbids exempting. The patterns are therefore scoped by path prefix.
- The Issue's open question "how to scope bypass, additive, and replaces the" is answered from the measurements above: "bypass" is scoped to the ingestion modules' meaning (`scripts/rag/`), because `SQLiteHelper`'s documented bypass is current behavior; "additive" is scoped to "additive wire field"; "replaces the" is deferred because one residual `scripts/` match (`scripts/eventbus/auth.py:134`, a docstring history note) needs a source edit that this Issue forbids.
- The Issue says `_HISTORICAL_CONTEXT_MARKERS` "lets a historical note pass"; it does so only for the opt-in removed-name check in documents, not for the compatibility patterns, so the trim cannot let a new leftover through or block one.
- A new module is required (the size baseline), and the existing pre-commit hook (`files:` regex) and CI workflow (`paths:` lists) name `tools/check_compat_shims.py` and `tools/compat_exceptions.toml` only; without adding the helper there, a change to the helper alone would not run the check. The Issue lists CI wiring as out of scope; the two edits only extend the path filters and change no behavior (UNK-02).
- `docs/00_governance/governance_04_documentation-checks.md` section 4 describes the check by scanned directories and intent and lists no patterns, so it needs no change.

## Problem
Every leftover found in the review was found by reading code. Without new patterns the same kinds of compatibility wording return unnoticed, and a marker set larger than necessary hides how little the removed-name exemption actually depends on.

## Reason for Change
Manual review does not scale; the checker already runs in CI, in pre-commit, and in the validation gates, so extending it is the cheapest way to keep the cleanup from regressing. Low urgency: it only prevents recurrence.

## Implementation Intent
- Each kind of leftover fails the checker automatically, with patterns specific enough that ordinary words do not cause false positives, and with a path scope that avoids `tests/` and `tools/` so no exemption is needed.
- The exemption mechanism stays fixture-only; the pattern text is written in self-safe form (character classes) so the checker's own source does not match.

## Requirements
- `REQ-001`: `tools/_compat_leftover_phrases.py` defines the eleven patterns below, each with a path scope, and `check_all` runs the check; re-adding any phrase in its scope makes `main()` exit non-zero. Patterns: `Extracted from`, `Refactored:`, `Precedent:`, `signature stability`, `re-exported for`, `predates`, `user-approved`, `pre-migration gate|database`, `additive (wire) field` (all under `scripts/`; `user-approved` also under `docs/`), `bypass(es) build_db_config` (under `scripts/rag/`), and a multi-line `mirror... exactly`.
- `REQ-002`: A phrase split across two adjacent lines is detected by testing each line joined with its successor.
- `REQ-003`: `tests/tools/test_check_compat_shims.py` has one failing fixture per pattern, a passing fixture that shows each ordinary use (bare "bypass" outside `scripts/rag/`, "replaces the oldest turns", "additive" in other prose), and a scope test; fixture phrases are built by concatenation so the test file needs no new exemption.
- `REQ-004`: `_HISTORICAL_CONTEXT_MARKERS` is `{legacy, removed}`; the fixtures that used other markers use these; `check_removed_name_reintroduction()` still reports no finding on the live documents.
- `REQ-005`: The helper is in the `files:` filter of the `check-compat-shims` hook and in both `paths:` lists of the workflow.
- `REQ-006`: `tools/TOOL_DESCRIPTIONS.md` describes the changed behavior and the helper; ruff, mypy, bandit, `check_tool_descriptions_sync.py`, and the tools module-size gate pass for the changed files.
- `REQ-007`: After the sweep Plan lands, `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` passes on the repository with no new exemption; the matches before and after are recorded.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/_compat_leftover_phrases.py` | Leftover phrase table and check | New file: the path-scoped patterns and `check_leftover_phrases()` including the adjacent-line join | REQ-001, REQ-002 / AC-1, AC-2 | the checker is 36243 bytes against a 36263-byte baseline, so new code cannot go in it (`tools/check_module_size_tools_baseline.txt:4`); `tools/` contains private helpers such as `_contract_manifests.py` (checked in Step 3) | `tests/tools/test_check_compat_shims.py` | Verified |
| `tools/check_compat_shims.py` | Checker | Import and call the helper in `check_all`; reduce `_HISTORICAL_CONTEXT_MARKERS` to `legacy` and `removed` | REQ-001, REQ-004 / AC-1, AC-4 | `check_all` lines 657-689; markers lines 344-363; sole marker use line 494 (checked in Step 2) | `tests/tools/test_check_compat_shims.py` | Verified |
| `tests/tools/test_check_compat_shims.py` | Checker tests | Add the pattern, scope, negative, and marker tests; move the three fixtures that use other markers | REQ-003, REQ-004 / AC-3, AC-4 | fixtures at lines 386-402, 427-432, 511-514 use `resolved` and `historical`; file is a `fixture` exemption at `compat_exceptions.toml:169` (checked in Step 3) | itself | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Tool documentation | Update the two `check_compat_shims.py` rows; add the private-helper row | REQ-006 / AC-6 | rows at lines 83 and 178; private-helper rows such as line 116 (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |
| `.pre-commit-config.yaml` | Hook path filter | Add the helper to the `files:` regex of `check-compat-shims` | REQ-005 / AC-5 | line 41 names only `check_compat_shims.py` and `compat_exceptions.toml` (checked in Step 2) | `tools/check_tool_descriptions_sync.py` | Verified |
| `.github/workflows/backward-compat-check.yml` | CI path filter | Add the helper to the `push` and `pull_request` `paths:` lists | REQ-005 / AC-5 | lines 9-10 and 16-17 (checked in Step 2) | `tools/check_tool_descriptions_sync.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/compat_exceptions.toml` | Fixture-only manifest and `[checker_self_reference]`; not edited (self-safe regexes and concatenated fixtures need no entry) | REQ-003, REQ-007 |
| `tools/check_module_size_tools_baseline.txt` | Records the 36263-byte ceiling for `check_compat_shims.py` | REQ-001 |
| `docs/00_governance/governance_04_documentation-checks.md` | Section 4 describes the check by scope and intent only; no pattern list to update | REQ-006 |
| `plans/20261111-111505_adrrev018_docs-checker-harden.md` | Owns the documentation history-phrasing rules in `config/doc_quality_rules.json`; avoids double ownership | REQ-001 |
| `scripts/db/helper.py` | The documented current "bypass" of `build_db_config()` that the scoped pattern must not flag | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001): for each of the eleven patterns a test writes the phrase into a file under its scope and `check_all` reports an issue naming the pattern; `main()` exits 1 on such a file.
- AC-2 (REQ-002): a test splits the `mirror... exactly` phrase over two lines and the check reports it.
- AC-3 (REQ-003): ordinary uses (bare "bypass" outside `scripts/rag/`, "replaces the oldest turns", unrelated "additive") produce no issue; a phrase outside its scope produces no issue.
- AC-4 (REQ-004): `_HISTORICAL_CONTEXT_MARKERS == frozenset({"legacy", "removed"})`; the removed-name tests pass; `uv run python tools/check_compat_shims.py --check-removed-names` reports no finding on the documents.
- AC-5 (REQ-005): the hook `files:` regex and both workflow `paths:` lists include `tools/_compat_leftover_phrases.py`.
- AC-6 (REQ-006): `uv run ruff`, `uv run mypy tools/_compat_leftover_phrases.py tools/check_compat_shims.py`, `uv run bandit`, `check_tool_descriptions_sync.py`, and both `check_module_size.py` invocations pass.
- AC-7 (REQ-007): `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` exits 0 on the repository after the sweep Plan lands; `compat_exceptions.toml` is unchanged.

## Tests
- REQ-001, REQ-002: a parametrized positive test over the pattern table (fixture text built by concatenation, written under a `tmp_path` that mimics `scripts/...`), plus the two-line case.
- REQ-003: parametrized negative tests and an out-of-scope test.
- REQ-004: a marker-set test and the updated removed-name fixtures.
- REQ-007: a smoke run on live repository data, recording the matches before and after the sweep (`routing.md` "Adding a new tool" step 4).

## Documentation Impact
- Documentation must be updated only in `tools/TOOL_DESCRIPTIONS.md` (REQ-006); `governance_04` needs no change because it lists scanned directories and intent, not patterns. Run `check_tool_descriptions_sync.py`.

## Assumptions
- The meaning of each phrase is the compatibility-leftover meaning the review found, expressed as the scoped regex; the maintainer can narrow or drop one at the procedure step without changing the structure (UNK-01).
- A pattern whose live match count is not zero after the sweep Plan lands is not enabled: the procedure stops and reports instead of adding an exemption (Issue AI Implementation Instruction). Today every selected pattern's `scripts/` matches are in files the earlier Plans or the sweep edit; `bypass(es) build_db_config` is limited to `scripts/rag/` so `scripts/db/helper.py` is not hit.
- Pattern text uses character classes (for example `Extracted[ ]from`) so neither the helper nor the checker matches its own source, as the existing tables do; if a literal cannot be avoided, the fallback is the existing `[checker_self_reference]` table, reported rather than widened.
- Step 8b overlap judgement (`tools/check_plan_target_overlaps.py`): `tools/TOOL_DESCRIPTIONS.md` with `plans/20261111-111505_adrrev018_docs-checker-harden.md` is compatible (that Plan updates the rows of the documentation checkers; this Plan updates the two `check_compat_shims.py` rows and adds one private-helper row, so re-read the file first); the checker, helper, test, hook, and workflow files are not targets of any other Frozen Plan, and the adrrev005 Plan that touched `check_compat_shims.py` has landed.
- The severity of the new patterns is blocking (exit non-zero), the behavior of every `COMPAT_PATTERNS` entry and the Issue's acceptance criteria; the documentation side of the same phrases is left to the adrrev018 rules.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the maintainer agrees with the scoped meaning and the `scripts/`-only scope of each pattern (and whether any should also cover `docs/`) | Maintainer decision | The Plan fixes a default from measurements; the user can adjust a row before the procedure step | False |
| UNK-02 | Whether adding the helper to the hook and workflow path filters is acceptable although the Issue lists CI wiring as out of scope | User decision | The edits only extend path filters (fallout); if rejected, put the table in a file those filters already watch | False |
| UNK-03 | How to handle "replaces the old/previous/...": one residual `scripts/` match (`scripts/eventbus/auth.py:134`) needs a source edit outside this Issue | Decision which Plan edits it | Deferred; extend the sweep Plan's patterns or fix the line in the EventBus Plan, then add the pattern | False |
| UNK-04 | Whether the checker passes on the repository after the sweep Plan lands (residual matches in `scripts/`) | The state after the sweep | Measured by the smoke run at the procedure step; any residual match removes that pattern from this change and is reported | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/_compat_leftover_phrases.py` | Create | Medium | N/A | N/A | not applicable (tools/ is not deployed) |
| `tools/check_compat_shims.py` | Modify | High | 15 | N/A | not applicable (tools/ is not deployed) |
| `tests/tools/test_check_compat_shims.py` | Modify | Low | 9 | N/A | not applicable (tests are not deployed) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | 73 | N/A | not applicable (tools/ is not deployed) |
| `.pre-commit-config.yaml` | Modify | Medium | 9 | N/A | not applicable (not deployed) |
| `.github/workflows/backward-compat-check.yml` | Modify | Medium | 3 | N/A | not applicable (not deployed) |

## Design
- Consumer scan: the checker's callers are the pre-commit hook, the CI workflow, and `tools/run_validation_gates.py` (its `check_compat_shims` gate runs the checker with defaults and has no path patterns, so the new helper needs no mapping there; `routing.md` lists the same default invocation); the change adds a new finding source and keeps the exit-code contract (non-zero on any issue). A text search of `tools/` and `.github/` found no other reference to `_HISTORICAL_CONTEXT_MARKERS` than line 494.
- Helper shape: `LEFTOVER_PHRASES: dict[str, tuple[re.Pattern[str], tuple[str, ...], bool]]` mapping a name to a compiled regex, path prefixes relative to the repository root, and a multi-line flag; `check_leftover_phrases(content, filepath, allowlist)` returns issue strings in the same format as `check_compat_patterns`, skips allowlisted files and files outside every prefix, and for a multi-line pattern tests each stripped line joined with the next. `check_all` calls it after `check_adr_prohibited_patterns`.
- Size: moving the check into the helper keeps `check_compat_shims.py` below its baseline (net change is an import and a call line against the removal of ten marker entries and a comment block).
- Alternatives rejected: putting the table in `check_compat_shims.py` (exceeds the 36263-byte baseline); unscoped phrases (hit `tests/` and `tools/` and force exemptions); bare "bypass", "additive", and "replaces the" (hundreds of ordinary uses).
- Architecture: `tools/` is checked by `lint-imports` only through `scripts` roots; the helper imports the standard library only. `radon`, `vulture`, and `bandit` baselines are recorded in the rmcompat001 Plan Design; `bandit` runs on the new file. No persisted schema, port, process, or dependency change (`rules/persisted-schema-change.md`, `ss`, `fuser`, `pip-audit` N/A). Churn above from `git log --since=30.days`; bus factor not measured.

## Implementation steps
1. **Phase 1: Marker set**
   - [ ] Measure the marker need again on the live documents, reduce the set to `legacy` and `removed`, and move the fixtures that use other markers (REQ-004; `tools/check_compat_shims.py`, `tests/tools/test_check_compat_shims.py`)
2. **Phase 2: Leftover phrase check**
   - [ ] Add the helper with the eleven scoped patterns and the adjacent-line join (REQ-001, REQ-002; `tools/_compat_leftover_phrases.py`)
   - [ ] Call it from `check_all` (REQ-001; `tools/check_compat_shims.py`)
   - [ ] Add the positive, negative, scope, and two-line tests (REQ-003; `tests/tools/test_check_compat_shims.py`)
   - [ ] Add the helper to the hook and workflow path filters (REQ-005; `.pre-commit-config.yaml`, `.github/workflows/backward-compat-check.yml`)
3. **Phase 3: Documentation and tool validation**
   - [ ] Update the rows (REQ-006; `tools/TOOL_DESCRIPTIONS.md`)
   - [ ] Run the lighter tool validation sequence of `routing.md` "Adding a new tool" for the changed files, including both module-size invocations (REQ-006)
4. **Phase 4: Live-repository smoke run**
   - [ ] After the sweep Plan lands, run the checker on the repository, record the matches before and after, and remove from this change any pattern with a residual match instead of exempting it (REQ-007). No deploy step: `tools/` is not deployed.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| Checker and helper | Unit | `uv run pytest tests/tools/test_check_compat_shims.py` | Pass |
| Changed tool files | Static | `uv run ruff format tools/_compat_leftover_phrases.py tools/check_compat_shims.py`, `uv run ruff check ...`, `uv run mypy tools/_compat_leftover_phrases.py tools/check_compat_shims.py`, `uv run bandit tools/_compat_leftover_phrases.py tools/check_compat_shims.py` | Clean |
| Size gates | Static | `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | `check_compat_shims.py` at or below 36263; helper below 24576 |
| Tool documentation | Consistency | `uv run python tools/check_tool_descriptions_sync.py` | No findings |
| Live repository | Smoke | `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` | Exit 0 after the sweep Plan lands |
| Markers | Measurement | one-off run of `check_removed_name_reintroduction()` over `docs/` with the reduced set | 0 findings |
| Docs | Docs | `uv run python tools/check_docs_quality.py` (only if a document changes) | N/A: no document changes |

## Risks
- **Risk**: A selected pattern still matches live text after the sweep Plan → **Mitigation**: the smoke run (Phase 4) removes that pattern from the change and reports it; no exemption is added.
- **Risk**: Path scoping lets a leftover return in `docs/`, `tests/`, or `tools/` → **Mitigation**: the documentation side is owned by the adrrev018 rules; `tests/` and `tools/` are intentionally outside the scope; UNK-01 records the decision.
- **Risk**: The hook and workflow edits are rejected as out-of-scope CI wiring → **Mitigation**: UNK-02; the alternative keeps the table in a file the filters already watch.
- **Risk**: Trimming markers hides a historical note in documents added later → **Mitigation**: the removed-name check is opt-in and docs-only; the measurement shows only two markers matter today; a new document that needs another marker fails visibly and can be fixed then.
- **Risk**: The helper or its tests match their own phrases → **Mitigation**: self-safe regexes, concatenated fixtures, and the existing `fixture` exemption of the test file; verified by running the checker on the new files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reduce the historical-context markers and update their fixtures | Pending | — | — | |
| 2 | Add the leftover phrase helper, its call, tests, and path filters | Pending | — | — | |
| 3 | Update the tool documentation and run the tool validation | Pending | — | — | |
| 4 | Smoke run on the live repository after the sweep Plan | Pending | — | — | Gated by the sweep Plan |

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
- **Source issue**: issues/20261110-171157_rmcompat008_compat-checker-patterns.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261112-122408
- **Related target files**: `tools/_compat_leftover_phrases.py`, `tools/check_compat_shims.py`, `tests/tools/test_check_compat_shims.py`, `tools/TOOL_DESCRIPTIONS.md`, `.pre-commit-config.yaml`, `.github/workflows/backward-compat-check.yml`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; measured match counts | `tools/_compat_leftover_phrases.py` | 2 | AC-1 | `tests/tools/test_check_compat_shims.py` | Derived from confirmed evidence |
| REQ-001 | Required Changes 1; `check_all` lines 657-689 | `tools/check_compat_shims.py` | 2 | AC-1 | `tests/tools/test_check_compat_shims.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1 (phrases that span lines) | `tools/_compat_leftover_phrases.py` | 2 | AC-2 | `tests/tools/test_check_compat_shims.py` | Explicit in issue |
| REQ-003 | Required Changes 2 | `tests/tools/test_check_compat_shims.py` | 2 | AC-3 | itself | Explicit in issue |
| REQ-004 | Required Changes 3; marker measurement | `tools/check_compat_shims.py` | 1 | AC-4 | `tests/tools/test_check_compat_shims.py` | Confirmed by repository evidence |
| REQ-004 | Derived from the fixtures at lines 386-402, 427-432, 511-514 | `tests/tools/test_check_compat_shims.py` | 1 | AC-4 | itself | Derived from confirmed evidence |
| REQ-005 | Derived from the 36263-byte baseline forcing a new module | `.pre-commit-config.yaml` | 2 | AC-5 | `tools/check_tool_descriptions_sync.py` | Derived from confirmed evidence |
| REQ-005 | Derived from the 36263-byte baseline forcing a new module | `.github/workflows/backward-compat-check.yml` | 2 | AC-5 | `tools/check_tool_descriptions_sync.py` | Derived from confirmed evidence |
| REQ-006 | Required Changes 4; `TOOL_DESCRIPTIONS.md:83,178` | `tools/TOOL_DESCRIPTIONS.md` | 3 | AC-6 | `tools/check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-006 | Constraints (lighter tool validation) | `tools/_compat_leftover_phrases.py` | 3 | AC-6 | ruff, mypy, bandit, size gates | Explicit in issue |
| REQ-007 | Acceptance Criteria 3; Testing Expectations smoke run | `tools/check_compat_shims.py` | 4 | AC-7 | smoke run on live data | Explicit in issue |
