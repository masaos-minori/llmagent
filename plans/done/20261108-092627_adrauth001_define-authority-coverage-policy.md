## Goal
- Document in ADR-016 whether `config/adr_authority.toml` registration is comprehensive or selective, define when a decision target must be registered, keep coverage rules separate from the primary-authority uniqueness rules, and record an explicit decision, with rationale, on whether the authority model needs a target governing itself.

## Priority
Low

## Scope
- **In-Scope**: edits to ADR-016 only: Decision Details (coverage rules separated from uniqueness and registration-duty rules), a statement of the current coverage as verified, the inclusion criteria, the self-governance decision with rationale and a revisit trigger, and the Verification note on what the checkers do and do not cover.
- **Out-of-Scope**: authority model redesign; registering any additional ADR or decision target without an approved decision; changes to `config/adr_authority.toml`, the generated index sections, or the validators (not required by the recommended decision); invariant evidence registry changes; adding or rewording an invariant.
- **Dependencies**: shared governance wording is coordinated with `plans/20261108-093000_adrdoc001_separate-adr-current-history.md`, with no required order: that Plan adds an ADR responsibility rule to `governance_01` and references, without restating, the authority rules that stay in ADR-016, while this Plan edits ADR-016 only, so the two touch different files. No dependency on another Plan; no other Plan or Issue targets ADR-016 (overlap tool checked in Step 8b).

## Background
Verified against the current files and validators (checked in Step 2):
- ADR-016 Decision Details item 1 requires exactly one `primary_adr` per governed target in `config/adr_authority.toml`; item 8 requires a registry change whenever an ADR is added, its `related` list changes, or a governed target's authority changes. The ADR contains no statement about whether registration must cover every decision (no occurrence of "comprehensive", "selective", or a completeness rule; checked by search).
- The registry holds 14 `[[authority]]` entries (`decision_target` plus `primary_adr`); its header comment says it was transcribed on 2026-10-30 from the prose authorities in `docs/10_adr/adr_01_index.md`. The primaries are ADR-001, -003, -005, -006, -007, -008, -010, -012, -013, -014 and -015. ADR-002, ADR-004, ADR-009 and ADR-016 are primary of no target; ADR-004 appears only as a supplemental entry with a limit.
- No registered target governs the authority model (ADR-016) itself.
- The generated index text states that "ADR-002 owns the isolation decision" and that ADR-004 "defines the failure-classification contract" (Intentional Circular References), yet neither topic is a registered decision target, so the uniqueness check cannot detect a competing claim on them.
- `uv run python tools/check_adr_authority.py` reports "Authority model OK: no findings" and `uv run python tools/generate_adr_authority.py --check` reports "No drift found" on the current tree (Operationally observed), so no dependency cycle or duplicate primary exists today. Neither validator checks coverage; their finding codes are `DUP_PRIMARY`, `DANGLING_ADR`, `AUTHORITY_CYCLE`, `ASSUMPTION_DRIFT`, `EDGE_UNKNOWN_TYPE`.

## Problem
Uniqueness and completeness are different properties. A registry can have one primary per registered target while intentionally covering only some decisions. Without a stated policy, a contributor can assume every ADR needs a target or omit an important decision without knowing it. The absence of a self-governance target is not by itself a confirmed violation, and the omission of the isolation and failure-classification topics is a coverage question, not a duplicate-primary defect.

## Reason for Change
A stated policy prevents inconsistent registration over time. Self-governance registration may add clarity but can also add metadata or cycles without a defined purpose. It is Low because it is a non-blocking governance clarification with no present defect.

## Implementation Intent
Establish and document the intended coverage, define inclusion criteria, and separate the coverage rules from the uniqueness rules in ADR-016. Record the self-governance decision with rationale. The recommendation, to be confirmed by the repository owner before the policy text is written, is: selective registration; a target is registered when authority over a topic must be machine-checked because the index designates a primary authority for it or more than one ADR makes a normative claim on it; no self-governance target while no other ADR can claim the authority model, with a revisit trigger when one can. Change configuration, generated content and validators only if the owner's decision requires it; the recommended decision requires none.

## Requirements
- `REQ-001`: ADR-016 states the verified current coverage of the registry: registration is selective in practice, it was derived from the index prose, and the registry does not claim to cover every decision of every ADR; no per-ADR inventory is copied into the ADR.
- `REQ-002`: The coverage rules and the uniqueness rules are separate Decision Details items; the registration-duty item references both; invariant identifiers and text are unchanged.
- `REQ-003`: ADR-016 defines the inclusion criteria so a contributor can tell when registration is required, written according to the owner's decision on coverage intent.
- `REQ-004`: ADR-016 records the decision on whether the authority model has its own decision target, with its rationale and a revisit trigger, without describing a missing self-registration as a defect.
- `REQ-005`: The ADR Verification section states what the checkers verify (uniqueness, acyclicity, generated-section drift, front matter consistency) and that coverage is not machine-checked; the Plan's report records the cycle and assignment check results and lists candidate unregistered topics for a separate decision.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | ADR authority model | Separate coverage from uniqueness, state current coverage, add inclusion criteria, record the self-governance decision and the Verification note | `REQ-001` to `REQ-005` / AC-01 to AC-06 | Decision Details items 1 and 8 at L57-L66, Invariants at L118-L124, Verification at L126-L130; no coverage language (checked in Step 2); registry header and 14 entries in `config/adr_authority.toml` (checked in Step 2) | `tools/check_adr_authority.py`, `tools/generate_adr_authority.py --check` (checkers, run unchanged) | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `config/adr_authority.toml` | The registry whose coverage is described; header comment states its origin | `REQ-001` |
| `docs/10_adr/adr_01_index.md` | Prose authorities and the generated Authority Graph and Intentional Circular References sections | `REQ-001`, `REQ-005` |
| `tools/check_adr_authority.py` | Defines what the validator checks, to state what it does not | `REQ-005` |
| `tools/generate_adr_authority.py` | Generator of the index sections; confirms no regeneration is needed | `REQ-005` |
| `tools/_adr_authority_core.py` | Shared validator core (finding codes) | `REQ-005` |
| `docs/00_governance/governance_01_documentation-policy.md` | Defines the task-level approval decision used to record the owner's choice | `REQ-003`, `REQ-004` |

## Acceptance Criteria
- AC-01 (`REQ-001`): ADR-016 states that registration is selective and how the registry was derived, with no per-ADR inventory.
- AC-02 (`REQ-002`): Coverage and uniqueness are separate Decision Details items; `check_adr_preservation.py` reports no ERROR (invariants unchanged).
- AC-03 (`REQ-003`): A contributor can decide from the ADR text alone whether a new decision requires a registry entry.
- AC-04 (`REQ-004`): The self-governance decision and rationale are present, state the revisit trigger, and do not call the omission a defect.
- AC-05 (`REQ-005`): The Verification section lists what the checkers verify and says coverage is not machine-checked; the report records the validator results and the candidate unregistered topics.
- AC-06: `check_adr_authority.py` and `generate_adr_authority.py --check` still pass; the documentation checkers pass; `config/adr_authority.toml` and the index are unchanged unless the owner's decision requires otherwise (then a Plan amendment is made first).

## Tests
- Documentation-only; no new test. `uv run python tools/check_adr_authority.py` and `uv run python tools/generate_adr_authority.py --check` run once to confirm the model and index stay valid (`REQ-001`, `REQ-005`).
- If the owner's decision requires a validator change, a Plan amendment adds the focused tests and follows `rules/toolchain.md` before any tool is edited.

## Documentation Impact
Yes. ADR-016 coverage policy and rationale (located through `docs/10_adr/adr_01_index.md`). The generated index sections change only through `tools/generate_adr_authority.py` and are not expected to change. Driven by `REQ-001` to `REQ-005`. English only.

## Assumptions
- Selective registration is the intended coverage (falsifiable by an owner decision for comprehensive registration, which would be a scope change and needs a Plan amendment before any registry edit).
- The current registry content is correct for the targets it holds; this Plan does not audit their primaries.
- Phase 1 states only verified facts and needs no owner decision; Phase 2 states a decision and starts only after the owner confirms it (see UNK-01 and UNK-03).
- ADR-016 is 14192 bytes, under the 24576-byte size limit, so the additions fit if they stay concise.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The intended coverage (comprehensive or selective) | An owner decision | Owner confirms the recommendation (selective) before Phase 2; comprehensive coverage becomes a separate scope change | False |
| UNK-02 | Whether the topics named as owned in the index prose but not registered (configuration isolation, failure classification, FTS5 text separation) should become decision targets | An owner decision and a per-topic primary assignment | Reported as candidates only; registration is a separate Issue after the owner decides | False |
| UNK-03 | Whether a self-governance target serves a concrete purpose | An owner decision; no competing claimant to ADR-016's authority is known | Owner confirms the recommendation (no target now, with a revisit trigger) before Phase 2 | False |
| UNK-04 | Shared governance wording with `plans/20261108-093000_adrdoc001_separate-adr-current-history.md`, which is open | Implementation status of that Plan | Coordinate the wording so ADR-016 stays the single owner of authority rules; no required order (recorded in `Scope`) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Classification: Path A (1 target file, no interface or schema change); architecture, dependency, historical and operational analyses are skipped. Direct verification of consumers: `tools/check_adr_authority.py`, `tools/generate_adr_authority.py` and `tools/check_adr_reference.py` read `config/adr_authority.toml` and the ADR front matter, not the ADR-016 prose, so editing the prose changes no tool input (checked in Step 3). Validation quality baseline: `N/A: no Python target`.

Decisions:
1. Invariants stay unchanged and no new invariant is added: a coverage rule is a Decision Details item verified by review, so the preservation checker reports no ERROR and no new matrix row is required.
2. The coverage policy is selective, because the registry already covers only the targets the index prose named, comprehensive registration is forbidden by the Issue, and a registry entry without a competing claimant adds a registration duty without detection value.
3. The self-governance target is not added now: uniqueness cannot fail for a topic no other ADR claims, ADR-016's own invariants and the validators already enforce the model, and a self-edge would add metadata and a possible cycle without a defined purpose. The revisit trigger is a second ADR making a normative claim on the authority model.
4. The unregistered topics found in verification are reported as candidates, not registered, per the Issue's constraint.

## Implementation steps
1. **Phase 1: Facts and structure** (no owner decision needed)
   - [ ] Separate the coverage rules from the uniqueness rules and state the verified current coverage (`REQ-001`, `REQ-002`; `docs/10_adr/adr_02_07_016_adr-authority-model.md`)
   - [ ] Add the Verification note on what the checkers cover (`REQ-005`; same file)
2. **Phase 2: Decision text** (starts only after the owner confirms UNK-01 and UNK-03)
   - [ ] Write the inclusion criteria (`REQ-003`; same file)
   - [ ] Record the self-governance decision, rationale and revisit trigger (`REQ-004`; same file)
3. **Phase 3: Verification**
   - [ ] Run the Validation plan commands and record the cycle and assignment results and the candidate topics (`REQ-001` to `REQ-005`; same file). No deploy step: no `scripts/` or `config/` file changes.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| Authority model | Model validation | `uv run python tools/check_adr_authority.py` | `Authority model OK: no findings` |
| Index generated sections | Drift check | `uv run python tools/generate_adr_authority.py --check` | `No drift found` |
| ADR-016 | Front matter consistency | `uv run python tools/check_adr_reference.py` | No findings |
| ADR-016 | Preservation, structure, invariant matrix | `uv run python tools/check_adr_preservation.py`; `uv run python tools/check_adr_structure.py`; `uv run python tools/check_adr_invariant_matrix.py` | No ERROR; invariants unchanged |
| ADR-016 | Documentation quality, policy, language | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py docs/10_adr/adr_02_07_016_adr-authority-model.md`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_japanese.py` | No findings |

## Risks
- **Risk**: The owner chooses comprehensive coverage after Phase 1 is written → **Mitigation**: Phase 1 states only facts and Phase 2 waits for the decision; a comprehensive decision is a scope change handled by a Plan amendment before any registry edit.
- **Risk**: The policy text is read as a requirement that the unregistered topics (isolation, failure classification) be registered now → **Mitigation**: the ADR states the criteria without a retroactive duty, and the topics are reported as candidates in a separate Issue.
- **Risk**: A new Decision Details item is read as a new architectural decision without approval → **Mitigation**: the item records the owner's confirmed choice under the task-level approval decision of `governance_01`, and Phase 2 does not start before that confirmation.
- **Risk**: Wording diverges from the `adrdoc001` change to governance text → **Mitigation**: coordinate through UNK-04 and sequence the edits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Facts and structure | Completed | — | 20261108-114358 |  |
| 2 | Decision text | Completed | — | 20261108-121925 |  |
| 3 | Verification | Completed | — | 20261108-121925 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261108-111727_01_docs_10_adr_adr_02_07_016_adr-authority-model.md.md | 1 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261107-050706_adrauth001_define-authority-coverage-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-092627
- **Related target files**: `docs/10_adr/adr_02_07_016_adr-authority-model.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; registry header; ADR-016 L57-L66 | `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Phase 1 | AC-01 | Full read-through; `check_docs_content_policy.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 3; ADR-016 Decision Details items 1 and 8 | `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Phase 1 | AC-02 | `check_adr_preservation.py`; `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 2; Unresolved Questions (coverage intent) | `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Phase 2 | AC-03 | Full read-through | Needs confirmation |
| REQ-004 | Required Changes 4; Unresolved Questions (self-governance) | `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Phase 2 | AC-04 | Full read-through | Needs confirmation |
| REQ-005 | Required Changes 5-6; validator runs in Step 2 | `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Phase 1, Phase 3 | AC-05, AC-06 | `check_adr_authority.py`; `generate_adr_authority.py --check`; `check_adr_reference.py` | Confirmed by repository evidence |