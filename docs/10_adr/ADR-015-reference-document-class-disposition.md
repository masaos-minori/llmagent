---
title: "ADR-015: Reference Document Class Disposition"
area: governance
tags:
  - documentation
  - governance
  - reference
related:
  - governance_01_documentation-policy.md
---

# ADR-015: Reference Document Class Disposition

## Keywords

reference document
document class
generated reference
disposition

## Status

Accepted

## Summary

`docs/00_governance/governance_01_documentation-policy.md`'s Document Classification defines a "Reference" class (API/command/configuration reference material), but a proposed documentation-slimming policy's mechanical-content removal criteria conflict with hand-written Reference documents by design — their entire content is exactly the kind of code-derivable listing the policy wants removed. This ADR recommends treating Reference-class documents as generated artifacts (Option B), produced from source code via `tools/generate_reference_table.py`, rather than retiring the class or accepting continued drift.

## Context

### Problem

Without an explicit decision, mechanical-content removal work cannot proceed against Reference-class documents without first knowing whether their content should be deleted, generated, or left alone. Three options exist:

- **Option A**: Retire the Reference class; keep only canonical-source pointers.
- **Option B**: Treat Reference documents as generated artifacts (auto-produced from code/docstrings; hand-editing prohibited).
- **Option C**: Keep the status quo and accept drift between Reference documents and the code they describe.

`tools/generate_reference_table.py` already implements Option B's pattern for MCP/RAG/deployment reference tables (guard-commented blocks, format `<!-- AUTO-GENERATED: <generator>.py <purpose> -->`, e.g. `GUARD_START_MCP`/`GUARD_START_DEPLOYMENT`, refreshed from `config/agent.toml` and source).

### Constraints

- This ADR records the disposition decision only — it does not implement any generation tooling or edit any existing Reference document's content.
- `GV-018` (`tools/check_docs_content_policy.py`) documents an intent to exempt guarded, auto-generated content from its mechanical-content warnings, but that exemption must actually recognize the real guard-comment format before Option B's guarded blocks are usable without warning noise (tracked separately).

## Assumptions

- The existing `rag`/`mcp`/`deployment` generator pattern in `tools/generate_reference_table.py` is a working, adoptable precedent for Reference-class documents generally, not specific to those three domains.
- Extending that tool to new domains (Agent, EventBus, Memory) is separate follow-up work, gated on this ADR's outcome, not performed here.

## Decision

### Decision Details

Adopt **Option B**: Reference-class documents are treated as generated artifacts. Their content between guard comments is produced only by running the corresponding `tools/generate_reference_table.py --type <domain>` generator from current source — it MUST NOT be hand-edited between the guard comments. A Reference-class document may still carry surrounding hand-written prose outside the guarded block (e.g. an introduction or cross-references), but the mechanically-derivable listing itself is generated.

### Scope

Applies to any `docs/*.md` document classified `class: Reference` per `docs/00_governance/governance_01_documentation-policy.md`'s Document Classification, once tooling exists to generate its content.

### Out of Scope

Which specific existing Reference-class documents migrate to generated status, and when, is recorded in Implementation Notes below as a starting list — actually performing that migration is separate follow-up work, not this ADR.

## Rationale

### 1. Preserves the "one place to look" value — Maintainability

A generated Reference document still gives a reader one place to look for a domain's API/configuration surface, without requiring them to read source code directly — Option A (retiring the class) would lose this value entirely.

### 2. Keeps the canonical source unique — Correctness

A generated projection is not a competing copy: the code remains the sole canonical source, and the generated block is mechanically kept in sync with it. This directly addresses the drift Option C (status quo) already produces.

### 3. Reuses a working precedent — Consistency

`tools/generate_reference_table.py` already implements this pattern successfully for three domains (`rag`/`mcp`/`deployment`); extending it is lower-risk than inventing a new mechanism.

## Alternatives Considered

### Alternative A: Retire the Reference class

Remove the "Reference" document class entirely, replacing existing Reference documents with pointers directly into source code (e.g. a short doc naming the module to read). Rejected: this loses the "one place to look" value Reference documents provide today, and does not by itself resolve the mechanical-content policy conflict for any Reference document still in active use during a transition period.

### Alternative C: Keep the status quo

Leave Reference-class documents hand-maintained and accept ongoing drift risk, treating each drift instance as a documentation bug to fix individually (per `rules/coding.md`'s "Documentation notes" classification). Rejected: this is exactly the problem the source issue identifies — the mechanical-content removal policy has no answer for Reference-class content under this option, since removing it would delete real information with no generation path to replace it.

## Consequences

### Positive Consequences

- Reference-class documents stop drifting from the code they describe once migrated.
- The mechanical-content removal policy gains a concrete disposition for Reference-class content instead of an open conflict.

### Negative Consequences

- Requires a `tools/generate_reference_table.py` generator function for any other domain with a Reference document before migration can happen for that domain — tracked separately, not implemented by this ADR. Generators for Agent/EventBus/Memory already exist.
- `GV-018`'s guard-comment exemption must actually recognize the real `<!-- AUTO-GENERATED: <generator>.py <purpose> -->` format (a pre-existing bug where it only matches a literal bare string) before newly generated guarded blocks are exempt from mechanical-content warnings — tracked separately, not implemented by this ADR.

## Invariants

- A Reference-class document migrated to Option B has its guarded-block content produced only by its corresponding `tools/generate_reference_table.py --type <domain>` generator — it is never hand-edited between the guard comments.

## Verification

Run the corresponding `tools/generate_reference_table.py --type <domain>` generator and confirm the guarded block matches current source (`--dry-run` output equals the live-written content). No automated CI check enforces this invariant yet; it is manually verified when a generator is run.

## Implementation Notes

Agent (`docs/23_agent/agent_12_reference-api.md`) and EventBus (`docs/24_eventbus/eventbus_09_reference_api.md`)
have both been migrated to generated Reference-class status under Option B.

This chapter is not a basis for design decisions. List detailed APIs, Classes, and Functions in the Implementation References.

## Known Deviations

Not applicable — Agent and EventBus Reference-class documents are already migrated to generated status under this decision (see Implementation Notes).

Do not unconditionally align the ADR text with the current implementation; manage discrepancies as Known Issues.

## Review Triggers

- A new Reference-class document is proposed.
- The generated-artifact tooling's scope changes materially (e.g. a new domain is added, or the guard-comment format changes).

## Approval

### Required Reviewers
- Documentation Governance Owner

### Approval Record

- **Approved By**: Masao Sugimoto (repository owner)
- **Approval Date**: 2026-09-19
- **Approval Reference**: Reviewed and approved via chat (Claude Code session llmagent-73), content presented in full (Summary, Context, Decision, Alternatives Considered, Consequences) before approval

This ADR reached `Accepted` via a Named Approval Record per the ADR Acceptance Evidence Standard (`docs/00_governance/governance_01_documentation-policy.md`) — not the task-level fallback path.

## Related Documents

- [Documentation Policy](../00_governance/governance_01_documentation-policy.md) — Document Classification, ADR Section Header Standardization, ADR Acceptance Evidence Standard
- `tools/generate_reference_table.py` — existing Option B precedent (rag/mcp/deployment/agent/eventbus/memory generators)
- `tools/check_docs_content_policy.py` — `GV-018`'s guard-comment exemption, currently mismatched against the real guard format (tracked separately)

## Completion Checklist

Confirm the following before changing the ADR to Accepted.

- [x] The problem to solve is clear
- [x] The Decision is narrowed to one primary design decision
- [x] The Decision is stated in clear terms such as mandatory, prohibited, canonical, or Fallback conditions
- [x] The reasons for adoption are explained from perspectives other than the current implementation
- [x] Substantive alternatives and the reasons for rejecting them are recorded
- [x] Positive Consequences are recorded
- [x] Negative Consequences are recorded
- [ ] The impact on Security has been evaluated (Not applicable — this ADR covers only the classification policy for governance documents and does not affect code or runtime)
- [ ] The impact on Operations, Monitoring, and Recovery has been evaluated (Not applicable — same as above)
- [x] Verifiable Invariants are defined
- [x] Exceptions or out-of-scope cases are clear
- [x] Each Invariant has a corresponding Verification
- [x] Automatable verification does not rely only on Manual Review (no automated verification at present; future CI integration is a Review Trigger)
- [x] Discrepancies with the current implementation are registered as Known Issues (none applicable; see Known Deviations)
- [x] The Owner and required Reviewers are defined (see Approval Record — review completed through a Named Approval Record)
- [x] Review Triggers are recorded
