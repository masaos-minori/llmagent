# Implementation Procedure Output Template (Canonical)

## Goal

Remove "local mode" references from `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md` that describe different behavior per environment, replacing them with language consistent with ADR-004's single common failure-handling policy.

## Scope

- Edit lines 12, 28, 34, 44, 51 of `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md` — replace "local mode" with unified language ("regardless of environment" or equivalent).
- Out-of-Scope: Modifying code; adding tests; changing configuration files.

## Assumptions

- ADR-004 Decision #1 and Decision #3 are authoritative for determining correct language.
- All five "local mode" occurrences in this document describe environment-specific behavior that contradicts ADR-004.
- Code does NOT use "local mode" terminology — it uses `is_prod` boolean checks.

## Design decisions

- Replace "In local mode, ..." with "Regardless of environment, ..." where the context implies environment-dependent behavior.
- Replace "MCP discovery behaves differently between production and local modes:" with "MCP discovery behavior differs based on validation strictness, not environment:" — this preserves the factual content while removing the environment distinction.
- Use "development" instead of "local mode" when the context refers to development-time forgiveness rather than runtime environment.

## Alternatives considered

- Keep "local mode" where it refers to development-time tooling (not runtime environment): rejected because ADR-004 eliminates environment-based distinctions regardless of intent.
- Add a glossary defining "local mode": rejected because it would perpetuate the contradiction with ADR-004.

## Implementation

### Target file

`docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md`

### Procedure

1. Read revised ADR-004 text (`docs/adr/ADR-004-environment-failure-handling-policy.md`) to extract correct unified language guidance.
2. Read each of the five lines identified in the plan, along with surrounding context (±5 lines).
3. Replace each occurrence of "local mode" with language consistent with ADR-004's unified approach.
4. Run grep for "local mode" to confirm zero matches remain in this document.
5. Review all updates for consistency with revised ADR-004 terminology.

### Method

Line-by-line replacement guided by ADR-004 Decision #1 and Decision #3.

### Details

| Line | Current Text | Replacement |
|------|-------------|-------------|
| 12 | "In local mode: SKIPPED outcome means all tool calls will fail for that session" | "Regardless of environment: SKIPPED outcome means all tool calls will fail for that session" |
| 28 | "Discovery was skipped entirely. In local mode, this may indicate a full-session tool-call outage." | "Discovery was skipped entirely. Regardless of environment, this may indicate a full-session tool-call outage." |
| 34 | "MCP discovery behaves differently between production and local modes:" | "MCP discovery behavior differs based on validation strictness, not environment:" |
| 44 | "This difference exists because local mode is designed to be more forgiving during development, while production mode enforces strict validation to prevent partial functionality." | "This difference exists because development tooling is designed to be more forgiving during iteration, while production enforcement prevents partial functionality." |
| 51 | "**Important:** If discovery is `SKIPPED` in local mode, startup continues but the `RuntimeToolRegistry` remains empty or incomplete." | "**Important:** If discovery is `SKIPPED`, startup continues but the `RuntimeToolRegistry` remains empty or incomplete." |

## Compatibility considerations

- These changes affect documentation only; no source code or configuration changes required.
- Operators relying on "local mode" terminology in existing runbooks will need to update their references.

## Security considerations

- No security impact — documentation-only change.
- The underlying behavior described (tool discovery failure handling) remains unchanged.

## Rollback considerations

- Changes are reversible via git revert without data loss.
- Reverting would restore environment-specific descriptions that contradict ADR-004.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md` | Manual review — check each replacement against revised ADR-004 | Grep for "local mode"; read document after edits | Zero matches for "local mode" in this document; all replacements use unified language |

## Completion criteria

- [ ] Line 12: "In local mode" replaced with "Regardless of environment"
- [ ] Line 28: "In local mode" replaced with "Regardless of environment"
- [ ] Line 34: "between production and local modes" replaced with "based on validation strictness, not environment"
- [ ] Line 44: "local mode" replaced with "development tooling"; "production mode" replaced with "production enforcement"
- [ ] Line 51: "in local mode" removed (context makes environment reference unnecessary)
- [ ] Grep for "local mode" returns zero matches in this document

## Out of scope

- Modifying `scripts/agent/services/mcp_tool_discovery.py` (uses `is_prod`, not "local mode" — separate issue).
- Adding automated tests for documentation consistency.
- Updating `docs/90_shared_90_inconsistencies_and_known_issues.md` (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 2026-09-02 | 2026-09-02 | All 5 replacements completed |
| 2 | Add or update tests per Validation plan | Done | 2026-09-02 | 2026-09-02 | N/A: documentation-only changes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 2026-09-02 | 2026-09-02 | Grep for "local mode" returns zero matches |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | 2026-09-02 | 2026-09-02 | Documentation updated per procedure |

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
- **Requirement ID**: REQ-002 (no document should describe different failure handling behavior based on environment name); REQ-005 (all remaining "local mode" references that imply environment-specific behavior must be removed)
- **Source issue**: issues/20260831-173019_adr004_03_related_docs_local_mode_language.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260901-000841_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-102630
- **Related target files**: docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md
