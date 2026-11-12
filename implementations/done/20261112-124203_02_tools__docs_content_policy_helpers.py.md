## Goal
Create `tools/_docs_content_policy_helpers.py` to hold the nodes extracted from `check_docs_content_policy.py` (`REQ-001`, `REQ-007` / `AC-1`, `AC-7`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The file does not exist (checked); `tools/` holds other `_*.py` helper modules (`_adr_authority_core.py`, `_docs_consistency_lib.py`) imported as `from tools._x import ...`.
- The final module name and node list are fixed at extraction time (UNK-03); if the name differs, amend this Plan with `tools/amend_plan.py` (fallout class).
- Created by the extraction in row 01, not by hand.

## Design decisions
- Module docstring states purpose and that it is owned by `check_docs_content_policy.py`; no behavior of its own.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`tools/_docs_content_policy_helpers.py` (new)

### Procedure
1. Create the file with a module docstring and `from __future__ import annotations`.
2. Receive nodes through `module_nodes.py extract` (row 01), verbatim.

### Method
- Keep the standard-library and `tools._docs_consistency_lib` imports the moved nodes need; no import back into `check_docs_content_policy.py` (no cycle).

### Details
- Add the module to `tools/TOOL_DESCRIPTIONS.md` (row 11) because `check_tool_descriptions_sync.py` requires every `tools/*.py`.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run ruff format <file>`, `uv run ruff check <file>`, `uv run mypy <file>`, `uv run bandit <file>` — clean.
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` — pass.
- `uv run pytest tests/tools/test_check_docs_content_policy.py -q` — pass.

## Completion criteria
- The module exists, holds only the extracted nodes, imports no tool that imports it, and passes ruff, mypy, bandit, and the size gate.

## Out of Scope
- New behavior; extracting more than needed.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the module and receive the extracted nodes | Completed | — | 20261112-211726 | 4 nodes extracted verbatim via module_nodes.py extract; compare identical; docstring + from __future__ import annotations added; helper imports only stdlib (no cycle) |
| 2 | Run the tests that import the moved names | Completed | 20261112-211726 | 20261112-211726 | tests importing DocFile/check_* pass (43 passed) - DocFile re-exported through the checker |
| 3 | Run the validation sequence for the new tool: ruff, mypy, bandit, size gate | Completed | 20261112-211726 | 20261112-211726 | ruff/mypy/bandit(-ll) clean; 1.5KB helper does not trip the 24576 size gate (no baseline row needed) |

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
- **Requirement ID**: `REQ-001` / `REQ-007` — new helper module receiving the extracted nodes
- **Source issue**: issues/20261109-113351_adrrev018_docs-checker-harden.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-111505_adrrev018_docs-checker-harden.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124203
- **Related target files**: `tools/_docs_content_policy_helpers.py`