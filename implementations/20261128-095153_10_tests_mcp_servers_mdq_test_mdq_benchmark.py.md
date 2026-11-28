## Goal

Create `tests/mcp_servers/mdq/test_mdq_benchmark.py`, the harness that measures p50, p95, and p99 for search, grep, index, refresh, and rebuild and prints the report, so the production claim for `REQ-002` has a reproducible measurement without asserting thresholds that the owner has not agreed (`AC-2`).

## Scope
**Release unit**: benchmark-marker-and-harness

- New test module: the harness plus its report, with no assertion on any measurement.
- The `benchmark` marker registration is row 04, and the plan declares the registration and the harness as one release unit, so they land in the same commit.

## Assumptions

- The module does not exist today; `pytest-benchmark` 5.2.3 is a dev dependency (`pyproject.toml:57`) and no test uses it, and `tests/mcp_servers/mdq/` has no `__init__.py`, so the module is imported as `tests.mcp_servers.mdq.test_mdq_benchmark`.
- `pytest_benchmark.stats.Stats` exposes `median`, `min`, `max`, `mean`, `rounds`, and `sorted_data()`, and has no percentile property, so p95 and p99 must be computed from the raw round data; `statistics.quantiles(..., n=100, method="inclusive")` gives the 99 cut points, where index 49 is p50, 94 is p95, and 98 is p99.
- Under xdist the plugin disables itself and the fixture calls the benchmarked callable once with `benchmark.stats` left as `None`, so the report must record "not measured" instead of failing; CI's single run uses `-n logical`, so CI cannot be the measurement environment (`UNK-07`).
- The four dimensions are chunk count, database size, chunk length, and concurrency, as `AC-2` names them; the specific fixed levels are chosen by this procedure as literal constants, because the plan names the dimensions and not the values.
- Determinism requires `-p no:randomly`, since `pytest-randomly` is installed (`pyproject.toml:60`) and reseeds each run.

## Design decisions

- Measure and print, assert nothing: a threshold assertion would read as an agreed contract that does not exist, so the module stays `characterization` and flips to `contract` only when the thresholds are agreed (`AC-2`).
- Build the corpus from a fixed generator with literal sizes, so two runs on the same machine are comparable and no fixture directory is introduced.
- Keep the harness in one module with one benchmark call per operation and level, so the printed report is grouped by operation and dimension without a second aggregation layer.

## Alternatives considered

- Run the harness inside CI: rejected, CI's `-n logical` run disables the plugin (pytest-benchmark's session disables itself under xdist), so a CI run produces no measurements (`UNK-07`).
- Assert against the plugin's own `median`/`iqr` fields: rejected, `AC-2` names p50, p95, and p99, and the plugin reports Tukey hinges (`q1`, `q3`), not the percentiles the criteria require.
- Classify as `contract`: rejected, there is no requirement-defined expected value to trace to until the thresholds exist.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_benchmark.py` (new)

### Procedure
1. Create the module with `import pytest`, `pytestmark = [pytest.mark.characterization, pytest.mark.benchmark]`, and a module docstring that states the harness measures and reports without asserting.
2. Define the fixed levels as module-level literal constants: corpus sizes (chunk count), chunk-length bands, and concurrency levels.
3. Add one benchmark test per operation (search, grep, index, refresh, rebuild) at each level, each calling `benchmark(...)` with a callable that runs the service call through `asyncio.run()`.
4. Print the report as operation, dimension, level, rounds, p50, p95, p99, and record "not measured" when `benchmark.stats` is `None`.

### Method

- Use `MdqService` with a `tmp_path` database and `tmp_path` in `allowed_dirs`, following the existing fixture precedent in `tests/mcp_servers/mdq/test_parser.py:28`, so the harness writes nothing under `/opt/llm`.
- The benchmark fixture requires a synchronous callable, so async service calls are wrapped in `asyncio.run()` inside the callable rather than making the test itself async.
- Concurrency levels are measured as `asyncio.gather` batches of the same call, so a level is one benchmarked call that runs N tasks.
- Land the module in the same commit as the marker registration (the `benchmark-marker-and-harness` release unit), because the marker would be selected as unknown without it.

### Details

- Percentiles are computed from `list(benchmark.sorted_data())` with `statistics.quantiles(..., n=100, method="inclusive")`; the module does not use `q1`/`q3` as substitutes.
- Database size is reported as the file size of the temp database after each build, so the dimension is observable from the run rather than assumed.
- `pytestmark` is written by hand here: `tools/apply_test_taxonomy_markers.py` validates an existing module and writes only the taxonomy marker, so it is not used for a created file.
- The checker sees only taxonomy names in `pytestmark`, so the two-element list is read as one classification (`characterization`) and produces no `module-level-both-kinds` finding.

## Compatibility considerations

- The module runs in the normal suite as well, where the plugin is disabled under xdist and each benchmarked call executes once, so it must not fail there; that is the reason the report handles `stats is None`.
- The report is printed, so CI log readers must not read it as evidence of the measured scale; the docs record measured values only from a run made outside xdist.
- A characterization failure remains report-only in the CI report step (`AC-6`).

## Security considerations

- `N/A: measurement harness only.` The harness works inside `tmp_path` and touches no path outside it, so no authorization behavior is involved.

## Rollback considerations

- Delete the module and revert the commit, together with the marker registration in the same release unit. No persisted state is involved.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_benchmark.py -m benchmark -p no:randomly` — p50, p95, and p99 printed for search, grep, index, refresh, and rebuild (`AC-2`)
- `uv run pytest tests/mcp_servers/mdq/test_mdq_benchmark.py` without `-m benchmark` under `-n logical` — the module stays green with no measurements
- `uv run python tools/check_test_taxonomy.py` — the module is `characterization`, `benchmark` is registered, no finding (`AC-3`)
- Full sequence per `rules/toolchain.md`, including `uv run ruff check tests/mcp_servers/mdq/test_mdq_benchmark.py` and `uv run mypy tests/mcp_servers/mdq/test_mdq_benchmark.py`.

## Completion criteria

- The harness reproduces p50, p95, and p99 for the five operations across the four dimensions (`AC-2`).
- No assertion depends on a threshold, so the run reports measurements only (`AC-2`).
- The module carries exactly one taxonomy marker, `characterization`, and the `benchmark` marker is selected without an unknown-marker warning (`AC-3`).
- The Phase 8 run outside xdist produces the values that `docs/22_mcp/mcp_04_04_mdq.md` records as the measured scale.

## Out of Scope

- The `benchmark` marker registration (`pyproject.toml`, row 04).
- The thresholds themselves and any status change, which are owner decisions (`UNK-02`).
- Any CI change that would run the harness outside xdist (`UNK-07`).
- The documentation section that records the measured scale (`docs/22_mcp/mcp_04_04_mdq.md`, row 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 6, same commit as the marker registration |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | The "Add or update tests" step does not apply: this row is the test module itself |

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
- **Requirement ID**: REQ-002 (reproducible benchmark harness for p50, p95, p99), AC-2
- **Source issue**: `issues/20261119-142132_mdqmcp010_mdq-release-readiness.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-203046_mdqmcp010_mdq-release-readiness.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-095153
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_benchmark.py`
