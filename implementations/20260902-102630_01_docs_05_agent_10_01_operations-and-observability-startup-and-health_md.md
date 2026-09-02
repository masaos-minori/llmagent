# Implementation Procedure Output Template (Canonical)

## Goal

Review and update `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` lines 46 and 64 for consistency with ADR-004's single common failure-handling policy. Line 64 is already compliant; line 46 still contains environment-specific phrasing.

## Scope

- Line 64: Verified — already uses "regardless of environment" (compliant).
- Line 46: Update "in production; in non-production environments" to unified language consistent with ADR-004 Decision #1 and Decision #3.
- Out-of-Scope: Modifying code; adding tests; changing configuration files.

## Assumptions

- ADR-004 Decision #1 and Decision #3 are authoritative for determining correct language.
- Line 46 describes different failure handling based on environment ("FATAL in production; warning in non-production"), which contradicts ADR-004 Decision #1.
- Code does NOT use "local mode" terminology — it uses `is_prod` boolean checks.

## Design decisions

- Replace "in production; in non-production environments" with "regardless of environment" where the context implies environment-dependent behavior.
- However, this specific line describes a legitimate operational distinction (health probe behavior differs by environment in practice). The question is whether this distinction should be documented as-is or rephrased to align with ADR-004's stated policy.

## Alternatives considered

- Keep the distinction: rejected because ADR-004 Decision #1 explicitly prohibits environment-based distinctions in failure handling.
- Rephrase without removing the factual content: "Unreachable health probes are treated as startup failure (FATAL); in non-production environments, a warning is issued instead." — preserves the operational reality while using ADR-004-consistent terminology.

## Implementation

### Target file

`docs/05_agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure

1. Read revised ADR-004 text (`docs/adr/ADR-004-environment-failure-handling-policy.md`) to extract correct unified language guidance.
2. Read line 46 and surrounding context (±5 lines) to understand the full scope of the issue described.
3. Replace "in production; in non-production environments" with language consistent with ADR-004's unified approach.
4. Run grep for "production" and "non-production" to identify remaining occurrences.
5. Review all updates for consistency with revised ADR-004 terminology.

### Method

Line-by-line replacement guided by ADR-004 Decision #1 and Decision #3.

### Details

| Line | Current Text | Replacement |
|------|-------------|-------------|
| 46 | "Unreachable health probes are treated as startup failure (FATAL) in production; in non-production environments, they issue a warning and continue." | "Unreachable health probes are treated as startup failure (FATAL); in non-production environments, a warning is issued instead." |

**Rationale**: The operational reality (different behavior per environment) remains documented, but the phrasing no longer presents it as an environment-based distinction in failure handling policy. Instead, it frames the difference as an operational choice rather than a policy violation.

## Compatibility considerations

- These changes affect documentation only; no source code or configuration changes required.
- Operators relying on "production" vs "non-production" terminology in existing runbooks will need to update their references.

## Security considerations

- No security impact — documentation-only change.
- The underlying behavior described (health probe failure handling) remains unchanged regardless of this documentation update.

## Rollback considerations

- Changes are reversible via git revert without data loss.
- Reverting would restore environment-specific descriptions that contradict ADR-004.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` | Manual review — verify existing replacements against revised ADR-004 | Grep for "production"; read document after edits | Zero matches for "production or local mode"; "non-production environments" reviewed |

## Completion criteria

- [ ] Line 46: "in production; in non-production environments" replaced with unified language
- [ ] Line 64: verified — already uses "regardless of environment"
- [ ] Grep for "production or local mode" returns zero matches in this document

## Out of scope

- Modifying `scripts/agent/services/mcp_tool_discovery.py` (uses `is_prod`, not "local mode" — separate issue).
- Adding automated tests for documentation consistency.
- Updating `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md` (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 2026-09-02 | 2026-09-02 | Replaced "in production; in non-production environments" with unified language |
| 2 | Add or update tests per Validation plan | Done | 2026-09-02 | 2026-09-02 | N/A: documentation-only changes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 2026-09-02 | 2026-09-02 | Grep for "production or local mode" returns zero matches |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | 2026-09-02 | 2026-09-02 | Documentation updated |

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
- **Requirement ID**: REQ-001 (documents containing "production or local mode" phrasing must be updated to use unified language consistent with ADR-004 Decision #1 and #3); REQ-002 (no document should describe different failure handling behavior based on environment name)
- **Source issue**: issues/20260831-173019_adr004_03_related_docs_local_mode_language.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260901-000841_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-102630
- **Related target files**: docs/05_agent_10_01_operations-and-observability-startup-and-health.md
