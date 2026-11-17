# Repair the canonical source registry and its checkers

## Priority
Medium

## Summary
`config/documentation_canonical_sources.toml` contradicts governance_01 and ADR-004, and the two checkers that should detect this do not. Fix the registry and the checkers together so the fix can be tested against real data.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-H10`; merged from ADRCHK-H11, H12, M25, L23 (review findings N10, N20, N21, N23, N36, N43)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
Claims come from the review (`Documentation only` until re-verified).

## Reason for Change
- The conflict checker misses conflicts: `tools/check_canonical_source_conflicts.py` runs its semantic checks only on the exception path, drops every error without a `decision_target`, routes by a code prefix no code matches (so every finding becomes a Known Issue instead of Blocking), reuses some codes with different meanings, and contains a duplicate `return conflicts`.
- The registry checker is inconsistent: a non-Accepted ADR status is an error in `validate()` but a warning in `validate_all()`, status is compared with an exact match, the base directory depends on the working directory, many methods are unused (Dead Code under governance_02), and the conflict checker's `--registry` help shows the wrong default.
- The registry has conflicting entries: the eventbus bootstrap DDL points to `scripts/db/schema_sql.py` instead of `scripts/eventbus/schema.sql`; the `agent.posture-failure-handling` note says fail-open in dev, which ADR-004 forbids; governance_01 is registered for `documentation-metadata`, which the Resolution Matrix assigns to governance_02; `registry/component_mandatoriness.yaml` is registered as `security-policy`, which the Resolution Matrix limits to ADR-007, ADR-012, and ADR-013, and ADR-017 and ADR-004 are missing from that list.
- Smaller errors remain: `overview.architecture-overview` is classified as `documentation-metadata`; the governance_02 front matter example miscounts optional fields; `config/adr_authority.toml` has a transcription-date note; generator comments use the non-standard ID `ADR-02.05 REQ-004`.

## Implementation Intent
- The semantic checks always run, every error is reported, and each rule code has one meaning.
- Routing assigns Blocking as governance requires.
- After the registry fix, each claim type has one owner, and the registry agrees with the Resolution Matrix and the ADRs.

## Target Files or Areas
- `tools/check_canonical_source_conflicts.py`
- `tools/check_canonical_source_registry.py`
- `config/documentation_canonical_sources.toml`
- config/adr_authority.toml (note only)
- tools/generate_reference_table.py (comments only)
- docs/00_governance/governance_01_documentation-policy.md (Resolution Matrix)
- `docs/00_governance/governance_02_documentation-metadata.md`
- `tests/tools/`

## Required Changes
- Add fixture tests that fail today: two owners for one claim, a missing referenced path, and a non-Accepted ADR status.
- Run the semantic checks on every path, keep errors without `decision_target`, fix the routing prefix, give each code one meaning, and remove the duplicate return.
- Unify status severity, parse the status token, resolve paths from the repository root, remove dead methods, and fix the help text.
- Fix the four registry entries and the smaller errors.
- Add ADR-017 and ADR-004 to the `security-policy` owners in the Resolution Matrix (a proposal; see AI Implementation Instruction).

## Constraints
- Changing the Resolution Matrix owners is a governance decision; prepare it as a proposal and stop before merging.
- Follow `routing.md` Tools: update `tools/TOOL_DESCRIPTIONS.md` and run `tools/check_tool_descriptions_sync.py` if tool files change shape; keep `tools/` modules within the module-size gate.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- The fixtures produce Blocking results, and running from another directory gives the same result.
- On the fixed registry, the conflict checker reports no Blocking finding.

## Testing Expectations
Fixture tests under `tests/tools/` (failing first); `uv run python tools/check_canonical_source_registry.py`, `tools/check_canonical_source_conflicts.py`, ruff, mypy, and bandit on changed tools. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. governance_01 Resolution Matrix, governance_02 front matter example; keep implementation details out per `skills/DESIGN.md`.

## Out of Scope
- ADR text changes (owned by the governance and ADR issues).
- Adding new claim types.

## Dependencies
- `issues/20261117-123011_adrchk011_adr-approval-governance.md` defines the governance mechanics the registry must match (soft dependency).

## Unresolved Questions
- The existing checker tests under `tests/tools/` were not reviewed.

## AI Implementation Instruction
- Prepare Resolution Matrix owner changes as a proposal and stop before merging.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123010
- **Related target files**: `tools/check_canonical_source_conflicts.py`; `tools/check_canonical_source_registry.py`; `config/documentation_canonical_sources.toml`; `config/adr_authority.toml (note only)`; `tools/generate_reference_table.py (comments only)`; `docs/00_governance/governance_01_documentation-policy.md (Resolution Matrix)`; `docs/00_governance/governance_02_documentation-metadata.md`; `tests/tools/`
