## Goal
Replace `docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md`'s
`agent.toml` `[mcp_servers.*]` field/type/default table (lines 22-36) with a pointer to
`scripts/shared/mcp_config.py::McpServerConfig`, per `REQ-004` (Plan
`plans/20260920-160121_plan.md`), so `tools/check_docs_content_policy.py` reports no
finding at this table's location, while the "Ownership" note above it and the
security-relevant `env` denylist information embedded in the table are both preserved.

## Scope
In scope: the `## Agent-side MCP fields` table (lines 20-36) only. Out of scope: the
"Ownership" note (lines 15-16), the `tool_names`/`role`/deprecation/`key`/
`startup_mode="none"` prose paragraphs (lines 38-46), the "Validation Rules" list
(lines 48-50), and every other section of this file — none of these were flagged by
`check_docs_content_policy.py` (re-confirmed 2026-09-20).

## Assumptions
The finding at line 22 and the file's exact current content (re-verified via Read
during this document's creation) have not shifted since the Plan was frozen — no
commit has touched this file or `scripts/shared/mcp_config.py` since.

## Design decisions
Step 3a's verification found the table contains one piece of content that is not
purely code-derivable and is not restated anywhere else in this file: the `env`
field's row states that `LD_PRELOAD`/`LD_LIBRARY_PATH`/`PYTHONPATH` are rejected via a
denylist — a security-boundary design decision (which environment variables are
blocked from subprocess injection), not a field/type/default fact. This refines the
Plan's `REQ-004` scope: the table is replaced with a canonical-source pointer, but the
`env` denylist sentence is carried forward as standalone prose rather than being
dropped along with the rest of the table. Two other table cells restate information
already present elsewhere in this same file and need no separate carry-forward:
`tool_names`'s "(described below)" and `role`'s "(described below)" already point to
the existing paragraphs at lines 38/40; `cmd`'s "must not be empty when using
subprocess mode" duplicates the existing "Validation Rules" bullet at line 50.

## Alternatives considered
- Replace the table with a bare pointer and no carried-forward prose at all: rejected —
  this would silently drop the `env` denylist, a security-relevant fact
  `skills/DESIGN.md` Docs content policy — retain protects, that exists nowhere else in
  the file.
- Keep the full table and only shrink the `Type`/`Default` columns: rejected — the
  table header shape itself (`| Field | Type | Default | Description |`) is what
  `check_docs_content_policy.py` flags; any table with that header reproduces the
  finding.

## Implementation
### Target file
`docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md`

### Procedure
1. Read lines 13-51 to confirm current content matches the Plan's recorded evidence.
2. Replace lines 18-36 (the `## Agent-side MCP fields` heading through the last table
   row) with: the same heading; a sentence stating the 13 fields plus the derived `key`
   field are defined in `scripts/shared/mcp_config.py::McpServerConfig`; and one
   retained sentence stating that the `env` field's values are filtered through a
   denylist that rejects `LD_PRELOAD`, `LD_LIBRARY_PATH`, and `PYTHONPATH`.
3. Leave lines 15-16 (Ownership note), 38-50 (per-field prose paragraphs and Validation
   Rules), and everything from line 52 onward unchanged.

### Method
Single localized `Edit`, replacing lines 20-36 (the "There are 13 configurable
fields..." sentence through the last table row) with the pointer sentence and the
retained `env`-denylist sentence from Procedure step 2. Do not touch lines 15-16,
38-50, or content outside this range.

### Details
Do not restate any field's `Type`/`Default` value from the table — all 13 fields plus
`key` are fully defined in `scripts/shared/mcp_config.py::McpServerConfig`. Do retain
the `env` denylist fact verbatim (the three specific variable names
`LD_PRELOAD`/`LD_LIBRARY_PATH`/`PYTHONPATH`) — this is the one security-boundary fact
in the table not restated elsewhere in this file. Do not re-add a "(described below)"
pointer for `tool_names`/`role` or a "must not be empty" note for `cmd` — those are
already covered by the surviving prose paragraphs and Validation Rules list.

## Compatibility considerations
`N/A: documentation-only change, no code, public interface, or data format is affected`.

## Security considerations
The `env` denylist sentence (rejecting `LD_PRELOAD`/`LD_LIBRARY_PATH`/`PYTHONPATH`) is a
security-boundary fact and MUST be preserved by this edit, not silently dropped along
with the rest of the table — see Design decisions.

## Rollback considerations
Revert via `git checkout` on this one file. The edit is independently revertable from
the other four Plan rows' files.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` — confirm zero findings for
  `docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md` (Plan `AC-4`).
- `uv run python tools/check_docs_quality.py`, scoped to this file — confirm no new
  warning is introduced.
- `uv run python tools/check_docs_structure.py docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md`
  — confirm it passes (this file had no pre-existing `check_docs_structure.py` finding
  recorded in the Plan).
- `uv run python tools/check_docs_consistency.py --domain mcp` — confirm no new drift
  finding.
- Manual spot-check: confirm the `env` denylist sentence's three variable names still
  match `scripts/shared/mcp_config.py`'s actual denylist implementation.

## Completion criteria
The field/type/default table is replaced by a canonical-source pointer to
`scripts/shared/mcp_config.py::McpServerConfig`; the `env` denylist fact is preserved
as prose; the Ownership note and all per-field prose paragraphs/Validation Rules
outside the table are unchanged; `check_docs_content_policy.py` reports zero findings
for this file.

## Out of scope
- The Ownership note, per-field prose paragraphs, Validation Rules, and Related
  Documents/Keywords sections (see Scope) — not flagged, not part of `REQ-004`.
- Any other `docs/*.md` file — see the Plan's other four target-file rows, each with
  its own implementation procedure document.
- Extending `check_docs_content_policy.py`'s detection rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-170423 | 20260920-170423 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260920-170423 | 20260920-170423 | N/A: documentation-only, no automated test beyond the doc checkers already listed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-170423 | 20260920-170423 | Scoped to the doc checkers in Validation plan, not the full Python toolchain (no `scripts/` change) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-170423 | 20260920-170423 | N/A: this document IS the documentation change |

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
- **Requirement ID**: `REQ-004` — replace the `agent.toml` field table with a canonical-source pointer
- **Source issue**: issues/20260920-154352_dcp010_mcp-docs-content-policy-cleanup-batch-2.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-160121_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-162636
- **Related target files**: docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md