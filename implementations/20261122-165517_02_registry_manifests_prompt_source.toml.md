## Goal

Create the single stored prompt source, the one place prompt content lives, with the three current prompt values carried over as data (REQ-001, single-source contract).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `default`, `strict`, `creative` are kept as data; no prompt content is dropped from the current values (`config/agent.toml` lines 215, 229-232).
- This file is a hand-authored source-of-truth data file, not a generator manifest: it is not added to `tools/generate_reference_table.py`'s `_MANIFEST_SOURCES` (Plan UNK-02, non-blocking).
- Caveat recorded in the Plan: every committed file in `registry/manifests/` is `.yaml`, so a `.toml` file here is outside the generator's `--check` drift gate and breaks the directory's format convention. The `.toml` name is kept per the recorded owner decision; changing the format is a Plan revision, not a procedure change.
- `registry/` is rsynced as a whole by `deploy/deploy.sh` (lines 79-82), so no deployment change is required.

## Design decisions
- Content only, no behaviour: the file holds name-to-content mappings; validation and name lookup belong to the reader in row 03, so nothing here raises errors.
- `default` is required, because the reader treats a missing `default` as an error at the read boundary rather than a silent default (REQ-001).

## Alternatives considered
- Registering the file as a generator manifest type so `--check` guards it: rejected here, the generator derives manifests from source code and this file is its own source (Plan UNK-02, owner decision pending).
- Keeping prompt content in `config/agent.toml` and pointing the reader at it: rejected, that keeps a config-layer copy, which is the failure mode REQ-002 removes.

## Implementation
### Target file
`registry/manifests/prompt_source.toml` (new)
### Procedure
Author the file with one entry per current prompt name.
### Method
- One top-level table mapping prompt name to content, matching the shape the reader in row 03 parses: `default`, `strict`, `creative`.
- Values are copied byte-for-byte from `config/agent.toml` lines 215 and 229-232 before that block is deleted by row 01.
- No default, no fallback, no comment describing behaviour — those live in the reader and in the documentation row 22.
### Details
- The file is read through `shared.runtime_paths.resolve_registry_dir` (row 03), so a compiled binary resolves the deployed `registry/` through `LLMAGENT_REGISTRY_DIR`; a file placed here is what the reader will find at runtime.
- Format convention: TOML is chosen for consistency with the config layer's data files and because the reader parses it with the standard library `tomllib`.

## Compatibility considerations
- Consumers are the startup path (row 11) and the reload path (row 10); no other reader exists today, so adding this file breaks nothing.
- The file is outside the generator's two-way drift check, so a hand edit can drift silently; recorded as a Plan risk and UNK-02.

## Security considerations
- Read-only contract: the file is data, never written by the application; no prompt content is stored in code defaults, so a missing entry fails loudly instead of substituting a default.

## Rollback considerations
- Deleting this file restores the previous state only together with row 01 and row 03, since the prompt content lives only here after the change.

## Validation plan
- `uv run python tools/stale_detector.py <this document>` and `uv run python tools/check_workitem_structure.py --file <this document>` (this pass).
- At execution time: row 12's reader contract tests (`uv run pytest tests/agent/test_prompt_source.py`), which read this file and assert the name lookup, the missing-file case, and the missing-entry case.

## Completion criteria
- The three prompt names resolve to the same content they hold today, `default` is present, and no prompt copy remains outside this file (AC-1).

## Out of Scope
- Name-selection behaviour and any selection command (Plan Out-of-Scope, UNK-04).
- Registering the file as a generator manifest type (UNK-02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | content copied from `config/agent.toml` before row 01 deletes it |
| 2 | Add or update tests per Validation plan | Pending | — | — | covered by row 12 |
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
- **Requirement ID**: `REQ-001` (single stored prompt source and one typed model)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `registry/manifests/prompt_source.toml`
