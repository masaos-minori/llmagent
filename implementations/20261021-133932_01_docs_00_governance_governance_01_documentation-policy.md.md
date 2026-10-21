## Goal
Apply the owner's approved compression/reference edits to `docs/00_governance/governance_01_documentation-policy.md` while preserving the gate contract (classification, canonical-source precedence, claim-type taxonomy, resolution matrix, ADR status/protocol, maintenance rules, and the Governance Verification Matrix).

## Scope
- Modify only owner-approved sections of `docs/00_governance/governance_01_documentation-policy.md`.
- Compress or replace with a canonical-source reference the machine-derivable sections (notably the "ADR Section Header Standardization" section at line 300).
- Do NOT change any gate, blocking status, timing, rule meaning, taxonomy, precedence, or ADR Decision text. Do not edit any tool or config.

## Assumptions
- The owner's compression decision is recorded before edits execute (Plan REQ-002); this procedure documents all branches so either can be applied once decided.
- Current-Specification-Only Policy: no history wording.
- The registry claim-type and authority rules are normative and are not compressed without explicit owner approval.

## Design decisions
- Classify each top-level section by the judgment order: currently valid, design value, mechanically re-derivable, change-time value, canonical source. Gate/taxonomy/precedence/matrix sections stay; tool-behavior / mechanical-standard sections are candidates for compression or reference replacement.
- Replace derivable content with a pointer to the canonical tool/config source — never copy it into a new summary that becomes a second normative source (REQ-004).

## Alternatives considered
- Inferring the owner's decision and editing proactively: rejected, REQ-002 makes the recorded decision a hard gate.

## Implementation
### Target file
`docs/00_governance/governance_01_documentation-policy.md`

### Procedure
1. Confirm the owner's compression/normative-section decision is recorded (REQ-002). If absent, stop and report; do not infer.
2. Produce the per-section Keep / Compress / Reference / Needs-Confirmation list (REQ-001) using the judgment order.
3. Apply only the owner-approved edits:
   - **Full keep**: no edit; record the list as the baseline.
   - **Compress-reference derivable only**: compress/replace the derivable sections (e.g. "ADR Section Header Standardization", L300) with a reference to the canonical source; leave gate/taxonomy/precedence/matrix text intact.
   - **Full compress under supervision**: apply the broader owner-approved reductions, still preserving every gate-contract region listed below.
4. Verify no dangling link, anchor, or rule ID remains and no second normative source was created (REQ-004).

### Method
- Locate the derivable region: "ADR Section Header Standardization" at line 300 (mechanical header standard, restates a tool/config fact).
- Gate-contract regions that MUST stay: Purpose, Document Classification, Canonical Source Precedence, Claim Type Taxonomy, Resolution Matrix, Authority vs. Evidence, Conflict / Code-vs-Document rules, Known Issues Registration Rule, Resolution Workflow, Merge Conditions (Blocking / Non-Blocking), ADR Status Definitions, ADR Change Protocol, Maintenance Rules, and the Governance Verification Matrix (17 rows).
- Edit in place; preserve headings, front matter, and `related:` links.

### Details
- If a derivable section is replaced by a reference, point to the canonical tool/config (e.g. the tool that defines the header standard) and to `routing.md` "When to run which tool", not to a new hand-written summary.
- Confirm `adr_01_index.md` is correctly out of scope (it is an automated check target, not edited here).

## Compatibility considerations
- Agents rely on `governance_01` as core policy; compression must not weaken normative text or break internal anchors/links.

## Security considerations
N/A: documentation-only compression of a governance policy doc; no code, secrets, or access changes.

## Rollback considerations
N/A: revert the commit that edits `governance_01_documentation-policy.md`.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_01_documentation-policy.md` | Docs quality / structure / content policy | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py` | Pass |
| Both docs | Canonical source registry conformance | `uv run python tools/check_canonical_source_registry.py` | Pass |
| `docs/10_adr/adr_01_index.md` | ADR preservation | `uv run python tools/check_adr_preservation.py` | Pass |
| Governance Verification Matrix | Manual gate-rule retention | Manual review | Every GV row retains its rule text and gate |

## Completion criteria
- Only owner-approved sections were changed; every gate-contract region is intact.
- No dangling link, anchor, or rule ID; no second normative source created.
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_canonical_source_registry.py`, `check_adr_preservation.py` pass.
- No gate, blocking status, timing, or ADR Decision changed.

## Out of Scope
- `docs/10_adr/adr_01_index.md` (automated check target, out of scope).
- Changing or adding verification rules; editing any tool or config.
- GV-016 wiring and follow-up work decisions (separate issues).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Classify each section Keep/Compress/Reference/Needs-Confirmation | Pending | — | — | REQ-001 deliverable |
| 2 | Apply owner-approved compression/reference edits (keep gate contract) | Pending | — | — | Branch selected by owner decision (REQ-002) |
| 3 | Run docs/registry/ADR checks and confirm gate rules retained | Pending | — | — | REQ-003, REQ-004 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | Owner compression/normative-section decision not available to the planning agent | N/A: pending external governance decision | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-004` — classify and apply owner-approved compression/reference edits to `governance_01` while preserving the gate contract
- **Source issue**: `issues/20261021-100322_govcompress_decide-the-compression-policy-for-governance_01-and-governance_04.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-123125_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-133932
- **Related target files**: `docs/00_governance/governance_01_documentation-policy.md`
