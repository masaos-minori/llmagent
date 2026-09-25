---
title: "Security: Document Guide"
area: governance
tags:
  - security
  - document-guide
related:
  - ../00_index.md
  - overview_00_document-guide.md
---
# Security: Document Guide

## Purpose

This directory contains security-related documentation including system security architecture, trust boundaries, and high-risk tool policies. Use it when implementing, auditing, or reviewing security controls.

## Reading Order

| Category | File |
|---|---|
| System Security Architecture & Trust Boundaries | `security_01_architecture-and-trust-boundaries.md` |
| High-Risk Tool Common Policy | `security_02_high-risk-tool-common-policy.md` |

## AI Query Routing

| Question | Rule |
|---|---|
| Security architecture & trust boundaries | `security_01` |
| High-risk tool policy | `security_02` |
| Access control & allowlists | `mcp_05_01_access-control-and-allowlists.md` |
| Fail-open/fail-closed risk tiers | `mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` |
| Auth profiles & sandboxing | `mcp_05_02_auth-profiles-and-sandboxing.md` |
| MDQ enforcement & lockdown | `mcp_05_05_mdq-enforcement-and-lockdown.md` |
| Local-to-production auth migration | `mcp_06_17_local-to-production-auth-migration.md` |
| Pre-production fail-open checklist | `mcp_06_16_pre-production-fail-open-checklist.md` |

## Canonical Source Rule

See [System Security Architecture and Trust Boundaries](/home/sugimoto/llmagent/docs/91_security/security_01_architecture-and-trust-boundaries.md) for the primary security architecture overview.

## Known Issues / Deferred Items

Known limitations, specification gaps, and pending items are centrally managed in `governance_03_issue-and-uncertainty-management.md`. Do not duplicate them in individual chapters.

## Reference API

No reference APIs exist in this directory. All files are security policy/architecture documents.

## Related ADRs

- [ADR-008](/home/sugimoto/llmagent/docs/10_adr/ADR-008-sqlite-4db-separation.md) — SQLiteを4DBへ分離する
- [ADR-013](/home/sugimoto/llmagent/docs/10_adr/ADR-013-eventbus-authentication-authorization.md) — EventBus認証認可
- [ADR-015](/home/sugimoto/llmagent/docs/10_adr/ADR-015-reference-document-class-disposition.md) — Reference document class disposition

## Related Documents

- `security_01_architecture-and-trust-boundaries.md`
- `security_02_high-risk-tool-common-policy.md`
