# Implementation Procedure: Update ADR-009 Known Deviations

## Goal

Update ADR-009's Known Deviations section to document the new enforcement mechanism (lint script), per REQ-07.

## Scope

- Modify `docs/adr/ADR-009-rag-ft5-text-separation.md`
- Update the DESIGN-2 Known Issue entry to reflect that enforcement has been added
- Document the whitelist mechanism and its rationale

## Assumptions

- The lint script exists at `tools/check_chunks_fts_invariant.py` (created by companion implementation procedure)
- The lint script is integrated into CI via `tox.ini` (created by companion implementation procedure)
- The Known Deviations section follows the existing format (see current content at line 358+)

## Design decisions

- Update the existing DESIGN-2 Known Issue entry rather than adding a new entry — the enforcement mechanism resolves the original gap
- Document the whitelist rationale: `schema_sql.py` is excluded because its INSERT statements are inside CREATE TRIGGER blocks (trigger definitions, not runtime writes); `mdq/db_schema.py` is excluded because it targets a separate database `/opt/llm/db/mdq.sqlite`
- Keep the entry in Japanese to match the existing ADR language

## Alternatives considered

- **Remove the Known Issue entirely**: Not appropriate yet — the enforcement mechanism detects violations but does not eliminate the risk of unsanctioned writes; it only catches them after they occur.
- **Add a new entry instead of updating**: Would duplicate information. Updating the existing entry keeps traceability clear.

## Implementation

### Target file

`docs/adr/ADR-009-rag-ft5-text-separation.md`

### Procedure

1. Read the current Known Deviations section (lines 358-367)
2. Replace the DESIGN-2 Known Issue entry with an updated version that documents the enforcement mechanism
3. Preserve the existing format and structure

### Method

**Step 1: Locate the DESIGN-2 entry**

Current content at lines 362-366:
```markdown
- **Known Issue**: DESIGN-2 — `chunks_fts`は`chunks`から派生しているが、直接INSERT/UPDATEは禁止されている。ただし、アプリケーションコードが`chunks_fts`を直接操作する経路がないことを保証するテストは存在しない。
- **Type**: Architectural Limitation
- **Summary**: `chunks_fts`の直接操作禁止を保証するテストが存在しない
- **Impact**: 意図せぬ`chunks_fts`の更新が発生する可能性がある
- **Resolution Target**: テストで直接操作を検出する
```

**Step 2: Replace with updated entry**

Replace the above block with:
```markdown
- **Known Issue**: DESIGN-2 — `chunks_fts`は`chunks`から派生しているが、直接INSERT/UPDATEは禁止されている。ただし、アプリケーションコードが`chunks_fts`を直接操作する経路がないことを保証するテストは存在しない。
- **Type**: Architectural Limitation
- **Summary**: `chunks_fts`の直接操作禁止を保証するテストが存在しない
- **Impact**: 意図せぬ`chunks_fts`の更新が発生する可能性がある
- **Resolution Target**: テストで直接操作を検出する
- **Enforcement**: `tools/check_chunks_fts_invariant.py` で直接INSERT/UPDATEを検出（CI統合済み）
  - Whitelist: `scripts/agent/services/rag_maintenance_service.py::rebuild_fts()`（AST関数コンテキスト検出）、`scripts/db/schema_sql.py`（CREATE TRIGGERブロック内のINSERTはランタイム書き込みではないため除外）、`scripts/mcp_servers/mdq/`（別DB `/opt/llm/db/mdq.sqlite` を対象）
```

### Details

- **REQ-07**: ADR-009's Known Deviations section must document the new enforcement mechanism
- **AC-06**: ADR-009's Known Deviations documents the new enforcement mechanism

## Compatibility considerations

- The update is documentation-only — no code changes required
- The entry adds English text alongside existing Japanese text, consistent with the ADR's mixed-language style

## Security considerations

- No security impact — this is a documentation update only

## Rollback considerations

- To revert, restore the original DESIGN-2 entry from git history

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|-----------------|----------------|-----------------|
| ADR-009 Known Deviations | Manual: documentation review | Read Known Deviations section | Enforcement documented |

## Completion criteria

- [ ] ADR-009 Known Deviations section includes the enforcement mechanism description
- [ ] Whitelist rationale is documented (TRIGGER blocks, separate DB)
- [ ] Entry references the lint script path (`tools/check_chunks_fts_invariant.py`)

## Out of scope

- Modifying the ADR body itself (only Known Deviations section)
- Adding enforcement for `chunks_fts_docsize` table operations
- Changing the ADR's architectural decisions

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-07
- **Source issue**: issues/20260924-054344_design2_no-test-guarantee-chunks_fts-direct-operation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-063321_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-121326
- **Related target files**: docs/adr/ADR-009-rag-ft5-text-separation.md
