# Plan: Rename the query-path RAG service-URL key to `rag_query_service_url`

## Goal
- Remove the name ambiguity between the two RAG service-URL config keys by renaming the
  query-path key `rag_service_url` to the purpose-obvious `rag_query_service_url`, propagating the
  rename through every declaration, reader, test, and doc, while leaving the ingestion-path key
  `rag_pipeline_service_url` and all behavior unchanged.

## Priority
Low

## Scope
- **In-Scope**:
  - Rename `rag_service_url` to `rag_query_service_url` in the declaration sites
    (`config_resolution.py` `_ALL_FIELDS`/`_DEFAULTS_FOR_ALL`, `models_config.py`,
    `shared/types.py` `RagConfig` protocol) and every reader.
  - Mechanical rename of all 14 test files that reference the key, plus one new regression test in
    `tests/rag/test_config_resolution.py` pinning the new spelling and the old spelling's
    documented "ignored as unknown field" behavior.
  - Rename every doc occurrence (8 pages) and add a purpose-distinction paragraph for the two keys
    in the RAG configuration reference.
- **Out-of-Scope**:
  - Renaming `rag_pipeline_service_url` (rejected — see Design: it is live in the deployed
    `config/ingester.toml`; renaming the query key has zero config-file impact).
  - Changing semantics or defaults of either key, or which path reads which key (carried from the
    Issue).
  - Renaming `rag_auth_token` or any other RAG config field (the Issue keeps the diff to the two
    keys; `rag_auth_token` stays paired with the renamed key).
  - Adding backward-compat mapping for the old spelling (see Design: no consumer exists).
  - Adding a third service-URL key (carried from the Issue).
- **Dependencies**:
  - The Issue's dependency "confirm whether the config key is consumed outside this repository"
    is **resolved by verification on 2026-10-27**: `rag_service_url` appears in no repo config file
    (`grep config/`), no deployed config under `/opt/llm/config/`, and `docs/10_adr/adr_02_06_010_rag-fallback.md`
    states no production process sets it. `rag_pipeline_service_url` appears in `config/ingester.toml`
    and the deployed `/opt/llm/config/ingester.toml` — which is why that key is the one NOT renamed.
  - Overlap with sibling Plans: `tests/rag/test_rag_pipeline.py` and `tests/rag/test_augment_refiner.py`
    are also targets of the rag001 Plan. Compatible: this Plan renames key-name strings inside them;
    rag001 appends new tests. Disjoint edit regions; whichever Plan implements second rebases.
    The rag002 Plan (`plans/20261027-110252_rag002_rag-timeout-enforcement-gap.md`) also targets
    `docs/21_rag/rag_05_01-configuration-reference.md`. Compatible: rag002 extends the
    `http_timeout` paragraph; this Plan renames key occurrences and adds the key-contrast
    paragraph. Disjoint paragraphs; the second implementer rebases.
    The rag004 Plan (`plans/20261027-111107_rag004_ingester-sqlite3-error-aborts-batch.md`) also
    targets `docs/21_rag/rag_05_04-error-handling-reference.md`. Compatible: this Plan renames the
    `rag_service_url` occurrence in the RagPipeline table; rag004 adds a row to the RagIngester
    table. Disjoint sections; the second implementer rebases.

## Background
- `scripts/rag/config_resolution.py` declares both keys in `_ALL_FIELDS` with defaults `None` in
  `_DEFAULTS_FOR_ALL`, and `resolve_rag_config` filters `_raw_cfg` to `_ALL_FIELDS` before building
  `RagConfigImpl` — the code comment records "Only pass known fields ... ignore extras from config
  loader", so an unrecognized key is silently ignored (verified; no field-specific validation exists
  for either URL key in the validator).
- Readers (verified): query path `scripts/rag/pipeline.py` (`if rag_url := self._cfg.rag_service_url:`),
  `scripts/rag/http_augment.py` (docstrings), `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`
  (`rag_service_url=""` pin in `build_rag_cfg_adapter()` to prevent HTTP loops),
  `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` (module docstring). Ingestion reader
  `scripts/rag/ingestion/ingester.py` reads `rag_pipeline_service_url` from `config/ingester.toml`.
- Config-file inventory (verified 2026-10-27): `rag_pipeline_service_url = "http://127.0.0.1:8010"`
  exists in `config/ingester.toml` and the deployed `/opt/llm/config/ingester.toml`; `rag_service_url`
  exists in no repo or deployed config file. `deploy/deploy.sh` copies `config/*.toml` to
  `/opt/llm/config/` on deploy.

## Problem
- `rag_service_url` vs `rag_pipeline_service_url` differ only by the `_pipeline_service` segment and
  are independent keys for independent paths (query delegation vs ingestion callback), inviting
  misconfiguration.
- Current doc coverage of the distinction is scattered: `docs/21_rag/rag_05_01-configuration-reference.md`
  documents `rag_service_url` only negatively ("is not a key of `config/agent.toml`"), and the ADR
  records "no configuration file sets `rag_service_url`" as a production-state fact — neither page
  contrasts the two key names as a pair.

## Reason for Change
- Settling the naming before more parallel RAG URLs appear keeps the query and ingestion surfaces
  distinguishable by name and shortens review of config changes.

## Implementation Intent
- Rename the **query-path** key to `rag_query_service_url` (the Issue's own example direction:
  prefixing the query-path key with `query`), across declarations, protocol, readers, tests, and
  docs; keep the ingestion key as-is; preserve the `None` default and all delegation semantics.

## Requirements
- `REQ-001`: The config surface exposes the query-path URL only as `rag_query_service_url`:
  `_ALL_FIELDS`/`_DEFAULTS_FOR_ALL` (`None` default), `RagConfigImpl.rag_query_service_url`, and the
  `RagConfig` protocol attribute in `scripts/shared/types.py` all carry the new name; `rag_service_url`
  no longer appears in `scripts/`.
- `REQ-002`: Every reader references the new name: `scripts/rag/pipeline.py` delegation check,
  `scripts/rag/http_augment.py` docstrings, the `build_rag_cfg_adapter()` empty-string pin in
  `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`, and the `rag_pipeline_server.py` module
  docstring. Which path reads which key is unchanged.
- `REQ-003`: `rag_pipeline_service_url` (name, default, `config/ingester.toml` entry, deployed
  config) is untouched.
- `REQ-004`: All 14 test files that reference the key use the new spelling; `tests/rag/test_config_resolution.py`
  additionally pins that the renamed key resolves from a config dict and that the old spelling
  `rag_service_url` in a config dict is ignored (stays `None`), matching the documented filter
  behavior.
- `REQ-005`: All 8 docs pages that name `rag_service_url` name `rag_query_service_url` instead;
  `docs/21_rag/rag_05_01-configuration-reference.md` gains an explicit paragraph contrasting the two
  service-URL keys (query delegation vs ingestion callback). ADR-010's present-tense claims are
  updated to the new name with a one-time "(renamed from `rag_service_url`)" note; its decision
  record and rationale text stay intact.
- `REQ-006`: Behavior is preserved end to end: empty/absent value still means "no HTTP delegation,
  run in-process"; the MCP adapter still pins the value to `""`; no new config key is added and no
  config file (repo or deployed) needs editing.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/rag/config_resolution.py | Rename in `_ALL_FIELDS` and `_DEFAULTS_FOR_ALL` (default `None` preserved) | Primary declaration of the config surface | REQ-001, REQ-006 | `_ALL_FIELDS` entry at L34, `_DEFAULTS_FOR_ALL` entry at L66 | tests/rag/test_config_resolution.py | Verified |
| scripts/rag/models_config.py | Rename `RagConfigImpl` field | Dataclass declaration of the field | REQ-001 | `rag_service_url: str` at L26 | tests/rag/test_config_resolution.py | Verified |
| scripts/shared/types.py | Rename `RagConfig` protocol attribute | Protocol contract consumed across packages | REQ-001 | `rag_service_url: str` at L97 | tests/agent/test_rag_get_cfg.py | Verified |
| scripts/rag/pipeline.py | Rename the delegation check `if rag_url := self._cfg.rag_query_service_url:` | Reader that selects HTTP vs in-process mode | REQ-002, REQ-006 | Delegation check at L243 with comment at L241 | tests/rag/test_rag_http_mode.py; tests/rag/test_pipeline_http_result_kind.py | Verified |
| scripts/rag/http_augment.py | Rename key references in module/class docstrings | Docstrings name the trigger key | REQ-002 | "When rag_service_url is configured ..." at L73 | tests/rag/test_augment_integration.py | Verified |
| scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py | Rename the `rag_service_url=""` pin keyword in `build_rag_cfg_adapter()` | HTTP-loop guard must bind to the renamed field | REQ-002, REQ-006 | `rag_service_url=""` keyword at L171 with anti-loop comment | tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py | Verified |
| scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py | Rename key references in module docstring | Docstring describes when the server replaces in-process augment | REQ-002 | Docstring lines 7-8 | N/A (docstring) | Verified |
| tests/rag/test_config_resolution.py | Rename key fixtures plus new test: renamed key resolves; old spelling is ignored (stays `None`) | Issue Testing Expectations | REQ-004 | File constructs configs with both key spellings today | the file itself | Verified |
| tests/rag/test_rag_pipeline.py | Rename key spellings in fixtures | References both keys in config fixtures | REQ-004 | Key appears in fixture dicts (L199 region) | the file itself | Verified |
| tests/rag/test_rag_http_mode.py | Rename key spellings in fixture configs | Fixture sets `cfg.rag_service_url` to drive HTTP mode | REQ-004 | `_make_pipeline(rag_service_url=...)` helper | the file itself | Verified |
| tests/rag/test_pipeline_http_result_kind.py | Rename key spellings | Constructs configs with the key | REQ-004 | Key present in file | the file itself | Verified |
| tests/rag/test_rag_quality_regression.py | Rename key spellings | Constructs configs with both keys | REQ-004 | Key present in file | the file itself | Verified |
| tests/rag/test_stage_observability.py | Rename key spellings | Constructs configs with both keys | REQ-004 | Key present in file | the file itself | Verified |
| tests/rag/test_stage_lifecycle.py | Rename key spellings | Constructs configs with both keys | REQ-004 | Key present in file | the file itself | Verified |
| tests/rag/test_rag_pipeline_no_cache_freshness.py | Rename key spellings | Constructs configs with both keys | REQ-004 | Key present in file | the file itself | Verified |
| tests/rag/test_augment_integration.py | Rename key spellings | Constructs configs with both keys | REQ-004 | Key present in file | the file itself | Verified |
| tests/rag/test_augment_refiner.py | Rename key spellings in `_make_*` config kwargs | Constructs configs with both keys | REQ-004 | Key present in file | the file itself | Verified |
| tests/rag/test_rag_pipeline_stage.py | Rename key spellings | Constructs configs with both keys | REQ-004 | Key present in file | the file itself | Verified |
| tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py | Rename key references (adapter pin assertions) | Asserts the anti-loop pin behavior | REQ-004 | Key present in file | the file itself | Verified |
| tests/agent/commands/test_agent_rag.py | Rename key references | Constructs configs with the key | REQ-004 | Key present in file | the file itself | Verified |
| tests/agent/test_rag_get_cfg.py | Rename key references (protocol attribute) | Exercises the `RagConfig` protocol surface | REQ-004 | Key present in file | the file itself | Verified |
| docs/21_rag/rag_05_01-configuration-reference.md | Rename all occurrences and add the two-key purpose-contrast paragraph | The Issue's Documentation Impact names the RAG config reference | REQ-005 | Two occurrences describing the key negatively (L90, L93) | N/A: documentation file | Verified |
| docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md | Rename heading "HTTP Mode (`rag_service_url`)", body, and prevention table | Query-path docs name the key in headings and tables | REQ-005 | Occurrences at L36, L38, L46 | N/A: documentation file | Verified |
| docs/21_rag/rag_03_01_query_pipeline-overview.md | Rename flow-diagram occurrence | Pipeline overview names the decision key | REQ-005 | Occurrence at L36 | N/A: documentation file | Verified |
| docs/21_rag/rag_01_system_overview.md | Rename delegation occurrence | System overview names the key | REQ-005 | Occurrence near L180 | N/A: documentation file | Verified |
| docs/21_rag/rag_05_04-error-handling-reference.md | Rename fallback-table row | Error table references the key | REQ-005 | Occurrence at L97 | N/A: documentation file | Verified |
| docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md | Rename adapter-pin bullet | MCP page records the anti-loop pin | REQ-005 | Occurrence at L41 | N/A: documentation file | Verified |
| docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md | Rename the `HttpAugment` presence condition | Agent diagnostics page names the key | REQ-005 | Occurrence at L48 | N/A: documentation file | Verified |
| docs/10_adr/adr_02_06_010_rag-fallback.md | Rename present-tense key references with a one-time "(renamed from `rag_service_url`)" note; decision record unchanged | ADR states production config facts keyed on the old name | REQ-005 | Occurrences at L43, L48 | N/A: documentation file | Verified |

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/rag/config_resolution.py `resolve_rag_config()` | Confirms the extras-ignoring filter that defines the old spelling's post-rename behavior | REQ-004 new test |
| scripts/rag/ingestion/ingester.py | The untouched ingestion reader that defines the contrast in the new docs paragraph | REQ-003, REQ-005 |
| config/ingester.toml, /opt/llm/config/ingester.toml | Deployed consumer inventory that fixes which key must NOT be renamed | REQ-003, Scope |
| deploy/deploy.sh | Confirms `config/*.toml` → `/opt/llm/config/` sync, so the rename requires no manual deployed-config edit | REQ-006 |
| scripts/rag/exceptions.py, `RagConfigValidator` usage in config_resolution.py | Confirms no validation is keyed on `rag_service_url` by name | REQ-006 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-002): `grep -rn "rag_service_url" scripts/` matches only
  `rag_pipeline_service_url` occurrences (ingestion); zero standalone `rag_service_url` occurrences
  remain in `scripts/` or `tests/`.
- `AC-2` (REQ-004): With `{"rag_query_service_url": "http://x"}` in a config dict,
  `resolve_rag_config` returns `rag_query_service_url == "http://x"`; with `{"rag_service_url": "http://x"}`,
  the resolved value stays `None` (old spelling ignored, documented behavior).
- `AC-3` (REQ-006): With the renamed key empty or absent, the pipeline still runs in-process; the
  MCP adapter still pins the value to `""` (existing anti-loop assertions pass with the new name).
- `AC-4` (REQ-003): `config/ingester.toml` and the ingestion reader are byte-identical to before.
- `AC-5` (REQ-005): No doc page still names `rag_service_url` except the ADR's one-time rename note;
  the config reference contrasts both keys.
- `AC-6` (REQ-006): Full test suite passes with only key-name changes in test files (no assertion
  or logic edits).

## Tests
- `REQ-004`: Unit — `tests/rag/test_config_resolution.py` new test: renamed key resolved from dict;
  old spelling yields the `None` default (documents the ignore-extras contract).
- `REQ-002, REQ-006`: Regression — renamed-key fixtures across `tests/rag/`,
  `tests/mcp_servers/rag_pipeline/`, `tests/agent/` pass unchanged in logic: HTTP-mode,
  result-kind, stage-lifecycle/observability, augment integration/refiner, adapter anti-loop pin.
- Static — `mypy` validates the protocol/dataclass rename across packages; `ruff` and `lint-imports`
  unchanged.

## Documentation Impact
- Required per `docs/00_index.md`'s task mapping: RAG query pipeline and configuration reference
  (21_rag), RAG pipeline MCP server (22_mcp), agent RAG diagnostics (23_agent), and the ADR's
  present-tense production-state claims (10_adr) — all renamed to `rag_query_service_url`, and the
  configuration reference gains the query-vs-ingestion key-contrast paragraph (REQ-005).

## Assumptions
- Naming decision adopted (recommended approach, 2026-10-27): rename the **query-path** key to
  `rag_query_service_url`. Rationale: the query key is referenced by no repo or deployed config file
  (verified inventory; ADR-010 records it is never set in production), while the ingestion key is
  live in `config/ingester.toml` and `/opt/llm/config/ingester.toml`; `rag_pipeline_service_url` also
  matches the name of the service it points at (rag_pipeline MCP server), so its spelling is already
  purpose-obvious in its own context.
- No backward-compat mapping: with zero consumers of the old spelling, keeping an alias would
  re-introduce the ambiguity the Plan removes. The new test pins the ignore-unknown behavior so a
  stray old key in any future config fails visibly (stays `None` = no delegation, which is the safe
  default).
- `rag_auth_token` keeps its name (it is the outbound token for the delegation pair and the Issue
  scopes the diff to the two URL keys); the docs paragraph will state the pairing.
- `rag_query_service_url` does not collide with existing identifiers; the only `rag_query*` names in
  the repo are the `rag_query_id` log context key and `rag_query_count` session stat (verified),
  which are unrelated observability fields.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | No blocking unknowns. The Issue's naming question is decided in Assumptions; the out-of-repo consumer question is resolved by the repo + deployed-config inventory recorded in Dependencies. | — | — | False |

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/rag/config_resolution.py, scripts/rag/models_config.py, scripts/shared/types.py | Key rename in declarations/protocol | Whole RAG config surface | 0, 0, 2 | High (single author, 100%) | None: repo config files keep valid keys; no deployed file references the renamed key |
| scripts/rag/pipeline.py, scripts/rag/http_augment.py, scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py, scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py | Reader/docstring renames | Query-path delegation logic | 2, 2, 4, 4 | High (single author, 100%) | None |
| 14 test files | Key-name renames in fixtures + 1 new test | Test suite only | 1 each (spot-checked); remainder not separately profiled (low) | High (single author) | None |
| 8 docs pages | Key-name renames + contrast paragraph (rag_05_01) + ADR rename note | Docs domains 21_rag, 22_mcp, 23_agent, 10_adr | 14, 15, 13, 32, 8, 16, 12, 2 (several high-churn — rebase before editing) | High (single author, 100%) | None |

## Design
- **Rename the query key, not the ingestion key**: config-key renames are only safe where no config
  file lives. The inventory shows `rag_pipeline_service_url` deployed (ingester.toml in repo and at
  `/opt/llm/config/`) and `rag_service_url` nowhere — so the query key is the zero-impact rename and
  the Issue's "coordinate external consumers" dependency is satisfied without touching deployed
  infrastructure.
- **`rag_query_service_url` as the name**: follows the Issue's own example direction ("prefix the
  query-path key with `query`"), mirrors the existing docs vocabulary ("query path" vs "ingestion
  path"), and pairs cleanly with the unchanged `rag_pipeline_service_url` (server-name style for the
  ingestion callback into the rag_pipeline MCP server).
- **No alias/back-compat**: the loader's ignore-extras filter already defines old-key behavior as
  "ignored → default `None` → no delegation", which is fail-safe; an alias would defeat the purpose
  of the rename. The new test converts this implicit behavior into a pinned contract.
- **ADR handling**: ADR-010 records a decision, but its Scope paragraph states present-tense config
  facts ("no configuration file sets `rag_service_url`"). Renaming those references with a one-time
  "(renamed from ...)" note keeps the ADR truthful about today without rewriting the decision record.
- **Mechanical propagation**: rename is a pure string/identifier change verified by grep
  exhaustiveness (`AC-1`) and mypy across the protocol boundary; no logic is touched in any reader.

## Implementation steps
1. **Phase 1: Characterization baseline**
   - [ ] Run `tests/rag/test_config_resolution.py`, `tests/rag/test_rag_http_mode.py`,
     `tests/mcp_servers/rag_pipeline/`, `tests/agent/` RAG tests unchanged (REQ-006).
2. **Phase 2: Declaration and reader rename**
   - [ ] Rename `_ALL_FIELDS`/`_DEFAULTS_FOR_ALL` entries (REQ-001; `scripts/rag/config_resolution.py`).
   - [ ] Rename `RagConfigImpl` field (REQ-001; `scripts/rag/models_config.py`).
   - [ ] Rename `RagConfig` protocol attribute (REQ-001; `scripts/shared/types.py`).
   - [ ] Rename delegation check and docstrings (REQ-002; `scripts/rag/pipeline.py`,
     `scripts/rag/http_augment.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`).
   - [ ] Rename the adapter pin keyword (REQ-002, REQ-006;
     `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`).
3. **Phase 3: Tests**
   - [ ] Rename key spellings across the 14 test files (REQ-004).
   - [ ] Add the new-key-resolves / old-key-ignored test (REQ-004;
     `tests/rag/test_config_resolution.py`).
4. **Phase 4: Docs, deployment check, and verification**
   - [ ] Rename all doc occurrences and add the two-key contrast paragraph (REQ-005;
     `docs/21_rag/rag_05_01-configuration-reference.md` and the other 7 pages, ADR with rename note).
   - [ ] Deployment validation/scripts check: confirm no repo or deployed config file references the
     old spelling (`grep` over `config/` and `/opt/llm/config/`), so `deploy.sh` and configs stay
     unchanged; note the key rename in the commit message for operators (REQ-006).
   - [ ] Run the full `rules/toolchain.md` validation sequence (all REQs).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/ (rename set) | Exhaustiveness | `grep -rn "rag_service_url" scripts/ tests/ \| grep -v "rag_pipeline_service_url"` | No matches |
| scripts/rag/config_resolution.py | Unit | `uv run pytest tests/rag/test_config_resolution.py` | New rename/ignore test passes; existing resolution tests pass with renamed fixtures |
| All rename targets | Regression | `uv run pytest tests/` | Full suite green; test edits are name-only |
| Rename targets | Static + contract | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean; protocol rename type-checks across packages |
| 8 docs pages | Documentation consistency (21_rag, 22_mcp, 23_agent, 10_adr domains) | `rules/toolchain.md` documentation consistency check | No stale key names; contrast paragraph present |
| All targets | Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | Renamed lines covered |

## Risks
- **Risk**: an out-of-repo config (not in repo or `/opt/llm/config/`) sets `rag_service_url` and
  silently stops delegating → **Mitigation**: inventory verified 2026-10-27 across repo and the
  deployed host; ADR-010 records delegation is unused in production, so the only failure mode
  (delegation silently off) is the current production state; fail-safe default `None`.
- **Risk**: mass rename touches two files also edited by the rag001 Plan (`test_rag_pipeline.py`,
  `test_augment_refiner.py`) → **Mitigation**: disjoint regions (fixture key names vs appended tests);
  overlap recorded Compatible; second implementer rebases.
- **Risk**: docs pages are high-churn (rag_01 at 32, mcp_04_03 at 16, rag_03_02 at 15, rag_05_01 at 14) →
  **Mitigation**: occurrences are single-token substitutions; rebase immediately before implementing
  and re-run the doc-occurrence grep (`AC-1`, `AC-5`).
- **Risk**: MagicMock-based fixtures accept any attribute name, so a missed rename could hide until
  a typed path breaks → **Mitigation**: `mypy` catches protocol/dataclass mismatches; `AC-1` grep
  exhaustiveness is part of the validation plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: characterization baseline | Completed | 20261027-214659 | 20261027-214659 | HEAD baseline green; post-rename full suite 10265 passed, 10 skipped, exit 0 |
| 2 | Phase 2: declaration and reader rename | Completed | 20261027-214659 | 20261027-214659 | Executed with Phase 3 as one serial batch (single validation pass); grep gate, mypy, bandit, lint-imports, targeted pytest all green |
| 3 | Phase 3: tests | Completed | 20261027-214659 | 20261027-214659 | 14 test files renamed + new AC-2 regression test in test_config_resolution.py; full suite exit 0; diff-cover 100% |
| 4 | Phase 4: docs, deployment check, verification | Completed | 20261027-214659 | 20261027-214659 | 7 docs pages + ADR renamed; docs checkers green; check_adr_preservation WARNING recorded (see procedure 29); config/ and deployed /opt/llm/config/ contain no old key |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261027-154425_01_scripts_rag_config_resolution.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261027-154425_02_scripts_rag_models_config.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261027-154425_03_scripts_shared_types.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261027-154425_04_scripts_rag_pipeline.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261027-154425_05_scripts_rag_http_augment.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261027-154425_06_scripts_mcp_servers_rag_pipeline_rag_pipeline_models.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261027-154425_07_scripts_mcp_servers_rag_pipeline_rag_pipeline_server.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261027-154425_08_tests_rag_test_config_resolution.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261027-154425_09_tests_rag_test_rag_pipeline.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261027-154425_10_tests_rag_test_rag_http_mode.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261027-154425_11_tests_rag_test_pipeline_http_result_kind.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261027-154425_12_tests_rag_test_rag_quality_regression.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261027-154425_13_tests_rag_test_stage_observability.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261027-154425_14_tests_rag_test_stage_lifecycle.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261027-154425_15_tests_rag_test_rag_pipeline_no_cache_freshness.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261027-154425_16_tests_rag_test_augment_integration.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261027-154425_17_tests_rag_test_augment_refiner.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261027-154425_18_tests_rag_test_rag_pipeline_stage.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261027-154425_19_tests_mcp_servers_rag_pipeline_test_rag_pipeline_mcp_service.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261027-154425_20_tests_agent_commands_test_agent_rag.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261027-154425_21_tests_agent_test_rag_get_cfg.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261027-154425_22_docs_21_rag_rag_05_01-configuration-reference.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261027-154425_23_docs_21_rag_rag_03_02_query_pipeline-rag-pipeline-class.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261027-154425_24_docs_21_rag_rag_03_01_query_pipeline-overview.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261027-154425_25_docs_21_rag_rag_01_system_overview.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261027-154425_26_docs_21_rag_rag_05_04-error-handling-reference.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261027-154425_27_docs_22_mcp_mcp_04_03_rag-pipeline-and-cicd.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261027-154425_28_docs_23_agent_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261027-154425_29_docs_10_adr_adr_02_06_010_rag-fallback.md.md | 4 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-071953_rag003_rag-url-key-ambiguity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-110727
- **Related target files**: scripts/rag/config_resolution.py, scripts/rag/models_config.py, scripts/shared/types.py, scripts/rag/pipeline.py, scripts/rag/http_augment.py, scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py, scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py, tests/rag/test_config_resolution.py, tests/rag/test_rag_pipeline.py, tests/rag/test_rag_http_mode.py, tests/rag/test_pipeline_http_result_kind.py, tests/rag/test_rag_quality_regression.py, tests/rag/test_stage_observability.py, tests/rag/test_stage_lifecycle.py, tests/rag/test_rag_pipeline_no_cache_freshness.py, tests/rag/test_augment_integration.py, tests/rag/test_augment_refiner.py, tests/rag/test_rag_pipeline_stage.py, tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py, tests/agent/commands/test_agent_rag.py, tests/agent/test_rag_get_cfg.py, docs/21_rag/rag_05_01-configuration-reference.md, docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md, docs/21_rag/rag_03_01_query_pipeline-overview.md, docs/21_rag/rag_01_system_overview.md, docs/21_rag/rag_05_04-error-handling-reference.md, docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md, docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md, docs/10_adr/adr_02_06_010_rag-fallback.md

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (rename declarations); verified declaration sites | scripts/rag/config_resolution.py | Phase 2 | AC-1 | Grep exhaustiveness | Confirmed by repository evidence |
| REQ-001 | `RagConfigImpl` field verified | scripts/rag/models_config.py | Phase 2 | AC-1 | `mypy` | Confirmed by repository evidence |
| REQ-001 | `RagConfig` protocol attribute verified | scripts/shared/types.py | Phase 2 | AC-1 | `mypy` | Confirmed by repository evidence |
| REQ-002 | Required Changes (propagate to readers); verified reader sites | scripts/rag/pipeline.py | Phase 2 | AC-1, AC-3 | HTTP-mode regression tests | Confirmed by repository evidence |
| REQ-002 | Docstring references verified | scripts/rag/http_augment.py | Phase 2 | AC-1 | Augment integration suite | Confirmed by repository evidence |
| REQ-002 | Adapter pin verified at L171 | scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py | Phase 2 | AC-3 | Adapter anti-loop test | Confirmed by repository evidence |
| REQ-002 | Server docstring verified | scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py | Phase 2 | AC-1 | N/A (docstring review) | Confirmed by repository evidence |
| REQ-003 | Constraints ("do not drop either field"); deployed inventory verified | config/ingester.toml (Reference) | Phase 4 | AC-4 | Config grep check | Confirmed by repository evidence |
| REQ-004 | Testing Expectations | tests/rag/test_config_resolution.py | Phase 3 | AC-2 | New rename/ignore test | Confirmed by repository evidence |
| REQ-004 | Fixture rename across test files (14 files verified by grep) | tests/rag/test_rag_pipeline.py | Phase 3 | AC-6 | Full-suite regression | Confirmed by repository evidence |
| REQ-004 | Same for remaining 13 test files | tests/rag/test_rag_http_mode.py | Phase 3 | AC-6 | Full-suite regression | Confirmed by repository evidence |
| REQ-005 | Documentation Impact; verified occurrences | docs/21_rag/rag_05_01-configuration-reference.md | Phase 4 | AC-5 | 21_rag documentation consistency check | Confirmed by repository evidence |
| REQ-005 | Verified occurrences in remaining 7 docs pages | docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md | Phase 4 | AC-5 | Docs consistency checks (21_rag, 22_mcp, 23_agent, 10_adr) | Confirmed by repository evidence |
| REQ-006 | Constraints (behavior preserved); ADR production-state fact | scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py | Phase 2 | AC-3 | Adapter anti-loop test + in-process mode tests | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261027-154425 -->
