## Goal
Add rules to `config/doc_quality_rules.json` for history phrasings and the lexical signatures of the resolved contradictions, with regression tests in `tests/tools/test_check_docs_quality.py` (`REQ-002`, `REQ-003`, `REQ-006` / `AC-2`, `AC-3`, `AC-6`). The plan-ID rule named by `REQ-002` is not added (see Assumptions: 8 corpus matches with no owning open Plan).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Rule shape (checked): `{ "pattern", "severity", "description", optional "exempt_historical_context" }` under `rules`; the default exempts historical context, so every new rule sets `exempt_historical_context: false`. Existing rules: six, none covers these phrasings.
- Corpus baseline (verified 2026-11-12, after the adrrev015, adrrev017, and adrrev011 procedures landed in `implementations/done/`): the history-phrasing pattern, `\bexceeded\s+max_retry\b`, `(?i)offsets?[^.|]*\bstrictly\s+monotonic`, and the empty-token signatures each have zero matches in `docs/`. These four rules are kept.
- Plan-ID gap (verified 2026-11-12): the plan-ID shape matches 8 lines — `governance_03` (2 `adrrev009` `First Found:` ledger lines), `mcp_06_06` and `agent_04_03` and `db_03_07` (`toolexec001`), `db_03_07` (`adrrev008`), `agent_10_01` (`adrrev005`), and `eventbus_08` (`EBAUTHGEN001`, inside an `AUTO-GENERATED` guard, which custom rules do not exempt). Owning Plans (adrrev005, adrrev008, adrrev009, toolexec001) are all in `plans/done/`, so no open Plan edits them. Maintainer decision 2026-11-12 (resolves UNK-02): do not add the plan-ID rule in this Plan; the corpus-cleanup of those citations is a separate follow-up item. `REQ-002` / `AC-2` are therefore met for the history phrasings only.
- UNK-01 (resolved 2026-11-12 by maintainer decision): every kept rule is `ERROR`. `check_docs_quality.py` exits 1 on any ERROR, so a kept rule must have zero corpus matches; it does.
- `tools/check_docs_quality.py` is at its size baseline and is not changed; the rules are JSON only.
- Execution order: the Depends-on procedures are already applied; the corpus smoke run was run in Step 3a on 2026-11-12 and is re-run in step 4 of this procedure before the completion gate.

## Design decisions
- Two rule groups: one `history_phrasing_in_active_doc` (new) rule (alternation) and one rule per contradiction signature, each specific enough for no corpus match (verified in Step 3a). The `plan_id_in_active_doc` rule the Plan names is not added.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`config/doc_quality_rules.json`

### Procedure
1. Write the failing live-rule tests (companion) first.
2. Add the rules to the JSON.
3. Smoke-run `uv run python tools/check_docs_quality.py` against `docs/`; record each remaining match and its owning Plan.
4. Keep only rules with zero unowned matches.

### Method
- `history_phrasing_in_active_doc` (new): `Amendment\s*\([^)]*\d{4}-\d{2}-\d{2}|superseded\s+\d{4}-\d{2}-\d{2}|replaces the previous|\b(?:was|were)\s+removed\s+(?:at|in|by)\b|\bformerly\b`, ERROR, `exempt_historical_context: false`.
- `dlq_threshold_exceeded_operator` (new): `\bexceeded\s+max_retry\b`; `offset_strictly_monotonic` (new): `(?i)offsets?[^.|]*\bstrictly\s+monotonic`; `empty_token_startup_statement` (new): `starts, but health checks fail|skips the authentication check`; each ERROR with a description naming the corrected wording.
- `plan_id_in_active_doc` — not added. The Plan's shape `\b(?!(?:http|HTTP|sha|SHA)\d)[A-Za-z]{4,12}[0-9]{3}\b` matches 8 corpus lines whose owning Plans are archived, so keeping it as ERROR would fail `check_docs_quality.py` and pre-commit until another Plan edits those documents.
- Tests use `_run_live_rule(rule_name, [line])` (the pattern at `tests/tools/test_check_docs_quality.py` line 445): one failing and one passing line per rule.

### Details
- The offset rule must not flag `non-decreasing` wording; the DLQ rule must not flag `>= max_retry` or `reached max_retry` wording.
- The dropped plan-ID shape and its 8 corpus matches are recorded in Assumptions so a follow-up Plan can add the rule after those citations are reworded.

### Companion test files
- `tests/tools/test_check_docs_quality.py`
  - Procedure: Add a `TestHistoryPhrasingRule` (new) and one class per contradiction rule using `_run_live_rule`, each with failing and passing lines, written before the rules exist. No `TestPlanIdRule` (the rule is not added).
  - Validation: `uv run pytest tests/tools/test_check_docs_quality.py -q`; show each new test failing before the JSON edit.

## Compatibility considerations
N/A: adds rules; an existing document that matches is reported by the checker, not changed here.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools -q` — pass.
- `uv run ruff format`/`ruff check`/`mypy` on the test file — clean.
- `uv run python tools/check_docs_quality.py` on real `docs/` — pass for every kept rule.

## Completion criteria
- Each kept rule fails its fixture and passes the corrected wording; no kept rule matches the corpus; remaining matches are reported to their owner.

## Out of Scope
- Editing flagged documents; changing `tools/check_docs_quality.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the failing live-rule tests first | Completed | 20261112-213817 | 20261112-215632 | 4 new rule-test classes added first; 13 failed (KeyError on the missing rule names) against the unmodified JSON |
| 2 | Add the rules to `config/doc_quality_rules.json` | Completed | 20261112-215632 | 20261112-215632 | 4 rules added (history_phrasing_in_active_doc, dlq_threshold_exceeded_operator, offset_strictly_monotonic, empty_token_startup_statement), all ERROR with exempt_historical_context false; plan_id_in_active_doc not added per maintainer decision |
| 3 | Run `uv run pytest tests/tools/test_check_docs_quality.py -q` and the validation sequence for the changed test file | Completed | 20261112-215632 | 20261112-215632 | 80 targeted tests pass (1 fixture line reworded to the procedure's superseded phrasing); full suite 12167 pass; CI mypy invocation clean; ruff/bandit(-ll) clean; tests/tools mypy is outside the CI gate and its one pre-existing error was confirmed unchanged from HEAD |
| 4 | Smoke-run `check_docs_quality.py` on real `docs/`; keep only rules with no unowned match and report the rest | Completed | 20261112-215632 | 20261112-215632 | check_docs_quality.py: No issues found (exit 0) - all 4 kept rules have zero corpus matches, so no rule was dropped and no owning Plan report was needed |

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
- **Requirement ID**: `REQ-002` / `REQ-003` / `REQ-006` — history, plan-ID, and contradiction-signature rules
- **Source issue**: issues/20261109-113351_adrrev018_docs-checker-harden.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-111505_adrrev018_docs-checker-harden.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124203
- **Related target files**: `config/doc_quality_rules.json`, `tests/tools/test_check_docs_quality.py`