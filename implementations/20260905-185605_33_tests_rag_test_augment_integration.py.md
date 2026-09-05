## Goal
Remove `use_semantic_cache`/`semantic_cache_max_size`/`semantic_cache_threshold`
`RagConfigImpl(...)` fixture keys from `tests/rag/test_augment_integration.py`, made
obsolete by procedure document `01` (`REQ-001`, `REQ-009`).

## Scope
- **In-Scope**: remove `use_semantic_cache=False,` (line 46),
  `semantic_cache_max_size=100,` (line 52), and `semantic_cache_threshold=0.0,` (line
  53) from a `RagConfigImpl(...)` fixture construction.
- **Out-of-Scope**: every other keyword argument in the same constructor call —
  confirmed unrelated by reading the surrounding lines.

## Assumptions
- `RagConfigImpl` (procedure document `01`) is a frozen `@dataclass` requiring every
  field as a constructor argument — once the three fields are removed there, this
  fixture must not pass them.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Remove all three keyword arguments together — this file's fixture is confirmed
  byte-identical in its cache-related lines to `tests/rag/test_augment_refiner.py`'s
  (procedure document `32`), suggesting both were copied from a shared template; the
  same edit applies to both files independently.

## Alternatives considered
N/A: straightforward removal of three now-invalid constructor arguments.

## Implementation
### Target file
`tests/rag/test_augment_integration.py`

### Procedure
1. Remove `use_semantic_cache=False,` (line 46).
2. Remove `semantic_cache_max_size=100,` (line 52).
3. Remove `semantic_cache_threshold=0.0,` (line 53).

### Method
Direct removal via `Edit`.

### Details
- Confirm after editing: `rg -n "semantic_cache"
  tests/rag/test_augment_integration.py` returns zero matches.

## Compatibility considerations
N/A: test-only file.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file; must be reverted together with
  procedure document `01` (`RagConfigImpl`).

## Validation plan
- `uv run pytest tests/rag/test_augment_integration.py -v` — all tests pass.
- `rg -n "semantic_cache" tests/rag/test_augment_integration.py` — zero matches.

## Completion criteria
- No reference to any of the three removed keys remains in this file (Plan `AC-1`,
  `AC-8`).

## Out of scope
- `scripts/rag/models_config.py`'s `RagConfigImpl` (procedure document `01`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixture cleanup only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-001` (fixture constructs `RagConfigImpl` directly with the removed fields)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/rag/test_augment_integration.py
