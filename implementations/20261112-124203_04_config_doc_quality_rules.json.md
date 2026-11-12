## Goal
Add rules to `config/doc_quality_rules.json` for history phrasings, plan IDs, and the lexical signatures of the resolved contradictions, with regression tests in `tests/tools/test_check_docs_quality.py` (`REQ-002`, `REQ-003`, `REQ-006` / `AC-2`, `AC-3`, `AC-6`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Rule shape (checked): `{ "pattern", "severity", "description", optional "exempt_historical_context" }` under `rules`; the default exempts historical context, so every new rule sets `exempt_historical_context: false`. Existing rules: six, none covers these phrasings.
- Corpus baseline (Step 3a, 2026-11-12) before the other Plans' procedures run: history phrasings match ADR-001, ADR-008, ADR-010, ADR-001 and the index, `db_03_07`, `db_07`, `eventbus_06`, `mcp_03_03` (adrrev017 removes these); `exceeded max_retry` matches ADR-006 INV-13 and `strictly monotonic` matches the index row (adrrev015 fixes both); the empty-token signatures match `mcp_06_14` and `mcp_02_02` (adrrev011 fixes).
- Plan-ID gap (Step 3a): the plan-ID shape also matches documents that no open Plan edits: `agent_10_01` (adrrev005), `governance_03` (adrrev009, ledger text), `db_03_07` (toolexec001, adrrev008), `agent_04_03` and `mcp_06_06` (toolexec001), and ADR-015 (mcpgate001/adrauth001, fixed by adrrev015). Do not keep the plan-ID rule unless the smoke run is clean: either the maintainer assigns those documents to a Plan (add rows with `tools/amend_plan.py`, fallout class), or narrow/exempt the rule; this is a non-blocking `Needs confirmation` (UNK-02), reported, not decided here.
- UNK-01: severity ERROR by default; the maintainer may choose WARNING (a one-word JSON change).
- `tools/check_docs_quality.py` is at its size baseline and is not changed; the rules are JSON only.
- Execution order: this Plan lands after the procedures of adrrev015, adrrev017, and adrrev011 are executed (Plan `Depends on`); `plan_dependency_order.py` reports this Plan `ready` because those Plans are archived, but their procedures may still be unexecuted, so the corpus smoke run in Phase 4 decides.

## Design decisions
- Three rule groups: one `history_phrasing_in_active_doc` (new) rule (alternation), one `plan_id_in_active_doc` (new) rule, and one rule per contradiction signature, each specific enough for no corpus match once the owning Plans land.

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
- `plan_id_in_active_doc` (new): `\b(?!(?:http|HTTP|sha|SHA)\d)[A-Za-z]{4,12}[0-9]{3}\b`, ERROR, `exempt_historical_context: false`; the passing fixture uses a token such as `HTTP200`.
- `dlq_threshold_exceeded_operator` (new): `\bexceeded\s+max_retry\b`; `offset_strictly_monotonic` (new): `(?i)offsets?[^.|]*\bstrictly\s+monotonic`; `empty_token_startup_statement` (new): `starts, but health checks fail|skips the authentication check`; each ERROR with a description naming the corrected wording.
- Tests use `_run_live_rule(rule_name, [line])` (the pattern at `tests/tools/test_check_docs_quality.py` line 445): one failing and one passing line per rule.

### Details
- The offset rule must not flag `non-decreasing` wording; the DLQ rule must not flag `>= max_retry` or `reached max_retry` wording.
- The Plan-ID shape must not match `ADR-006`, `REQ-001`, `INV-13` (hyphen) or `sha256`.

### Companion test files
- `tests/tools/test_check_docs_quality.py`
  - Procedure: Add a `TestHistoryPhrasingRule` (new), `TestPlanIdRule` (new), and one class per contradiction rule using `_run_live_rule`, each with failing and passing lines, written before the rules exist.
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
| 1 | Write the failing live-rule tests first | Pending | — | — | |
| 2 | Add the rules to `config/doc_quality_rules.json` | Pending | — | — | |
| 3 | Run `uv run pytest tests/tools/test_check_docs_quality.py -q` and the validation sequence for the changed test file | Pending | — | — | |
| 4 | Smoke-run `check_docs_quality.py` on real `docs/`; keep only rules with no unowned match and report the rest | Pending | — | — | |

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
