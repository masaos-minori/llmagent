## Goal

Reword `docs/adr/ADR-010-rag-fallback.md`'s "Data Ownership and Persistence" `System of Record` line so it accurately describes one shared `rag.sqlite` file accessed via two execution paths (HTTP delegation and in-process), not two independent systems of record. Per REQ-002.

## Scope

- Reword exactly one line in `docs/adr/ADR-010-rag-fallback.md`: the `**System of Record**:` line (line 267)
- Do not alter any other part of `ADR-010`'s Decision/Invariants/Rationale sections
- Out-of-scope: changing any other ADR section; adding automated checks for `rag_db_path` divergence

## Assumptions

- The "Data Ownership and Persistence" section exists at lines 265-273 of `ADR-010` — confirmed via direct read
- The current `System of Record` line reads: `**System of Record**: \`rag.sqlite\`（ローカルRAG用）、外部RAGサービス（リモートRAG用）` — confirmed via direct read
- Other lines in the same section (`Derived Data`, `Ownership`, `Persistence`, `Transaction Boundary`, `Recovery Source`, `Deletion Rule`) were read but not individually re-verified against the shared-corpus correction during this Plan's investigation — this is UNK-01 from the Plan
- The existing Japanese-language formatting conventions apply (full-width parentheses, etc.)

## Design decisions

1. Change only the `System of Record` line — the Plan's investigation identified this as the clear issue; other lines were not individually verified
2. Keep the line in Japanese to match the document's existing language convention
3. Explicitly state "one shared `rag.sqlite`" rather than listing two separate systems
4. Retain the original structure (`**System of Record**: ...`) to preserve the section's formatting consistency

## Alternatives considered

1. Rewording all seven fields in the section: rejected — the Plan's investigation found the `System of Record` line as the clear issue; other lines were not individually verified and would require additional analysis
2. Creating a new subsection: rejected — the Plan specifies rewording the existing line, not restructuring the section

## Implementation

### Target file

`docs/adr/ADR-010-rag-fallback.md`

### Procedure

1. Re-read the full "Data Ownership and Persistence" section (lines 265-273) to resolve UNK-01 — verify no other line beyond the `System of Record` line implies separate corpora
2. If no other lines need correction, reword only the `System of Record` line
3. If other lines are found to imply separate corpora, correct them alongside the `System of Record` line
4. Verify the updated section maintains consistency with the document's existing formatting conventions

### Method

1. Read `ADR-010-rag-fallback.md` lines 265-273 to confirm the exact current content
2. Apply edits using the Edit tool to modify the identified line(s)
3. Verify the updated section maintains formatting consistency

### Details

**Step 1 — Re-read section to resolve UNK-01:**

Current "Data Ownership and Persistence" section (lines 265-273):

```markdown
## Data Ownership and Persistence

- **System of Record**: `rag.sqlite`（ローカルRAG用）、外部RAGサービス（リモートRAG用）
- **Derived Data**: 再生成可能な派生データ（FTS5、Vector Index）
- **Ownership**: RAGチーム（正本の所有）
- **Persistence**: ファイルシステム（`/opt/llm/db/`ディレクトリ）
- **Transaction Boundary**: DB単位
- **Recovery Source**: 各DBの手動復旧
- **Deletion Rule**: 各DBの削除は独立して実行する
```

UNK-01 resolution: After re-reading, the `System of Record` line is the only line that clearly declares two separate Systems of Record. The other lines use terms like "各DB" (each DB) in the context of operational procedures (recovery/deletion), not data-source declarations. These are acceptable as-is because they describe operational procedures for the single corpus database, not claims about separate data sources.

**Step 2 — Reword the `System of Record` line:**

Change line 267 from:

```markdown
- **System of Record**: `rag.sqlite`（ローカルRAG用）、外部RAGサービス（リモートRAG用）
```

To:

```markdown
- **System of Record**: `rag.sqlite`（外部RAGとローカルRAGで共有、実行モード別経路：HTTP委譲またはインプロセス）
```

Rationale: explicitly states one shared `rag.sqlite` file, clarifies that the distinction between external/local RAG is an execution-mode difference (HTTP delegation vs. in-process) over the same corpus, not a data-source difference.

Reference files read (must NOT be modified):
- `config/agent.toml:7` — confirms `rag_db_path = "/opt/llm/db/rag.sqlite"`
- `config/rag_pipeline_mcp_server.toml:13` — confirms `rag_db_path = "/opt/llm/db/rag.sqlite"`
- `docs/adr/ADR-010-rag-fallback.md:265-273` — confirms current section content

## Compatibility considerations

- No public API changes; only documentation wording change
- Document structure preserved — only one line's wording changed
- Existing content unaffected by the modification

## Security considerations

N/A — documentation-only change, no security-sensitive operations introduced.

## Rollback considerations

- Revert the reworded line to restore original state
- No data loss risk — only documentation changes

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/adr/ADR-010-rag-fallback.md | Documentation quality/consistency check | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_adr_reference.py`, `uv run python tools/check_adr_invariant_matrix.py` | No new findings; ADR Invariant Matrix and cross-reference checks still pass since Decision/Invariants are unchanged |

## Completion criteria

- [ ] `System of Record` line reworded to describe one shared `rag.sqlite` file
- [ ] Line explicitly states the shared-corpus fact, not two separate systems of record
- [ ] Line retains the original `**System of Record**: ...` format
- [ ] No other part of `ADR-010`'s Decision/Invariants/Rationale is changed
- [ ] Doc-quality tools pass without new findings

## Out of scope

- Rewording all seven fields in the section (only `System of Record` line is in scope per Plan)
- Adding automated divergence checks between config files
- Changing any other ADR section

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Requires UNK-01 resolution first |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only change |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | N/A: documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docstring already describes delegation |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-01: Must re-read full section before editing to confirm no other lines need correction | False | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260914-112416_ragsvc04_execution-mode-shared-corpus-doc.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-151434_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-170933
- **Related target files**: docs/adr/ADR-010-rag-fallback.md
