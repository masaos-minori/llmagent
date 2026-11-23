## Goal

Add the check_skill_size gate so fast mode selects it when a covered instruction file changes.

## Scope
**Release unit**: skill-size-gate

In scope: one `Gate(...)` entry. No existing gate changes.

## Assumptions

- Verified: `check_config_comment_length` is declared as `Gate(name=..., command=(("uv", "run", "python", "tools/<tool>.py"),), source=SOURCE_ROUTING, mode=MODE_FAST, patterns=("config/**",))` (around lines 413-419); an existing gate already matches `tools/*.py`, so this gate's patterns name the covered instruction files and the baseline only.
- The tool reads the whole covered set and takes no file arguments, so the command has no `__CHANGED_FILES__` placeholder.

## Design decisions

- Gate named check_skill_size, patterns `skills/**`, `rules/*.md`, `prompts/*.md`, `templates/*.md`, `routing.md`, `AGENTS.md`, `CLAUDE.md`, `tools/check_skill_size.py`, and `tools/check_skill_size_baseline.txt`.

## Alternatives considered

Rejected: no patterns (a gate without patterns is never auto-selected in fast mode, so growth would not be caught at commit time).

## Implementation
### Target file
`tools/_validation_gate_defs.py`

### Procedure
1. Add the gate after `check_config_comment_length`, keeping the file's ordering convention.

### Method
One Edit.

### Details
- `tests/tools/test_run_validation_gates.py` checks that every CI lint command has a gate and that the gate definitions are well formed.

## Compatibility considerations

Additive; selected only when a covered file changes.

## Security considerations

N/A: no new data path.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/tools/test_run_validation_gates.py -q`
- `uv run python tools/run_validation_gates.py drift`

## Completion criteria

- The gate exists with the patterns above and the gate tests and drift check pass.

## Out of Scope

CI (procedure 06) and the tool-gate table (procedure 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: `REQ-002` (gate, CI, inventory wiring)
- **Source issue**: issues/20261123-155457_skillsize001_compress-skill-workflows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-155813_skillsize001_compress-skill-workflows.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-160210
- **Related target files**: `tools/_validation_gate_defs.py`
