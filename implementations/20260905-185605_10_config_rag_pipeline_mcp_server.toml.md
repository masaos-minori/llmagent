## Goal
Remove `semantic_cache_max_size`/`semantic_cache_threshold` (and the
`use_semantic_cache` key, if present) from `config/rag_pipeline_mcp_server.toml`
(`REQ-008`).

## Scope
- **In-Scope**: remove the `# Semantic cache settings` comment line (line 56),
  `semantic_cache_max_size   = 100` (line 57), and `semantic_cache_threshold  = 0.92`
  (line 58). Note: this file does not set `use_semantic_cache` (confirmed by `grep` —
  only the two numeric-tuning keys are present, matching this Plan's own evidence
  "the 3 key/value lines" as an upper bound, not a literal count for this specific
  file).
- **Out-of-Scope**: every other configuration section in this file (`max_chunks_per_doc`,
  the "# Refiner settings" block and its keys) — confirmed unrelated by reading the
  surrounding context; `config/agent.toml` — confirmed by this Plan's Reference Files
  to not set any of the three removed keys, so no change is needed there.

## Assumptions
- Same hard ordering dependency as procedure documents `01`-`09`: this change must not
  be applied until procedure document `06`
  (`scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`, which wires
  `RagConfigValidator().validate()` into `RagPipelineConfig.load()`) has landed —
  landing this file's edit first is harmless in isolation (the keys would simply stop
  being read once `RagPipelineConfig` no longer declares them), but landing `06`
  first without this edit would cause `RagPipelineConfig.load()` to reject this file's
  still-present keys with the new migration error, breaking server startup. Land both
  in the same deployment.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §6/§9, narrow bullet only)
- Remove the `# Semantic cache settings` comment along with its two key/value lines,
  not just the keys — an orphaned section-header comment with no content beneath it
  would be misleading to a future reader of this config file.

## Alternatives considered
N/A: straightforward removal of an obsolete configuration section.

## Implementation
### Target file
`config/rag_pipeline_mcp_server.toml`

### Procedure
1. Re-verify procedure document `06` has landed (Assumptions) before proceeding —
   removing these keys must happen no earlier than the validator wiring that would
   otherwise reject a config file still setting them under a *future*, stricter
   check, and no later than that wiring's activation (they must land together for a
   clean deploy).
2. Remove the `# Semantic cache settings` comment line (line 56).
3. Remove `semantic_cache_max_size   = 100` (line 57).
4. Remove `semantic_cache_threshold  = 0.92` (line 58).
5. Confirm the blank line before line 56 and the `# Refiner settings` comment after
   (previously line 60) are left with normal single-blank-line spacing, matching this
   file's existing section-separator convention.

### Method
Direct removal via `Edit` on a TOML config file — no schema migration tooling applies
(plain key/value TOML, not a versioned schema).

### Details
- This is a deployed, active configuration file per this Plan's own Repository
  Evidence ("Confirmed active deployed config file setting
  `semantic_cache_max_size`/`semantic_cache_threshold`") — per `rules/toolchain.md`'s
  completion checklist, no `deploy/deploy.sh` change is needed since this file is
  edited in place, not added or removed (Plan Affected areas: "not applicable (no
  `deploy.sh` cp-line change; existing file edited in place, not added/removed)").
- Confirm after editing: `rg -n "semantic_cache" config/rag_pipeline_mcp_server.toml`
  returns zero matches.

## Compatibility considerations
- Once procedure document `06`'s validator wiring is active, this file must not set
  any of the three removed keys or the RAG MCP server will fail to start
  (`RagPipelineConfig.load()` raises) — this document's removal and `06`'s wiring must
  be deployed together, not independently.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; must be reverted together with
  procedure document `06`'s validator wiring to avoid deploying a validator that
  rejects a config this file (if reverted alone) would still contain.

## Validation plan
- `rg -n "semantic_cache" config/rag_pipeline_mcp_server.toml` — zero matches.
- Manual startup verification of `rag-pipeline-mcp` after deployment (per the `deploy`
  skill's standard process) confirms `RagPipelineConfig.load()` succeeds against the
  edited file.

## Completion criteria
- `config/rag_pipeline_mcp_server.toml` no longer sets any of the three removed keys
  (Plan `AC-6`).
- `rag-pipeline-mcp` starts successfully against the edited file once procedure
  document `06` has also landed.

## Out of scope
- `config/agent.toml` (confirmed to not require this change).
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`'s validator wiring itself
  (procedure document `06`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Must land together with procedure document `06` — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: config file, no test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: documentation deferred to `semcachedocs` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Must be deployed together with procedure document `06`'s validator wiring | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-008` (remove the three keys from `config/rag_pipeline_mcp_server.toml`)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: config/rag_pipeline_mcp_server.toml
