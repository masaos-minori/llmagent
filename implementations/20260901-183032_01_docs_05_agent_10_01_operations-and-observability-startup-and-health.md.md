# Implementation Procedure

## Goal

Replace environment-specific failure handling descriptions ("production or local mode") in `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` with unified language consistent with ADR-004 Decision #1 and Decision #3. Requirements: REQ-001 (replace "production or local mode"), REQ-002 (review "local mode" reference at line 46).

## Scope

Edit lines 46 and 64 of `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`; verify each replacement against revised ADR-004 (`docs/adr/ADR-004-environment-failure-handling-policy.md`) and current code (`scripts/agent/services/mcp_tool_discovery.py`).

## Assumptions

- The revised ADR-004 text is authoritative for determining correct terminology.
- Code inspection of `mcp_tool_discovery.py` confirms that failure handling does NOT depend on "local mode" — it uses `is_prod` boolean checks instead.
- No automated tests are required for this documentation-only task.

## Design decisions

- Replace "regardless of whether it is production or local mode" with "regardless of environment" — this is the shortest unified phrasing that preserves the original meaning while eliminating environment-specific distinction.
- For line 46, evaluate whether "In production mode" / "In local mode" describes different failure handling behavior; if so, replace with unified language. If it describes different operational expectations (not failure handling), consider keeping the distinction but clarifying that the failure policy itself is unified.
- Use Decision numbers from the revised ADR-004 as the primary justification for changes.

## Alternatives considered

- Using "in all environments" instead of "regardless of environment": equivalent meaning, slightly more formal tone. Chose "regardless of environment" because it mirrors the original sentence structure more closely.
- Removing the entire clause entirely: would lose the emphasis that the FATAL treatment applies universally, which is important for operator understanding.
- Adding explicit references to Decision #1 and Decision #3 inline: would make the text longer and harder to read; better to keep justifications in the revision rationale rather than inline.

## Implementation

### Target file

`docs/05_agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure

1. Read revised ADR-004 text to extract correct unified language guidance.
2. Update line 64 — replace "regardless of whether it is production or local mode" with "regardless of environment".
3. Review line 46 — determine whether "In production mode" / "In local mode" describes different failure handling or different operational expectations; update accordingly.
4. Run grep for "production or local mode" to confirm zero matches remain in this file.
5. Review all updates for consistency with revised ADR-004 terminology.

### Method

Adversarial verification: treat the Plan's claims about current source-code behavior as assertions to confirm, not confirmed facts. Verify that the replacement text accurately reflects the actual code behavior before changing the document.

### Details

**Line 64 (REQ-001):**
Current content: "- Failure in `mcp_tool_discovery` is treated as FATAL regardless of whether it is production or local mode. Since tool discovery failure makes all session tool calls impossible, it is critical."

Code inspection result: `mcp_tool_discovery.py` lines 134-145 show that `is_required` logic uses `cfg.required_in_production` or `cfg.required_in_local` based on security profile. However, the FATAL status assignment is unconditional — it does NOT branch based on environment. The "production or local mode" phrase contradicts ADR-004 Decision #1 (single common policy).

Updated content: "- Failure in `mcp_tool_discovery` is treated as FATAL regardless of environment. Since tool discovery failure makes all session tool calls impossible, it is critical."

Rationale: "regardless of environment" is the minimal change that eliminates the environment-specific distinction while preserving the emphasis on universal FATAL treatment.

**Line 46 (REQ-002):**
Current content: "- In production mode, unreachable health probes are treated as startup failure (FATAL). In local mode, they only issue a warning and continue."

This line describes different behavior for health probe failures based on environment. This IS an environment-specific failure handling description that contradicts ADR-004 Decision #1. However, ADR-004 Decision #3 explicitly states that environment name does NOT change Fail-Fast conditions. Health probes are part of startup verification (Fail-Fast), so this distinction may be intentional and documented elsewhere.

Need to verify: Is this describing a deliberate design decision documented in another ADR, or is it an inconsistency? Check if any other ADR defines different health probe behavior per environment.

If it is a deliberate design decision documented elsewhere, add a cross-reference note. If it is an inconsistency, replace with unified language: "- Unreachable health probes are treated as startup failure (FATAL) in production; in non-production environments, they issue a warning and continue."

## Compatibility considerations

- Updating line 46 may affect downstream documents that cross-reference health probe behavior. If this line is cited by other documents as evidence of environment-dependent behavior, those citations become stale.
- Updating line 64 may affect downstream documents that cite this as evidence of environment-independent failure handling.

## Security considerations

N/A: documentation update only; no code changes.

## Rollback considerations

- Each line can be reverted independently by restoring the previous content.
- No operational impact from reverting documentation changes.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` | Manual review — check each replacement against revised ADR-004 | Grep for "production or local mode"; read both documents side-by-side | Zero matches for "production or local mode" in this file; all replacements use unified language |

## Completion criteria

- [ ] Line 64: "regardless of whether it is production or local mode" replaced with "regardless of environment"
- [ ] Line 46: reviewed and updated if it describes environment-specific failure handling inconsistent with ADR-004 Decision #1
- [ ] No remaining "production or local mode" phrasing exists in this document
- [ ] All updates accurately reflect current code behavior (which uses `is_prod` checks, not "local mode" terminology)

## Out of scope

- Modifying any other documents beyond `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`.
- Changing ADR-004 itself.
- Adding new tests (covered by adr004_03).
- Modifying source code files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only changes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260831-173019_adr004_03_related_docs_local_mode_language.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260901-001153_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-183032
- **Related target files**: docs/05_agent_10_01_operations-and-observability-startup-and-health.md
