## Goal

Regenerate the EventBus API manifest so the admin endpoint summary names only `consumer_authorization` (REQ-007).

## Scope
**Release unit**: N/A: generated artifact; run after rows 01-07 land (Plan Phase 7).

## Assumptions
- The manifest is a generated file; the only supported edit path is the generator (`tools/generate_reference_table.py`), never hand-editing the guarded block.

## Design decisions
- N/A.

## Alternatives considered
- Hand-editing line 25: rejected; generated content must reproduce from source.

## Implementation
### Target file
`registry/manifests/eventbus_api.yaml`
### Procedure
Refresh the manifest with the generator after the source docstrings change.
### Method
Run `uv run python tools/generate_reference_table.py --type eventbus`; verify with `--check`.
### Details
- The endpoint entry summary (line 25: "Update `consumer_authorization`/`topic_authorization` at runtime and ...") is taken from `admin_route.py`'s docstring; it updates automatically once row 04 removes the second name.
- Confirm the audit row signatures (from `audit.py`) reflect the new `log_authorization_change` and the trimmed `log_privileged_action` from row 03. Verified 2026-11-13: the current manifest carries `log_privileged_action` at lines 45-46 with the generation kwargs in the signature; the generator will add a `log_authorization_change` row and trim this one.
- Allowed-red note (verification 2026-11-13): between unit 1/2 completion and this row's regeneration, `generate_reference_table.py --check` is expected to report drift; treat it as an allowed transient state (Plan Phase 7 ordering), and run this row only after rows 01-07 (including row 03) have landed, then confirm `--check` is clean at the end-of-Phase-7 validation.
- The generator reads `_ROUTE_ROLE_MAP` (`auth.py:75` via AST at `tools/generate_reference_table.py:572-574`); row 02 keeps it, so role columns are unchanged.

## Compatibility considerations
- rmcompat005 and rmcompat007 also name this manifest; run this Plan first and re-run the generator after each later plan (Plan Dependencies).

## Security considerations
- N/A: generated documentation artifact.

## Rollback considerations
- Re-run the generator against reverted sources, or restore the previous file from git.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` reports no drift.
- AC-7: manifest matches code.

## Completion criteria
- `--check` is clean and the summary names only `consumer_authorization`.

## Out of Scope
- Manifest entries outside the eventbus domain.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-13 | 2026-11-13 | generator --type eventbus --manifests run; --check clean |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-13 | 2026-11-13 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-13 | 2026-11-13 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-13 | 2026-11-13 | — |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/done/20261110-170832_rmcompat004_eventbus-config-auth-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-135237
- **Related target files**: `registry/manifests/eventbus_api.yaml`
