# Implementation Procedure

## Goal

Replace environment-specific failure handling descriptions ("production or local mode") in `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md` with unified language consistent with ADR-004 Decision #1 and Decision #3. Requirement: REQ-001 (replace "production or local mode").

## Scope

Edit line 42 of `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`; verify the replacement against revised ADR-004 (`docs/adr/ADR-004-environment-failure-handling-policy.md`) and current code (`scripts/agent/services/mcp_tool_discovery.py`).

## Assumptions

- The revised ADR-004 text is authoritative for determining correct terminology.
- Code inspection of `mcp_tool_discovery.py` confirms that failure handling does NOT depend on "local mode" — it uses `is_prod` boolean checks instead.
- No automated tests are required for this documentation-only task.

## Design decisions

- Replace "regardless of whether it is production or local mode" with "regardless of environment" — this is the shortest unified phrasing that preserves the original meaning while eliminating environment-specific distinction.
- Use Decision numbers from the revised ADR-004 as the primary justification for changes.

## Alternatives considered

- Using "in all environments" instead of "regardless of environment": equivalent meaning, slightly more formal tone. Chose "regardless of environment" because it mirrors the original sentence structure more closely.
- Removing the entire clause entirely: would lose the emphasis that the FATAL treatment applies universally, which is important for operator understanding.
- Adding explicit references to Decision #1 and Decision #3 inline: would make the text longer and harder to read; better to keep justifications in the revision rationale rather than inline.

## Implementation

### Target file

`docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`

### Procedure

1. Read revised ADR-004 text to extract correct unified language guidance.
2. Update line 42 — replace "regardless of whether it is production or local mode" with "regardless of environment".
3. Run grep for "production or local mode" to confirm zero matches remain in this file.
4. Review all updates for consistency with revised ADR-004 terminology.

### Method

Adversarial verification: treat the Plan's claims about current source-code behavior as assertions to confirm, not confirmed facts. Verify that the replacement text accurately reflects the actual code behavior before changing the document.

### Details

**Line 42 (REQ-001):**
Current content: "- Failure in `mcp_tool_discovery` is treated as FATAL regardless of whether it is production or local mode. Since tool discovery failure makes all session tool calls impossible, it is critical."

Code inspection result: `mcp_tool_discovery.py` lines 134-145 show that `is_required` logic uses `cfg.required_in_production` or `cfg.required_in_local` based on security profile. However, the FATAL status assignment is unconditional — it does NOT branch based on environment. The "production or local mode" phrase contradicts ADR-004 Decision #1 (single common policy).

Updated content: "- Failure in `mcp_tool_discovery` is treated as FATAL regardless of environment. Since tool discovery failure makes all session tool calls impossible, it is critical."

Rationale: "regardless of environment" is the minimal change that eliminates the environment-specific distinction while preserving the emphasis on universal FATAL treatment. This is identical to the same change in the companion document `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` line 64, ensuring consistency across both documents.

## Compatibility considerations

- Updating this line may affect downstream documents that cross-reference health probe behavior. If this line is cited by other documents as evidence of environment-independent failure handling, those citations become stale.

## Security considerations

N/A: documentation update only; no code changes.

## Rollback considerations

- This line can be reverted independently by restoring the previous content.
- No operational impact from reverting documentation changes.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md` | Manual review — check each replacement against revised ADR-004 | Grep for "production or local mode"; read both documents side-by-side | Zero matches for "production or local mode" in this file; all replacements use unified language |

## Completion criteria

- [ ] Line 42: "regardless of whether it is production or local mode" replaced with "regardless of environment"
- [ ] No remaining "production or local mode" phrasing exists in this document
- [ ] All updates accurately reflect current code behavior (which uses `is_prod` checks, not "local mode" terminology)

## Out of scope

- Modifying any other documents beyond `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`.
- Changing ADR-004 itself.
- Adding new tests (covered by adr004_03).
- Modifying source code files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 2026-09-01TXX:XX:XX | 2026-09-01TXX:XX:XX | Replaced "regardless of whether it is production or local mode" with "regardless of environment" on line 42 |
| 2 | Add or update tests per Validation plan | Done | — | — | N/A: documentation-only changes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 2026-09-01TXX:XX:XX | 2026-09-01TXX:XX:XX | Zero matches for "production or local mode"; docs consistency check passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | — | — | No additional documentation updates needed |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260831-173019_adr004_03_related_docs_local_mode_language.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260901-000735_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-175237
- **Related target files**: docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md
