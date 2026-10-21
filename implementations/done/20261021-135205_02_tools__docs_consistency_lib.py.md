## Goal
Add a shared matcher/helper for the uncovered identifier-reference forms (bare snake_case names, and/or non-`_db_path` config keys) to `tools/_docs_consistency_lib.py` so per-domain callers in `tools/check_docs_consistency.py` reuse it instead of duplicating extraction logic.

## Scope
- Modify exactly `tools/_docs_consistency_lib.py`: add one shared helper for the uncovered reference forms, referenced by `check_docs_consistency.py` (this row).
- Only create this row's change if Phase 1 (UNK-02) determines a shared matcher is warranted (i.e. more than one caller needs it). If a single inline check suffices, leave this file unchanged.
- Keep `tools/TOOL_DESCRIPTIONS.md` in sync only if the tool's documented capability changes (that is a separate row).

## Assumptions
- The owner's decision is recorded before this executes (Plan REQ-001); this documents the mechanical-branch sub-case so it can be applied once decided.
- The shared helper reuses the allowlist mechanism (`# ...-ok`) for bare-variable false-positive control (UNK-02).
- Canonical config model or `config/*.toml` is the source of truth for config-key checks, not a hardcoded list.

## Design decisions
- Add a single small, well-typed helper (e.g. `iter_bare_identifier_refs(text)` and/or a config-key extractor) rather than inlining per caller.
- Keep it report-only (Warning) and gate-free, consistent with the parent tool.

## Alternatives considered
- Inlining the matcher in `check_docs_consistency.py` only: preferred if only one caller needs it; this row exists only if multiple callers warrant a shared helper.
- Recording an accepted limit instead: out of scope for this row — that is the `docs/00_governance/governance_04_documentation-checks.md` row.
- Inferring the owner's decision: rejected, REQ-001 makes the recorded decision a hard gate.

## Implementation
### Target file
`tools/_docs_consistency_lib.py`

### Procedure
1. Confirm the owner's decision is recorded (REQ-001). If absent, stop and report; do not infer.
2. Confirm Phase 1 decided a shared matcher is warranted (more than one per-domain caller). If not, skip this file — no change.
3. Add the shared extractor/matcher for the uncovered forms; export/import it into `check_docs_consistency.py`.
4. Ensure callers emit at Warning level and honor the allowlist.

### Method
- Locate the existing shared helpers (`check_function_references`, `check_file_path_references` live here). Add the new helper alongside them with matching typing and error-handling conventions.
- The helper returns candidate uncovered references given a text/config source; callers filter against defined names and emit warnings.

### Details
- Verified at planning time: `_docs_consistency_lib.py` holds `check_file_path_references` (L297) and `check_function_references` (L404). Whether the bare-variable check needs a shared helper vs. a single inline call is a Phase 1 decision (UNK-02). If implementing requires a file not listed in `Implementation Target Files`, that is an additional-target-file discovery — stop and report `Blocked`.

## Compatibility considerations
- The helper is imported by `check_docs_consistency.py`; keep its signature backward-compatible. The tool must not fail on the current corpus.

## Security considerations
Report-only (Warning) helper over local docs/scripts/config; no secrets, network, or access changes.

## Rollback considerations
Revert the commit that edits the lib and its tests; revert the `check_docs_consistency.py` / `TOOL_DESCRIPTIONS.md` updates if present.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| Shared matcher | Unit (via callers) + fixture | `uv run pytest tests/tools/test_check_agent_docs_consistency.py` | New-form fixtures pass; existing suite green |
| Changed tool | Lint / type / security | `uv run ruff check`, `uv run mypy tools/<file>.py`, `uv run bandit tools/<file>.py` | Pass |

## Completion criteria
- The shared matcher exists in `_docs_consistency_lib.py` and is imported by `check_docs_consistency.py` only if multiple callers need it.
- `ruff`, `mypy`, `bandit` pass; existing suite green.
- No blocking gate introduced.

## Out of Scope
- Adding a new one-off script against the routing policy.
- Implementing the per-domain wiring (that is `check_docs_consistency.py`, this row).
- Editing `tools/TOOL_DESCRIPTIONS.md` unless the capability changed (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the shared identifier-reference matcher to `_docs_consistency_lib.py` | Pending | — | — | Only if Phase 1 (UNK-02) decides a shared matcher is warranted |
| 2 | Run lint/type/bandit and the existing suite | Pending | — | — | Depends on step 1 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Owner decision (mechanical / accept-limit) not available to the planning agent | N/A: pending external governance decision | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` and `REQ-003` — shared matcher/helper for uncovered reference forms used by `check_docs_consistency.py` callers
- **Source issue**: `issues/20261021-100351_identmatch_extend-identifier-matching-to-snake_case-names-and-config-keys-in-docs-verification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-125149_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-135205
- **Related target files**: `tools/_docs_consistency_lib.py`
