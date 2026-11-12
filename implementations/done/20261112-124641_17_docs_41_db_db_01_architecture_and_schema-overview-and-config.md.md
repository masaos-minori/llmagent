## Goal
State in `db_01` that `sqlite_vec_so` is required for the processes that open `rag.sqlite` or `session.sqlite`, and make the database count wording precise (`REQ-006` / `AC-6`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan; locate each passage by its quoted text, and skip and report it if it is already correct (Phase 1 rule).
- Current text: `Four DB files exist; ...` followed by `A fifth store, mcp_dedup.sqlite ...`; `db_03` names `mdq.sqlite` as a further database file (checked). UNK-02: the maintainer confirms the wording; default is `four platform databases` with the derived and disposable stores (`mcp_dedup.sqlite`, `mdq.sqlite`) named separately, without numbering them.
- Step 3a: section 2 also says the store modules are `re-exported through store.py`, but `scripts/db/store.py` does not exist (checked with `ls scripts/db/`), which contradicts the facade-deleted rule that adrrev017 row 08 rewrites; fix this clause in the same pass so the file is consistent.
- `sqlite_vec_so` appears in section 4 (`SQLiteHelper`) and its `load_vec` paragraph: `empty ... not loaded`; adjust to say the key is required by `build_db_config()` and an empty value is rejected there, while explicit `db_path` helpers may still pass an empty value.
- Execute after the adrrev017 procedures (this Plan `Depends on` them) so each passage is edited once on cleaned text.

## Design decisions
- Keep the edits to the count sentence, one requirement sentence, and the `store.py` clause.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/41_db/db_01_architecture_and_schema-overview-and-config.md`

### Procedure
1. Section 2: `Four DB files exist` becomes `Four platform databases exist`; name `mcp_dedup.sqlite` and `mdq.sqlite` as separate derived or disposable stores.
2. Section 2: remove `re-exported through store.py` from the module list.
3. Section 4: state that `sqlite_vec_so` is required for processes that open `rag.sqlite` or `session.sqlite` and that an empty value is rejected by `build_db_config()` and Agent startup validation.

### Method
- Verify against `scripts/db/config.py` and `scripts/agent/production_config_validator.py` after rows 13 and 14, so the text describes the implemented behavior.

### Details
- Do not describe `DbConfig`'s empty default as a supported production configuration.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain db` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_needs_confirmation_inventory.py` — pass.

## Completion criteria
- `db_01` states the requirement, the database count wording, and no `store.py` re-export; the db consistency check passes.

## Out of Scope
- `db_03` and `db_04` text; code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-204830 | 20261112-204830 |  |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112-204830 | 20261112-204830 |  |

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
- **Requirement ID**: `REQ-006` — `sqlite_vec_so` requirement and the database count wording
- **Source issue**: issues/20261109-113421_adrrev019_docs-stale-statements.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-112439_adrrev019_docs-stale-statements.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124641
- **Related target files**: `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`