## Goal

Update `DESIGN-1` in `docs/00_governance_03_issue-and-uncertainty-management.md` to reflect that both documentation updates (REQ-001: shared-corpus note in system overview; REQ-002: ADR-010 wording correction) are complete, and remove it from the active inventory per this document's existing resolved-entry convention (heading retained with a resolution note, per the pattern already used for `SHARED-001`/`EVENTBUS-008`/`CI-005`/`CI-006`/`RAG-003`/`RAG-004`/`CI-004`). Per REQ-003.

## Scope

- Update the `DESIGN-1` section in `docs/00_governance_03_issue-and-uncertainty-management.md`
- Replace the bullet-point entries with a single resolution note following the existing resolved-entry convention
- Keep the `#### DESIGN-1` heading (per the pattern used for resolved entries like `CI-004`)
- Out-of-scope: modifying any other Known Issue entry

## Assumptions

- Both REQ-001 and REQ-002 have been completed (shared-corpus note added to system overview; ADR-010 wording corrected)
- The resolved-entry convention follows the pattern used for `CI-004` (lines 307-309): heading retained, bullet-point entries replaced with a single paragraph explaining resolution
- The current `DESIGN-1` entry format (lines 128-145) uses bullet-point fields consistent with other active entries
- The Plan's source Issue (`issues/20260914-112416_ragsvc04_execution-mode-shared-corpus-doc.md`) is the definitive reference for what constitutes completion

## Design decisions

1. Keep the `#### DESIGN-1` heading — per the pattern used for `CI-004` and other resolved entries where the heading is retained
2. Replace all bullet-point entries with a single resolution paragraph — per the established convention
3. State clearly that both documentation updates are complete — provides traceability for operators reviewing the history
4. Retain the original date context (First Found: 2026-08-22) in the resolution note — preserves historical accuracy

## Alternatives considered

1. Removing the heading entirely: rejected — the existing pattern for resolved entries retains the heading even when the entry is resolved (e.g., `CI-004`); removing it would break consistency
2. Keeping the bullet-point structure but changing Status to "Resolved": rejected — the established convention replaces bullets with a narrative paragraph, not just a status change

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Read the current `DESIGN-1` section (lines 128-145) to confirm current content
2. Replace the bullet-point entries with a single resolution paragraph following the `CI-004` pattern
3. Verify the updated section maintains consistency with adjacent resolved entries

### Method

1. Read `docs/00_governance_03_issue-and-uncertainty-management.md` lines 128-145 to confirm the exact current content
2. Apply edits using the Edit tool to replace the bullet-point entries with a resolution paragraph
3. Verify the updated section maintains formatting consistency

### Details

**Step 1 — Read current DESIGN-1 section:**

Current `DESIGN-1` section (lines 128-145):

```markdown
#### DESIGN-1

- **ID**: DESIGN-1
- **Title**: External RAG and local RAG corpus difference not documented
- **Status**: open
- **Severity**: Medium
- **Area**: RAG
- **Type**: missing-documentation
- **Source**: `scripts/rag/`
- **Owner**: Team
- **First Found**: 2026-08-22
- **Target**: `docs/03_rag_01_system_overview.md`
- **Related**: ADR-010
- **Summary (corrected 2026-09-14)**: External RAG (HTTP, via `rag_pipeline_mcp_server`) and local/in-process RAG use the same corpus — both read `rag_db_path` from their respective config files (`config/rag_pipeline_mcp_server.toml`, `config/agent.toml`), and both are currently configured to `/opt/llm/db/rag.sqlite`. The original claim below ("different corpora") does not match this configuration and is retained only as historical context. What remains genuinely undocumented is the *execution-mode* distinction (HTTP delegation vs. in-process pipeline) and the operational fact that both modes are expected to point at the same database.
- **Current Description (superseded, retained as historical context)**: Two separate RAG implementations exist — one for external search and one for local search — each operating on different data stores.
- **Observed Implementation (superseded, retained as historical context)**: External RAG uses a vector store connected to an external API endpoint; local RAG uses SQLite with the sqlite-vec extension storing embeddings derived from ingested documents.
- **Impact**: Operators may not understand that "external"/"local" RAG is an execution-mode distinction over one shared corpus, not a corpus difference — this is a narrower documentation gap than the entry originally described.
- **Recommended Action**: Document, in the RAG system overview, that "external" and "local" RAG execution modes share one corpus (`rag_db_path`) by configuration convention, and that `rag_service_url`'s presence/absence (per `ADR-010`) selects the execution mode, not the data source. Tracked as `issues/20260914-112416_ragsvc04_execution-mode-shared-corpus-doc.md`.
```

**Step 2 — Replace bullet-point entries with resolution paragraph:**

After the `#### DESIGN-1` heading and before the `#### DESIGN-2` heading, insert:

```markdown
DESIGN-1 ("External RAG and local RAG corpus difference not documented") was resolved and removed from this active inventory 2026-09-14. Both documentation updates required by the source Issue (`issues/20260914-112416_ragsvc04_execution-mode-shared-corpus-doc.md`) are complete: (1) a shared-corpus note was added to `docs/03_rag_01_system_overview.md` stating that external/local RAG modes share one corpus by configuration convention (not an enforced invariant), citing both `config/agent.toml` and `config/rag_pipeline_mcp_server.toml`; (2) `docs/adr/ADR-010-rag-fallback.md`'s "Data Ownership and Persistence" `System of Record` line was reworded to describe one shared `rag.sqlite` file accessed via two execution paths, not two independent systems of record. Its absence from the active list is the correct, policy-compliant state — do not create a `#### DESIGN-1` heading.
```

Reference files read (must NOT be modified):
- `docs/00_governance_03_issue-and-uncertainty-management.md:128-145` — confirms current DESIGN-1 entry format
- `docs/00_governance_03_issue-and-uncertainty-management.md:307-309` — confirms resolved-entry convention pattern

## Compatibility considerations

- No public API changes; only documentation update
- Governance entry format preserved — heading retained, bullet points replaced with narrative paragraph per established convention
- Adjacent entries unaffected by the modification

## Security considerations

N/A — documentation-only change, no security-sensitive operations introduced.

## Rollback considerations

- Revert the resolution paragraph to restore original bullet-point entries
- No data loss risk — only documentation changes

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_03_issue-and-uncertainty-management.md | Documentation quality check | `uv run python tools/check_docs_quality.py` | No new findings; `DESIGN-1` follows the same resolved-entry format already used elsewhere in this file |

## Completion criteria

- [ ] `DESIGN-1` heading retained
- [ ] Bullet-point entries replaced with a single resolution paragraph
- [ ] Resolution paragraph states both documentation updates are complete
- [ ] Resolution paragraph cites both target files updated
- [ ] Entry format consistent with adjacent resolved entries (e.g., `CI-004`)
- [ ] Doc-quality tools pass without new findings

## Out of scope

- Modifying the E2E test itself (separate implementation procedure)
- Changing the severity or area classification of DESIGN-1
- Updating other Known Issue entries

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Requires REQ-001 and REQ-002 to be completed first |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only change |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | N/A: documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docstring already describes delegation |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | REQ-001 and REQ-002 must be completed before governance update | False | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260914-112416_ragsvc04_execution-mode-shared-corpus-doc.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-151434_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-170933
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
