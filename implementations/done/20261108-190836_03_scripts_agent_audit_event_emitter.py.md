## Goal
Delete the unused `_format_session_id` alias in the audit event emitter so the strict COMPAT scan reports no finding in this file (`REQ-002`).

## Scope
**Release unit**: wfaudit012-full

- Covers Plan `plans/20261108-084013_wfaudit012_shim-checker-case-gap.md` row 3 only: `scripts/agent/audit_event_emitter.py`.

## Assumptions
- Procedure 01 (`implementations/20261108-190836_01_tools_check_compat_shims.py.md`) lands in the same change unit; the alias is invisible to the current case-sensitive scan, so this deletion is the follow-through that makes the strict run clean (`REQ-002`).
- The alias has no callers: the 2026-11-08 grep over `scripts/`, `tests/`, `docs/`, `tools/` finds `_format_session_id` only at `scripts/agent/audit_event_emitter.py:6` (module docstring naming the pre-extraction name in `orchestrator.py`), `:31` (the comment), and `:32` (the alias assignment).

## Design decisions
- Delete rather than reword: the name exists only to keep an import path alive for callers that do not exist, which is exactly what the no-compatibility policy forbids; the same disposition `wfaudit008` applies to the adapter aliases (`implementations/20261108-162804_01_scripts_agent_workflow_engine_adapter.py.md`).
- Keep the module docstring at L6 untouched: it records the extraction history ("Extracted from orchestrator.py (`_format_session_id`, ...)") and carries no pattern the COMPAT stage matches.

## Alternatives considered
- Reword the comment to drop the "Backward-compatible" wording while keeping the alias: rejected — it hides a live leftover from the checker without removing the leftover.
- Keep the alias and add a `fixture`-category manifest entry: rejected — the policy accepts `fixture` entries only for genuine negative-test data, and this is production source.

## Implementation
### Target file
`scripts/agent/audit_event_emitter.py`

### Procedure
Delete two lines: the comment at L31 and the alias assignment at L32.

### Method
Remove `# Backward-compatible alias for existing callers that import _format_session_id` (L31) and `_format_session_id = format_session_id` (L32), leaving the public `format_session_id` definition (L26-28) and the class body starting at L35 unchanged; the blank-line spacing around the `# ── AuditEventEmitter class ──` separator (L34) collapses to one blank line after the function block.

### Details
- Live consumers of the public name stay intact: `scripts/agent/orchestrator.py:31` imports `format_session_id` and uses it at `scripts/agent/orchestrator.py:179`; the method form is used at `scripts/agent/audit_event_emitter.py:78` and `:96`; `docs/23_agent/agent_13_reference-api-generated.md:36` documents only `format_session_id`, and the alias is not listed there, so no reference-table regeneration is needed.
- No import, export list, or `__all__` entry references the alias.

## Compatibility considerations
- Public surface unchanged: `format_session_id` keeps its signature and behavior; the removed name was never imported anywhere (grep census above), so no consumer needs updating.
- After this edit the file produces no COMPAT finding in the strict run.

## Security considerations
- No security-relevant code touched; the audit log formatting path is unchanged.

## Rollback considerations
- Revert the commit restores both lines with no state to unwind. Rolling this back while procedure 01 stays landed re-opens the `audit_event_emitter.py:31` finding and the strict run turns red, so a rollback here must come with the census gate re-check.

## Validation plan
- Grep gate: `grep -rn "_format_session_id" scripts/ tests/ docs/ tools/` returns only `scripts/agent/audit_event_emitter.py:6` (the history sentence in the module docstring) and nothing else.
- Targeted tests: `uv run pytest tests/agent/workflow/test_session_diagnostics_wiring.py tests/agent/test_import_smoke.py -q` (the suite that exercises `format_session_id` behavior and module imports), then `uv run pytest tests/agent/ -q`.
- Checker gate: `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` reports no finding for this file; the full run exits 0 only after procedures 03-09 and `wfaudit008` have all landed.
- `uv run ruff check scripts/agent/audit_event_emitter.py`, `uv run ty check scripts/agent/audit_event_emitter.py` per `rules/toolchain.md`.

## Completion criteria
- L31-32 gone, `format_session_id` unchanged and still the only exported session-id formatter, the strict checker reports nothing for this file, and the grep gate shows no remaining `_format_session_id` consumer.

## Out of Scope
- The module docstring history sentence (L6) and the `docs/23_agent/agent_13_reference-api-generated.md` table row.
- The other census files and the checker semantics flip (procedures 01-02, 04-09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-090426 | 20261109-090426 | two-line deletion (L31-32) |
| 2 | Add or update tests per Validation plan | Completed | 20261109-090426 | 20261109-090426 | no new test: existing suite plus the grep gate N/A: no new test, existing suite + grep gate |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-101109 | 20261109-101109 | repo-clean gate depends on procedures 03-09 and `wfaudit008` STEP 3: per-member validators + targeted tests pass; diff-cover 100%; census 0 findings. End-of-unit full suite has 28 pre-existing eventbus failures (verified on clean HEAD, unrelated to unit); user approved proceeding. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-090426 | 20261109-090426 | no doc edit in scope N/A: no doc edit in scope |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261107-203225_wfaudit012_shim-checker-case-gap.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084013_wfaudit012_shim-checker-case-gap.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-190836
- **Related target files**: `scripts/agent/audit_event_emitter.py`; consumers `scripts/agent/orchestrator.py` (L31 import, L179 call), `tests/agent/workflow/test_session_diagnostics_wiring.py` (L132), `docs/23_agent/agent_13_reference-api-generated.md` (L36)