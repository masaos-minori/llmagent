## Goal

Record the failure-class-by-phase matrix evidence and update the Automated Tests and Manual Review status/evidence text in `adr_02_004_environment-failure-handling-policy.md`, without changing any Decision or Invariant (`REQ-005`: refresh ADR-004's verification evidence so the status matches what is actually verified).

## Scope

Edit only the Automated Tests table cells for INV-06/INV-07, INV-10, and INV-15/INV-16 and the Manual Review fallback-audit subsection. No Decision, Invariant, Rationale, or Exceptions text changes.

## Assumptions

- Current ADR-004 still uses the same failure-class names (INV-06, INV-07, INV-10, INV-15, INV-16) as the plan; Phase 1 re-reads the current Invariants/Decisions before mapping (`UNK-01`).
- audit001's rewrite of ADR-004's posture-failure classification is reflected in the current live text.
- Existing tests already cover more failure classes than the `Partial` status suggests; the matrix starts from them rather than from zero.

## Design decisions

- Split each class's evidence by phase (Fail-Fast startup abort vs Fail-Closed runtime reject) instead of listing both together in one `Partial` cell — this separation is the gap this Plan closes.
- Record per-cell evidence as exactly one of three kinds — existing test reference, new test (added via additional-target-file-discovery), or reasoned manual-review fallback — and claim an evidence level only when a test or command output shows it.

## Alternatives considered

N/A: this is a docs-only status/evidence edit; there is no architectural, behavioral, or public-contract decision to make.

## Implementation
### Target file
`docs/10_adr/adr_02_004_environment-failure-handling-policy.md`

### Procedure
Replace the three Automated Tests status cells (INV-06/INV-07, INV-10, INV-15/INV-16) and the Manual Review fallback-audit subsection with the failure-class-by-phase matrix evidence and updated status, editing status/evidence text only.

### Method
1. Re-read the current ADR-004 Invariants/Decisions and audit001's rewrite (`plans/done/20261015-112526_plan.md`) to confirm the failure-class names match the current text (`REQ-001`, `UNK-01`).
2. Map each listed class (authentication, authorization, Allowlist, Safety Tier, Config Isolation, approval-control establishment, RuntimeToolRegistry init, duplicate tool ownership, required DB connection, safety/integrity) to its startup-validation symbol and to any existing test; classify each as Fail-Fast, Fail-Closed, or both (`REQ-001`).
3. Apply the automatability gate: mark each class automatable or manual. For each automatable class, identify the test file to create or extend; that file is an ADDITIONAL TARGET FILE added to the Plan through additional-target-file-discovery and re-frozen before any test is written — it is NOT a modification target of this document (`REQ-002`). Where a class cannot be reached through configuration-isolated fixtures without opening a production DB, record the manual reason instead.
4. Record the matrix (class x phase -> existing test / new test / manual-reason) in the Automated Tests table (`REQ-001`).
5. Add the partial-availability check across the matrix classes, or document why a class cannot be checked automatically (`REQ-003`, `AC-002`).
6. Record the REQ-004 fallback-audit decision (registry of permitted fallbacks vs keep manual release review) with its rationale in the Manual Review fallback-audit subsection; implement a registry/check only if its scope is bounded (`REQ-004`, `UNK-02`, `AC-003`).

### Details
Name the exact cells:
- Automated Tests table, INV-06/INV-07 row (current status `Partial (see adr_01_index.md)`): replace with the by-phase evidence — which classes abort at startup (Fail-Fast) via which test/symbol, which reject at runtime (Fail-Closed) via which test/symbol, and which remain manual with the reason.
- Automated Tests table, INV-10 row (current status `Partial (see adr_01_index.md)`): replace with the partial-availability check evidence (each matrix class yields a startup abort or runtime reject, never continued partial availability), or the documented reason per class.
- Automated Tests table, INV-15/INV-16 row (current status `Not verified (manual audit only; see Manual Review)`): replace with the REQ-004 decision — automated check present, or recorded manual-release-review decision with rationale.
- Manual Review section, fallback-audit subsection (current "Why not automated" + Procedure + Baseline + Classification of known paths): preserve the baseline classification as evidence; append the REQ-004 decision (registry vs keep manual) and its rationale; update Cadence/Owner if the decision changes them.

## Compatibility considerations

N/A: docs-only status/evidence edit; no code, config, or public-contract change.

## Security considerations

N/A: no secret, credential, or security-control change; status/evidence text only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target | Strategy | Tool | Expected |
|---|---|---|---|
| `adr_02_004` Automated Tests + Manual Review edit | Doc consistency | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py` | No warnings/errors; structure valid |
| ADR-004 status vs recorded evidence | Preservation | `uv run python tools/check_adr_preservation.py` | No ERROR (Decisions/Invariants unchanged) |

## Completion criteria

The INV-06/INV-07, INV-10, and INV-15/INV-16 status cells and the Manual Review fallback-audit subsection reflect the by-phase matrix evidence; no Decision or Invariant text changed; `check_adr_preservation.py` reports no ERROR.

## Out of scope

Any production code change; any Decision/Invariant/Rationale/Exceptions text change; ADR-010 fallback policy; new test files (handled as additional target files via separate plan amendment).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record the by-phase matrix in the Automated Tests table (status/evidence only) | Pending | — | — | REQ-005 |
| 2 | Update the Manual Review fallback-audit subsection with the REQ-004 decision | Pending | — | — | REQ-004 |
| 3 | Run check_adr_preservation, check_docs_quality, check_docs_structure | Pending | — | — | AC-004 |

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
- **Requirement ID**: `REQ-005` (refresh ADR-004's verification evidence)
- **Source issue**: `issues/20261016-125807_adr004_extend-adr-004-failure-policy-verification-coverage.md`
- **Source plan**: `plans/20261016-231246_plan.md`
- **Generated at**: 20261017-002628
- **Related target files**: `docs/10_adr/adr_02_004_environment-failure-handling-policy.md`
