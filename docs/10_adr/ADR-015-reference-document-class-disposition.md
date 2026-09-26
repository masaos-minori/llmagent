---
title: "ADR-015: Reference Document Class Disposition"
area: governance
tags:
  - documentation
  - governance
  - reference
related:
  - ../00_governance/governance_01_documentation-policy.md
---

# ADR-015: Reference Document Class Disposition

## Keywords
<placeholder>

## Status

Accepted

使用可能なStatusは次のとおりとする。

- `Proposed`: 提案中、レビューまたは承認前
- `Accepted`: 採用済みであり、現行設計として有効

Accepted後に現在の判断を変更する場合は、本ADR本文を直接更新する。同じ変更の中で、影響を受けるSpecification、Reference、Operations文書および検証要件を更新する。

## Summary

`docs/governance_01_documentation-policy.md`'s Document Classification defines a "Reference" class (API/command/configuration reference material), but a proposed documentation-slimming policy's mechanical-content removal criteria conflict with hand-written Reference documents by design — their entire content is exactly the kind of code-derivable listing the policy wants removed. This ADR recommends treating Reference-class documents as generated artifacts (Option B), produced from source code via `tools/generate_reference_table.py`, rather than retiring the class or accepting continued drift.

## Context

### Problem

Without an explicit decision, mechanical-content removal work cannot proceed against Reference-class documents without first knowing whether their content should be deleted, generated, or left alone. Three options exist:

- **Option A**: Retire the Reference class; keep only canonical-source pointers.
- **Option B**: Treat Reference documents as generated artifacts (auto-produced from code/docstrings; hand-editing prohibited).
- **Option C**: Keep the status quo and accept drift between Reference documents and the code they describe.

`tools/generate_reference_table.py` already implements Option B's pattern for MCP/RAG/deployment reference tables (guard-commented blocks, format `<!-- AUTO-GENERATED: <generator>.py <purpose> -->`, e.g. `GUARD_START_MCP`/`GUARD_START_DEPLOYMENT`, refreshed from `config/agent.toml` and source).

### Constraints

- This ADR records the disposition decision only — it does not implement any generation tooling or edit any existing Reference document's content.
- `GV-021` (`tools/check_docs_content_policy.py`) documents an intent to exempt guarded, auto-generated content from its mechanical-content warnings, but that exemption must actually recognize the real guard-comment format before Option B's guarded blocks are usable without warning noise (tracked separately).

## Assumptions

- The existing `rag`/`mcp`/`deployment` generator pattern in `tools/generate_reference_table.py` is a working, adoptable precedent for Reference-class documents generally, not specific to those three domains.
- Extending that tool to new domains (Agent, EventBus, Memory) is separate follow-up work, gated on this ADR's outcome, not performed here.

## Decision

### Decision Details

Adopt **Option B**: Reference-class documents are treated as generated artifacts. Their content between guard comments is produced only by running the corresponding `tools/generate_reference_table.py --type <domain>` generator from current source — it MUST NOT be hand-edited between the guard comments. A Reference-class document may still carry surrounding hand-written prose outside the guarded block (e.g. an introduction or cross-references), but the mechanically-derivable listing itself is generated.

### Scope

Applies to any `docs/*.md` document classified `class: Reference` per `docs/governance_01_documentation-policy.md`'s Document Classification, once tooling exists to generate its content.

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

- Requires building new `tools/generate_reference_table.py` generator functions (Agent/EventBus/Memory, and any other domain with a Reference document) before migration can happen for those domains — tracked separately, not implemented by this ADR.
- `GV-021`'s guard-comment exemption must actually recognize the real `<!-- AUTO-GENERATED: <generator>.py <purpose> -->` format (a pre-existing bug where it only matches a literal bare string) before newly generated guarded blocks are exempt from mechanical-content warnings — tracked separately, not implemented by this ADR.

## Invariants

- A Reference-class document migrated to Option B has its guarded-block content produced only by its corresponding `tools/generate_reference_table.py --type <domain>` generator — it is never hand-edited between the guard comments.

## Verification

Run the corresponding `tools/generate_reference_table.py --type <domain>` generator and confirm the guarded block matches current source (`--dry-run` output equals the live-written content). No automated CI check enforces this invariant yet; it is manually verified when a generator is run.

## Implementation Notes

Agent (`docs/agent_13_reference-api.md`) and EventBus (`docs/eventbus_10_reference_api.md`)
have both been migrated to generated Reference-class status under Option B.

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

## Known Deviations

対象外 — no existing Reference-class document has yet been migrated to generated status under this decision.

ADR本文を現行実装へ無条件に合わせず、差異はKnown Issueで管理する。

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

This ADR reached `Accepted` via a Named Approval Record per the ADR Acceptance Evidence Standard (`docs/governance_01_documentation-policy.md`) — not the task-level fallback path.

## Related Documents

- [Documentation Policy](../00_governance/governance_01_documentation-policy.md) — Document Classification, ADR Section Header Standardization, ADR Acceptance Evidence Standard
- `tools/generate_reference_table.py` — existing Option B precedent (rag/mcp/deployment generators)
- `tools/check_docs_content_policy.py` — `GV-021`'s guard-comment exemption, currently mismatched against the real guard format (tracked separately)
- `plans/done/20260919-105034_plan.md` — the gated follow-up extending `tools/generate_reference_table.py` to Agent/EventBus/Memory

## Completion Checklist

ADRをAcceptedへ変更する前に確認する。

- [x] 解決する問題が明確である
- [x] Decisionが1つの主要な設計判断に絞られている
- [x] Decisionが必須、禁止、正本、Fallback条件などの明確な表現で記載されている
- [x] 採用理由が現在の実装以外の観点で説明されている
- [x] 実質的な代替案と不採用理由が記載されている
- [x] Positive Consequencesが記載されている
- [x] Negative Consequencesが記載されている
- [ ] Securityへの影響が評価されている（対象外 — 本ADRはガバナンス文書の分類方針のみを扱い、コードやランタイムに影響しない）
- [ ] Operations、Monitoring、Recoveryへの影響が評価されている（対象外 — 同上）
- [x] 検証可能なInvariantsが定義されている
- [x] Exceptionsまたは適用対象外が明確である
- [x] 各InvariantにVerificationが対応している
- [x] 自動化可能な検証がManual Reviewだけになっていない（現時点では自動検証なし。将来のCI統合はReview Triggers対象）
- [x] 現行実装との差異がKnown Issueへ登録されている（対象なし、Known Deviations参照）
- [x] Ownerと必要なReviewerが定義されている（Approval Record参照 — Named Approval Recordによりレビュー実施済み）
- [x] Review Triggersが記載されている
