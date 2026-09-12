# Implementation Procedure: Remove implementation-location mapping from docs/04_mcp_03_03_transport-and-health.md

## Goal

Remove "is defined in `{file}`" / "does not exist in that file" claims from the `HttpTransport` section of `docs/04_mcp_03_03_transport-and-health.md`, preserving responsibility-boundary content about class/component ownership without naming specific `.py` files.

## Scope

- **In-Scope**: Rewrite line 24's paragraph in `docs/04_mcp_03_03_transport-and-health.md` to remove file-path claims while keeping class/symbol responsibility content (`HttpTransport`, `ToolTransportInvoker`, `TransportError`).
- **Out-of-Scope**: The `full file tree` findings on lines 52-56 (tracked separately in `dcp008`). Any file other than `docs/04_mcp_03_03_transport-and-health.md`.

## Assumptions

- The current line numbering (line 24) remains accurate at time of implementation.
- The responsibility-boundary facts (which component instantiates `HttpTransport`, which imports `TransportError`) remain correct and unchanged.

## Design decisions

- Replace the file-path-heavy paragraph with one that uses class/symbol names (`HttpTransport`, `ToolTransportInvoker`, `TransportError`) instead of module paths (`shared/http_transport.py`, `shared/tool_executor.py`, etc.).
- If the remaining content no longer constitutes an "inconsistency", drop the "Inconsistency (Record of required fix)" heading and write as plain prose per `rules/coding.md` "Documentation notes — Current behavior classification".

## Alternatives considered

- Keep the "Inconsistency (Record of required fix)" framing if the remaining content still qualifies as an inconsistency after removing file-path claims.
- Fold the surviving responsibility-boundary content into plain prose without any special heading if it no longer represents an inconsistency.

## Implementation

### Target file

`docs/04_mcp_03_03_transport-and-health.md`

### Procedure

Rewrite the paragraph at line 24 to remove all "is defined in `{file}`" / "does not exist in that file" phrasing while preserving class/symbol responsibility content.

### Method

1. Locate the current paragraph at line 24 using `rg` or `grep` to confirm its position (do not rely solely on line number — line numbers may have shifted).
2. Extract the current paragraph text and identify all file-path claims ("is defined in `{file}`", "does not exist in that file").
3. Identify the responsibility-boundary content to preserve: which component instantiates `HttpTransport`, which imports `TransportError`, and which class/component owns which responsibility.
4. Rewrite the paragraph using class/symbol names only, without naming or claiming any specific `.py` file as the location where implementation is defined or does not exist.
5. Evaluate whether the "Inconsistency (Record of required fix)" framing still applies after removing file-path claims. If not, fold the surviving content into plain prose (no special heading).

### Details

**Current paragraph (line 24):**
> **Inconsistency (Record of required fix):** This section header was previously `shared/tool_executor.py`, but the actual implementation of the `HttpTransport` class is defined in `shared/http_transport.py` (Explicit in code). Instantiation and retention are handled by `shared/tool_transport_invoker.py`, while `shared/tool_executor.py` only imports the `TransportError` exception type from the same module. Although the module docstring of `shared/tool_executor.py` states "Provides HttpTransport implementation for POST /v1/call_tool over httpx.", the actual implementation does not exist in that file (Explicit in code).

**File-path claims to remove:**
- "was previously `shared/tool_executor.py`"
- "is defined in `shared/http_transport.py`"
- "handled by `shared/tool_transport_invoker.py`"
- "`shared/tool_executor.py` only imports"
- "the module docstring of `shared/tool_executor.py` states"
- "does not exist in that file"

**Responsibility-boundary content to preserve:**
- Which component/class instantiates `HttpTransport`
- Which component/class handles retention
- Which component/class imports `TransportError`
- The fact that `HttpTransport` provides POST `/v1/call_tool` over httpx

**Rewritten approach:** Use class/symbol names (`HttpTransport`, `ToolTransportInvoker`, `TransportError`) instead of module paths. If the remaining content no longer constitutes an "inconsistency", drop the "Inconsistency (Record of required fix)" heading and write as plain prose.

## Compatibility considerations

- The rewrite must not alter the semantic meaning of the responsibility-boundary information.
- The "Inconsistency (Record of required fix)" framing should be preserved only if the remaining content still qualifies as an inconsistency; otherwise it should be folded into plain prose per `rules/coding.md`.

## Security considerations

N/A: documentation-only change, no security impact.

## Rollback considerations

- Revert the paragraph back to its original state if the rewrite introduces unintended changes to the responsibility-boundary content.
- Verify against `skills/DESIGN.md` Docs content policy — retain to ensure the rewritten content does not inadvertently introduce new violations.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/04_mcp_03_03_transport-and-health.md | Documentation consistency check | `uv run python tools/check_docs_content_policy.py docs/04_mcp_03_03_transport-and-health.md` | Zero `implementation-location mapping` warnings |
| docs/04_mcp_03_03_transport-and-health.md | Domain consistency check | `uv run python tools/check_docs_consistency.py --domain mcp` | Pass (exit 0) |

## Completion criteria

- `uv run python tools/check_docs_content_policy.py` reports zero `implementation-location mapping` findings for `docs/04_mcp_03_03_transport-and-health.md` (REQ-003)
- `uv run python tools/check_docs_consistency.py --domain mcp` passes (REQ-004)
- The `HttpTransport` section still conveys which component owns instantiation and which exception type is consumed where, without naming a `.py` file (REQ-002)

## Out of scope

- The `full file tree` findings in the same file (lines 52-56) — see `dcp008`.
- Any file other than `docs/04_mcp_03_03_transport-and-health.md`.
- Editing any source code file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260913-072000 | 20260913-072100 | Rewrote paragraph to use class/symbol names; dropped "Inconsistency" framing since remaining content is plain prose |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260913-072100 | 20260913-072200 | Zero implementation-location mapping findings; domain consistency check passes |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: this document IS the documentation change |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260909-200213_dcp007_transport_health_implementation_location_mapping.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-065958_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-071713
- **Related target files**: docs/04_mcp_03_03_transport-and-health.md
