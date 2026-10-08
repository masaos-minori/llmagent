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

- reference document
- document class
- generated reference
- disposition

## Status

Accepted

## Summary

`docs/00_governance/governance_01_documentation-policy.md`'s Document Classification defines a "Reference" class (API/command/configuration reference material), but the mechanical-content removal criteria of the documentation policy conflict with hand-written Reference documents by design — their entire content is exactly the kind of code-derivable listing the policy wants removed. This ADR adopts treating Reference-class documents as generated artifacts (Option B), produced from source code via `tools/generate_reference_table.py`, rather than retiring the class or accepting continued drift.

## Context

### Problem

Mechanical-content removal against Reference-class documents requires knowing whether their content should be deleted, generated, or left alone. Three options exist:

- **Option A**: Retire the Reference class; keep only canonical-source pointers.
- **Option B**: Treat Reference documents as generated artifacts (auto-produced from code/docstrings; hand-editing prohibited).
- **Option C**: Keep the status quo and accept drift between Reference documents and the code they describe.

`tools/generate_reference_table.py` already implements Option B's pattern through its `DOMAIN_GENERATORS` (see Implementation Notes for the current domains) (guard-commented blocks, format `<!-- AUTO-GENERATED: <generator>.py <purpose> -->`, e.g. `GUARD_START_MCP`/`GUARD_START_DEPLOYMENT`, refreshed from `config/agent.toml` and source).

### Constraints

- This ADR records the disposition decision only; generation tooling and the content of individual Reference documents are defined elsewhere.
- `GV-018` (`tools/check_docs_content_policy.py`) exempts guarded, auto-generated content (blocks opened by a `<!-- AUTO-GENERATED: <generator>.py <purpose> -->` comment) from its mechanical-content warnings.

## Assumptions

- The existing generator pattern in `tools/generate_reference_table.py` is adoptable for Reference-class content in any domain.
- The same generator pattern is reused for further domains (the generator also covers `agent`, `eventbus`, and `memory`).

## Decision

### Decision Details

Adopt **Option B**: Reference-class documents are treated as generated artifacts. Their content between guard comments is produced only by running the corresponding `tools/generate_reference_table.py --type <domain>` generator from current source — it MUST NOT be hand-edited between the guard comments. A Reference-class document may still carry surrounding hand-written prose outside the guarded block (e.g. an introduction or cross-references), but the mechanically-derivable listing itself is generated.

### Scope

Applies to every document that carries a generated guarded block (a `<!-- AUTO-GENERATED: <generator>.py <purpose> -->` comment). Such a document SHOULD also declare `class: Reference` in its front matter; the guarded block, not the class field, decides where this ADR applies.

### Out of Scope

Selecting which Reference-class documents migrate to generated status, and when, and performing that migration, are outside this ADR; Implementation Notes lists the documents currently generated.

## Rationale

### 1. Preserves the "one place to look" value — Maintainability

A generated Reference document still gives a reader one place to look for a domain's API/configuration surface, without requiring them to read source code directly — Option A (retiring the class) would lose this value entirely.

### 2. Keeps the canonical source unique — Correctness

A generated projection is not a competing copy: the code remains the sole canonical source, and the generated block is mechanically kept in sync with it. This directly addresses the drift Option C (status quo) already produces.

### 3. Reuses a working precedent — Consistency

`tools/generate_reference_table.py` already implements this pattern for several domains; extending it is lower-risk than inventing a new mechanism.

## Alternatives Considered

### Alternative A: Retire the Reference class

Remove the "Reference" document class entirely, replacing existing Reference documents with pointers directly into source code (e.g. a short doc naming the module to read). Rejected: this loses the "one place to look" value Reference documents provide today, and does not by itself resolve the mechanical-content policy conflict for any Reference document still in active use during a transition period.

### Alternative C: Keep the status quo

Leave Reference-class documents hand-maintained and accept ongoing drift risk, treating each drift instance as a documentation bug to fix individually (per `rules/coding.md`'s "Documentation notes" classification). Rejected: the mechanical-content removal policy has no answer for Reference-class content under this option, since removing it would delete real information with no generation path to replace it.

## Consequences

### Positive Consequences

- Reference-class documents stop drifting from the code they describe once migrated.
- The mechanical-content removal policy gains a concrete disposition for Reference-class content instead of an open conflict.

### Negative Consequences

- A Reference document can be migrated to generated status only for a domain that has a generator function in `tools/generate_reference_table.py`.

## Invariants

- INV-01: A Reference-class document migrated to Option B has its guarded-block content produced only by its corresponding `tools/generate_reference_table.py --type <domain>` generator — it is never hand-edited between the guard comments.

## Verification

- **Test**: Run the corresponding `tools/generate_reference_table.py --type <domain>` generator and confirm the guarded block matches current source (`--dry-run` output equals the live-written content). No automated CI check enforces this invariant yet; it is manually verified when a generator is run. — **Verifies**: INV-01 — **Type**: Manual Review — **Blocking**: No

## Implementation Notes

Documents carrying a generated guarded block (Explicit in code — `tools/generate_reference_table.py` `DOMAIN_GENERATORS` and its `REFERENCE_DOC_*` targets):

- `mcp` — `docs/22_mcp/mcp_01_tool_ownership_matrix.md`
- `deployment` — `docs/90_deployment/deployment_01_deployment.md`
- `agent` — `docs/23_agent/agent_13_reference-api-generated.md`
- `eventbus` — `docs/24_eventbus/eventbus_08_reference_api.md`
- `memory` — `docs/23_agent/agent_11_04_memory-module-reference-generated.md`

See Implementation References for the tool list.

## Known Deviations

Not applicable.

## Review Triggers

- A new Reference-class document is proposed.
- The generated-artifact tooling's scope changes materially (e.g. a new domain is added, or the guard-comment format changes).

## Approval

### Required Reviewers
- Documentation Governance Owner

### Approval Record

- **Approved By**: repository owner
- **Approval Date**: 2026-09-19
- **Approval Reference**: Reviewed and approved via chat (Claude Code session llmagent-73), content presented in full (Summary, Context, Decision, Alternatives Considered, Consequences) before approval
- **Decision Change (2026-10-08)**: The change of the Scope from documents classified `class: Reference` to documents carrying a generated guarded block was approved as a task-level approval decision (repository administrator instruction); the Named Approval Record above is unchanged and individual reviewer names are not recorded for this change.

This ADR reached `Accepted` via a Named Approval Record per the ADR Acceptance Evidence Standard (`docs/00_governance/governance_01_documentation-policy.md`) — not the task-level fallback path.

## Related ADRs

Not applicable.

## Implementation References

- `tools/generate_reference_table.py` — `DOMAIN_GENERATORS`, `--type <domain>`, `--dry-run`, guard comments (`<!-- AUTO-GENERATED: ... -->` / `<!-- END AUTO-GENERATED -->`)
- `tools/check_docs_content_policy.py` — exemption of guarded auto-generated content (`GV-018`)

## Completion Checklist

Confirm the following before changing the ADR to Accepted.

- [x] The problem to solve is clear
- [x] The Decision is narrowed to one primary design decision
- [x] The Decision is stated in clear terms such as mandatory, prohibited, canonical, or Fallback conditions
- [x] The reasons for adoption are explained from perspectives other than the current implementation
- [x] Substantive alternatives and the reasons for rejecting them are recorded
- [x] Positive Consequences are recorded
- [x] Negative Consequences are recorded
- [x] The impact on Security has been evaluated (Not applicable — this ADR covers only the classification policy for governance documents and does not affect code or runtime)
- [x] The impact on Operations, Monitoring, and Recovery has been evaluated (Not applicable — same as above)
- [x] Verifiable Invariants are defined
- [x] Exceptions or out-of-scope cases are clear
- [x] Each Invariant has a corresponding Verification
- [ ] Automatable verification does not rely only on Manual Review (INV-01 is verified manually; no automated check exists)
- [x] Discrepancies with the current implementation are registered as Known Issues (none applicable; see Known Deviations)
- [x] The Owner and required Reviewers are defined (see Approval Record — review completed through a Named Approval Record)
- [x] Review Triggers are recorded
- [ ] The ADR is registered in the ADR index and the Document Guides of related areas (separate confirmation required)
- [ ] The documents listed in Implementation Notes declare `class: Reference` in their front matter
