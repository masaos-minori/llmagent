## Goal
Remove the two prompt entries from the reload field registry so the removed keys have no reload classification (REQ-003, single-function row).

## Scope
**Release unit**: RU-1
## Assumptions
- Cross-plan overlap with `plans/20261121-172154_mcpdl003_dedup-config-isolation.md` on this row is judged compatible: that plan adds the approval-grant TTL entry here, this row deletes the prompt entries.
- The Plan's registry-vs-dataclass check reports `stale entries: []`, so no other stale entry exists to remove, and no test or document pins the entry count (`rg` — no match per the Plan's predictable-fallout check).
- Companion judgement: `tests/agent/services/test_config_reload_classification.py` (row 16) is not a companion, because condition 2 fails — no other row's `Related Tests` cell names it — so it keeps its own document.
## Design decisions
- N/A: two entries are deleted from one list; no classification or policy decision.
## Alternatives considered
- Reclassifying the entries as startup-only instead of removing them: rejected, the fields no longer exist in the config layer.
## Implementation
### Target file
`scripts/agent/services/config_field_registry.py`
### Procedure
Delete `ConfigFieldRegistry("system_prompt_tool", "tool", True)` and `ConfigFieldRegistry("system_prompts", "tool", True)` (lines 78-79); neither entry carries a validator, so nothing else is removed.

### Details
- Consequences that need no code change here: `config_section_reload.py`, `config_outcome_classification.py`, and `config_service_sync.py` are generic or hold no prompt reference (Plan Reference Files); `scripts/agent/commands/cmd_config.py` lines 68-91 reports hot-reloadable fields from the registry, so the prompt fields simply disappear from the report.
- The generated manifest `registry/manifests/config_ownership.yaml` must be regenerated after this deletion (row 08).
## Compatibility considerations
- `/reload` keeps the observable behaviour that the prompt is hot-reloadable (Plan UNK-01 default); the classification report no longer lists the prompt as a config field. The prompt path itself moves to the typed read in row 10.
## Security considerations
- N/A: no trust boundary is involved.
## Rollback considerations
- N/A: revert the commit as part of RU-1; regenerate the manifest if rolled back.
## Validation plan
- `uv run pytest tests/agent/services/test_config_reload.py` (row 15) and `tests/agent/services/test_config_reload_classification.py` (row 16); `uv run python tools/generate_reference_table.py --manifests` then `--check` (row 08); `uv run ruff check .`, `uv run mypy scripts/`.
## Completion criteria
- The registry and the regenerated manifest contain no prompt entry and the tool-section field set assertion matches (AC-2).
## Out of Scope
- The approval-grant TTL entry added by `mcpdl003`; adding the two registered-but-absent config fields (Plan UNK-05).
## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure | Pending | — | — | RU-1; regeneration is row 08 |
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
- **Requirement ID**: `REQ-003` (remove both prompt registry entries and confirm no other stale entry)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `scripts/agent/services/config_field_registry.py`
