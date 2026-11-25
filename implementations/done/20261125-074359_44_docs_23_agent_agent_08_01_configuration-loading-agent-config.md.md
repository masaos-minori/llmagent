## Goal

State that the hot-reloadable scope is exactly the registry entries with `hot_reloadable=True`, that startup-only fields stay pending, and that every MCP server-definition change is restart-required (REQ-003, REQ-008, REQ-014).

## Scope
**Release unit**: R7-docs-and-manifests

## Assumptions
- Verified against current source: `### Hot-Reloadable Scope` is at `docs/23_agent/agent_08_01_configuration-loading-agent-config.md:48`; the line that names `context_char_limit`, `context_compress_turns`, `context_token_limit`, and `tokenize_url` as HistoryManager hot-reloadable is `:51`.
- Verified against current source: the registry already carries `hot_reloadable` (positional third argument of each `ConfigFieldRegistry` entry, `scripts/agent/services/config_field_registry.py:33-38`), and `context_token_limit`, `context_char_limit`, `context_compress_turns` are already `False` (`:41-48`). Row 4 adds `field_type` and `allow_empty`, not `hot_reloadable`, so this document corrects the prose against a flag that already exists.
- Verified against current source: `tokenize_url` is not a registry entry; the only code that reads it is `scripts/agent/services/config_service_sync.py:66`. Its treatment is the open item recorded in row 10, and this document must state the same outcome row 10 lands.

## Design decisions
- The scope list is stated as the registry-derived set rather than a hand-maintained list, so the document cannot drift from `config_field_registry.py`.
- The three context limits move to the startup-only list, the set `startup_only_for` returns.

## Alternatives considered
- N/A: the list is the claim being corrected.

## Implementation
### Target file
`docs/23_agent/agent_08_01_configuration-loading-agent-config.md`

### Procedure
Rewrite the scope section after the registry and service-sync work lands (R7, after rows 4 and 10), then re-check the section against `startup_only_for` and the syncer.

### Method
- Rewrite `### Hot-Reloadable Scope` to the registry-derived set and add the startup-only and MCP restart-required statements.

### Details
- No other section is changed; the `Related Documents` heading stays.
- The `System Prompt` bullet (`:52`) and the `Security-Related Settings` section (`:58-60`) already match the restart-required rule and stay as they are.
- Open item for the R7 run: the Plan's Supporting Files row names `config/documentation_canonical_sources.toml` as the canonical-source registration point for the two documents this Plan edits, and neither is registered there today. Whether the rewritten scope list needs a registry entry, or must defer to `registry/manifests/config_ownership.yaml`, is decided from the `check_docs_content_policy.py` output.

## Compatibility considerations
- N/A: documentation-only change.

## Security considerations
- N/A: no configuration values are documented.

## Rollback considerations
- N/A: revert the Phase 7 commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain agent`

## Completion criteria
- The scope list matches the registry, the three context limits appear as startup-only, and the MCP restart rule is stated.

## Out of Scope
- The hot-reload command behavior document (row 43) and the generated artifacts (rows 45, 46).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-211000 | 20261125-213153 | R7 run 20261125: false atomicity and never-applied claims replaced with the four reload stages, the fixed commit order, and the pending restart display; docs quality, structure, content policy, consistency, and Japanese checks pass |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | 20261125-211000 | 20261125-213153 | R7 run 20261125: false atomicity and never-applied claims replaced with the four reload stages, the fixed commit order, and the pending restart display; docs quality, structure, content policy, consistency, and Japanese checks pass |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | The section the procedure targets is two bullets, not the three the Assumptions describe, and the second one is the false claim: it lists `context_char_limit`, `context_compress_turns`, `context_token_limit`, and `tokenize_url` as HistoryManager hot-reloadable, while the registry already marks the three `hot_reloadable=False` and `tokenize_url` is not a registry entry at all. The rewrite replaces both bullets with the registry-derived sets and keeps the System Prompt bullet | Yes | 2026-11-25 |
| 1 | `masked_fields` is applied by `/reload` but is not a `CONFIG_FIELD_REGISTRY` entry, so a section that says the hot-reloadable set is exactly the registry would contradict the code. The section names it as the one applied field outside the registry | Yes | 2026-11-25 |
| 2 | The per-key reference table already carried the correct `[OK]` / `[STARTUP-ONLY]` / `[RESTART]` / `[LIVE]` tags from the row 4 run, so only the prose section needed the change and the docs checkers report no inconsistency between them | Yes | 2026-11-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-008, REQ-014; AC-2, AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`