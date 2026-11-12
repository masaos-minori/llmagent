## Goal
- Finish the removal of the remote RAG delegation path: delete the unused `rag_pipeline_service_url` key, the unused ingester state and dead members, and the stale "gate refuses fallback" startup warning text, so only gates that exist are described. RAG search, ingestion, and consistency-check behavior stay unchanged.

## Priority
Medium

## Scope
- **In-Scope**: remove `rag_pipeline_service_url` from `config/ingester.toml`, `RagConfig`, `RagConfigImpl`, the resolution tables, and `RagIngester`; reject it as a removed key in `RagConfigValidator`; delete `RagIngester.__del__` and `RagIngester._log_ingest_failure` and the compatibility docstring sentence; close the ingester client explicitly in `main()`; make `AugmentRefiner.last_stage_results` read the attribute directly; reword the two `startup_validation.py` warnings; record the removed key in `rag_05_01`.
- **Out-of-Scope**: the corpus identity table and reader (`corpus_identity.py`, `identity_gate.py`, the identity view of the rag-pipeline MCP server), decided in `issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md`; the diagnostics model and its output shape; writing the maintainer's approval statement for the ADR-010 withdrawal and the ADR-004 Decision Group 10 amendment; the severity policy of the RAG consistency check; adding a validator to the ingester's own `ingester.toml` load path; any migration, alias, shim, or tolerant fallback (`compatrm001`).
- **Dependencies**: None open. The history-comment sweep (rmcompat007) and the adrrev013 consistency-policy Plan (closed) both follow this Plan. No open Plan or procedure edits `scripts/agent/startup_validation.py` (the adrrev004 bypass removal landed as `cad5e91ea`).

## Background
`plans/done/20261110-092546_adrrev003_rag-http-delegation.md` (commit `b217f999b`) removed the HTTP augment path, the remote call module, and `ResultSource.REMOTE`/`FALLBACK`. Leftovers remain (re-verified 2026-11-12, Step 2): the `rag_pipeline_service_url` key in five production files, a never-read `_rag_pipeline_service_url` attribute on the ingester, a `__del__` that duplicates `close()`, an uncalled `_log_ingest_failure` on `RagIngester` (the same-named method in `chunk_preparation.py` is called), a `getattr` default in `AugmentRefiner.last_stage_results`, and two startup warnings that say "the gate refuses fallback while unverified (REQ-007)".

Corrections found against the Issue's claims (Step 2 and Step 3):
- `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` contains no identity-gate wording (search for "gate" returned no match; line 26 describes the identity-unverified warning, which stays accurate). It is a reference file here, not a target.
- `docs/21_rag/rag_05_01-configuration-reference.md` never lists `rag_pipeline_service_url`; the only doc change is adding it to the removed-key sentence at line 92.
- `RagConfigValidator` runs only inside `resolve_rag_config` and `config_section_builders`, on dictionaries from `ConfigLoader.load_all()` (which loads `agent.toml` only) or a module configuration. `RagIngester.__init__` loads `ingester.toml` directly and never validates it. The new rejection therefore does not stop the ingester when the deployed `ingester.toml` still carries the key; the Issue's deployment-order concern does not apply.
- No test builds `AugmentRefiner` without `__init__` (`RagPipeline.__new__` is used elsewhere, not this class), so replacing the `getattr` needs no test fix.
- `__init__` always sets `_last_stage_results`, so direct access is safe.

## Problem
A configuration key, an ingester attribute, and two warning messages describe a remote service and an identity gate that cannot run, so operators are told fallback is gated when no gate exists. `__del__` closes the client at an undefined time and hides a missing `close()`; an uncalled method and a docstring sentence about a past signature change are dead weight; the `getattr` default tolerates objects that no production code creates.

## Reason for Change
The project accepts only the current configuration and schema (`compatrm001`). A key that is accepted but unused invites a reader to wire a remote call back in; the warning text is the only item that can mislead an operator today. No external deadline.

## Implementation Intent
- The ingester has one explicit lifecycle: `main()` calls `close()` in a `try/finally`; no `__del__`, no unused attribute or method.
- The RAG configuration contains only keys that production code reads, and `rag_pipeline_service_url` is rejected like the three already-removed keys.
- The warnings keep severity, the `RAG identity-unverified:` prefix, and the continue-startup behavior; only the gate clause and the `REQ-007` reference are dropped.

## Requirements
- `REQ-001`: `RagConfigValidator` rejects `rag_pipeline_service_url` as a removed key with the existing message style, covered by a test; a valid configuration test no longer uses that key.
- `REQ-002`: `rag_pipeline_service_url` no longer appears in `config/ingester.toml`, `RagConfig`, `RagConfigImpl`, the key list or default table of `config_resolution.py`, or any test configuration.
- `REQ-003`: `RagIngester` has no `_rag_pipeline_service_url`, no `__del__`, no `_log_ingest_failure`, no compatibility sentence in the `ingest_all` docstring; `main()` closes the client in a `finally` block.
- `REQ-004`: `AugmentRefiner.last_stage_results` returns `self._last_stage_results` directly.
- `REQ-005`: the two `startup_validation.py` warnings and the nearby comment no longer mention a gate refusing fallback or `REQ-007`; severity and fail-open-with-warning behavior are unchanged.
- `REQ-006`: `rag_05_01` names `rag_pipeline_service_url` among the rejected removed keys without adding config values or file lists.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `config/ingester.toml` | Ingester configuration | Delete the `rag_pipeline_service_url` line and its comment | REQ-002 / AC-2 | line 28 sets the key; comment at line 27 (checked in Step 2) | `tests/rag/ingestion/test_rag_ingester.py` | Verified |
| `scripts/shared/types.py` | `RagConfig` type | Remove the `rag_pipeline_service_url` field | REQ-002 / AC-2 | line 109 `rag_pipeline_service_url: str \| None` (checked in Step 3) | `tests/rag/test_config_resolution.py` | Verified |
| `scripts/shared/config_validator.py` | Removed-key rejection | Add `rag_pipeline_service_url` to `_check_removed_rag_delegation_keys` | REQ-001 / AC-1 | removed-key set at lines 92-98 holds three keys (checked in Step 2) | `tests/shared/test_config_validator.py` | Verified |
| `scripts/rag/models_config.py` | `RagConfigImpl` dataclass | Remove the `rag_pipeline_service_url` field | REQ-002 / AC-2 | line 38 field (checked in Step 3) | `tests/rag/test_config_resolution.py` | Verified |
| `scripts/rag/config_resolution.py` | Key list and default table | Remove the key from `_ALL_FIELDS` and `_DEFAULTS_FOR_ALL` | REQ-002 / AC-2 | lines 46 and 76 (checked in Step 3) | `tests/rag/test_config_resolution.py` | Verified |
| `scripts/rag/augment.py` | `AugmentRefiner` | Replace `getattr(self, "_last_stage_results", [])` with direct access | REQ-004 / AC-4 | line 54; `__init__` sets the attribute at line 49 (checked in Step 2) | `tests/rag/test_augment_refiner.py` | Verified |
| `scripts/rag/ingestion/ingester.py` | `RagIngester` lifecycle | Remove attribute, `__del__`, `_log_ingest_failure`, docstring sentence; close in `main()` | REQ-003 / AC-3 | lines 123, 138, 156, 392, 511-512 (checked in Step 2) | `tests/rag/ingestion/test_rag_ingester.py` | Verified |
| `scripts/agent/startup_validation.py` | Startup RAG consistency warnings | Reword two warnings and the comment at line 253 | REQ-005 / AC-5 | lines 246-261 (checked in Step 2) | `tests/agent/test_startup_validation.py` | Verified |
| `docs/21_rag/rag_05_01-configuration-reference.md` | RAG configuration reference | Add the key to the rejected removed-key sentence | REQ-006 / AC-6 | line 92 lists three keys (checked in Step 2) | N/A: documentation | Verified |
| `tests/shared/test_config_validator.py` | Validator tests | Reject the key; stop asserting it is accepted | REQ-001 / AC-1 | line 221 asserts the key is accepted (checked in Step 2) | itself | Verified |
| `tests/rag/ingestion/test_rag_ingester.py` | Ingester test config | Drop the key from the test configuration | REQ-002 / AC-2 | line 78 (checked in Step 3) | itself | Verified |
| `tests/rag/test_rag_quality_regression.py` | Config construction | Remove the keyword argument | REQ-002 / AC-2 | line 52 (checked in Step 3) | itself | Verified |
| `tests/rag/test_augment_integration.py` | Config construction | Remove the keyword argument | REQ-002 / AC-2 | line 32 (checked in Step 3) | itself | Verified |
| `tests/rag/test_rag_pipeline_stage.py` | Test config double | Remove the field at line 44 and the argument at line 74 | REQ-002 / AC-2 | lines 44 and 74 (checked in Step 3) | itself | Verified |
| `tests/rag/test_stage_observability.py` | Config construction | Remove the keyword argument | REQ-002 / AC-2 | line 36 (checked in Step 3) | itself | Verified |
| `tests/rag/test_config_resolution.py` | Resolution tests | Remove the key from the fixtures at lines 44, 90, 216 | REQ-002 / AC-2 | lines 44, 90, 216 (checked in Step 3) | itself | Verified |
| `tests/rag/test_rag_pipeline_no_cache_freshness.py` | Config construction | Remove the keyword argument | REQ-002 / AC-2 | line 68 (checked in Step 3) | itself | Verified |
| `tests/rag/test_rag_pipeline.py` | Config construction | Remove the keyword argument at lines 310 and 384 | REQ-002 / AC-2 | lines 310, 384 (checked in Step 3) | itself | Verified |
| `tests/rag/test_llm_client_timeout.py` | Config construction | Remove the keyword argument | REQ-002 / AC-2 | line 40 (checked in Step 3) | itself | Verified |
| `tests/rag/test_stage_lifecycle.py` | Config construction | Remove the keyword argument | REQ-002 / AC-2 | line 53 (checked in Step 3) | itself | Verified |
| `tests/rag/test_augment_refiner.py` | Config construction | Remove the keyword argument | REQ-002 / AC-2 | line 37 (checked in Step 3) | itself | Verified |
| `tests/agent/test_rag_get_cfg.py` | Config construction | Remove the keyword argument | REQ-002 / AC-2 | line 36 (checked in Step 3) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Line 26 describes the identity-unverified warning; verified to contain no gate wording, so it is not edited | REQ-005 |
| `scripts/rag/ingestion/chunk_preparation.py` | Holds the separate, called `_log_ingest_failure` (line 82, caller at line 72); must stay untouched | REQ-003 |
| `scripts/shared/config_loader.py` | `load_all` loads `agent.toml` only, so `ingester.toml` never reaches `RagConfigValidator` | REQ-001 |
| `scripts/agent/config_section_builders.py` | Second call site of `RagConfigValidator` (line 166) | REQ-001 |
| `tests/agent/test_startup_validation.py` | Asserts only `identity-unverified`, `timed out`, and the failure category; none asserts the gate text | REQ-005 |
| `plans/done/20261111-102935_adrrev013_rag-consistency-policy.md` | Names this issue as its ordering dependency | REQ-005 |

## Acceptance Criteria
- AC-1 (REQ-001): `RagConfigValidator().validate({"rag_pipeline_service_url": "http://x"})` returns one error naming the key; a configuration without removed keys stays valid.
- AC-2 (REQ-002): `rg -n "rag_pipeline_service_url" scripts config docs tests` returns only the removed-key rejection, its tests, and the `rag_05_01` sentence.
- AC-3 (REQ-003): `RagIngester` defines no `__del__` and no `_log_ingest_failure`; `main()` closes its client in a `finally` block.
- AC-4 (REQ-004): `scripts/rag/augment.py` has no `getattr(self, ...)` in `last_stage_results`.
- AC-5 (REQ-005): `rg -n "gate refuses fallback" scripts docs` returns nothing; the existing startup-validation tests pass unchanged.
- AC-6 (REQ-006): `rag_05_01` lists the key among rejected keys and the docs checkers pass.
- AC-7: the RAG, ingestion, shared, and agent test suites pass.

## Tests
- REQ-001: extend `tests/shared/test_config_validator.py` so the removed-key tests include `rag_pipeline_service_url`, and replace the "key accepted" assertion with a configuration that has no removed keys.
- REQ-002: run `tests/rag/`, `tests/rag/ingestion/`, and `tests/agent/test_rag_get_cfg.py` after the keyword removals.
- REQ-003: no new lifecycle test; the acceptance searches cover it (no existing lifecycle test pattern), as the Issue allows.
- REQ-004 and REQ-005: existing `tests/rag/test_augment_refiner.py` and `tests/agent/test_startup_validation.py` / `test_startup.py` / `test_startup_severity_classification.py` must pass unchanged.

## Documentation Impact
- Documentation must be updated for REQ-006: the RAG configuration reference (`docs/21_rag/rag_05_01-configuration-reference.md`, via `docs/00_index.md` "Document References by Task") gains the key in its rejected-key sentence. `rag_05_07` needs no edit. Run the `routing.md` checkers for `docs/` edits.

## Assumptions
- Keeping the `RAG identity-unverified:` prefix is correct: `corpus_identity.py` still returns `verified=False`, and three test modules assert the prefix. Whether the prefix survives is decided by `rmcompat003`.
- `main()` uses `try/finally` rather than a context manager; both satisfy the Issue and `try/finally` adds no new protocol to `RagIngester` (resolves the Issue's open question).
- The deployed `/opt/llm/config/ingester.toml` is not inspected; it does not block this change because the ingester never validates the file.
- Sequencing with `plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md` (Option B, remove the corpus identity): it depends on this Plan; it later removes the `identity-unverified` prefix from the same two warnings and the `bump_index_generation()` call from `ingester.py`, so this Plan must land first.
- Compatible with `plans/done/20261111-102935_adrrev013_rag-consistency-policy.md`: that Plan leaves `startup_validation.py` unchanged and documents behavior only.
- The in-flight procedure `implementations/20261112-063813_01_docs_21_rag_rag_05_07-rag-index-consistency-checks.md.md` assumes this Plan rewrites a `rag_05_07` paragraph; this Plan does not edit `rag_05_07`, so that procedure's gating note is stale (owned by that procedure).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the maintainer has stated approval for the ADR-010 withdrawal and the ADR-004 Decision Group 10 amendment (both read `Pending maintainer statement`) | Maintainer statement | Maintainer records it per `governance_05`; out of scope here | False |
| UNK-02 | Whether the deployed `/opt/llm/config/ingester.toml` still sets the key | Read access to production configuration | After deploy, check the file; the key is harmless if present | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `config/ingester.toml` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/shared/types.py` | Modify | Medium | 5 | N/A | not applicable (rsynced) |
| `scripts/shared/config_validator.py` | Modify | Medium | 2 | N/A | not applicable (rsynced) |
| `scripts/rag/models_config.py` | Modify | Medium | 3 | N/A | not applicable (rsynced) |
| `scripts/rag/config_resolution.py` | Modify | Medium | 4 | N/A | not applicable (rsynced) |
| `scripts/rag/augment.py` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/ingester.py` | Modify | Medium | 7 | N/A | not applicable (rsynced) |
| `scripts/agent/startup_validation.py` | Modify | Medium | 8 | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_05_01-configuration-reference.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_config_validator.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/ingestion/test_rag_ingester.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_quality_regression.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_augment_integration.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_pipeline_stage.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_stage_observability.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_config_resolution.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_pipeline_no_cache_freshness.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_pipeline.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_llm_client_timeout.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_stage_lifecycle.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_augment_refiner.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_rag_get_cfg.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Consumer scan (`tools/scan_change_consumers.py --seed rag_pipeline_service_url`): scripts candidates are `config_resolution.py` (2 lines), `ingester.py`, `models_config.py`, `types.py`, all target rows; 17 test candidates are all target rows above; five `adr-test-citation` candidates (ADR-009 and `adr_01_index.md` citing `test_rag_pipeline.py` and `test_rag_pipeline_stage.py` nodes) are `not affected: they cite test node names, not the key`; the `implementations/done/` inventory hit is `not affected: archived text`. The scan is text-only; the `docs/` search found no other mention.
- Architecture: `lint-imports` baseline 6 contracts kept, 0 broken; the change deletes members and one dictionary key, adds no import, and `rag` still imports nothing from `agent`.
- Rejection placement: the key goes into the existing frozenset in `_check_removed_rag_delegation_keys`; the message already says the delegation path was removed. No new check, no alias. The ingester's own load stays unvalidated by decision (Out-of-Scope).
- `main()` shape: `ingester = RagIngester()` then `try: ingester.ingest_all(args.force)` / `finally: ingester.close()`.
- Imports in `ingester.py` stay used after deleting `_log_ingest_failure` (`read_chunk_json` and `ChunkFormatError` remain used at lines 231-253 and 388-390).
- Complexity baseline (`radon cc`): `ingest_url_group` C (20) and `ingest_all` C (14) are untouched. `vulture --min-confidence 80`: findings are pre-existing and none is in the touched code. `bandit -r scripts/` baseline: 0 Undefined, 0 Low, 6 Medium, 39 High by confidence; the change only deletes code, so no new finding is expected.
- Operational check: no MCP server, port, or database schema changes; `ss` and `fuser` not run (N/A). No persisted-schema change (`rules/persisted-schema-change.md` N/A). No dependency upgrade (`pip-audit` N/A).
- Historical: churn above is from `git log --since=30.days`; bus factor not measured (`git-fame` not run).

## Implementation steps
Test-file rows share one mechanical edit (delete one keyword or dict entry), so they are grouped in Phase 3.

1. **Phase 1: Reject the removed key**
   - [ ] Add `rag_pipeline_service_url` to the removed-key set (REQ-001; `scripts/shared/config_validator.py`)
   - [ ] Add it to the removed-key tests and change the "stays valid" test to use a configuration with no removed keys (REQ-001; `tests/shared/test_config_validator.py`)
   - [ ] Add the key to the rejected-key sentence (REQ-006; `docs/21_rag/rag_05_01-configuration-reference.md`)
2. **Phase 2: Remove the key from the RAG configuration model**
   - [ ] Remove the field (REQ-002; `scripts/shared/types.py`, `scripts/rag/models_config.py`)
   - [ ] Remove it from `_ALL_FIELDS` and `_DEFAULTS_FOR_ALL` (REQ-002; `scripts/rag/config_resolution.py`)
3. **Phase 3: Update tests that construct the configuration**
   - [ ] Remove the keyword or dict entry (REQ-002; `tests/rag/test_rag_quality_regression.py`, `tests/rag/test_augment_integration.py`, `tests/rag/test_rag_pipeline_stage.py`, `tests/rag/test_stage_observability.py`, `tests/rag/test_config_resolution.py`, `tests/rag/test_rag_pipeline_no_cache_freshness.py`, `tests/rag/test_rag_pipeline.py`, `tests/rag/test_llm_client_timeout.py`, `tests/rag/test_stage_lifecycle.py`, `tests/rag/test_augment_refiner.py`, `tests/agent/test_rag_get_cfg.py`)
4. **Phase 4: Ingester cleanup**
   - [ ] Remove the attribute, `__del__`, `_log_ingest_failure`, the docstring sentence; add `try/finally` close in `main()` (REQ-003; `scripts/rag/ingestion/ingester.py`)
   - [ ] Delete the key and its comment (REQ-002; `config/ingester.toml`)
   - [ ] Drop the key from the test configuration (REQ-002; `tests/rag/ingestion/test_rag_ingester.py`)
5. **Phase 5: Direct attribute access**
   - [ ] Replace the `getattr` (REQ-004; `scripts/rag/augment.py`)
6. **Phase 6: Startup warning text**
   - [ ] Reword the two warnings and the comment at line 253 without the gate clause or `REQ-007` (REQ-005; `scripts/agent/startup_validation.py`)
7. **Phase 7: Deployment and verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` after the change is committed and pushed; deploying is the user's decision (approval gate). Run the acceptance searches, the validation sequence, and the docs checkers (REQ-001 to REQ-006)

### Release units
**Unit**: rag-config-field-removal | **Phases**: 2, 3 | **Reason**: removing the field from `RagConfig`/`RagConfigImpl` breaks every test that passes it as a keyword until Phase 3 lands.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/config_validator.py` | Unit | `uv run pytest tests/shared/test_config_validator.py` | Key rejected; clean configuration valid |
| RAG configuration model and tests | Unit | `uv run pytest tests/rag tests/agent/test_rag_get_cfg.py` | All pass with the key gone |
| `scripts/rag/ingestion/ingester.py` | Unit | `uv run pytest tests/rag/ingestion` | All pass; no `__del__` |
| `scripts/agent/startup_validation.py` | Unit | `uv run pytest tests/agent/test_startup_validation.py tests/agent/test_startup.py tests/agent/test_startup_severity_classification.py` | All pass unchanged |
| Changed Python files | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages`, `uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml` | No new finding |
| Whole change | Search | `rg -n "rag_pipeline_service_url" scripts config docs tests` and `rg -n "gate refuses fallback" scripts docs` | Only the allowed matches in AC-2; none for the second |
| `docs/21_rag/rag_05_01-configuration-reference.md` | Docs | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag` | No findings |
| Coverage | Coverage | diff-cover sequence in `rules/toolchain.md` section 7 | At or above the `rules/toolchain.md` threshold |

## Risks
- **Risk**: Another Plan edits `scripts/agent/startup_validation.py` or `ingester.py` concurrently → **Mitigation**: no open Plan targets them (`tools/check_plan_target_overlaps.py` run at freeze); re-run the Issue's searches before editing and stop if a leftover is already gone.
- **Risk**: The rejection is read as covering `ingester.toml` → **Mitigation**: the Design and Assumptions state it covers only the `RagConfigValidator` path; acceptance tests target the validator.
- **Risk**: The stale gating note in the `rag_05_07` procedure leads someone to expect a `rag_05_07` edit here → **Mitigation**: recorded in Assumptions; the procedure owner clears it.
- **Risk**: Removing `__del__` leaves an unclosed `httpx.Client` for callers that never call `close()` → **Mitigation**: the only production caller is `main()` (now closing); tests construct the ingester directly and already call `close()` or mock `_client`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reject the removed key (validator, its tests, `rag_05_01`) | Completed | — | 20261112-215935 |  |
| 2 | Remove the key from the RAG configuration model | Completed | — | 20261112-215935 | Release unit rag-config-field-removal with step 3 |
| 3 | Update tests that construct the configuration | Completed | — | 20261112-215935 | Release unit rag-config-field-removal with step 2 |
| 4 | Ingester cleanup (`ingester.py`, `ingester.toml`, its test) | Completed | — | 20261112-215935 |  |
| 5 | Direct attribute access in `augment.py` | Completed | — | 20261112-215935 |  |
| 6 | Reword startup warnings in `startup_validation.py` | Completed | — | 20261112-215935 |  |
| 7 | Deployment hand-off and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261112-115458
- **Related target files**: `config/ingester.toml`, `scripts/shared/types.py`, `scripts/shared/config_validator.py`, `scripts/rag/models_config.py`, `scripts/rag/config_resolution.py`, `scripts/rag/augment.py`, `scripts/rag/ingestion/ingester.py`, `scripts/agent/startup_validation.py`, `docs/21_rag/rag_05_01-configuration-reference.md`, `tests/shared/test_config_validator.py`, `tests/rag/ingestion/test_rag_ingester.py`, `tests/rag/test_rag_quality_regression.py`, `tests/rag/test_augment_integration.py`, `tests/rag/test_rag_pipeline_stage.py`, `tests/rag/test_stage_observability.py`, `tests/rag/test_config_resolution.py`, `tests/rag/test_rag_pipeline_no_cache_freshness.py`, `tests/rag/test_rag_pipeline.py`, `tests/rag/test_llm_client_timeout.py`, `tests/rag/test_stage_lifecycle.py`, `tests/rag/test_augment_refiner.py`, `tests/agent/test_rag_get_cfg.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `config_validator.py:92-98` | `scripts/shared/config_validator.py` | 1 | AC-1 | `tests/shared/test_config_validator.py` | Confirmed by repository evidence |
| REQ-001 | Acceptance Criteria 2; `test_config_validator.py:221` | `tests/shared/test_config_validator.py` | 1 | AC-1 | validator tests | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; `ingester.toml:28` | `config/ingester.toml` | 4 | AC-2 | acceptance search | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; `types.py:109` | `scripts/shared/types.py` | 2 | AC-2 | `tests/rag/test_config_resolution.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; `models_config.py:38` | `scripts/rag/models_config.py` | 2 | AC-2 | `tests/rag/test_config_resolution.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; `config_resolution.py:46,76` | `scripts/rag/config_resolution.py` | 2 | AC-2 | `tests/rag/test_config_resolution.py` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; scan seed `rag_pipeline_service_url` | `tests/rag/ingestion/test_rag_ingester.py` | 4 | AC-2 | `tests/rag/ingestion` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; scan seed | `tests/rag/test_rag_quality_regression.py` | 3 | AC-2 | `tests/rag` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; scan seed | `tests/rag/test_augment_integration.py` | 3 | AC-2 | `tests/rag` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; scan seed | `tests/rag/test_rag_pipeline_stage.py` | 3 | AC-2 | `tests/rag` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; scan seed | `tests/rag/test_stage_observability.py` | 3 | AC-2 | `tests/rag` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; scan seed | `tests/rag/test_config_resolution.py` | 3 | AC-2 | `tests/rag` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; scan seed | `tests/rag/test_rag_pipeline_no_cache_freshness.py` | 3 | AC-2 | `tests/rag` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; scan seed | `tests/rag/test_rag_pipeline.py` | 3 | AC-2 | `tests/rag` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; scan seed | `tests/rag/test_llm_client_timeout.py` | 3 | AC-2 | `tests/rag` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; scan seed | `tests/rag/test_stage_lifecycle.py` | 3 | AC-2 | `tests/rag` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; scan seed | `tests/rag/test_augment_refiner.py` | 3 | AC-2 | `tests/rag` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; scan seed | `tests/agent/test_rag_get_cfg.py` | 3 | AC-2 | `tests/agent/test_rag_get_cfg.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 2; `ingester.py:123,138,156,392,511` | `scripts/rag/ingestion/ingester.py` | 4 | AC-3 | `tests/rag/ingestion`; acceptance search | Confirmed by repository evidence |
| REQ-004 | Required Changes 3; `augment.py:54` | `scripts/rag/augment.py` | 5 | AC-4 | `tests/rag/test_augment_refiner.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes 4; `startup_validation.py:246-261` | `scripts/agent/startup_validation.py` | 6 | AC-5 | `tests/agent/test_startup_validation.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes 5; `rag_05_01:92` | `docs/21_rag/rag_05_01-configuration-reference.md` | 1 | AC-6 | docs checkers | Derived from confirmed evidence |
