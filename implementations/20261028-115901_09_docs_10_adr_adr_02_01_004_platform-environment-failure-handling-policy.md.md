# Procedure: replace the stale fetch_tools() code reference in ADR-004

## Goal

Replace the citation of the removed fetch_tools function in `scripts/agent/services/mcp_tool_discovery.py` with the function that exists (Plan REQ-002).

## Scope

- Modify only `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`.
- Documentation-only change; state current behavior only.

## Assumptions

- `_fetch_server_tools` is the per-server fetch entry point (checked in the planning phase).
- Overlap (compatible): `plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md` edits only the ADR-006 Implementation Notes, while this Plan edits ADR-006's Verification table. Any citation added by that Plan must resolve to an existing test node once the node validation of this Plan is in force.

## Design decisions

- Edit the named sentences after re-reading the current text; do not reflow surrounding paragraphs.

## Alternatives considered

N/A: lightweight row.

## Implementation

### Target file

`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`

### Procedure

- In the retry-policy bullet, replace the citation with `scripts/agent/services/mcp_tool_discovery_fetch.py::_fetch_server_tools()` (the fetch layer was split out and the old name fetch_tools no longer exists).
- Confirm with `rg -n "def _fetch_server_tools" scripts/agent/services/mcp_tool_discovery_fetch.py`.

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- One identifier and path change; the sentence's meaning (no retry for live discovery) is unchanged.

## Compatibility considerations

N/A: documentation-only.

## Security considerations

N/A: documentation-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py --strict`; `uv run python tools/check_docs_japanese.py`; `uv run python tools/check_docs_consistency.py --domain governance` | No finding |

## Completion criteria

- The document states the behavior described in Details.
- All listed documentation checkers report no finding.

## Out of Scope

- Every other document.
- Code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (stale code reference)
- **Source issue**: issues/20261027-155848_adrgate005_enforce-adr-evidence-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093931_adrgate005_enforce-adr-evidence-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115901
- **Related target files**: docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md
