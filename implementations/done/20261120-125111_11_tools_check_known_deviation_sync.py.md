## Goal

- Report an `UNK-` or `NC-` reference in `docs/10_adr/` that does not resolve to exactly one `governance_03` heading (`REQ-008`).
- Gated: apply the same rule to `scripts/` once the owner resolves UNK-01 (`REQ-009`).

## Scope
**Release unit**: N/A: not part of a release unit

- Plan steps 5 and 7. Step 5 runs after the data procedures of Plan steps 1 to 3 (the ADR-006, ADR-013, ADR-009, and `governance_03` procedures), because the rule must pass on the live repository; step 7 is gated on UNK-01.
- The test file is a companion of this document (`### Companion test files`).

## Assumptions

- The checker is 23492 bytes against the 24576 byte gate for `tools/`; the new rule is expected to exceed it, so splitting with `module_nodes.py` is part of this document and the new module is recorded with `tools/amend_plan.py` (class fallout) before it is created (Plan Risks).
- The rule reuses `_CANONICAL_ID_HEADER_RE`; it counts every `#### <ID>` heading of `governance_03` across all parts, including Part 2 (the existing parsers stop at Part 2).
- Step 7 starts only after UNK-01 is resolved and the extra `scripts/` files are added to the Plan.

## Design decisions

- A cited identifier resolves when exactly one heading carries it; zero or several is an `ERROR` (Plan D2).
- Alternatives rejected: adding `UNK` to the prefix set of the dangling check (it scans all of `docs/`), and a baseline file (a tolerant mode).

## Alternatives considered

- Add `UNK` to the prefix set of `find_dangling_general_references`: rejected, it scans every document under `docs/` and would flag six non-ADR documents (UNK-02).
- A baseline file of grandfathered tokens: rejected, it is a tolerant mode.

## Implementation
### Target file
`tools/check_known_deviation_sync.py`
### Procedure
1. Add `_CITED_IDENTIFIER_RE` (new) matching `\b(?:UNK|NC)-\d+\b(?!-?\w)`.
2. Add `collect_governance_heading_counts` (new): for the canonical documents, count every line matched by `_CANONICAL_ID_HEADER_RE`, without the Part 2 boundary.
3. Add `find_unresolved_identifiers` (new): for each ADR document line, each match whose heading count is not 1 returns an `Issue` (severity `ERROR`) naming the identifier and whether it has no entry or several.
4. Call it from `collect_issues()` with `discover_adr_docs()` and the counts; update the module docstring (a sixth failure mode) and the `--help` description.
5. Run `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`; when it fails, move the new functions and constants into a new `tools/` module with `module_nodes.py` and import them.
6. (Gated, Plan step 7) Add `discover_script_files` (new) reading `scripts/**/*.py` into `DocFile` records and apply `find_unresolved_identifiers` (new) to them in `collect_issues()`.
### Method
- Reuse `DocFile`, `Issue`, `discover_adr_docs()`, and `_CANONICAL_ID_HEADER_RE`; no new parsing library.
### Details
- Message shape follows the existing checks, for example `UNK-01 has no entry in the canonical Known Issue document (a plan-local identifier must not be cited in an ADR)`.
- A token followed by `-` and a word character is not matched (as `_ID_LOOKAHEAD_RE` does for `ADR-004-D1-...`).

### Companion test files
- `tests/tools/test_check_known_deviation_sync.py`
  - Procedure: Write each fixture first and see it fail: an unresolved `UNK-` reference in an ADR line, a heading present twice in the governance document, an unresolved `NC-` reference, a resolved `NC-` heading under `## Part 2` (clean), and a token with a word suffix (not matched); import `find_unresolved_identifiers` (new) and `collect_governance_heading_counts` (new). Gated: a fixture for a `scripts/` comment.
  - Validation: `uv run pytest tests/tools/test_check_known_deviation_sync.py -q`.

## Compatibility considerations

The CLI, JSON shape, and exit-code semantics are unchanged; one check is added. Importers keep the names they use.

## Security considerations

N/A: a read-only documentation checker.

## Rollback considerations

N/A: revert the commit; a module split reverts with the rule that forced it.

## Validation plan

- `uv run ruff format tools/check_known_deviation_sync.py`, `uv run ruff check tools/check_known_deviation_sync.py`, `uv run mypy tools/check_known_deviation_sync.py`, `uv run bandit tools/check_known_deviation_sync.py`.
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`.
- `uv run pytest tests/tools/test_check_known_deviation_sync.py -q`; `uv run python tools/check_known_deviation_sync.py` exits 0.

## Completion criteria

- Fixtures for an unresolved `UNK-` reference, a duplicated heading, and an unresolved `NC-` reference each exit non-zero and failed before the rule; a resolved `NC-` reference is clean (AC-1).
- The live run exits 0 and the size gate passes (AC-1).
- Gated: a fixture with an unresolved token in a `scripts/` comment fails the rule and `grep -rn -E "UNK-[0-9]+" scripts` returns nothing (AC-6).

## Out of Scope

- The ADR, ledger, and script comment edits (their own procedures); the six non-ADR documents of UNK-02.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the failing fixtures first (companion test file) | Completed | 20261120-151407 | 20261120-151407 | Fixtures shown failing before the rule 5 fixture tests added first; collection failed with ImportError before the rule existed (failing-first evidence). |
| 2 | Add the identifier rule for ADR documents (Plan step 5) | Completed | 20261120-151407 | 20261120-151407 | After the data procedures of Plan steps 1 to 3 Rule 6 added: _CITED_IDENTIFIER_RE plus heading counts across all Parts; 25 tests pass; live run reports no issues (exit 0). |
| 3 | Split the checker if the size gate fails and record the module as a fallout amendment (Plan step 5) | Completed | 20261120-151407 | 20261120-151407 | Only when the gate fails Split executed with tools/module_nodes.py: tools/_known_deviation_identifiers.py created (3684 B); checker 24106 B under the 24576 gate; tools/amend_plan.py refuses archived plans (plans/done/), so the fallout is recorded here and documented as an Index row in tools/TOOL_DESCRIPTIONS.md. |
| 4 | Extend the rule to scripts/ (Plan step 7) | N/A | — | — | Gated: plans/20261120-124329_adrchk012_traceability-id-uniqueness.md phase 7 - UNK-01 owner decision pending Row not executed in this batch: the extension is owned by Plan phase 7, whose gate stays open in the Plan Execution Status row. |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-151422 | 20261120-151422 | ruff format/check, mypy, bandit, pytest 25 passed, live checker run, check_module_size all pass. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-008` (ADR identifier rule), `REQ-009` (scripts rule, gated)
- **Source issue**: issues/20261117-123012_adrchk012_traceability-id-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-124329_adrchk012_traceability-id-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-125111
- **Related target files**: `tools/check_known_deviation_sync.py`, `tests/tools/test_check_known_deviation_sync.py`