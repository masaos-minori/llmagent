# Remove the unused file-based offset helpers and the offsets_dir key

## Priority
Medium

## Summary
Decide and apply the removal of the file-based consumer offset helpers in `scripts/eventbus/offsets.py` (`read_offset`, `write_offset`, and their private helpers) and of the `offsets_dir` configuration key, now that no production code reads or writes offset files.

## Background
`memo-issue.md` item H-01 asked to complete the legacy offset migration and remove the file-based offset compatibility. Most of that work is already done: the startup import (`migrate_legacy_offsets()`, the `offset_migrator` module, its re-export, and its startup call) was removed, `consumer_offsets` is the only resume source, and a test now checks that startup neither reads nor modifies files in `offsets_dir`. A read-only inspection of the deployed host on 2026-10-22 found `/opt/llm/offsets` empty and `consumer_offsets` empty. (Confirmed by repository evidence)

What remains, confirmed by search of `scripts/` and `tests/`:
- `scripts/eventbus/offsets.py` still defines `CorruptOffsetError`, `read_offset()`, `write_offset()`, `_validate_consumer_identity()`, and `_sanitize_consumer_id()`. No module under `scripts/` calls them; `ack_route.py` carries a comment that `write_offset` was replaced by the transactional ACK path. Only tests under `tests/eventbus/` import them.
- `offsets_dir` is still a required configuration key (`scripts/eventbus/config.py`, `config/eventbus.toml`, `rules/env.md`), `deploy/deploy.sh` still creates `/opt/llm/offsets`, and `tests/` references `offsets_dir` in about 120 places.
- `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` records the removal of these helpers as an open decision owned by the EventBus service.

The memo items about call-site inventory, value reconciliation, health reporting of migration status, and migration completion markers no longer apply because the migration path does not exist.

## Problem
Dead file-format code and a required configuration key remain for a feature that has no runtime user. They keep tests, documentation, and the configuration contract alive, and an operator can mistake `offsets_dir` for an active resume source.

## Reason for Change
Removing code with no caller lowers maintenance cost and removes a misleading configuration key. The owner decision that the only supported deployment holds no offset files makes the removal safe to decide now.

## Implementation Intent
Obtain the owner's decision first (the open decision in the semantics document). If the helpers are removed: delete `offsets.py` and its tests, remove `offsets_dir` from the configuration model, the sample configuration, the deploy script's directory creation, the documentation, and the test fixtures in one reviewable change, and keep ACK-advanced offset and resume behavior untouched. If they are kept, state their current purpose in the documentation instead of calling the question open.

## Target Files or Areas
- `scripts/eventbus/offsets.py`
- `scripts/eventbus/config.py`, `config/eventbus.toml`, `deploy/deploy.sh`
- `tests/eventbus/test_eventbus_offsets.py` and other tests that build the EventBus configuration with `offsets_dir`
- `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/24_eventbus/eventbus_08_reference_api.md`, `rules/env.md`
- `tools/check_docstrings_baseline.txt` (entry for `eventbus/offsets.py`)

## Required Changes
- Record the owner's decision on removing the helpers and the `offsets_dir` key.
- Delete the helpers, their tests, and the configuration key as one change, or document their retained purpose.
- Update the documents and the generated reference block; remove the open decision.
- Remove the stale baseline entry for the deleted module.

## Constraints
- Offset storage, monotonic advancement, ACK-advanced offsets, and resume computation must not change.
- The configuration change must keep the service starting against the deployed configuration (a config file that still contains the key must not break startup, or the deployed file must be updated in the same deploy).
- Do not delete any offset file from any host.

## Acceptance Criteria
- `rg "read_offset|write_offset|offsets_dir" scripts tests config deploy docs rules` returns no match, or each remaining match is explained by the retained design.
- Offset ACK and resume tests pass unchanged and the full suite passes.
- `ruff`, `mypy --no-namespace-packages`, `lint-imports`, `generate_reference_table.py --check`, `check_docstrings.py`, and the documentation checkers pass.
- The EventBus starts against the deployed configuration.

## Testing Expectations
- Run `tests/eventbus` and the full suite once; `uv run ruff check scripts/`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports`; `uv run python tools/generate_reference_table.py --check`.
- Start the service with the updated configuration against a copy of the deployed database.

## Documentation Impact
Yes. Remove the open decision and the operations section that describe offset files, update the configuration reference, and keep the statement that `consumer_offsets` is the only resume source.

## Out of Scope
- Event replay API redesign, DLQ behavior, and schema changes.
- Deleting offset files from any host.

## Dependencies
- Depends on the already merged removal of the legacy offset import.
- Sibling-issue check: no open issue under `issues/` and no active plan under `plans/` touches these files; the open ADR decision for the EventBus persistence ADR (offset-store wording) is separate and needs the owner's approval.

## Unresolved Questions
- Does the owner approve removing the helpers and the `offsets_dir` key (the open decision in the semantics document)?
- Is any external script or operator tooling outside this repository using the offset file format? Unknown; the repository search finds none.

## AI Implementation Instruction
Do not remove anything before the owner's decision is recorded; stop and report if it is missing. Change only the files listed; do not alter offset storage or resume behavior; do not edit ADR text.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261022-124119
- **Related target files**: scripts/eventbus/offsets.py, scripts/eventbus/config.py, config/eventbus.toml, deploy/deploy.sh, tests/eventbus/test_eventbus_offsets.py, docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md, docs/24_eventbus/eventbus_07_configuration-and-operations.md, docs/24_eventbus/eventbus_08_reference_api.md, rules/env.md, tools/check_docstrings_baseline.txt
