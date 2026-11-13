## Goal

Replace the consumer-authorization test's TOML fixture that uses the removed `topic_authorization` format (REQ-002).

## Scope
**Release unit**: single-authorization-format (with rows 01, 02, 04, 05, 06, 07, 14)

## Assumptions
- This row gets its own document (not a companion) because no other row names this file in its `Related Tests` cell, which fails the companion eligibility rule (SKILL.md Core Execution Rules).
- After row 01 removes the key from the allowed list, writing it in a TOML fixture fails load with the unknown-key error, so this fixture must change in the same unit.

## Design decisions
- Express the same topic-grant scenario through `consumer_authorization` only (`{ "c1" = ["topicA"] }`).

## Alternatives considered
- Deleting the fixture scenario: rejected; consumer topic grants remain enforced and their coverage must survive.

## Implementation
### Target file
`tests/eventbus/test_eventbus_consumer_authorization.py`
### Procedure
Rewrite the TOML fixture string and keep the assertions meaningful under the single format.
### Method
One fixture edit; verify dependent assertions still describe the same allow/deny behavior.
### Details
- Line 303: replace `'topic_authorization = { "topicA" = ["c1"] }\n'` with the equivalent `consumer_authorization` entry — verified 2026-11-13: the adjacent line 302 already carries `consumer_authorization = { "c1" = ["topicA"] }`, so line 303 can simply be deleted; the assertion at 306 then locks the single mapping.
- Verified 2026-11-13: the original claim that this file "carries class-level `REQ-007`/`REQ-008` labels near lines 84, 146, 182, 222" is false — `rg "REQ-"` finds no label in this file; nothing in this row touches rmcompat007 label scope.

## Compatibility considerations
- Land in the same unit as row 01; otherwise the suite is red between the key removal and this fixture.

## Security considerations
- N/A: tests.

## Rollback considerations
- Git revert.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_consumer_authorization.py`
- AC-2: `rg -n "topic_authorization" tests/eventbus/test_eventbus_consumer_authorization.py` returns nothing.

## Completion criteria
- The fixture carries no removed-format key and the suite passes against the post-change `config.py`/`auth.py`.

## Out of Scope
- `REQ-` labels in `scripts/eventbus/` test/docstring locations generally (rmcompat007); this file itself carries none (verified 2026-11-13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-13 | 2026-11-13 | TOML fixture line removed; targeted tests green |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-13 | 2026-11-13 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-13 | 2026-11-13 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-13 | 2026-11-13 | — |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/done/20261110-170832_rmcompat004_eventbus-config-auth-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-135237
- **Related target files**: `tests/eventbus/test_eventbus_consumer_authorization.py`
