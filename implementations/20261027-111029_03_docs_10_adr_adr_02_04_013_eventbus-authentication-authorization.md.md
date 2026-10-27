## Goal

Remove the `Known Deviations` citation of EVENTBUS-020 from ADR-013 and keep the requirements it stood for in the ADR's current sections (`REQ-004`: ADR-013 citation; `REQ-007`: state still-applicable requirements).

## Scope

- Edit `## Known Deviations` and the decision/implementation text that states config-loading behavior in the target file only.
- Add one short statement; do not add a Decision or change the role model.

## Assumptions

- Plan Step 3a found that the current text states fail-closed validation of unknown, missing and wrong-type keys in `load_config()` but states no duplicate-token rejection requirement. Source evidence: `scripts/eventbus/auth.py` (duplicate-non-empty-token guard that raises on two distinct token roles sharing one value) and `scripts/eventbus/config.py` (`consumer_authorization` and `topic_authorization` fields); cited tests `tests/eventbus/test_eventbus_config.py` and `tests/eventbus/test_eventbus_consumer_authorization.py`.
- The mapping-delivery requirement is already carried by Decision Details item 3 (explicit `consumer_id` and topic authorizations) and the "Authorization generation" items; only the duplicate-token requirement is missing.
- `check_known_deviation_sync.py` is run after row 05.
- Size gate (measured in Step 3a, UTF-8 bytes): the file is 23846 B against the default limit of 24576 B with no per-file exception, so the added sentence MUST stay within about 870 B after the Known Issue bullet is removed; one sentence fits.
- Plan overlap check: no other Frozen Plan targets this file.

## Design decisions

- Add the duplicate-token requirement as one sentence next to the existing `load_config()` fail-closed validation statement (Decision Details item 6).
- Follow `skills/DESIGN.md`: no line numbers, no concrete config values.

## Alternatives considered

- A new numbered Decision for duplicate tokens: rejected, because it changes the ADR's decision surface and goes beyond the Plan's REQ-007.

## Implementation
### Target file

`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Procedure

1. Locate Decision Details item 6 (`rg -n "Fail-closed rejection of unknown" <target>`) and `## Known Deviations`.
2. Extend item 6 with one sentence: EventBus configuration loading also rejects a configuration in which distinct token roles share one non-empty token value, and a TOML authorization mapping reaches the Consumer principal through `load_config()`.
3. Replace the body of `## Known Deviations` (the single EVENTBUS-020 bullet) with the single line `Not applicable`.

### Method

Exact-string edits. Verify the added sentence against `scripts/eventbus/auth.py` and `scripts/eventbus/config.py` once before writing it; if unconfirmed, report `Needs confirmation` and do not add it.

### Details

- The `Related target`/Tests lines of the ADR already cite `test_eventbus_config.py` and `test_eventbus_consumer_authorization.py`; do not edit them.
- Match the `Not applicable` form of other ADRs.

## Compatibility considerations

N/A: documentation only. `check_adr_preservation.py` may report the Known Deviations removal and added sentence; review as intended.

## Security considerations

N/A: the sentence names no token value; it states a rejection rule only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_structure.py` and `uv run python tools/check_adr_preservation.py` (review every report).
- `check_docs_quality.py`, `check_docs_structure.py` on this file, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`, `check_docs_consistency.py --domain eventbus`.
- `uv run python tools/check_known_deviation_sync.py` after rows 01 to 05.

## Completion criteria

- `## Known Deviations` reads `Not applicable`.
- The ADR text states duplicate-token rejection at configuration load.
- The checkers above report no unreviewed finding.

## Out of Scope

- The ledger, the other ADRs and the ADR guide (other rows).
- Any change to the role model, routes or Decision Details numbering.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the duplicate-token sentence and set Known Deviations to `Not applicable` | Pending | — | — | |
| 2 | Run the ADR and documentation checkers named in the Validation plan | Pending | — | — | Sync checker passes only after all rows |

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
- **Requirement ID**: `REQ-004` (ADR-013 citation removed), `REQ-007` (still-applicable requirement stated)
- **Source issue**: issues/20261027-102048_govrev006_eventbus-ledger-stale-entries.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-103437_govrev006_eventbus-ledger-stale-entries.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-111029
- **Related target files**: docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md
