---
title: "Security: Document Guide"
area: governance
tags:
  - security
  - document-guide
related:
  - 00_index.md
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
| MCP authentication setup | `mcp_06_14_mcp-authentication-setup.md` |
| Pre-production fail-open checklist | `mcp_06_13_pre-production-fail-open-checklist.md` |

## Canonical Sources

Canonical sources for this area are defined in the [Canonical Source Registry](../00_governance/governance_01_documentation-policy.md#canonical-source-registry): security constraints (`security-policy`) are normative in the Accepted security ADRs listed there. This area guide does not maintain an independent mapping. [System Security Architecture and Trust Boundaries](security_01_architecture-and-trust-boundaries.md) is an overview, not a canonical source.

## Known Issues / Deferred Items

Known limitations, specification gaps, and pending items are centrally managed in `governance_03_issue-and-uncertainty-management.md`. Do not duplicate them in individual chapters.

## Reference API

No reference APIs exist in this directory. All files are security policy/architecture documents.

## Keywords

- security
- document-guide
