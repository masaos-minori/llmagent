## Goal

Remove the plan-local identifiers (REQ, UNK, AC, SEQ labels) from the comments and docstrings of `tests/eventbus/test_eventbus_crash_ack.py`, replacing each with a reference to a canonical definition (an ADR invariant or a `docs/24_eventbus/` section) or with plain wording, with no code change (`REQ-002`: rewrite or remove per mapping; `REQ-003`: no unresolved or doubly-meant identifier remains; `REQ-004`: comment and docstring changes only).

## Scope

Comment and docstring text in `tests/eventbus/test_eventbus_crash_ack.py` only. No assertion, fixture, name, or behavior change, no renamed test, no ADR or docs edit. Other files in the Plan's table are separate documents.

## Assumptions

- Occurrences re-verified this cycle with `rg -n -e '\b(REQ|UNK|AC|SEQ)-[0-9]+' tests/eventbus/test_eventbus_crash_ack.py` (all sit in comments or docstrings; none is inside an assertion, `match=`, `pytest.mark`, or test name). Lines shift when other procedures land first, so the search is re-run at implementation time and every hit is handled by the rules below, including labels that other procedures add.
- Canonical sources available: ADR-006 (docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md) INV-01 to INV-16 and ADR-013 (docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md) INV-01 to INV-07 (invariant texts read this cycle). A mapping is applied only when the invariant or doc section actually states the rule the test protects; otherwise the identifier is removed and the rule is written in plain words, and a rule that matters but has no canonical statement becomes an owner question in the change description (`REQ-005` of the Plan), not a definition in the test.
- Overlap with other Frozen Plans or generated procedures: `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md` edits this file; compatible.
- `EVENTBUS-nnn` labels are outside this Plan's identifier list (Plan UNK-04) and stay unchanged.

## Design decisions

- Preference order per identifier: (a) cite the ADR invariant or doc section that states the rule; (b) restate the rule in plain words; (c) delete the label when the surrounding text already says enough. Never introduce a new numbering scheme.
- Delete plan-history wording on the lines touched; keep the comment or docstring grammatical and within 88 columns.

## Alternatives considered

N/A: the Plan fixes the mapping approach; no alternative is needed for a comment-only row.

## Implementation

### Target file

`tests/eventbus/test_eventbus_crash_ack.py`

### Procedure

1. Run `rg -n -e '\b(REQ|UNK|AC|SEQ)-[0-9]+' tests/eventbus/test_eventbus_crash_ack.py` and compare the hits with the list in Details (about 2 line references recorded this cycle).
2. For each hit, apply the treatment in Details; edit only the comment or docstring text, never code.
3. Re-run the search and confirm that no label remains unless it is cited together with a definition reachable from the repository docs.

### Method

Treat each hit by the preference order in Design decisions. Example shapes: a docstring `"""REQ-002: ..."""` becomes `"""Per-consumer DLQ promotion (ADR-006 INV-13): ..."""` or plain wording; a comment `(REQ-006)` is deleted when the sentence is complete without it.

### Details

Recorded hits in `test_eventbus_crash_ack.py` (as of this cycle; line numbers are for orientation):

- line 83, 93: REQ-006 (x2) — no direct principal-map mutation is needed -> delete the label and keep the remark in plain wording

## Compatibility considerations

N/A: comments and docstrings only; test behavior is unchanged.

## Security considerations

N/A: no code, credentials, or tokens change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

1. `uv run pytest tests/eventbus/test_eventbus_crash_ack.py -v` (pass count unchanged; for a helper module, run `uv run pytest tests/eventbus`).
2. AST comparison of `tests/eventbus/test_eventbus_crash_ack.py` against `HEAD` with docstrings removed reports no difference (comment-only check).
3. `rg -n -e '\b(REQ|UNK|AC|SEQ)-[0-9]+' tests/eventbus/test_eventbus_crash_ack.py` shows only cited identifiers with a reachable definition.
4. `uv run ruff check tests/eventbus`; `uv run ruff format --check tests/eventbus`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`.
5. `uv run python tools/stale_detector.py implementations/20261029-102038_13_tests_eventbus_test_eventbus_crash_ack.py.md`.

## Completion criteria

- No identifier in `test_eventbus_crash_ack.py` lacks a definition reachable from the repository docs; none carries two meanings.
- The diff of `tests/eventbus/test_eventbus_crash_ack.py` is comment and docstring text only and the file's tests pass with the same count.
- ruff, format, and mypy are clean; owner questions for gaps are noted for the change description.

## Out of Scope

- Other target files of the Plan, production comments under `scripts/eventbus/`, `docs/` identifiers, ADR edits, test renames, and `EVENTBUS-nnn` labels.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-run the identifier search and apply the mapping to comments and docstrings (Implementation > Procedure/Method/Details) | Pending | — | — | |
| 2 | Run the tests and the comment-only AST comparison (Validation plan) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261029-090453_eventbus004_test-requirement-id-cleanup.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-092617_eventbus004_test-requirement-id-cleanup.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-102038
- **Related target files**: `tests/eventbus/test_eventbus_crash_ack.py`
