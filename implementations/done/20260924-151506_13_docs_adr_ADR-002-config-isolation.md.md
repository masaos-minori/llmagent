## Goal
Fix `docs/adr/ADR-002-config-isolation.md`'s inbound Markdown link to `docs/90_shared_03_01_runtime_and_execution-config-and-logging.md` — currently `../90_shared_03_01_runtime_and_execution-config-and-logging.md` — to `../40_shared/90_shared_03_01_runtime_and_execution-config-and-logging.md`, per Plan `plans/20260924-150508_plan.md` REQ-002.

## Scope
- In scope: rewriting the single Markdown link at line 431 (pre-fix line number, confirmed via `rg -n` during Plan creation).
- Out of scope: seq 06 (the linked file's own move into `docs/40_shared/`, a prerequisite for the link to actually resolve, though not a prerequisite for this text edit itself); any other content in this ADR file.

## Assumptions
- This ADR file resides at `docs/adr/ADR-002-config-isolation.md` and is not itself relocated by this Plan — only the link's target-path depth needs adjusting to account for the target file's new `docs/40_shared/` location.
- The existing `../` prefix already accounts for `docs/adr/`'s own directory depth relative to `docs/`; inserting `40_shared/` after that prefix (rather than adding a second `../`) correctly targets `docs/40_shared/90_shared_03_01_...md`.

## Design decisions
A minimal relative-path insertion (`../90_shared_03_01_...` → `../40_shared/90_shared_03_01_...`) — the existing `../` level is preserved since `docs/adr/`'s depth relative to `docs/` is unchanged; only the target's own subdirectory component is added.

## Alternatives considered
Same as seq 10-12: relative-path fix preferred over an absolute-from-docs-root link, per this repository's existing convention.

## Implementation
### Target file
`docs/adr/ADR-002-config-isolation.md`

### Procedure
1. Locate the link with `rg -n '\]\([^)]*/90_shared_03_01_runtime_and_execution-config-and-logging\.md(#[^)]*)?\)' docs/adr/ADR-002-config-isolation.md` — expect exactly 1 match (line 431).
2. Edit line 431: `- [Runtime and Execution - Config and Logging](../shared_03_01_runtime_and_execution-config-and-logging.md) — ランタイム設定とロギング` → `- [Runtime and Execution - Config and Logging](../40_shared/shared_03_01_runtime_and_execution-config-and-logging.md) — ランタイム設定とロギング`.
3. Re-run the same `rg` command to confirm the match now shows the `40_shared/` component.

### Method
Single-line text substitution via Edit.

### Details
- Confirmed via `rg -n '\]\([^)]*/90_shared_03_01_runtime_and_execution-config-and-logging\.md(#[^)]*)?\)' docs/adr/ADR-002-config-isolation.md`: exactly 1 match (line 431).
- Only the link's target path changes; the link text and trailing Japanese annotation are untouched.

## Compatibility considerations
After this fix, `tools/check_docs_structure.py`'s link checker resolves this link correctly, once seq 06 has moved the target file into `docs/40_shared/`.

## Security considerations
N/A: a documentation link-path edit has no security surface.

## Rollback considerations
Revert via Edit back to `../90_shared_03_01_runtime_and_execution-config-and-logging.md` if needed before commit; after commit, `git revert` the commit that performed this fix.

## Validation plan
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json` reports no broken-link finding for this file (AC-3).
- `rg -n '\]\([^)]*/90_shared_03_01_runtime_and_execution-config-and-logging\.md(#[^)]*)?\)' docs/adr/ADR-002-config-isolation.md` shows the link now reading `../40_shared/90_shared_03_01_runtime_and_execution-config-and-logging.md`.

## Completion criteria
The Markdown link at the former line 431 resolves to `docs/40_shared/90_shared_03_01_runtime_and_execution-config-and-logging.md`, verified via `tools/check_docs_structure.py`.

## Out of scope
Seq 06 (the linked file's own move, a prerequisite for the link to resolve); any other ADR-002 content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260925-085424 | 20260925-085424 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260925-085428 | 20260925-085428 | N/A: no test code applies to a docs link fix; validation is `tools/check_docs_structure.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260925-085432 | 20260925-085432 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260925-085435 | 20260925-085435 | N/A: this row's own edit IS the documentation change |

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
- **Related target files**: docs/adr/ADR-002-config-isolation.md