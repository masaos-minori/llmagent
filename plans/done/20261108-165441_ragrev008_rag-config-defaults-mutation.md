## Goal
- Make `resolve_rag_config` resolve into a new mapping without mutating the caller's dict or object, make `rag_db_path` a required, non-defaulted key whenever `use_search=True`, and make an explicitly passed `module_cfg` supply keys that a dict or object `cfg` omits, so the rag-pipeline MCP service (which today silently falls back to `:memory:`) gets its configured database.

## Priority
Medium

## Scope
- **In-Scope**:
  - `resolve_rag_config` in `scripts/rag/config_resolution.py`: copy before applying defaults; layer `cfg` over `module_cfg` over defaults for dict/object `cfg`; default `rag_db_path` to `""` so the existing non-empty check reports it with `llm_url` and `embed_url`.
  - Tests for non-mutation, missing-path error, and `module_cfg` layering; fallout fixes for tests that relied on the implicit `:memory:` default.
  - The configuration-resolution description in the RAG docs.
- **Out-of-Scope**:
  - How configuration files are loaded, the `cfg is None` branch (config loader first, `module_cfg` only as fallback; its test stays as is), removing `:memory:` from test helpers that set it explicitly, changing unrelated default values, changing `build_rag_cfg_adapter` in the MCP package.
- **Dependencies**: N/A: none.

## Background
Review finding F-010. In `scripts/rag/config_resolution.py` the dict branch assigns `_raw_cfg = cfg` and the object branch `_raw_cfg = cfg.__dict__`, then the defaults loop writes into it (`resolve_rag_config`, L113-141); `_DEFAULTS_FOR_ALL["rag_db_path"] = ":memory:"` (L75) is non-empty, so the later `use_search` check over `rag_db_path`, `llm_url`, `embed_url` (L152-164) never reports it. Reproduced in Step 3: a `SimpleNamespace` with 18 attributes had 29 after `resolve_rag_config`. A larger consequence was found while verifying: `module_cfg` is consulted only when `cfg` is `None` (`config_resolution.py:134`), but the rag-pipeline MCP service passes an object `cfg` (`build_rag_cfg_adapter`, which has no `rag_db_path`, `sqlite_*`, `mqe_n_queries`, or template attributes) together with `module_cfg` carrying exactly those values (`scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py:80-115`). Reproduction with the adapter shape and `module_cfg={"rag_db_path": "/opt/llm/data/rag.db", "sqlite_timeout": 9, "mqe_n_queries": 7}` returned `rag_db_path=':memory:'`, `sqlite_timeout=5`, `mqe_n_queries=3` (checked in Step 3). The service's own comment says `module_cfg` is the intended source (service L114). The only production caller of `resolve_rag_config` is `RagPipeline.__init__` (`scripts/rag/pipeline.py:103`); `RagPipeline.augment` opens `self._rag_db_path` (`pipeline.py:273`).

## Problem
A missing database path produces a healthy-looking pipeline that never returns hits, with the cause hidden in a degraded counter, and mutating shared config objects leaks defaults into other consumers. In MCP mode the configured database and tuning values are ignored in favor of defaults (what a deployed server does is `不明`; only the in-process resolution was reproduced).

## Reason for Change
Ambiguous config behavior, defaults that mask a required key, is a fault that surfaces only in production. Making `rag_db_path` required as the Issue asks would, taken alone, make the MCP service fail at startup, so the `module_cfg` layering is a prerequisite of the requested validation.

## Implementation Intent
Resolve in this order for dict/object `cfg`: the caller's values, then `module_cfg` for keys the caller omits, then defaults, all in a fresh mapping. Keep the `cfg is None` branch untouched. Change only the `rag_db_path` default to `""`. Split the function into small helpers (it is already complexity D (24)) so the fix does not raise it.

## Requirements
- `REQ-001`: After `resolve_rag_config`, a caller dict or object is unchanged (same keys, same values, same attribute count).
- `REQ-002`: `use_search=True` without a non-empty `rag_db_path` (after layering) raises `ValueError` naming `rag_db_path`, reported together with any empty `llm_url` / `embed_url`.
- `REQ-003`: For a dict or object `cfg`, keys missing from `cfg` are taken from an explicitly passed `module_cfg` before defaults; keys present in `cfg` always win.
- `REQ-004`: The `cfg is None` branch, the `RagConfigImpl` passthrough, the filtering of unknown keys, and all other default values are unchanged.
- `REQ-005`: The MCP service's `RagPipeline(http, rag_cfg, module_cfg=...)` construction resolves to the `module_cfg` database path and tuning values.
- `REQ-006`: In-tree tests that relied on the implicit `:memory:` default are fixed to set the path explicitly (fallout; no behavior test is weakened).
- `REQ-007`: The RAG docs describe the resolution order and the required `rag_db_path`.

## Implementation Target Files
**Freeze status**: Frozen
Amended 2026-11-09 (fallout): added tests/agent/commands/test_agent_rag.py — Fixture _make_cfg builds a SimpleNamespace with use_search=True and no rag_db_path, so RagPipeline construction would raise once rag_db_path is required; set the path explicitly (fallout, no behavior test weakened)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/config_resolution.py` | Modify | Non-mutating resolution, `module_cfg` layering for dict/object `cfg`, `rag_db_path` default `""`, helper extraction | `REQ-001`..`REQ-005` / AC-1..AC-5 | Mutation at L113-141, default at L75, check at L152-164, `module_cfg` only on the `None` branch L134 (checked in Step 3) | `tests/rag/test_config_resolution.py` | Verified |
| `tests/rag/test_config_resolution.py` | Modify | Non-mutation, missing-path error, layering, MCP-adapter-shape, and `None`-branch-unchanged tests | `REQ-001`..`REQ-005` / AC-1..AC-5 | Existing resolver tests at L90-190 incl. `test_module_cfg_fallback_when_no_loader_and_no_exception` (checked in Step 3) | self | Verified |
| `docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md` | Modify | State the resolution order and the required `rag_db_path` when search is enabled (L30 area) | `REQ-007` / AC-7 | L30 describes construction from a flat `module_cfg` (checked in Step 3) | docs gates | Verified |
| `tests/agent/commands/test_agent_rag.py` | Modify | Fixture _make_cfg builds a SimpleNamespace with use_search=True and no rag_db_path, so RagPipeline construction would raise once rag_db_path is required; set the path explicitly (fallout, no behavior test weakened) | REQ-006 / AC-6 | tests/agent/commands/test_agent_rag.py _make_cfg defaults (use_search True, no rag_db_path) feed RagPipeline(http, cfg) at five call sites (checked in Step 3a) | tests/agent/commands/test_agent_rag.py | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/pipeline.py` | Sole production caller (L103); DB path use at L111, L273 | `REQ-005` |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` | `_build_module_cfg` (L80-95) and construction (L115) | `REQ-003`, `REQ-005` |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | `build_rag_cfg_adapter` omits the DB and tuning keys (L154-185) | `REQ-003` |
| `scripts/shared/config_validator.py` | `RagConfigValidator`; comment that `resolve_rag_config` fills template defaults (L89) | `REQ-004` |
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` | Service construction tests; must stay green | `REQ-005` |
| `docs/21_rag/rag_05_01-configuration-reference.md` | Config key reference; verify no key is documented as optional-with-default `:memory:` (none found by grep) | `REQ-007` |

## Acceptance Criteria
- AC-1 (`REQ-001`): input dict and `SimpleNamespace` snapshots compare equal before and after (keys, values, attribute count).
- AC-2 (`REQ-002`): `{"use_search": True, "llm_url": "http://l", "embed_url": "http://e"}` raises `ValueError` whose message names `rag_db_path`; all three empty names are listed together.
- AC-3 (`REQ-003`): adapter-shaped object plus `module_cfg={"rag_db_path": "/x", "sqlite_timeout": 9, "mqe_n_queries": 7}` resolves to those values; a key present on `cfg` beats the same key in `module_cfg`.
- AC-4 (`REQ-004`): existing resolver tests pass unmodified.
- AC-5 (`REQ-005`): a `RagPipeline` built the way the MCP service builds it has `_rag_db_path` equal to the `module_cfg` value.
- AC-6 (`REQ-006`): `uv run pytest tests -q` shows no new failures relative to the pre-change baseline; each fixed test sets `rag_db_path` explicitly.
- AC-7 (`REQ-007`): the doc states order and requirement; docs checkers pass.

## Tests
- `REQ-001`: dict and object non-mutation tests.
- `REQ-002`: missing, empty, and `None` `rag_db_path` with `use_search=True`; `use_search=False` without a path still resolves.
- `REQ-003`: layering tests including precedence and the MCP adapter shape.
- `REQ-004`: existing tests unmodified.
- `REQ-005`: a service-shaped construction test.
- `REQ-006`: census run of the full suite after the change.

## Documentation Impact
Yes (`REQ-007`): `docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md` (located via `docs/00_index.md` RAG rows and the Step 3 grep), intent and boundary only. Run `check_docs_quality`, `check_docs_structure`, `check_docs_content_policy`, `check_docs_consistency --domain rag`, `check_docs_japanese`.

## Assumptions
- Layering `module_cfg` under a dict/object `cfg` keeps the documented priority order (the caller's values are highest) and only changes the case where `module_cfg` was ignored entirely; this is the reading of the Issue constraint "keep the priority order".
- No in-tree production caller other than the MCP service constructs `RagPipeline` (grep of `scripts/` found only `rag_pipeline_service.py`); in-tree tests that omit `rag_db_path` with `use_search=True` are found by the Phase 1 census, not guessed here (the Issue's open question).
- Step 3a correction (plan-to-implementation-procedure): a static census of `tests/` (files with `use_search` true or `RagPipeline(`, minus those that set `rag_db_path`) found one fallout file that reaches `resolve_rag_config` without a path, `tests/agent/commands/test_agent_rag.py` (added as a fallout row); the other candidates (`tests/agent/test_tool_result_formatter.py`, `tests/integration/test_agent_integration.py`, `tests/rag/test_rag_stages.py`) never pass their config to the resolver. The Phase 1 full-suite baseline remains the authoritative census (UNK-02).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the deployed rag-pipeline MCP server currently searches `:memory:` (behavior in production) | Deployed `config/rag_pipeline_mcp_server.toml` and a live run were not inspected | Owner check after deploy; the code-path reproduction is the evidence here | False |
| UNK-02 | Which in-tree tests rely on the implicit `:memory:` default with `use_search=True` | Suite not run against the change | Phase 1 census; fixes are fallout under the Plan Amendment Approval Classes | False |
| UNK-03 | Whether the owner prefers fixing the adapter (`build_rag_cfg_adapter`) instead of the layering | Owner preference | Layering chosen (matches the service comment and covers other callers); an adapter change would be a separate Plan | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/config_resolution.py` | Modify | High (config entry for every `RagPipeline`; `radon`: `resolve_rag_config` D (24)) | 2 | N/A | not applicable (rsynced) |
| `tests/rag/test_config_resolution.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/commands/test_agent_rag.py` | Modify | Not assessed (amendment 2026-11-09) | N/A | N/A | Not assessed (amendment 2026-11-09) |

## Design
Path B (runtime-facing config contract change). Architecture: `resolve_rag_config` is a leaf in `rag/`; the only production caller is `RagPipeline.__init__`; `lint-imports` 6 contracts kept at plan time, no import changes planned. Consumer scan for `resolve_rag_config` (checked in Step 3): 9 script candidates (the caller and docstring/comment mentions), 15 test candidates; production validators only mention it in comments. Complexity: D (24) today; extraction of `_select_raw_cfg`, `_layer_config`, and `_require_search_fields` keeps each helper at A or B.

Alternatives: (a) only copy and require the path, rejected: it would break the MCP service start (the adapter lacks `rag_db_path`); (b) add the missing keys to `build_rag_cfg_adapter`, viable but touches the MCP package and leaves other callers exposed (UNK-03); (c) keep `:memory:` and check the original input for the key, rejected: the check would still pass for callers that deliberately rely on resolution. Chosen: non-mutating layering plus `""` default.

Persisted schema check: not applicable (no DDL).

Validation baseline: `vulture`/`bandit` pre-existing findings recorded in `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md` (source unchanged); `diff-cover`: none at plan time, 90 percent at implementation.

## Implementation steps
1. **Phase 1: Tests first and census**
   - [ ] Add non-mutation, missing-path, layering, adapter-shape tests (`REQ-001`..`REQ-005`; `tests/rag/test_config_resolution.py`)
   - [ ] Record the pre-change `uv run pytest tests -q` baseline for the census (`REQ-006`; no file change)
2. **Phase 2: Resolution change**
   - [ ] Helper extraction, layering, `""` default (`REQ-001`..`REQ-004`; `scripts/rag/config_resolution.py`)
3. **Phase 3: Fallout and documentation**
   - [ ] Fix tests that relied on the implicit default, each as a Plan Amendment of class fallout (`REQ-006`; files named by the census)
   - [ ] Document the resolution order and required path (`REQ-007`; `docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md`)
   - [ ] Modify (REQ-006; `tests/agent/commands/test_agent_rag.py`) — amendment 2026-11-09
4. **Phase 4: Deployment & Verification**
   - [ ] Full suite and gates; deploy hand-off to `skills/deploy/SKILL.md` after commit and push, at the user's decision, with an owner check of the deployed DB path (all requirements; `scripts/rag/config_resolution.py`)

### Release units
**Unit**: ragrev008-core | **Phases**: 2, 3 | **Reason**: the new required-path validation breaks tests and the service constructor until the layering and the fallout fixes land together.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/config_resolution.py` | Unit | `uv run pytest tests/rag/test_config_resolution.py tests/agent/test_rag_get_cfg.py -q` | new tests fail on HEAD, pass after |
| MCP service construction | Integration | `uv run pytest tests/mcp_servers/rag_pipeline -q` | green |
| whole suite | Census / regression | `uv run pytest tests -q` | no new failures versus the recorded baseline |
| touched code | Static | `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` | clean |
| docs | Docs gates | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` | no findings |

## Risks
- **Risk**: layering changes the effective config of the MCP service (tuning values now honored) → **Mitigation**: the values come from the service's own TOML; the change matches the service comment; UNK-01 owner check after deploy.
- **Risk**: required `rag_db_path` breaks other in-tree callers and tests → **Mitigation**: census in Phase 1/3; fallout fixes only add explicit paths.
- **Risk**: helper extraction alters validation order or messages → **Mitigation**: existing tests (including the real-validator template tests) run unmodified; message text keeps the current form.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first and census | Completed | — | 20261109-202305 |  |
| 2 | Phase 2: resolution change | Completed | — | 20261109-202305 |  |
| 3 | Phase 3: fallout and documentation | Completed | — | 20261109-202305 |  |
| 4 | Phase 4: deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261109-135232_01_scripts_rag_config_resolution.py.md | 1, 2 | Procedure | Completed | — | — |
| implementations/20261109-135232_03_docs_21_rag_rag_03_02_query_pipeline-rag-pipeline-class.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261109-135232_04_tests_agent_commands_test_agent_rag.py.md | 3 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-131121_ragrev008_rag-config-defaults-mutation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-165441
- **Related target files**: `scripts/rag/config_resolution.py`, `tests/rag/test_config_resolution.py`, `docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md`, `tests/agent/commands/test_agent_rag.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `config_resolution.py:113-141` | `scripts/rag/config_resolution.py` | Phase 2 | AC-1 | non-mutation tests | Confirmed by repository evidence |
| REQ-001 | Testing Expectations | `tests/rag/test_config_resolution.py` | Phase 1 | AC-1 | non-mutation tests | Explicit in issue |
| REQ-002 | Required Changes 2; `config_resolution.py:152-164` | `scripts/rag/config_resolution.py` | Phase 2 | AC-2 | missing-path tests | Confirmed by repository evidence |
| REQ-002 | Required Changes 2 | `tests/rag/test_config_resolution.py` | Phase 1 | AC-2 | missing-path tests | Explicit in issue |
| REQ-003 | Step 3 reproduction: `module_cfg` ignored for object cfg | `scripts/rag/config_resolution.py` | Phase 2 | AC-3 | layering tests | Confirmed by repository evidence |
| REQ-003 | Step 3 reproduction | `tests/rag/test_config_resolution.py` | Phase 1 | AC-3 | layering tests | Confirmed by repository evidence |
| REQ-004 | Constraints | `scripts/rag/config_resolution.py` | Phase 2 | AC-4 | existing resolver tests | Explicit in issue |
| REQ-005 | Step 3 reproduction; service L80-115 | `scripts/rag/config_resolution.py` | Phase 2 | AC-5 | service-shaped test | Confirmed by repository evidence |
| REQ-005 | Step 3 reproduction | `tests/rag/test_config_resolution.py` | Phase 1 | AC-5 | service-shaped test | Confirmed by repository evidence |
| REQ-006 | Unresolved Questions; Out of Scope | `tests/rag/test_config_resolution.py` | Phase 3 | AC-6 | full-suite census | Confirmed by repository evidence (Step 3a static census: one fallout file, `tests/agent/commands/test_agent_rag.py`, added by amendment; the full-suite run in Phase 1 can still add files, each as a fallout amendment) |
| REQ-007 | Documentation Impact | `docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md` | Phase 3 | AC-7 | docs gates | Explicit in issue |
| REQ-006 | Amendment 2026-11-09: Fixture _make_cfg builds a SimpleNamespace with use_search=True and no rag_db_path, so RagPipeline construction would raise once rag_db_path is required; set the path explicitly (fallout, no behavior test weakened) | tests/agent/commands/test_agent_rag.py | Phase 3 | AC-6 | tests/agent/commands/test_agent_rag.py | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261109-135232 -->
