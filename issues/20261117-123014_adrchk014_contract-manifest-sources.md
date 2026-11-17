# Derive contract manifests from enforced sources

## Priority
Medium

## Summary
Manifests written by `tools/generate_reference_table.py` contain values that are not in their sources, or come from sources the runtime does not enforce, and the manifest schema is too loose to catch this.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-M02`; merged from ADRCHK-M05, M14, M24, L24 (review findings N9, N12, N28, N41, N54)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
Claims come from the review (`Documentation only` until re-verified).

## Reason for Change
- The gate column holds the wrong data: `invariant_coverage` stores the matrix Type column as `gate` and discards the Blocking column, and the schema accepts any string.
- The route-role manifest is not enforced: `eventbus_route_roles` comes from `_ROUTE_ROLE_MAP`, which authorization never uses, and lists route paths that do not exist; the `_do_ack` docstring and audit records use non-route paths.
- Some values are constants: `health_contracts` `disposition: fail-fast` is a generator constant, while ADR-015 allows generating only mechanically derivable facts.
- Classifications and descriptions are inconsistent: `component_mandatoriness` is classified as both bound and unbound, the memory source description differs between modes, and the `db_schema_versions` description still mentions removed version mechanisms.
- The API reference is incomplete: `agent_api.yaml` omits `scripts/agent/workflow/` and `scripts/agent/services/`.

## Implementation Intent
- Every manifest field is derived from a source that the runtime enforces, and the schema rejects malformed values.
- Route paths in the manifest, docstrings, and audit records match the registered routes.

## Target Files or Areas
- `tools/generate_reference_table.py`
- `tools/_contract_manifests.py`
- `schemas/contract_manifest.json`
- scripts/eventbus/auth.py (`_ROUTE_ROLE_MAP`)
- scripts/eventbus/ack_route.py, scripts/eventbus/dlq_route.py, scripts/eventbus/authz_ttl.py (route strings and docstrings)
- registry/manifests/*.yaml (regenerated)
- docs/23_agent/agent_13_reference-api-generated.md (regenerated)
- docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md (only if the derivation rule changes)
- `tests/tools/`
- `tests/eventbus/`

## Required Changes
- Store Blocking as `gate` with the enum Blocking or Non-Blocking, keep Type as a separate enum field, and bump the manifest version.
- Derive route roles from the FastAPI routes and their `require_role` dependencies, or make `_ROUTE_ROLE_MAP` the enforced source; allow `{}` in the schema route pattern.
- Use the real route paths in audit records and docstrings.
- Remove `disposition` or derive it from a source field; give each manifest one bound or unbound classification; unify the memory description; update the version description to the fingerprint model.
- Add `scripts/agent/workflow/` and `scripts/agent/services/` to `agent_api`.
- Regenerate all manifests.

## Constraints
- Do not edit the YAML files by hand; regenerate them.
- Audit record path changes affect `scripts/eventbus/` consumers; measure blast radius with `rg` first (`rules/toolchain.md`).
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- The schema rejects a `gate` value other than Blocking or Non-Blocking.
- A test asserts that every registered EventBus route's role matches the manifest.
- `uv run python tools/generate_reference_table.py --check` passes.

## Testing Expectations
Tests under `tests/tools/` and `tests/eventbus/`; generator `--check`; ruff, mypy, bandit. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. The regenerated API reference and ADR-015 only if the derivation rule changes.

## Out of Scope
- Changing authorization behavior (see the EventBus authorization issue).

## Dependencies
- `issues/20261117-123002_adrchk002_eventbus-authz-model.md` and `issues/20261117-123017_adrchk017_eventbus-task-supervision.md` edit EventBus route and auth files; fix the order with the owner.

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
- Do not edit the YAML files by hand. Regenerate them.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123014
- **Related target files**: `tools/generate_reference_table.py`; `tools/_contract_manifests.py`; `schemas/contract_manifest.json`; `scripts/eventbus/auth.py (`_ROUTE_ROLE_MAP`)`; scripts/eventbus/ack_route.py, scripts/eventbus/dlq_route.py, scripts/eventbus/authz_ttl.py (route strings and docstrings); `registry/manifests/*.yaml (regenerated)`; `docs/23_agent/agent_13_reference-api-generated.md (regenerated)`; `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md (only if the derivation rule changes)`; `tests/tools/`; `tests/eventbus/`
