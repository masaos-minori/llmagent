## Goal
- Make the `get_resume_position()` docstring in `scripts/eventbus/delivery_repo.py` describe exactly what the function returns, without changing its behavior.

## Priority
Low

## Scope
- **In-Scope**: Rewrite the docstring of `get_resume_position()` (summary line unchanged, body and `Returns` section corrected).
- **Out-of-Scope**: any behavior or signature change; edits under `docs/` (they already state the rule); the removed slash commands, Workflow bypass text and the ADR dependency-graph line named in the original memo (not confirmed); resume or replay behavior.
- **Dependencies**: N/A: none. No Frozen Plan targets `scripts/eventbus/delivery_repo.py`.

## Background
`get_resume_position()` returns `0` when the consumer has no stored offset. Otherwise it takes `MIN(e.seq)` over events with `seq <= stored_offset` that this consumer has not acknowledged (a `consumer_delivery` row with `acked = 0`, or no row at all) and returns it when found, else `stored_offset + 1`. `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` already states this rule as `lowest_unacked_seq` when an unacked event exists at or below the stored offset, otherwise `stored_offset + 1`.

## Problem
The docstring says the function "returns the maximum of" the stored offset and the lowest unacked sequence. The lowest unacked sequence is at most the stored offset by the query's own `seq <= ?` bound, so the "maximum" wording would imply the stored offset is always returned, and neither branch of the code returns the stored offset itself. The docstring also calls an event "unacked" without saying that an event with no delivery record for this consumer counts as unacked.

## Reason for Change
A reader implementing a consumer or a test can be misled by a docstring that contradicts both the code and the documentation. Fixing it now stops the wrong statement from being repeated in later issues. The priority is Low because it cannot by itself cause a wrong operator action.

## Implementation Intent
State the three outcomes in the order the code evaluates them and define "unacked" the way the code does. Use the terminology of the EventBus offsets doc. Change only the docstring.

## Requirements
- `REQ-001`: The `get_resume_position()` docstring states the three outcomes: no offset row returns 0; an unacked event at or below the stored offset returns the lowest such `seq`; otherwise the function returns the stored offset plus one.
- `REQ-002`: The docstring defines an unacked event as one with a `consumer_delivery` row where `acked = 0` or with no `consumer_delivery` row for this consumer, and no longer mentions a maximum.
- `REQ-003`: The function body, signature and first docstring line are unchanged, so the generated API reference row and behavior stay as they are.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/delivery_repo.py` | Docstring of `get_resume_position` | Replace the "maximum of" description with the implemented three-outcome rule and the definition of unacked | REQ-001, REQ-002, REQ-003 / AC-1, AC-2 | The docstring says "Returns the maximum of: the stored offset ...; the lowest unacked seq ..."; the body returns `0`, `int(row[0])` from `MIN(e.seq) ... e.seq <= ?`, or `stored_offset + 1`; the query's `LEFT JOIN` comment treats an event with no delivery record as unacked (checked in Step 3) | `tests/eventbus/test_eventbus_restart_resume.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | States the rule as `lowest_unacked_seq` or `stored_offset + 1`; the docstring must use the same terms | REQ-001 |
| `docs/24_eventbus/eventbus_08_reference_api.md` | The generated row quotes only the first docstring line, which stays unchanged | REQ-003 |
| `tests/eventbus/test_eventbus_restart_resume.py` | Existing tests cover no offset, an unacked event below the offset (including one with no delivery record) and the all-acked case | REQ-003 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-002): The docstring matches the function's behavior for all three outcomes, defines unacked as the code does, and contains no mention of a maximum.
- AC-2 (REQ-003): The function body, signature and first docstring line are byte-for-byte unchanged, and `uv run pytest tests/eventbus -q`, ruff and `tools/check_docstrings.py` pass.

## Tests
- No new test: behavior is unchanged. The existing resume-position tests in `tests/eventbus/test_eventbus_restart_resume.py` cover each outcome and must keep passing (REQ-003).
- Run `uv run pytest tests/eventbus -q` and `uv run ruff check scripts/eventbus/delivery_repo.py`.

## Documentation Impact
N/A: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` already states the rule; confirm with `uv run python tools/check_docs_consistency.py --domain eventbus` and `uv run python tools/generate_reference_table.py --check`.

## Assumptions
- Path A: one target file, no public interface change, no schema change.
- Keeping the first docstring line unchanged keeps the generated reference row identical, so no doc regeneration is needed.
- The `if row and row[0]:` truthiness test in the body is not changed here; `seq` starts at 1, so a falsy `0` cannot occur.
- The original memo item's other claims (removed slash commands, Workflow descriptions, the ADR dependency-graph line) are not confirmed: `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` passes on the current tree, so they stay out of this Plan.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Location of the "malformed ADR dependency-graph line" named in the original memo | Not found in verification | Excluded from this Plan; file a separate Issue with evidence if it is found | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/delivery_repo.py` | Modify | Low | 15 | N/A | not applicable (rsynced) |

## Design
- Path A (one file, docstring only), so the architecture, dependency and historical analyses are skipped. Blast radius is Low because a docstring change has no runtime effect; `get_resume_position` is re-exported by `scripts/eventbus/db.py`, which is unaffected. `radon cc` reports `nack_event` C (12) and `ack_event_for_consumer` C (11) in the file, neither touched.
- Proposed wording: "Return the first `seq` to deliver on reconnect. Return 0 when the consumer has no stored offset. Otherwise return the lowest `seq` at or below the stored offset that this consumer has not acknowledged (a `consumer_delivery` row with `acked = 0`, or no row), or `stored_offset + 1` when every such event is acknowledged."

## Implementation steps
1. **Phase 1: Docstring correction**
   - [ ] Rewrite the `get_resume_position` docstring body and `Returns` section with the proposed wording, leaving the first line, signature and body unchanged (REQ-001, REQ-002, REQ-003; `scripts/eventbus/delivery_repo.py`)
2. **Phase 2: Verification**
   - [ ] Run the validation plan and confirm the docs checkers and the reference-table check still pass (REQ-003; `scripts/eventbus/delivery_repo.py`)
3. **Phase 3: Deployment & Verification**
   - [ ] After commit and push, hand off to `skills/deploy/SKILL.md` (the user decides to deploy) because a `scripts/` file changes; the change is documentation-only, so deployment can ride with the next EventBus release (REQ-003; `scripts/eventbus/delivery_repo.py`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/delivery_repo.py` | Existing resume-position tests | `uv run pytest tests/eventbus -q` | All pass, unchanged |
| Static | Lint, types, docstring format | `uv run ruff check scripts/eventbus/delivery_repo.py`; `uv run mypy --no-namespace-packages scripts/`; `uv run python tools/check_docstrings.py` | Clean |
| Reference table | Generated block drift | `uv run python tools/generate_reference_table.py --check` | No drift |
| Docs | Consistency | `uv run python tools/check_docs_consistency.py --domain eventbus` | No errors |

Baseline recorded in Step 5: `radon cc` reports no change-relevant function at C or above in `get_resume_position`; `vulture scripts/ --min-confidence 80` earlier in this batch listed no finding in `scripts/eventbus/delivery_repo.py`; `bandit -r scripts/` reported no Medium or High finding.

## Risks
- **Risk**: The new wording drifts from the offsets doc → **Mitigation**: reuse the doc's terms (`lowest_unacked_seq`, `stored_offset + 1`) and run `tools/check_docs_consistency.py --domain eventbus`.
- **Risk**: An accidental code edit alongside the docstring → **Mitigation**: the diff must touch only docstring lines, which acceptance criterion AC-2 checks.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the `get_resume_position` docstring | Completed | — | 2026-10-28 |  |
| 2 | Run the validation plan and docs checkers | Completed | — | 2026-10-28 | pytest 411 passed; ruff/mypy/lint-imports/bandit/size/docstring/reference/docs checkers clean |
| 3 | Deployment and verification hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261028-120349_01_scripts_eventbus_delivery_repo.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-155852_ebresume009_fix-resume-position-docstring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-094951
- **Related target files**: `scripts/eventbus/delivery_repo.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; docstring says "maximum of" | `scripts/eventbus/delivery_repo.py` | Step 1 | AC-1 | `uv run pytest tests/eventbus -q` | Confirmed by repository evidence |
| REQ-002 | Required Changes 2; `LEFT JOIN` comment treats an event with no delivery record as unacked | `scripts/eventbus/delivery_repo.py` | Step 1 | AC-1 | `uv run python tools/check_docstrings.py` | Confirmed by repository evidence |
| REQ-003 | Constraints (no behavior or signature change) | `scripts/eventbus/delivery_repo.py` | Steps 1 and 2 | AC-2 | `uv run python tools/generate_reference_table.py --check` | Explicit in issue |