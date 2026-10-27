# Implementation Procedure: Rename the config-surface key in `_ALL_FIELDS`/`_DEFAULTS_FOR_ALL`

## Goal

Rename the query-path service-URL key `rag_service_url` to `rag_query_service_url` (new) in
the primary declaration site `scripts/rag/config_resolution.py`, preserving the `None`
default and the ignore-extras filter behavior (REQ-001, REQ-006).

## Scope

- Two string renames in `scripts/rag/config_resolution.py`: the `_ALL_FIELDS` entry (verified
  at L34) and the `_DEFAULTS_FOR_ALL` entry (verified at L66, value `None`).
- No change to `resolve_rag_config`'s filter logic, the validator, or any other field.

## Assumptions

- This rename is one row of a single mass rename spanning all 29 target files of this Plan:
  the declaration rows (this file, `models_config.py`, `types.py`) and the reader rows must
  land together in one implementation sequence; a partial landing breaks the typed config
  surface (Plan AC-1 gates completion with a grep).
- `RagConfigValidator` is not keyed on the URL field by name (Plan Reference Files).
- Overlap with the rag002 Plan on this file: none (rag002 does not touch this file).

## Design decisions

- Rename only the query-path key; `rag_pipeline_service_url` stays untouched (deployed in
  `config/ingester.toml`; Plan Design).
- No backward-compat alias: the ignore-extras filter already defines old-spelling behavior as
  "ignored → `None` → no delegation", the fail-safe default (Plan Design).

## Alternatives considered

- Renaming the ingestion key instead — rejected: it has live repo and deployed config entries
  (Plan Assumptions naming decision).

## Implementation
### Target file

`scripts/rag/config_resolution.py`

### Procedure

1. Rename the `"rag_service_url"` entry in `_ALL_FIELDS` (L34, verified) to the new spelling.
2. Rename the `"rag_service_url": None` entry in `_DEFAULTS_FOR_ALL` (L66, verified) to the
   new spelling; keep the `None` default value byte-identical.

### Method

Two single-token string renames; no logic change.

### Details

- `resolve_rag_config` filters `_raw_cfg` against `_ALL_FIELDS` before constructing
  `RagConfigImpl`; after the rename the old spelling is filtered out as an unknown field —
  the behavior pinned by the new test in `tests/rag/test_config_resolution.py` (sibling
  procedure).

## Compatibility considerations

- Repo config files and deployed `/opt/llm/config/` files reference neither spelling of the
  query key (verified inventory), so no config edit is required (REQ-006).

## Security considerations

- N/A: naming change; fail-safe default preserved.

## Rollback considerations

- N/A: revert the commit (two strings).

## Validation plan

- `grep -rn "rag_service_url" scripts/ tests/ | grep -v "rag_pipeline_service_url"` — no
  matches once all rename rows land (AC-1).
- `uv run pytest tests/rag/test_config_resolution.py` — renamed fixtures plus the new
  rename/ignore test pass.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`
  — clean.

## Completion criteria

- AC-1: zero standalone `rag_service_url` occurrences remain in this file; AC-2 (via the
  sibling test procedure): renamed key resolves from a config dict, old spelling stays `None`.

## Out of Scope

- `RagConfigImpl` and `RagConfig` renames (own procedure documents), test renames, doc
  renames, and `rag_pipeline_service_url` (REQ-003).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Land with the other Phase 2 rows before Phase 3 tests |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests live in `implementations/20261027-154619_08_tests_rag_test_config_resolution.py.md` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs covered by rows 22-29 |

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
- **Requirement ID**: REQ-001, REQ-006
- **Source issue**: issues/20261027-071953_rag003_rag-url-key-ambiguity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110727_rag003_rag-url-key-ambiguity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-154619
- **Related target files**: scripts/rag/config_resolution.py
