## Goal

Reject `rag_pipeline_service_url` as a removed RAG delegation key in `scripts/shared/config_validator.py`, and update its tests (REQ-001 / AC-1).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `RagConfigValidator` runs only inside `resolve_rag_config` and `config_section_builders`, on dicts from `ConfigLoader.load_all()` (which loads `agent.toml` only) or a module configuration. It never sees `ingester.toml`, so the rejection does not stop the ingester.
- The existing message already states the delegation path was removed; only the frozenset grows.

## Design decisions

- Add the key to the existing `_check_removed_rag_delegation_keys` frozenset; no new check, no alias.

## Alternatives considered

N/A: adding one member to an existing frozenset; no design trade-off.

## Implementation
### Target file
`scripts/shared/config_validator.py`

### Procedure
Add `rag_pipeline_service_url` to the removed-key frozenset in `_check_removed_rag_delegation_keys`.

### Method
Edit.

### Details
Inside `_check_removed_rag_delegation_keys`, change:

```
        removed_keys = frozenset(
            (
                "rag_query_service_url",
                "rag_auth_token",
                "rag_identity_mismatch_policy",
            )
        )
```

to:

```
        removed_keys = frozenset(
            (
                "rag_query_service_url",
                "rag_auth_token",
                "rag_identity_mismatch_policy",
                "rag_pipeline_service_url",
            )
        )
```

Leave the message text unchanged.

### Companion test files
- `tests/shared/test_config_validator.py`
  - Procedure: add `rag_pipeline_service_url` to the removed-key rejection assertions; replace the assertion at line 221 that the key is *accepted* with a valid configuration that carries no removed keys.
  - Validation: `uv run pytest tests/shared/test_config_validator.py` — the removed-key test names the key; a clean configuration stays valid.

## Compatibility considerations

None: the validator only gains a rejected key.

## Security considerations

N/A: configuration-key rejection.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_config_validator.py` — key rejected; clean config valid.
- `uv run ruff format` / `ruff check` clean.

## Completion criteria

`rag_pipeline_service_url` is in the removed-key frozenset; its tests assert rejection.

## Out of Scope

`ingester.toml` load path (never validated by this class).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion row above |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001 — reject `rag_pipeline_service_url` as a removed key
- **Source issue**: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-210705
- **Related target files**: `scripts/shared/config_validator.py`, `tests/shared/test_config_validator.py`
