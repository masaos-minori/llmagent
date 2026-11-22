## Goal

Assert that a Memory reload is validated through a typed candidate, and remove the `RAGConfig` fixtures the section no longer has (REQ-001, REQ-002; AC-002).

## Scope
**Release unit**: RU-1

## Assumptions
- This row is not a companion: `tests/agent/services/test_config_reload.py` is named by two rows (`config_field_registry.py` and `config_section_reload.py`), so it keeps its own document.
- `tests/agent/services/test_config_reload_classification.py` is run as an affected test and is not a target row.

## Design decisions
- The new cases assert the outcome the typed path guarantees: an invalid `memory_embed_url` (new) raises `ConfigReloadValidationError` and leaves the live configuration unchanged; a valid value is applied.
- The fixture changes follow the dataclass change (Plan row 1): the `AgentConfig(..., rag=...)` construction disappears, and the Memory fixture carries the endpoint.

## Alternatives considered
- Assert only the field classification: rejected — classification alone does not prove that validation runs before commit, which is what REQ-002 requires.

## Implementation
### Target file
`tests/agent/services/test_config_reload.py`
### Procedure
- Remove the `RAGConfig` import (line 17) and the `rag_cfg` fixture constructions (lines 49, 95, 1055); build the Memory fixture with `memory_embed_url` instead.
- Add cases for the typed Memory path: invalid value raises and the live config is unchanged; valid value is applied.
- Extend `test_memory_section_fields_are_classified_correctly`'s expected set with `memory_embed_url` (new).
### Method
- Same fixture style as the existing cases (`MagicMock()` context plus real dataclasses); no new helper.
### Details
- Verified 2026-11-21: `test_memory_section_fields_are_classified_correctly` compares the registry entries whose `section_path == "memory"` against a closed set, so the new key must be added there or the test fails; the existing atomicity tests already show the pattern the new cases follow.
- Finding (2026-11-22, execution): the fixture change required more than replacing `rag=`. `AgentConfig` has no defaults for `db` and `maintenance`, so every fixture that builds a real `AgentConfig` must supply them (`MIN_DB_CONFIG`, `MIN_MAINTENANCE_CONFIG` from `tests/agent/_config_test_defaults.py`), and a Memory fixture with `memory_embed_enabled=True` must carry a URL because `MemoryConfig.__post_init__` raises otherwise. The classification expectation includes `memory_embed_url`; `memory_embed_enabled` stays startup-only, so the new key is the hot-reloadable one.

## Compatibility considerations
- `test_direct_fields_unchanged_on_later_failure` covers the direct path for `mcp`; Memory moves to the validated path, so that test keeps its `mcp` scope and is not repurposed.

## Security considerations
- N/A: test-only change.

## Rollback considerations
- N/A: revert the commit (Phase 2 is not part of a release unit).

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload.py tests/agent/services/test_config_reload_classification.py -v`
- `uv run ruff check tests/agent/services/test_config_reload.py`, `uv run mypy tests/agent/services/test_config_reload.py`

## Completion criteria
- The suite shows a Memory value rejected before commit and applied after validation; the registry classification includes the new key; no test constructs `RAGConfig`.

## Out of Scope
- The registry entry (Plan row 5), the section-reload implementation (Plan rows 6, 33).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method | Completed | 2026-11-22 | 2026-11-22 | Implemented under the gate: the RAGConfig import and its cases are removed and the moved key is asserted through the memory section. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-22 | 2026-11-22 | File is green. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22 | $V |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-22 | 2026-11-22 | Documentation rows are separate procedure documents. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002 (typed-candidate validation for the Memory section)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `tests/agent/services/test_config_reload.py`
