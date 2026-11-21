## Goal

Declare the extended per-tool field set on the 6 tool entries in this module (REQ-003; AC-03).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- The field set and the value types come from rows 01, 02 and 68 in the same release unit.
- The field-set version value is `2.1` (UNK-01, owner decision 2026-11-21); the version is recorded in one place.

## Design decisions
- The declared values reproduce the classification this module already encodes, so the change is a declaration of what is already true, not a behavior change.
- Where the module already splits metadata into a shared TypedDict, the shared part is extended rather than repeated per entry, so the shared values stay in one place.

## Alternatives considered
- N/A: REQ-003 requires the fields to be declared by the producer, so a consumer-side default is not an option here.

## Implementation
### Target file
`scripts/mcp_servers/github/tools_pull_requests.py`
### Procedure
- Extend the shared metadata TypedDict and its literal (`_GITHUB_PR_NO_SCOPE_TAIL`, `_GITHUB_PR_REPO_SCOPE_TAIL`, `_GITHUB_PR_TOOL_METADATA_HEAD`) with the new fields, and leave the per-entry values that already vary inline unchanged.
### Method
- Add the new required fields to each entry with the values that match the classification this module already encodes (read entries declare `read_only`, write entries the matching write class).
- Convert `resource_scope_keys` from a key list to the key-to-kind mapping using the declared kind of this module's scope.
### Details
- Verified 2026-11-21: the module declares 6 tool entries with scope kind /github_repo and keys owner, repo.
- The shared head/tail split is preserved; only the fields that are identical across all entries move into the shared TypedDict.
- Keys owner cannot be classified as path/branch/repo, so they take the value approved for keys no escalation rule reads.

## Compatibility considerations
- Every entry must carry the full set; `tests/mcp_servers/test_tool_schema_contract.py` (T-03) is the check that no entry is defaulted.

## Security considerations
- A declaration that lowers risk relative to the current classification would change approval behaviour; the values are written from the current classification to keep it identical.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_tool_schema_contract.py -v`
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- Every entry in this module declares the required fields, and the contract test reports no entry with a missing field.
- The declared values match the classification the module expresses today.

## Out of Scope
- The per-server write-protection gate that reads this module's tool list, and the runtime decision code that consumes the declared values (rows 22 to 25).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 3; release unit: contract-and-producers Implemented via tools/apply_producer_policy_fields.py; declared values mirror reference data (agent.toml tier map, tool_constants write sets, RETRYABLE_TOOLS, per-interface dry_run capability). |
| 2 | Add or update tests per Validation plan | N/A | — | — | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue No companion test update needed: tests/mcp_servers subtree green (2662 passed, 2026-11-21). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-203302 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue ruff/format/lint-imports/pytest targeted green 2026-11-21. Allowed red: mypy typeddict-unknown-key/typeddict-item on McpTool until row 68 lands (same release unit). unit-end validation: full suite 13314 passed / 7 skipped; ruff format+check clean; mypy 590 files clean; lint-imports 6 kept; diff-cover 97% (fail-under 90) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/mcp_servers/github/tools_pull_requests.py`