---
title: "Documentation Policy"
area: governance
tags:
  - governance
related:
  - 00_index.md
  - overview_00_document-guide.md
  - governance_05_change-impact-and-dependency-graphs.md
---

# Documentation Policy

## Purpose

This document consolidates policy-level rules for the LLM agent design documentation set. It covers document classification, canonical source precedence, conflict resolution, and ADR conventions; change-impact rules and dependency graphs are defined in [Change Impact and Dependency Graphs](governance_05_change-impact-and-dependency-graphs.md).

## Current-Specification-Only Policy

The active design documentation set describes the current system only: what is
required to understand, implement, configure, operate, and validate the system as it
exists today.

The active documentation set does not retain:

- Deprecated specifications
- Superseded specifications
- Rejected architectural decisions
- Migration history
- Change history
- Archived issues
- Resolved Needs Confirmation entries
- Historical document structures
- Replacement mappings for removed items
- Historical compatibility records

Before historical content of this kind is removed from a document, any requirement,
constraint, invariant, rationale, or verification rule it contains that still applies
to the current system must be transferred into the appropriate current canonical
document. Removal of the historical content itself is a separate, later change and is
not performed by adding or updating this policy.

## Document Classification

Documents in the design documentation set are classified into seven classes:

- **Governance** — Cross-cutting rules, policies, and standards that apply across areas
- **Guide** — Navigation documents that provide an overview of an area's documentation structure
- **Specification** — Detailed technical specifications describing how components work
- **Reference** — API references, command references, and configuration reference materials
- **Operations** — Operational guidance including monitoring, troubleshooting, and diagnostics
- **Note** — Working notes, investigation results, and temporary documentation
- **Known Issues** — Documents tracking known inconsistencies between documentation and implementation

## Canonical Source Precedence

Canonical authority is resolved by the Claim Type Taxonomy and the Decision Target Canonical Source Matrix below, at the level of individual claims rather than whole-document-level rankings.

## Claim Type Taxonomy

The Claim Type Taxonomy resolves canonical authority at the level of individual claims rather than whole-document-level rankings.

### architecture-decision

An adopted architectural decision documented in an accepted ADR (`docs/10_adr/ADR-{NNN}-*.md`). Boundary against `functional-requirement`: an architecture-decision may constrain how a requirement is implemented but does not itself define what the requirement specifies.

### functional-requirement

A normative statement of what the system must do, expressed in an Accepted ADR (`docs/10_adr/ADR-{NNN}-*.md`) or in a source registered for it in the Canonical Source Registry. No per-area `*_specification.md` document is maintained. Boundary against `architecture-decision`: a functional-requirement defines the desired outcome; it does not prescribe how that outcome is achieved architecturally.

### external-behavior

Observable behavior of the system as experienced by external consumers — inputs, outputs, side effects, and timing characteristics.

### api-contract

The formal interface contract between the system and its callers — request/response shapes, headers, status codes, error semantics.

### runtime-behavior

Current execution-time behavior of the running system as exercised by source code under `scripts/`. Boundary against `verification-contract`: runtime-behavior describes what the system actually does; verification-contract describes what the system ought to do according to test expectations.

### verification-contract

Executable assertions about expected behavior — unit tests, acceptance tests, integration tests. Boundary against `runtime-behavior`: verification-contract encodes the intended behavior; runtime-behavior encodes the actual behavior. Boundary against `functional-requirement`: verification-contract validates specific scenarios; functional-requirement states the broader obligation.

### production-effective-value

The effective value of a parameter in a deployed environment, which may differ from the declared default or the value in any single configuration file.

### configuration-schema

Valid structure, allowed values, and constraints for configuration files.

### database-schema

The authoritative definition of tables, columns, indexes, and constraints.

### operational-procedure

How operators interact with the system — runbooks, escalation paths, recovery steps.

### security-policy

Security-relevant constraints — access control rules, encryption requirements, data classification mandates.

### documentation-metadata

Metadata fields attached to documentation assets (title, area, tags, related, etc.).

### unconfirmed-claim

A claim whose truth has not yet been verified through evidence.

### Resolution Matrix

| Claim type | Definition | Canonical source kind | Auxiliary evidence | Conflict destination | Notes or constraints |
|------------|-----------|----------------------|--------------------|---------------------|---------------------|
| architecture-decision | Adopted architectural decision in accepted ADR | `docs/10_adr/ADR-{NNN}-*.md` | Code, Test, Operational Observation | Known Issues | Does not grant code authority over adopted design (AC4) |
| functional-requirement | Normative requirement in an Accepted ADR or Registry-registered source | `docs/10_adr/ADR-{NNN}-*.md` or the Canonical Source Registry entry | Acceptance Test | Known Issues | No per-area `*_specification.md` is maintained |
| external-behavior | Observable system behavior for external consumers | Registry-registered source + Integration Test | Runtime Log, Test | Known Issues | |
| api-contract | Formal interface contract | Official API Schema or Contract | Integration Test | Known Issues | |
| runtime-behavior | Current execution-time behavior | Source under `scripts/` | Runtime Log, Test | Known Issues | Code authority does not extend to adopted design (AC4) |
| verification-contract | Executable assertions about expected behavior | `tests/` + the requirement source | ADR | Known Issues | Tests cannot silently redefine requirements (AC5) |
| production-effective-value | Effective parameter value in deployment | Deployed Configuration (`config/*.toml`) | Startup Diagnostics | Configuration Drift | |
| configuration-schema | Valid configuration structure and constraints | Configuration Schema | Configuration Validation | Configuration Drift | |
| database-schema | Tables, columns, indexes, constraints | Schema Generator or official DDL | Schema Test | Known Issues | |
| operational-procedure | Operator interaction guidance | Operations / Runbook | Operational Validation | Known Issues | |
| security-policy | Security constraints and mandates | Governance + Security Policy Spec | Audit Evidence | Known Issues | |
| documentation-metadata | Metadata on documentation assets | `docs/00_governance/governance_02_documentation-metadata.md` | Metadata Validator | Known Issues | |
| unconfirmed-claim | Unverified claim | Needs Confirmation inventory | Investigation Evidence | Needs Confirmation | |

Any rule for deciding whether documentation content is mechanically removable (verifiable from code, config, or schema alone) belongs in `governance_02_documentation-metadata.md`'s "Guidelines for Recording Information Verifiable via Implementation Reference" section — do not add a second, independently-worded rule here.

### Authority vs. Evidence

The "Canonical source kind" column identifies **authority** — the artifact whose word settles the question. The "Auxiliary evidence" column identifies **evidence** — supporting material that can confirm or challenge the authority's position. These are never interchangeable: evidence alone does not establish authority, and authority without evidence is incomplete.

### Multi-Type Documents

A single document may carry claims of more than one type. Classification is by claim, not by the document as a whole. For example, an ADR may contain both `architecture-decision` claims and `documentation-metadata` claims; each claim type is resolved independently using the row for that type.

### Decision Target Canonical Source Matrix

Defines which artifact is authoritative for each decision target, so Code is not
treated as the top canonical source for every kind of decision.

| Decision Target | Canonical | Auxiliary Evidence | Discrepancy Registration Target |
|-----------------|-----------|--------------------|----------------------------------|
| Adopted Architecture Decision | `docs/10_adr/ADR-{NNN}-*.md` | Code, Test, Operational Observation | Known Issues |
| Requirements | Accepted ADR or Canonical Source Registry entry | Acceptance Test | Known Issues |
| External Behavior | Canonical Source Registry entry | Acceptance Test | Known Issues |
| Current Runtime Behavior | Source under `scripts/` | Runtime Log, Test | Known Issues |
| Expected Behavior | `tests/` + the requirement source | ADR | Known Issues |
| Effective Value in Production | Deployed Configuration (`config/*.toml`) | Startup Diagnostics | Configuration Drift |
| DB Schema | Schema Generator or official DDL | Schema Test | Known Issues |
| API Contract | API Schema or official Contract | Integration Test | Known Issues |
| Operational Procedures | Operations / Runbook | Operational Validation | Known Issues |
| Unconfirmed Items | `governance_03_issue-and-uncertainty-management.md` | Investigation Evidence | Needs Confirmation |

**Code is canonical for current behavior, NOT for adopted design.** When code
contradicts an ADR, the ADR represents the intended architecture and the discrepancy
must be registered as a Known Issue. Each area's document-guide identifies the
canonical source within that area — this matrix provides cross-cutting guidance only.

Intended state (e.g., an ADR's adopted design) and observed state (e.g., current
runtime behavior) may both be documented simultaneously without one silently
overwriting the other. An automatic documentation change MUST NOT convert an
implementation deviation into an approved specification without explicit review.

### Recency Is Not Authority

Review date, modification date, commit date, and document recency do not determine canonical authority. Recency may be used only for the following purposes:

- Detecting staleness of non-canonical content during maintenance sweeps
- Prioritizing investigation of potential discrepancies
- Scheduling periodic review cycles
- Identifying which revision of a single file is newer

Recency must never be used for any of the following:

- Overriding an accepted ADR
- Overriding a canonical Specification
- Overriding an official API contract or schema
- Overriding deployed configuration
- Overriding an Operations runbook
- Promoting a Note or Reference to canonical status

## Area Canonical Maps (derived from Registry)

This section holds no hand-maintained per-area mapping table. The only
authoritative per-area mapping is the Canonical Source Registry below; do not
restate it here by hand.

### Canonical Source Registry

`config/documentation_canonical_sources.toml` is the system of record for
canonical-source ownership and the sole authoritative per-area mapping. Area guides (each area's own
"Canonical Source Rule(s)" section) must not maintain an independent,
hand-edited canonical-source mapping going forward — new or changed canonical
mappings are recorded in the registry, not restated by hand per area.

## Conflict Resolution Rule

When two documents contradict each other:

1. Identify the area(s) each document belongs to
2. Determine if both documents are in the same area — if so, consult the area's document-guide for the canonical source
3. If documents span different areas, identify the decision target the conflict concerns and apply the Decision Target Canonical Source Matrix (see `## Claim Type Taxonomy` > `### Decision Target Canonical Source Matrix`) to determine the authoritative source for that decision target
4. If neither rule resolves the conflict, register a Known Issue and defer resolution until the next review cycle

## Code vs Document Conflict Rule

When code contradicts a document, classify the conflict into one of five categories:

- **Outdated code** — Code has not been updated to reflect a recent design decision documented elsewhere
- **Design deviation** — Code intentionally deviates from the documented design (documented as such)
- **Provisional implementation** — Code implements a feature before formal documentation approval
- **Bug** — Code contains an error that produces behavior inconsistent with the documented intent
- **Missing documentation** — Code works correctly but no corresponding documentation exists

## Known Issues Registration Rule

Register a Known Issue when:

- A document-to-document conflict cannot be resolved using the Conflict Resolution Rule
- A code-vs-document conflict is classified as "design deviation" without documented justification
- A suspected bug requires investigation to confirm whether code or documentation is incorrect
- An unresolved conflict affects more than one area simultaneously

## Resolution Workflow

From detection to record-keeping:

1. Detect the conflict during normal review or through automated checks
2. Classify the conflict type using the rules above
3. Apply the appropriate resolution rule based on classification
4. Update affected documents or code to eliminate the conflict
5. Record the resolution in the relevant Known Issues document if applicable

### Routing Rules

When a canonical source conflict is detected, route it to exactly one destination:

1. **design-vs-code** → Known Issue — Design intent conflicts with current implementation behavior
2. **functional-requirement-vs-implementation** → Known Issue — Functional requirements contradict actual implementation
3. **Specification-vs-acceptance-test** → blocking Canonical Source Conflict — Specification claims conflict with acceptance test outcomes
4. **deployed-vs-approved config** → Configuration Drift — Deployed operational value differs from approved value
5. **undetermined intent** → Needs Confirmation — Cannot determine whether discrepancy reflects intentional design or omission
6. **missing canonical source** → design/governance gap — No authoritative source exists for the claim
7. **multiple normative sources** → blocking Canonical Source Conflict — Two or more normative sources disagree on the same decision target
8. **stale non-canonical wording only** → documentation-correction task — Only non-canonical documentation is stale; no code/config change needed

### Merge Conditions Extension

Canonical Source Conflict severity and blocking behavior:

- **Blocking**: Canonical Source Conflict severity is `High` when the conflicting source is a normative source; `Medium` when the conflicting source is a non-normative reference.
- **Non-Blocking**: Configuration Drift has no behavioral impact (already listed under Non-Blocking Conditions).

## Change Impact and Dependency Graphs

The Update Rule, Change Impact Rule, Change-Impact Matrix, RACI Model (the accountable-party model behind "RACI approval" in `## Merge Conditions` and `### ADR Acceptance Evidence Standard`), and the dependency-graph taxonomy (Software Runtime Dependency Graph, Deployment Management Graph, Documentation Reference Graph, Governance Applicability Matrix) are defined in [Change Impact and Dependency Graphs](governance_05_change-impact-and-dependency-graphs.md).

## Review Rule

The following conditions require review before merging:

- Any change to Governance-class documents
- Any change affecting more than three area documents simultaneously
- Any change that removes or renames a documented feature
- Any change that alters cross-area relationships or dependencies

## ADR Status Definitions

- `Proposed`: Under review, not yet adopted. A Proposed ADR is not a current
  architectural specification and must not be treated as one until it becomes
  Accepted.
- `Accepted`: Adopted and currently valid. An Accepted ADR is the current
  architectural specification for its decision.

### ADR Acceptance Evidence Standard

An ADR's `## Approval` > `### Approval Record` section satisfies the "RACI approval not
obtained from accountable party" Blocking Condition (see Merge Conditions) when either of
the following holds:

1. **Named Approval Record**: the section records a specific reviewer, approval date, and
   reference (e.g., a review ticket or PR) for that ADR.
2. **Task-level approval decision**: the accountable party (repository owner) issued an
   explicit instruction, given as part of a specific documented task, to set the ADR's
   Status to `Accepted`. That instruction is itself sufficient acceptance evidence; no
   separate named Approval Record is required.

Where an ADR relies on a task-level approval decision, its Approval Record section must
say so explicitly. It must not use `pending` for `Approved By` / `Approval Date` /
`Approval Reference` (`pending` asserts that acceptance evidence is still outstanding,
which is false once a task-level decision has been made), and must not fabricate a
reviewer name, date, or reference that was never given.

## ADR Change Protocol

When the current architectural decision changes, update the current Accepted ADR
directly rather than creating a new ADR. In the same change, update every
Specification, Reference, Operations document, and verification requirement that the
changed decision affects.

## ADR Section Header Standardization

All ADRs must use these section headers in order: Context (Problem, Constraints), Assumptions, Decision, Rationale, Alternatives Considered, Consequences (Positive/Negative), Invariants, Verification, Implementation Notes, Known Deviations, Review Triggers, Approval, Related Documents, Completion Checklist.

Duplicate notes shared across all ADRs:
- This chapter is not a basis for design decisions.
- If not applicable, write "Not applicable".
- Do not unconditionally align the ADR text with the current implementation; manage discrepancies as Known Issues.

The ADR list, dependency graph, and invariant verification matrix are maintained in
`adr-index.md`, not here.

## Merge Conditions

### Blocking Conditions (Prevent Merge)
- Critical open issue exists in affected area
- RACI approval not obtained from accountable party (for ADRs, see ADR Acceptance
  Evidence Standard for what counts as approval)
- Canonical source conflict unresolved
- Test suite failing

### Non-Blocking Conditions (Allow Merge with Warning)
- High-severity open issue exists in affected area
- Documentation outdated but code is correct
- Config drift detected but no behavioral impact
- Removed-name reintroduction detected by `check_compat_shims.py --check-removed-names` (`GV-020`), without an approved temporary exception (`docs/00_governance/governance_03_issue-and-uncertainty-management.md`)

### Merge Workflow
1. Check blocking conditions — if any fail, reject merge.
2. If non-blocking conditions exist, add warning to PR description.
3. Obtain RACI approval from accountable party.
4. Resolve canonical source conflicts before merging.
5. Verify test suite passes before merging.

## Maintenance Rules

- New ADRs must be created within one week of the decision being made
- "Proposed" ADRs must be reviewed quarterly
- "Needs confirmation" items must be reviewed quarterly
- Consumed by: [Documentation Checks](governance_04_documentation-checks.md)

## Non-Goals

This document does not cover:

- Source code review processes
- Testing strategy per area
- Individual area architectural decisions
- Document formatting conventions within Specification documents
- Defining how AI agents parse or use metadata fields
- Specifying enforcement mechanisms for metadata compliance
- Defining metadata for non-document assets (code, configuration files)

## Keywords

documentation
policy
governance
canonical source
ADR
conflict resolution
RACI
