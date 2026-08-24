---
title: "Governance Verification Matrix.Md"
area: governance
tags:
  - governance
related:
  - 00_index.md
  - 01_overview.md
---

# Governance Verification Matrix

## Purpose

This matrix maps governance rules to their enforcement methods, distinguishing auto-validated rules from Manual Review rules. It tracks whether each rule currently has an inspection tool and identifies follow-up work needed.

## Governance Verification Matrix

| Rule ID | Rule | Canonical Document | Enforcement Method | Tool or Review | Execution Timing | Blocking / Warning | Existing / Missing | Follow-up Issue |
|---------|------|--------------------|--------------------|----------------|------------------|--------------------|--------------------|-----------------|
| GV-001 | Required Front Matter | `00_governance_13_documentation-metadata.md` | Auto-validate | `check_doc_quality.py` | PR review | Blocking | Existing | None |
| GV-002 | Valid Document Status | `00_governance_13_documentation-metadata.md` | Auto-validate | `check_doc_quality.py` | PR review | Blocking | Existing | None |
| GV-003 | Unique ADR ID | `00_governance_12_documentation-policy.md` | Auto-validate | `check_doc_quality.py` | PR review | Blocking | Existing | None |
| GV-004 | Successor references for superseded ADRs | `00_governance_12_documentation-policy.md` | Auto-validate | `check_doc_quality.py` | PR review | Blocking | Existing | None |
| GV-005 | Existence of Related Documents | `00_governance_13_documentation-metadata.md` | Auto-validate | `check_doc_quality.py` | PR review | Warning | Existing | None |
| GV-006 | Self-reference prohibition | `00_governance_13_documentation-metadata.md` | Auto-validate | `check_doc_quality.py` | PR review | Blocking | Existing | None |
| GV-007 | Duplicate Related Link prohibition | `00_governance_13_documentation-metadata.md` | Auto-validate | `check_doc_quality.py` | PR review | Warning | Existing | None |
| GV-008 | Known Issue required fields | `00_governance_14_issue-and-uncertainty-management.md` | Auto-validate | `check_doc_quality.py` | PR review | Blocking | Existing | None |
| GV-009 | Needs Confirmation owner and deadline | `00_governance_14_issue-and-uncertainty-management.md` | Auto-validate | `check_doc_quality.py` | PR review | Warning | Existing | None |
| GV-010 | Deprecated name residual presence in current Specifications | `00_governance_14_issue-and-uncertainty-management.md` | Auto-validate | `check_doc_quality.py` | PR review | Warning | Existing | None |
| GV-011 | Duplicate canonical document specification | `00_governance_12_documentation-policy.md` | Manual Review | Human review | PR review | Warning | Missing | Register Known Issue |
| GV-012 | Multiple Primary Canonical Sources within the same area | `00_governance_12_documentation-policy.md` | Manual Review | Human review | PR review | Warning | Missing | Register Known Issue |
| GV-013 | References to non-existent canonical documents | `00_governance_12_documentation-policy.md` | Auto-validate | `check_doc_quality.py` | PR review | Warning | Existing | None |
| GV-014 | Code is NOT canonical for adopted design decisions | `00_governance_12_documentation-policy.md` | Manual Review | Human review | PR review | Warning | Missing | Register Known Issue |
| GV-015 | Software Dependency Graph and Documentation Reference Graph separation | `00_governance_12_documentation-policy.md` | Manual Review | Human review | PR review | Warning | Missing | Register Known Issue |
| GV-016 | No unimplemented auto-checks documented as implemented | `00_governance_15_documentation-checks.md` | Manual Review | Human review | Periodic audit | Warning | Missing | Register Known Issue |
| GV-017 | Resolved Issues/Needs Confirmations moved to Archive | `00_governance_14_issue-and-uncertainty-management.md` | Manual Review | Human review | Periodic audit | Warning | Missing | Register Known Issue |
| GV-018 | Glossary limited to project-specific terms | `00_governance_13_documentation-metadata.md` | Manual Review | Human review | Periodic audit | Warning | Missing | Register Known Issue |
| GV-019 | No unnecessary Metadata or Status fields added | `00_governance_13_documentation-metadata.md` | Manual Review | Human review | Periodic audit | Warning | Missing | Register Known Issue |
| GV-020 | Old Governance documents not used as current canonical sources | `governance-migration-mapping.md` | Manual Review | Human review | Post-migration audit | Warning | Missing | Register Known Issue |

## Auto-Validated Rules Summary

The following rules should be auto-validated wherever possible:

- GV-001: Required Front Matter
- GV-002: Valid Document Status
- GV-003: Unique ADR ID
- GV-004: Successor references for superseded ADRs
- GV-005: Existence of Related Documents
- GV-006: Self-reference prohibition
- GV-007: Duplicate Related Link prohibition
- GV-008: Known Issue required fields
- GV-009: Needs Confirmation owner and deadline
- GV-010: Deprecated name residual presence in current Specifications
- GV-013: References to non-existent canonical documents

## Manual Review Rules Summary

The following rules require manual review because they cannot be fully automated:

- GV-011: Duplicate canonical document specification
- GV-012: Multiple Primary Canonical Sources within the same area
- GV-014: Code is NOT canonical for adopted design decisions
- GV-015: Software Dependency Graph and Documentation Reference Graph separation
- GV-016: No unimplemented auto-checks documented as implemented
- GV-017: Resolved Issues/Needs Confirmations moved to Archive
- GV-018: Glossary limited to project-specific terms
- GV-019: No unnecessary Metadata or Status fields added
- GV-020: Old Governance documents not used as current canonical sources

## Follow-up Work Needed

Rules marked "Missing" in the Existing/Missing column need new inspection tools or processes:

1. **GV-011, GV-012**: Implement cross-document canonical source conflict detection
2. **GV-014**: Add ADR-vs-code contradiction detection to CI
3. **GV-015**: Separate dependency graph analysis by type
4. **GV-016**: Audit auto-check implementations against documentation claims
5. **GV-017**: Implement archive migration for resolved NC items
6. **GV-018**: Add glossary term classification validation
7. **GV-019**: Add metadata field usage policy enforcement
8. **GV-020**: Post-migration verification that old governance docs are not referenced as canonical

## Related Documents

Cross-cutting documentation rules and policies:

- [Documentation Policy](00_governance_12_documentation-policy.md)
- [Canonical Source Matrix](canonical-source-matrix.md)

## Keywords

governance
verification
auto-validation
manual review
CI
