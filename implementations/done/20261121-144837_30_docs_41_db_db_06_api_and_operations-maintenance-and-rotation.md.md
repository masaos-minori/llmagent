## Goal

Document that maintenance and retention values come from the typed configuration supplied by the owning process, instead of `scripts/db/` reading `agent.toml` (REQ-004; Documentation Impact).

## Scope
**Release unit**: N/A: documentation update (Phase 5)

## Assumptions
- The behaviour described (retention rules, tie-breaking order, the 0-disables rule, the BEST_EFFORT exception) is unchanged; only the source of the values is restated.
- `tools/check_docs_consistency.py --domain db` cross-checks config keys against `config/agent.toml`; the keys themselves stay in the file, so the check keeps passing.

## Design decisions
- Every statement of the form "read from `agent.toml::key`" becomes "read from the key in the configuration the owner supplies", because after Plan rows 8-10 no `db` module loads a file.
- The BEST_EFFORT exception paragraph keeps its meaning but is re-attributed: with injection there is no config load inside `db/`, so the propagate-in-both-modes rule applies to the caller that constructs the typed configuration (Plan row 16).

## Alternatives considered
- Keep the existing wording and add a note: rejected — documentation describes the current specification, and a note about a load that no longer happens is stale by construction.

## Implementation
### Target file
`docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`
### Procedure
- Update the checkpoint-mode paragraph (line 21) so the default comes from the injected typed configuration.
- Update the BEST_EFFORT exception paragraph (line 30) to name the typed-configuration construction instead of `RetentionConfig.from_config`, `CorruptArchiveRetentionConfig.from_config`, and `build_db_config`.
- Update the retention, archive-directory, corrupt-archive, and artifact-retention paragraphs (lines 32, 40, 42, 44) to describe values supplied by the configuration owner.
- Keep the key names and the fail-closed contract wording, since the keys remain in `config/agent.toml`.
### Method
- Wording changes only; no new section.
### Details
- Verified 2026-11-21: the code-level default for an absent `sqlite_archive_dir` is preserved by Plan row 10, so the "fallback when absent" sentence stays.

## Compatibility considerations
- The generated API table (Plan row 31) is refreshed separately; this document must not duplicate its contents.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain db`

## Completion criteria
- No sentence in this document attributes a config-file read to `scripts/db/`; the typed-injection contract matches the code after Plan rows 8, 9, 10, 12, 14, 16.

## Out of Scope
- The dataclass definitions (Plan rows 8, 9), the code changes, the generated API table (Plan row 31).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method | Completed | 2026-11-22 | 2026-11-22 | Implemented: the checkpoint, BEST_EFFORT, retention, archive-directory, corrupt-archive and artifact-retention paragraphs now describe values supplied by the typed configuration. Finding: the file read is attributed to the owning process while build_db_config() and from_mapping() keep validating the mapping inside db/, so the exception paragraph is re-attributed to that construction; ProductionConfigValidator now derives the accepted keys from DbMaintenanceConfig fields plus the file's sqlite_ prefix. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-22 | 2026-11-22 | N/A: documentation row; the checkers listed in the Validation plan are the verification. Gated: same as step 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22 | check_docs_quality, check_docs_structure, check_docs_content_policy pass; check_docs_consistency --domain db reports no issues. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-22 | 2026-11-22 | Gated: same - sibling documentation rows are separate procedure documents |

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
- **Requirement ID**: REQ-004 (documentation impact)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`
