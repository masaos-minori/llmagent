## Goal

Replace the stale "gated on idempotency-key presence" claim in the "Idempotency and retry"
section of `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` with the classification gate actually
being added to `HttpTransport.call()`, and state the corrected always-retry scope (REQ-005).

## Scope

- Rewrite the "Write-tool retry" bullet (current file L66: "a write-tool post-send retry is
  gated on idempotency-key presence ... read-tool retry is unchanged") to describe the
  failure-classification gate: pre-send errors (`httpx.ConnectError`, `httpx.ProxyError`) retry
  for every tool; post-send ambiguous `RequestError`s and the ambiguous statuses 502/503/504 are
  not retried for side-effecting tools; 429 keeps retrying for all tools; timeouts never retry.
- Keep the surrounding bullets (key ownership L61, server-side `_duplicate_cache`) intact; only
  the retry-scope wording changes.

## Assumptions

- The doc update lands AFTER `20261028-004925_01` so the documented behavior matches shipped
  code (AC-5 requires comment/doc/code to describe the same gate).
- `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` is a high-churn file also targeted by sibling
  plan `plans/20261027-103047_mcpinv002_remove-dead-check-startup-mode-guard.md` (recorded by
  `tools/check_plan_target_overlaps.py`); the two plans edit different sections of the file —
  re-read the section before editing and rebase if another plan's doc change landed first.
- English doc content per `skills/DESIGN.md` Output language (repo docs convention), regardless
  of chat language.

## Design decisions

- Single-bullet replacement inside the existing "Idempotency and retry" section (L57-66) rather
  than a new subsection: the section already carries the key-ownership and server-cache facts;
  the retry-scope bullet is the only stale claim (plan Implementation Target Files row).
- The corrected bullet must name the safe set and the gated statuses explicitly so a reader can
  predict attempt counts without reading the transport source.

## Alternatives considered

- Deleting the bullet entirely: rejected — the retry scope is exactly what callers of
  side-effecting tools need to know; the plan row requires documenting the new layer alongside
  the server cache.
- Moving the gate description to `docs/22_mcp/mcp_03_03_transport-and-health.md`: rejected —
  mcpinv001's target row names `mcp_03_01` (the idempotency/dispatch doc); mcpinv003's
  message-shape change is what belongs in `mcp_03_03` (its own target row).

## Implementation

### Target file

`docs/22_mcp/mcp_03_01_dispatch-and-routing.md`

### Procedure

1. Locate the "### Idempotency and retry" section (L57) and its "Write-tool retry" bullet (L66).
2. Replace the L66 bullet with wording of this shape:
   ```markdown
   - **Write-tool retry:** side-effecting tools (the transport's `_WRITE_TOOLS`, mirroring the
     dispatch layer's write set) are retried only on pre-send connection failures
     (`httpx.ConnectError`, `httpx.ProxyError`) and on `429`; post-send ambiguous request errors
     and ambiguous statuses `502`/`503`/`504` raise `TransportError` immediately
     (fail-closed, ADR-004) because the server may already have executed the write. Read-tool
     retry is unchanged. Timeouts are never retried for any tool. `call()` always emits a
     per-call key, so retried writes keep a stable identity.
   ```
3. Confirm no other bullet in the section contradicts the new wording (server-side
   `_duplicate_cache` bullet stays; add no new claims beyond REQ-001/REQ-002 behavior).

### Method

Targeted Markdown edit of one bullet; preserve surrounding list structure and heading.

### Details

- Terms to match the code exactly: `_WRITE_TOOLS` (scripts/shared/http_transport.py L34),
  statuses `429/502/503/504` (transport `_RETRYABLE_STATUS` L112), exception class names as in
  the REQ-001/REQ-002 gate.
- The removed gate's phrasing ("gated on idempotency-key presence") must not survive anywhere
  in the file (AC-5 grep gate).
- Do not restate ADR-004 here; link/reference only, consistent with the file's existing style.

## Compatibility considerations

- Documentation-only change: no tests reference this file's prose except the docs-consistency
  checks wired through `tools/check_docs_consistency.py` per `routing.md`; run the 22_mcp domain
  documentation consistency check from `rules/toolchain.md` after the edit.
- Sequencing with sibling plans: implement after mcpinv003's `mcp_03_03` doc edit is irrelevant
  to this file (different doc), but implement after `20261028-004925_01` (same plan's code row).
  If mcpinv002's doc edit lands first, rebase this edit onto the updated file.

## Security considerations

- None beyond accuracy: the doc currently advertises a safety gate that does not exist; leaving
  it invites false confidence in write-retry safety.

## Rollback considerations

- `git checkout -- docs/22_mcp/mcp_03_01_dispatch-and-routing.md` restores the prior text; if
  rolled back together with `20261028-004925_01`, the file returns to describing the
  (reinstated) always-retry policy — acceptable as a unit revert.

## Validation plan

- 22_mcp documentation consistency check per `rules/toolchain.md`
  (`tools/check_docs_consistency.py` domain run).
- Manual review: bullet matches shipped `HttpTransport.call()` behavior line-by-line
  (REQ-001/REQ-002/REQ-003/REQ-004 classes and statuses enumerated identically).
- `grep -n "idempotency-key presence" docs/22_mcp/mcp_03_01_dispatch-and-routing.md` returns
  nothing (stale claim removed, AC-5).

## Completion criteria

- L66 bullet describes the classification gate with the exact safe set, gated statuses, 429
  exception, and read-tool/timeouts invariance.
- Stale key-presence claim absent from the file.
- Documentation consistency check for the 22_mcp domain passes.

## Out of Scope

- Other sections of `mcp_03_01` (routing, startup modes) — untouched.
- `docs/22_mcp/mcp_03_03_transport-and-health.md` (owned by mcpinv003's target row).
- Any `scripts/` or `tests/` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | After 20261028-004925_01 ships |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation file (plan row) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | 22_mcp docs consistency check |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This document is the docs row |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261027-001245_mcpinv001_mcp-write-idempotency-backstop.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-102512_mcpinv001_mcp-write-idempotency-backstop.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-004925
- **Related target files**: docs/22_mcp/mcp_03_01_dispatch-and-routing.md
