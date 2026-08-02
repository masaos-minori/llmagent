# Remove verbatim Pydantic model/dataclass field transcription in docs/04_mcp_02_01

## Priority
Low

## Summary
`docs/04_mcp_02_01_endpoints-and-transport.md` transcribes Pydantic model and dataclass definitions directly into the document body — content that is code, not design intent.

## Reason for Change
Type definitions are code-derived detail that goes stale whenever a field changes; the source code is the authoritative definition and does not need duplication here.

## Implementation Intent
Remove the verbatim model/field transcription, keeping only file/class-name references and the design-relevant notes (correlation-key table, `health()`'s fixed `deps={}` behavior, etc.) that aren't derivable by simply reading the class definition.

## Target Files or Areas
`docs/04_mcp_02_01_endpoints-and-transport.md`

## Required Changes
- Remove the verbatim Pydantic model/dataclass field listings.
- Keep the correlation-key table and the `health()` fixed-`deps={}` note (or any other design-intent content not visible from the class definition alone).
- Replace removed content with a reference to the class name/file path only.

## Acceptance Criteria
The file no longer transcribes model fields verbatim; design-intent content (correlation keys, health() behavior notes) remains.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/04_mcp_02_01` shortened; no information lost (source remains authoritative for field-level detail).

## Out of Scope
Do not change the actual Pydantic models/dataclasses in this issue — documentation only.

## AI Implementation Instruction
Read the file fully before removing content, to correctly separate "code transcription" (remove) from "design intent not visible in code" (keep) — do not remove the correlation-key table or the health() note by mistake.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §1 (コード説明に寄りすぎている領域), §2 削除候補 item 3
- Generated at: 2026-08-02
