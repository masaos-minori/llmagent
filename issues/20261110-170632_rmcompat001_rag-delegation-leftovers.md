# Remove the RAG delegation leftovers that remain after the HTTP path removal

## Priority
Medium

## Summary
Finish the removal of the remote RAG delegation path: delete the configuration key, the unused ingester state, the implicit `__del__` cleanup, and the stale startup warning text that still describe a path and an identity gate that no longer exist.

## Background
- Source: `memo-issue.md` item H-01 (consolidated version), re-checked against current source on 2026-11-10. Most of H-01 is already implemented by `plans/done/20261110-092546_adrrev003_rag-http-delegation.md` (commit `b217f999b`): the HTTP augment module, the remote call module, the HTTP branch of `RagPipeline.augment()`, the HTTP-only members of `AugmentRefiner`, and `ResultSource.REMOTE`/`FALLBACK` no longer exist, and ADR-010 carries `Withdrawn` status.
- `Explicit in code`, leftovers found by search on 2026-11-10:
  - `rag_pipeline_service_url` is still declared in `config/ingester.toml`, the `RagConfig` type in `scripts/shared/types.py`, `scripts/rag/models_config.py`, and `scripts/rag/config_resolution.py` (key list and default table); the ingester stores it in `_rag_pipeline_service_url` and nothing reads that attribute.
  - `RagIngester` in `scripts/rag/ingestion/ingester.py` has a `__del__` that closes the HTTP client in addition to `close()`; its `_log_ingest_failure` method has no caller (a separate method of the same name in `chunk_preparation.py` is called); the `ingest_all` docstring says "Callers that do not inspect the return value are unaffected".
  - `AugmentRefiner.last_stage_results` in `scripts/rag/augment.py` reads `getattr(self, "_last_stage_results", [])`.
  - `scripts/agent/startup_validation.py` still emits two warnings saying "the gate refuses fallback while unverified (REQ-007)".
  - The rejection of removed keys (`_check_removed_rag_delegation_keys` in `scripts/shared/config_validator.py`) covers three removed keys but not `rag_pipeline_service_url`; `tests/shared/test_config_validator.py` asserts that this key is currently accepted.
- `Documentation only`: ADR-010 (`docs/10_adr/adr_02_06_010_rag-fallback.md`) says `Withdrawn By: Pending maintainer statement`, and ADR-004's current-decision approval line says the Decision Group 10 amendment is `Pending maintainer statement`.
- Refuted memo claims: the memo's NC-42, NC-43, and NC-44 entries do not appear in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (search found no match), so no ledger entry has to be closed here.

## Problem
- A configuration key, an ingester attribute, and two warning messages describe a remote service and an identity gate that cannot run, so operators and readers are told that fallback is gated when no gate exists.
- Cleanup in `__del__` runs at an undefined time and hides a missing `close()` call; a method with no caller and a docstring sentence describing a past signature change are dead weight.
- The `getattr` default exists only to tolerate test objects created without `__init__`, which is a test workaround in production code.

## Reason for Change
- The project accepts only the current configuration and schema (`compatrm001`); a key that is accepted but unused invites a future reader to wire a remote call back in. No external deadline; the warning text is the only item that can mislead an operator today.

## Implementation Intent
- The ingester has one explicit lifecycle (`close()` called by the entry point or a context manager) and no unused attribute or method.
- The RAG configuration contains only keys that production code reads, and a removed key is rejected at load like the three already removed.
- Startup warnings describe only gates that exist.
- Keep behavior of RAG search, ingestion, and consistency checks unchanged.

## Target Files or Areas
- `config/ingester.toml`
- `scripts/shared/types.py`, `scripts/shared/config_validator.py`
- `scripts/rag/models_config.py`, `scripts/rag/config_resolution.py`, `scripts/rag/augment.py`
- `scripts/rag/ingestion/ingester.py`
- `scripts/agent/startup_validation.py`
- `docs/21_rag/rag_05_01-configuration-reference.md`, `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`
- Tests that construct the config dataclasses with `rag_pipeline_service_url` (under `tests/rag/`, `tests/shared/`, `tests/agent/`) and `tests/rag/ingestion/test_rag_ingester.py`

## Required Changes
- Remove `rag_pipeline_service_url` from the config file, the config dataclasses, the resolution tables, and the ingester; add it to the removed-key rejection so an old config fails load with the existing message style.
- Delete `_log_ingest_failure` from `RagIngester` and remove `__del__`; make the entry point close the client explicitly (or use a context manager), and remove the compatibility sentence from the `ingest_all` docstring.
- Replace the `getattr` in `last_stage_results` with direct attribute access and fix tests that build the object without `__init__`.
- Reword the two `startup_validation.py` warnings so they no longer mention a gate; keep the severity and the fail-closed behavior of the surrounding code unchanged.
- Update the RAG configuration reference and `rag_05_07` so they no longer describe the removed key or an identity gate.

## Constraints
- Do not add migrations, aliases, shims, or tolerant fallbacks (`compatrm001` policy).
- `scripts/agent/startup_validation.py` is also edited by the in-flight procedures of `plans/done/20261110-094140_adrrev004_non-strict-bypass-removal.md` (for example `implementations/20261110-154603_02_scripts_agent_startup_validation.py.md`); sequence the edits so neither overwrites the other.
- A change to an ADR decision needs an approval record in the same change (`governance_05`); the implementer must not write the maintainer's statement.

## Acceptance Criteria
- `rg -n "rag_pipeline_service_url" scripts config docs` returns only the removed-key rejection and its message.
- A config containing `rag_pipeline_service_url` fails load as an unknown/removed key, covered by a test in `tests/shared/test_config_validator.py`.
- `RagIngester` has no `__del__` and no `_log_ingest_failure`, and the entry point closes its client explicitly.
- `scripts/rag/augment.py` has no `getattr(self, ...)` in `last_stage_results`.
- `rg -n "gate refuses fallback" scripts docs` returns nothing.
- Existing RAG, ingestion, and startup-validation tests pass.

## Testing Expectations
- Update and run `tests/shared/test_config_validator.py`, `tests/rag/`, `tests/rag/ingestion/`, and the startup-validation tests in `tests/agent/`.
- Run the validation sequence in `rules/toolchain.md` (ruff, mypy with `--no-namespace-packages`, import-linter, bandit, pytest) and `uv run python tools/check_docs_consistency.py --domain rag`.
- Add a regression test that the ingester no longer defines `__del__` only if an existing test pattern covers lifecycle; otherwise rely on the acceptance searches.

## Documentation Impact
- Documentation must be updated: remove the key from the RAG configuration reference and remove identity-gate wording from `rag_05_07`; describe only current behavior and failure behavior (a failed or timed-out consistency check prints a warning and lets startup continue). Do not add file lists or config values (`skills/DESIGN.md` Docs content policy).
- Run the checkers listed in `routing.md` for `docs/` edits.

## Out of Scope
- The corpus identity table and reader (`corpus_identity.py`, `identity_gate.py`, the identity view of the rag-pipeline MCP server): decided in `issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md`.
- The diagnostics model and its output shape.
- Writing the maintainer's approval statement for the ADR-010 withdrawal and the ADR-004 Decision Group 10 amendment.
- Severity policy of the RAG consistency check (`issues/20261109-113123_adrrev013_rag-consistency-policy.md`).

## Dependencies
- Related, already implemented: `plans/done/20261110-092546_adrrev003_rag-http-delegation.md` (this issue finishes what it left).
- Coordinate with `plans/done/20261110-094140_adrrev004_non-strict-bypass-removal.md` and its open procedures (same file `scripts/agent/startup_validation.py`); apply this issue's warning-text edit after those procedures are executed or in the same pass.
- Coordinate with `issues/20261109-113123_adrrev013_rag-consistency-policy.md` (same startup RAG consistency block; it may change the severity of the same warnings).
- Blocks: the sweep issue for history comments filed in the same batch (`issues/20261110-171040_rmcompat007_history-comment-sweep.md`), which depends on all earlier issues of the batch.

## Unresolved Questions
- `不明`: whether the maintainer has stated approval for the ADR-010 withdrawal and the ADR-004 Decision Group 10 amendment; both records currently read `Pending maintainer statement`. This issue does not depend on the answer, but the ADR records stay incomplete until then.
- `不明`: whether the deployed `ingester.toml` under `/opt/llm/config` still sets `rag_pipeline_service_url` (not inspected; the answer needs read access to the production configuration). If it does, the new load-time rejection stops the ingester until the key is removed, so the deployment step (`deploy` skill) must remove it first.
- `Needs confirmation`: whether the `main()` entry point of the ingester should use a context manager or a `try/finally` close; either satisfies the acceptance criteria.

## AI Implementation Instruction
- Change only the files listed under Target Files or Areas; do not touch the diagnostics model, corpus identity, or ADR approval text.
- Do not write approval statements on behalf of the maintainer.
- Re-run the searches in Acceptance Criteria before editing, because neighboring plans edit the same files; stop and report if a listed leftover is already gone.
- Keep comments and log text in English.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261110-170632
- **Related target files**: `config/ingester.toml`, `scripts/shared/types.py`, `scripts/shared/config_validator.py`, `scripts/rag/models_config.py`, `scripts/rag/config_resolution.py`, `scripts/rag/augment.py`, `scripts/rag/ingestion/ingester.py`, `scripts/agent/startup_validation.py`, `docs/21_rag/rag_05_01-configuration-reference.md`, `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`
