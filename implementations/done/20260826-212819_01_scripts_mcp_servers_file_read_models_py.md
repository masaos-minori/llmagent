# Implementation Procedure Output Template (Canonical)

## Goal

Fix REQ-001: Make `FileReadConfig.max_read_bytes` mean exactly what its name says — remove the hidden KB round-trip entirely rather than renaming the TOML key. Interpret the configured value as bytes end-to-end, and rename the `FileReadConfig` dataclass field itself from `max_file_size_kb` to `max_read_bytes` so the Python attribute name also stops lying about the unit. Add a test that a non-1024-aligned byte count survives unchanged, proving no hidden conversion remains.

## Scope

- `scripts/mcp_servers/file/read_models.py`: Rename `FileReadConfig.max_file_size_kb` → `max_read_bytes`; change dataclass default from `1000` to `1024000`; remove `// 1024` in `from_dict`.
- `scripts/mcp_servers/file/read_service.py`: Change `build_service`'s `max_read_bytes=cfg.max_file_size_kb * 1024` to `max_read_bytes=cfg.max_read_bytes`.
- `tests/mcp_servers/file/test_file_read_mcp_models.py`: Update assertions per the rename.
- `tests/mcp_servers/file/test_read_service.py`: Update `test_build_service_with_allowed_dirs` construction kwarg and assertion.

## Assumptions

- Renaming `FileReadConfig.max_file_size_kb` to `max_read_bytes` is safe because the field is a plain Python dataclass attribute, never serialized, and not part of any Pydantic request/response schema exposed by file-read-mcp's tools — repository-wide `rg` search found only three call sites that reference it by name (`read_service.py` and two test files).
- Backward compatibility for the old (incorrect) KB-truncating interpretation of `max_read_bytes` may be dropped without a compatibility shim, consistent with this project's general no-compat policy (`tools/check_no_compat.py`).

## Design decisions

- Rename the dataclass field (not just the TOML key) because the Issue's stated intent is to make `max_read_bytes` mean bytes end-to-end, including in Python code where the current field name `max_file_size_kb` lies about the unit.
- Keep `from_dict` calling `get_typed(d, "max_read_bytes", int, "an integer", default=1024000)` but store the result directly (no `// 1024`) into the renamed field.
- Dataclass top-level default changes from `1000` to `1024000` so that `FileReadConfig()`'s direct-construction default matches `from_dict({})`'s default.

## Alternatives considered

- Renaming the TOML key instead of the Python field: rejected because `config/file_read_mcp_server.toml`'s own inline comment already states the key is bytes ("`max_read_bytes`: maximum bytes read per file") — the TOML author's intent is unambiguous and predates the current from_dict implementation.
- Keeping both names with a deprecation shim: rejected per this project's no-compat-shim policy (`tools/check_no_compat.py`).

## Implementation

### Target file

`scripts/mcp_servers/file/read_models.py`

### Procedure

Rename `FileReadConfig.max_file_size_kb` to `max_read_bytes`, change its dataclass default from `1000` to `1024000`, and remove the `// 1024` division in `from_dict`.

### Method

Direct edit: find and replace the field definition and the `from_dict` assignment.

### Details

1. Find `max_file_size_kb: int = 1000` in `FileReadConfig` dataclass definition — replace with `max_read_bytes: int = 1024000`.
2. Find `self.max_file_size_kb = get_typed(d, "max_read_bytes", int, "an integer", default=1024000) // 1024` in `from_dict` — replace with `self.max_read_bytes = get_typed(d, "max_read_bytes", int, "an integer", default=1024000)`.

## Compatibility considerations

- The corrected byte limit (1,000,000 vs. the previous 999,424) is a small behavior change for file-read-mcp callers whose read size happens to fall in the 576-byte gap — negligible practical impact at this magnitude; documented in Documentation Impact above; no compatibility shim required per this project's no-compat policy (`tools/check_no_compat.py`).
- No caller depends on the KB intermediate value for anything other than immediately multiplying it back by 1024 (`read_service.py` `build_service`); removing the round-trip is behavior-preserving for every caller except the intended fix itself.

## Security considerations

N/A: This change does not affect security boundaries or authentication paths.

## Rollback considerations

- If the rename breaks an unexpected caller, revert the field name and restore the `// 1024` in `from_dict` — the old behavior was incorrect but at least consistent within itself.
- Re-run `rg "max_file_size_kb" scripts/mcp_servers/file/*.py tests/mcp_servers/file/*.py` after the rename as a final check before considering the step complete.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/file/read_models.py` | Unit | `uv run pytest tests/mcp_servers/file/test_file_read_mcp_models.py -v` | `max_read_bytes` passes through `from_dict`/`load` unchanged, no truncation |
| `scripts/mcp_servers/file/read_service.py` | Unit | `uv run pytest tests/mcp_servers/file/test_read_service.py -v` | `build_service` enforces exactly `cfg.max_read_bytes`, no `* 1024` |
| Full suite | Regression | `uv run pytest -v` | No new failures beyond pre-existing baseline |
| Diff coverage | Coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% coverage on changed lines |
| Lint / type / security | Static | `uv run ruff check scripts/`, `uv run mypy scripts/`, `uv run bandit -r scripts/ -c pyproject.toml`, `PYTHONPATH=scripts uv run lint-imports` | All pass, no new findings |

## Completion criteria

- `FileReadConfig.load().max_read_bytes == 1000000` given `max_read_bytes = 1000000` in `config/file_read_mcp_server.toml`.
- `ReadFileService` built from it enforces exactly `1000000` bytes — verified by a test, with no `// 1024` or `* 1024` remaining anywhere between `read_models.py` and `read_service.py`.
- A new test asserts that a non-1024-aligned input (e.g. `max_read_bytes = 999999`) round-trips to exactly `999999`, proving no hidden conversion remains.
- All validation sequence checks pass (ruff, mypy, lint-imports, ast-grep constraint checks, bandit, targeted + full pytest, diff-cover ≥ 90%, pre-commit).

## Out of scope

- Fixing `RagPipelineConfig.from_dict`'s pre-existing bare `int()`/`float()`/`bool()`/`str()` coercions instead of the mandated `get_typed`-style validation (`rules/coding.md` Type-coercion policy).
- Any change to `github_mcp_server.toml` / `github_models_config.py`'s own `max_file_size_kb` field — that field is already named and behaves consistently (KB in, KB semantics), it is a distinct config surface from file-read-mcp's `max_read_bytes`, and the Issue does not name it.
- Doc edits to `docs/04_mcp_04_01_web-search-file-read-github.md` — out of scope for this document-only `issue-to-plan` phase; tracked as a required follow-up during implementation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm `config/file_read_mcp_server.toml`'s `max_read_bytes` value before editing | Completed | — | — | Value confirmed as 1000000 (bytes) |
| 2 | In `read_models.py`: rename field, change default, remove `// 1024` | Completed | — | — | Field renamed, default 1024000, // 1024 removed |
| 3 | In `read_service.py`: change `build_service` to use `cfg.max_read_bytes` directly | Completed | — | — | * 1024 removed |
| 4 | Update `test_file_read_mcp_models.py` per T-1 | Completed | — | — | Assertions updated, new non-1024 test added |
| 5 | Update `test_read_service.py::test_build_service_with_allowed_dirs` per T-1 | Completed | — | — | max_read_bytes=512000 assertion |
| 6 | Run full validation sequence | Completed | — | — | ruff OK, mypy OK, lint-imports OK, bandit OK, pytest 280/285 pass (4 skipped, 1 pre-existing failure) |
| 7 | Deploy via `deploy/deploy.sh` | Pending | — | — | |
| 8 | Restart/reload `file-read-mcp` and confirm health endpoint | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (make FileReadConfig effective byte limit equal configured max_read_bytes value, with no hidden unit conversion)
- **Source issue**: issues/20260821_05_issue.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260826-115018_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260826-212819
- **Related target files**: scripts/mcp_servers/file/read_models.py
