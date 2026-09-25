## Goal
Fix `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`'s inbound Markdown link to `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md` — currently `../90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md` — to `../40_shared/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`, per Plan `plans/20260924-150508_plan.md` REQ-002.

## Scope
- In scope: rewriting the single Markdown link at line 464 (pre-fix line number, confirmed via `rg -n` during Plan creation).
- Out of scope: seq 08 (the linked file's own move into `docs/40_shared/`, a prerequisite for the link to actually resolve, though not a prerequisite for this text edit itself); any other content in this ADR file.

## Assumptions
- This ADR file resides at `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` and is not itself relocated by this Plan — only the link's target-path depth needs adjusting.
- The existing `../` prefix already accounts for `docs/adr/`'s own directory depth relative to `docs/`; inserting `40_shared/` after that prefix correctly targets `docs/40_shared/90_shared_03_03_...md`.

## Design decisions
A minimal relative-path insertion (`../90_shared_03_03_...` → `../40_shared/90_shared_03_03_...`).

## Alternatives considered
Same as seq 10-13: relative-path fix preferred over an absolute-from-docs-root link, per this repository's existing convention.

## Implementation
### Target file
`docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`

### Procedure
1. Locate the link with `rg -n '\]\([^)]*/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients\.md(#[^)]*)?\)' docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` — expect exactly 1 match (line 464).
2. Edit line 464: `- [90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md](../shared_03_03_runtime_and_execution-llm-and-mcp-clients.md) — Shared Runtime` → `- [90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md](../40_shared/shared_03_03_runtime_and_execution-llm-and-mcp-clients.md) — Shared Runtime`.
3. Re-run the same `rg` command to confirm the match now shows the `40_shared/` component.

### Method
Single-line text substitution via Edit.

### Details
- Confirmed via `rg -n '\]\([^)]*/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients\.md(#[^)]*)?\)' docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`: exactly 1 match (line 464).
- Only the link's target path changes; the link text (the filename itself) and trailing annotation are untouched.

## Compatibility considerations
After this fix, `tools/check_docs_structure.py`'s link checker resolves this link correctly, once seq 08 has moved the target file into `docs/40_shared/`.

## Security considerations
N/A: a documentation link-path edit has no security surface.

## Rollback considerations
Revert via Edit back to `../90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md` if needed before commit; after commit, `git revert` the commit that performed this fix.

## Validation plan
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json` reports no broken-link finding for this file (AC-3).
- `rg -n '\]\([^)]*/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients\.md(#[^)]*)?\)' docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` shows the link now reading `../40_shared/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`.

## Completion criteria
The Markdown link at the former line 464 resolves to `docs/40_shared/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`, verified via `tools/check_docs_structure.py`.

## Out of scope
Seq 08 (the linked file's own move, a prerequisite for the link to resolve); any other ADR-003 content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260925-090635 | 20260925-090635 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260925-090639 | 20260925-090639 | N/A: no test code applies to a docs link fix; validation is `tools/check_docs_structure.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260925-090643 | 20260925-090643 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260925-090648 | 20260925-090648 | N/A: this row's own edit IS the documentation change |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260923-141137_docsreorg09_move-general-shared-docs-into-new-shared-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-150508_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-151506
- **Related target files**: docs/adr/ADR-003-runtime-tool-registry-routing-authority.md