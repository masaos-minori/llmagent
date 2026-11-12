# Sweep the remaining history comments and plan identifiers from scripts and config

## Priority
Low

## Summary
After the other compatibility-removal issues land, remove or rewrite the module docstrings and comments in `scripts/` and `config/` that describe where code came from or which plan created it, so comments describe only current responsibility and behavior.

## Background
- Source: `memo-issue.md` item L-01 (consolidated version), re-checked against current source on 2026-11-10.
- `Explicit in code`, measured by search on 2026-11-10 over `scripts/` and `config/`:
  - "Extracted from" appears in many module docstrings and comments across `scripts/`.
  - "Refactored:" appears in two places, `RAGCORPUS001` in about a dozen, `EBAUTHGEN001` in a handful, and `crawl003` once, spread across `scripts/rag/`, `scripts/db/`, `scripts/eventbus/`, and `scripts/agent/`.
  - `user-approved` no longer appears (already removed).
  - `REQ-<number>` plan-requirement identifiers appear in several hundred comments, concentrated in `scripts/agent/`, `scripts/mcp_servers/`, and `scripts/eventbus/`, plus `config/mcp_dedup.toml` and `config/eventbus.toml`.
- `Explicit in code`: tests under `tests/eventbus/` and `tests/rag/` also cite `EBAUTHGEN001`, `RAGCORPUS001`, and requirement identifiers in docstrings; the memo's scope is `scripts/` and `config/` only.
- Related: `plans/done/20261110-094140_adrrev004_non-strict-bypass-removal.md` (open procedures edit many `scripts/agent/` files that carry such comments) and the other issues of this batch remove the comments in files they edit.

## Problem
- Notes about where code came from, or which plan created it, go stale after later changes, are meaningless without the plan documents, and hide the few comments that point at real compatibility code.

## Reason for Change
- Git history and the issue and plan documents already keep this information; the current-only policy (`compatrm001`) wants current-behavior comments. Low urgency: nothing is failing, and most of the comments disappear as other issues land.

## Implementation Intent
- Comments and docstrings describe only current responsibility and behavior.
- Do the sweep last, after the other compatibility-removal issues, so files are not edited twice; keep behavior unchanged.

## Target Files or Areas
- `scripts/` and `config/` files that match the search patterns below, for example `scripts/rag/diagnostics.py`, `scripts/rag/augment.py`, `scripts/rag/ingestion/crawler.py`, `scripts/agent/services/workflow_schema.py`, `scripts/rag/pipeline.py`, `scripts/eventbus/config.py`, `config/mcp_dedup.toml`, `config/eventbus.toml`
- The full list is `Unknown` until the search is re-run after the dependencies land.

## Required Changes
- Re-run the searches for "Extracted from", "Refactored:", `RAGCORPUS001`, `EBAUTHGEN001`, `crawl003`, and the requirement-identifier pattern, and rewrite or remove each match that earlier issues did not already remove.
- Keep a comment only if it states current behavior or a constraint that is not obvious from the code; rewrite it in that form instead of deleting the information.
- Do not remove identifiers that a checker requires (for example the ADR markers verified by `tools/check_adr_reference.py`).

## Constraints
- Comment-only change: no code, logic, or test behavior changes.
- Comments and log text stay in English (`rules/coding.md`).
- Do not touch `tests/` or `docs/` in this issue.

## Acceptance Criteria
- `rg -n "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003" scripts config` returns nothing.
- `rg -n "REQ-[0-9]+" scripts config` returns nothing after the last phase; each phase (one directory per change) leaves that directory free of matches.
- `git diff` shows comment and docstring changes only.
- The validation sequence in `rules/toolchain.md` passes unchanged.

## Testing Expectations
- No new tests. Run `rules/toolchain.md` validation (ruff, mypy with `--no-namespace-packages`, import-linter, bandit, full pytest), `uv run python tools/check_adr_reference.py`, and `uv run python tools/check_suppression_justification.py` (suppression comments may carry plan identifiers).
- Confirm with `git diff` that no non-comment line changed.

## Documentation Impact
- No documentation change is required. If a comment removal leaves a non-obvious constraint undocumented, record that constraint in the owning document only when it is intent or failure behavior, not implementation detail.

## Out of Scope
- Tests and `docs/` (history wording in documents is tracked by `issues/20261109-113318_adrrev017_docs-history-wording.md`; minor stale statements by `issues/20261109-113421_adrrev019_docs-stale-statements.md`).
- Any behavior change, and the compatibility-pattern checker (`issues/20261110-171157_rmcompat008_compat-checker-patterns.md`).

## Dependencies
- Depends on all other issues of this batch, so that their edits land first: `issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md`, `issues/20261110-170709_rmcompat002_rag-diagnostics-model.md`, `issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md`, `issues/20261110-170832_rmcompat004_eventbus-config-auth-audit.md`, `issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md`, `issues/20261110-171004_rmcompat006_rag-ingestion-cleanup.md`.
- Also schedule after the open procedures of `plans/done/20261110-094140_adrrev004_non-strict-bypass-removal.md` and after `plans/20261110-095137_adrrev005_schema-fingerprint-unify.md`, which edit many of the same files.
- Blocks `issues/20261110-171157_rmcompat008_compat-checker-patterns.md`.

## Unresolved Questions
- Decided (2026-11-10): `REQ-<number>` identifiers are in scope, and the sweep is done in phases by directory (for example `scripts/agent/`, `scripts/mcp_servers/`, `scripts/eventbus/`, then the rest); removing all matches is the acceptance criterion of the whole issue.
- `Needs confirmation`: whether tests that cite the same identifiers should be swept in a later issue.

## AI Implementation Instruction
- Edit comments and docstrings only; if a line other than a comment must change, stop and report.
- Re-run the search before starting, because earlier issues remove many matches.
- Do not delete a non-obvious constraint; rewrite it as current-tense text.
- Keep comments and log text in English.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261110-171040
- **Related target files**: `scripts/rag/diagnostics.py`, `scripts/rag/augment.py`, `scripts/rag/ingestion/crawler.py`, `scripts/agent/services/workflow_schema.py`, `scripts/rag/pipeline.py`, `scripts/eventbus/config.py`, `config/mcp_dedup.toml`, `config/eventbus.toml`
