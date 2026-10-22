## Goal
Remove `offsets_dir` from the EventBus configuration contract (REQ-003: the key has no runtime consumer).

## Scope
- In: the `EventBusConfig` field, the entries in `_KNOWN_CONFIG_KEYS`, `_REQUIRED_CONFIG_KEYS`, and `_CONFIG_KEY_TYPES`, and the `offsets_dir=data["offsets_dir"]` argument in `load_config()`.
- Out: other keys, validation logic, defaults.

## Assumptions
- `load_config()` rejects unknown keys, so a TOML file that still carries `offsets_dir` fails to load after this change (intended; the sample file is seq 03).
- Nothing else under `scripts/` reads `offsets_dir` (`rg offsets_dir scripts` finds only this file and the module deleted by seq 01).

## Design decisions
- Delete exactly the five occurrences (field at about line 86, two key-set entries at about 201 and 230, the type entry at about 243, the constructor argument at about 334); change no other behavior.
- Keep the dataclass field order of the remaining fields.

## Alternatives considered
Keeping the key as an ignored optional field was rejected: it would keep a misleading key alive and contradict the owner's decision.

## Implementation
### Target file
`scripts/eventbus/config.py`

### Procedure
1. Delete the `offsets_dir: str` field from `EventBusConfig`.
2. Delete `"offsets_dir"` from `_KNOWN_CONFIG_KEYS` and `_REQUIRED_CONFIG_KEYS`.
3. Delete the `"offsets_dir": str` entry from `_CONFIG_KEY_TYPES`.
4. Delete the `offsets_dir=data["offsets_dir"],` line in `load_config()`.
5. Re-run `rg offsets_dir scripts/eventbus/config.py` (expect no match).

### Method
Pure deletion; no new symbol.

### Details
- The dataclass is constructed by keyword in `load_config()` and in tests, so removing the field breaks every `EventBusConfig(offsets_dir=...)` call until seq 06-31 are applied.
- Run only after the fixture rows are prepared, or apply seq 02 and the fixture rows in one working-tree pass before running the suite.

## Compatibility considerations
Configuration contract change: a configuration file with the key is rejected, one without it loads. Deploy code and configuration together (Plan REQ-006).

## Security considerations
N/A: no new input is accepted; the unknown-key check stays fail-closed.

## Rollback considerations
Revert the commit; roll back the sample configuration with it (Plan Risks).

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_config.py -q` (after seq 08), then `uv run pytest tests/eventbus -q`.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run python tools/check_module_size.py`.

## Completion criteria
- No `offsets_dir` occurrence remains in the file and the loader rejects a config containing it (REQ-003; Plan AC-2, AC-3).

## Out of Scope
Every other file of the Plan (each has its own procedure document); ADR text (Plan UNK-01); deleting `/opt/llm/offsets` (Plan UNK-03); offset storage, monotonic advancement, ACK-advanced offsets, and resume computation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the field, key-set entries, and constructor argument | Completed | 20261022-134012 | 20261022-134012 | Changed: see commit |
| 2 | Run the EventBus tests after the fixture rows are applied | Completed | 20261022-134012 | 20261022-134012 | Verified: tests/eventbus 324 passed, full suite 9649 passed; ruff, mypy, lint-imports, docs checkers pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261022-134012 | 20261022-134012 | Verified: tests/eventbus 324 passed, full suite 9649 passed; ruff, mypy, lint-imports, docs checkers pass |

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
- **Requirement ID**: `REQ-003` (remove the key from the configuration model)
- **Source issue**: `issues/20261022-124119_offhelper_remove-unused-file-offset-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-125806_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-132500
- **Related target files**: `scripts/eventbus/config.py`