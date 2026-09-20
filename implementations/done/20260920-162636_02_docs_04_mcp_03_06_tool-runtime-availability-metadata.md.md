## Goal
Remove the full JSON `/v1/tools` response example (lines 52-69) in
`docs/04_mcp_03_06_tool-runtime-availability-metadata.md`, per `REQ-002` (Plan
`plans/20260920-160121_plan.md`), so `tools/check_docs_content_policy.py` reports no
finding at this location while the "Always returns every implemented tool" prose rule
and the existing per-server handler-function list are preserved.

## Scope
In scope: the JSON example block under "## 4. `/v1/tools` behavioral rules" (lines
52-69) only. Out of scope: every other section of this file — the `disabled_reason`
value table (lines 38-44), the Field Mapping table (lines 83-86), the `disabled_code`
table (lines 125-131), and all ADR-003 cross-reference sections — none of these were
flagged by `check_docs_content_policy.py` (re-confirmed 2026-09-20). Also out of scope:
the pre-existing missing `## Related Documents`/`## Keywords` sections — a
`check_docs_structure.py` finding recorded in the Plan as pre-existing, not part of
`REQ-002`.

## Assumptions
The finding at line 52 and the file's exact current content (re-verified via Read
during this document's creation) have not shifted since the Plan was frozen — no
commit has touched this file since.

## Design decisions
Remove the JSON example entirely and keep the existing prose sentence at line 50
("Always returns every implemented tool; disabled tools are never omitted from the
response.") unchanged, immediately followed by a new one-sentence pointer noting that
each tool entry carries `config_dependent`/`enabled`/`disabled_reason` and referring to
each server's own `/v1/tools` handler (already named in section 3's "Implemented:"
paragraph at line 46) for the exact response shape — reusing that existing reference
rather than inventing a new one.

## Alternatives considered
- Point to a single handler file as "the" canonical source: rejected — Step 3's
  inspection of the source Issue and this file confirmed the response shape is
  produced independently by 8 different servers' own `/v1/tools` handlers (already
  enumerated in line 46's "Implemented:" sentence), so naming only one would be
  misleading about the other seven.
- Shrink the JSON example to a single field instead of removing it: rejected — any
  literal JSON payload snippet reproduces the exact finding pattern
  (`check_docs_content_policy.py`'s full-JSON-payload-example detection), regardless of
  size.

## Implementation
### Target file
`docs/04_mcp_03_06_tool-runtime-availability-metadata.md`

### Procedure
1. Read lines 48-70 to confirm current content matches the Plan's recorded evidence.
2. Remove the JSON code block (lines 52-69), keeping the "## 4. `/v1/tools` behavioral
   rules" heading and the line 50 sentence unchanged.
3. Immediately after line 50's sentence, add one sentence stating that each tool entry
   carries `config_dependent`, `enabled`, and `disabled_reason`, and pointing to each
   server's own `/v1/tools` handler (see section 3's existing "Implemented:" list) for
   the exact response shape.
4. Leave every other section of this file unchanged.

### Method
Single localized `Edit`, replacing the JSON code block (lines 52-69) and inserting the
new pointer sentence in its place. Do not touch line 46's existing handler-function
list or any other line.

### Details
Do not reproduce any JSON field/value pair from the removed example (`git_status`,
`config_dependent: true`, `disabled_reason: "read_only=true"`, etc.) — the exact field
names are already documented in the `disabled_reason` value table (lines 38-44, not
flagged, out of scope) and the Field Mapping table (lines 83-86, not flagged, out of
scope); this edit does not need to restate them again.

## Compatibility considerations
`N/A: documentation-only change, no code, public interface, or data format is affected`.

## Security considerations
`N/A: no security-relevant content is touched`.

## Rollback considerations
Revert via `git checkout` on this one file. The edit is independently revertable from
the other four Plan rows' files.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` — confirm zero findings for
  `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` (Plan `AC-2`).
- `uv run python tools/check_docs_quality.py`, scoped to this file — confirm no new
  warning is introduced.
- `uv run python tools/check_docs_structure.py docs/04_mcp_03_06_tool-runtime-availability-metadata.md`
  — confirm the finding count does not exceed the pre-existing missing `## Related
  Documents`/`## Keywords` findings already recorded in the Plan.
- `uv run python tools/check_docs_consistency.py --domain mcp` — confirm no new drift
  finding.

## Completion criteria
The JSON response example is gone; the "Always returns every implemented tool" prose
rule is unchanged and immediately followed by a pointer to each server's own `/v1/tools`
handler; `check_docs_content_policy.py` reports zero findings for this file.

## Out of scope
- Every other section of this file (see Scope) — not flagged, not part of `REQ-002`.
- The pre-existing missing `## Related Documents`/`## Keywords` sections — tracked in
  the Plan as a pre-existing, out-of-scope structural finding.
- Any other `docs/*.md` file — see the Plan's other four target-file rows, each with
  its own implementation procedure document.
- Extending `check_docs_content_policy.py`'s detection rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-170156 | 20260920-170156 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260920-170156 | 20260920-170156 | N/A: documentation-only, no automated test beyond the doc checkers already listed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-170156 | 20260920-170156 | Scoped to the doc checkers in Validation plan, not the full Python toolchain (no `scripts/` change) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-170156 | 20260920-170156 | N/A: this document IS the documentation change |

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
- **Requirement ID**: `REQ-002` — remove the full JSON `/v1/tools` response example
- **Source issue**: issues/20260920-154352_dcp010_mcp-docs-content-policy-cleanup-batch-2.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-160121_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-162636
- **Related target files**: docs/04_mcp_03_06_tool-runtime-availability-metadata.md