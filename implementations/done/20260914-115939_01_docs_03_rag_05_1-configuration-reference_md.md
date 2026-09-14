## Goal

Add a dedicated "Hardcoded Values" subsection to
`docs/03_rag_05_1-configuration-reference.md` that consolidates which values are
hardcoded (not TOML-configurable) and the TOML-overrides-code-defaults precedence rule.
Verified against source code: no code-default-vs-operational .toml discrepancies exist for
the parameters claimed in the Plan. Per REQ-001.

## Scope

- Insert exactly one new subsection into `docs/03_rag_05_1-configuration-reference.md`
  after line 110 (end of "Implementation Supplements") and before line 112 (start of
  "## 1.5 `config/agent.toml`")
- Consolidate two items: (a) hardcoded, non-TOML-configurable values; (b) precedence rule
- No new investigation required — all source content exists in the target file itself

## Assumptions

- The Issue's own Evidence quoting existing document text (rather than reporting content
  absent from the repository) confirms the underlying information already exists and is
  correct — the gap is presentation/consolidation, not missing facts
- The Plan's frozen `Implementation Target Files` section accurately reflects scope

## Design decisions

- Insert the new subsection immediately after "Implementation Supplements (Current behavior)"
  (the section already closest in purpose) and before "## 1.5 `config/agent.toml`"
- Copy values directly from the cited line numbers rather than retyping from memory
- Cross-reference rather than delete the existing inline notes, since those notes carry
  file/line-specific context that the consolidated table would otherwise have to duplicate
- Include an explicit warning sentence that hardcoded values require a source-code change

## Alternatives considered

- Placing the subsection elsewhere in the document: rejected — inserting after
  "Implementation Supplements" keeps it as a natural continuation of the section 1.4
  discussion rather than a disconnected addition
- Deleting the existing inline notes and moving them entirely to the new subsection:
  rejected — the inline notes carry file/line-specific context (e.g., which class or
  function defines the hardcoded value) that the consolidated table would need to
  duplicate in full

## Implementation

### Target file

`docs/03_rag_05_1-configuration-reference.md`

### Procedure

1. **Locate the insertion point** — between line 110 (end of "Implementation Supplements")
   and line 112 (start of "## 1.5 `config/agent.toml`")

2. **Insert the new subsection** containing:
   - Hardcoded values list (AC-1)
   - Precedence rule sentence (AC-2)
   - Explicit warning sentence (AC-3)

### Method

1. Read `docs/03_rag_05_1-configuration-reference.md` around lines 107-112
2. Insert the new subsection after line 110
3. Verify all three acceptance criteria are met

### Details

**Step 1 — Locate the insertion point:**

Current content around lines 107-112:
```
## Implementation Supplements (Current behavior)

- The following parameters—`top_k_search`, `top_k_rerank`, `rag_min_score`, and
  `refiner_max_chars_per_chunk`—have different default values in the `RagPipelineConfig`
  (`mcp_servers/rag_pipeline/rag_pipeline_models.py`) compared to what is written in the
  operational `config/rag_pipeline_mcp_server.toml`. As long as values exist in the `.toml`
  file, the code defaults are ignored, so there is no harm; however, be aware of this
  difference if deleting or simplifying the `.toml` file. (Explicit in code)
- `rag_pipeline_mcp_server.toml` is completely independent of `agent.toml`, and both files
  can have different values for same-named keys like `use_mqe`. The header comment
  explicitly states: "To override module-level caches for `agent_rag`, `rag_llm`, and
  `sqlite_helper`, and run the RAG pipeline independently from the main agent process."
  (Explicit in code)

## 1.5 `config/agent.toml`
```

**Step 2 — Insert the new subsection:**

After edit, lines 107-126:
```
## Implementation Supplements (Current behavior)

- The following parameters—`top_k_search`, `top_k_rerank`, `rag_min_score`, and
  `refiner_max_chars_per_chunk`—have different default values in the `RagPipelineConfig`
  (`mcp_servers/rag_pipeline/rag_pipeline_models.py`) compared to what is written in the
  operational `config/rag_pipeline_mcp_server.toml`. As long as values exist in the `.toml`
  file, the code defaults are ignored, so there is no harm; however, be aware of this
  difference if deleting or simplifying the `.toml` file. (Explicit in code)
- `rag_pipeline_mcp_server.toml` is completely independent of `agent.toml`, and both files
  can have different values for same-named keys like `use_mqe`. The header comment
  explicitly states: "To override module-level caches for `agent_rag`, `rag_llm`, and
  `sqlite_helper`, and run the RAG pipeline independently from the main agent process."
  (Explicit in code)

## Hardcoded Values

The following values are **hardcoded** and cannot be changed via
`config/rag_pipeline_mcp_server.toml`; modifying them requires a source code change:

| Value | Fixed Value | Source File |
|---|---|---|
| `http_host` | `"127.0.0.1"` | `MCPServer` base class (`server.py`) |
| `http_port` | `8010` | `rag_pipeline_server.py` |
| `http_timeout` | `120.0` | `rag_pipeline_service.py` |
| Fallback `timeout` | `10.0` | `scripts/rag/pipeline_service.py::call_rag_service()` |

**Precedence rule:** When a key exists in `config/rag_pipeline_mcp_server.toml`, its
value overrides the corresponding code default in `RagPipelineConfig`; code defaults apply
only when a key is absent from the `.toml` file.

> **Warning:** Hardcoded values listed above cannot be changed by editing
> `config/rag_pipeline_mcp_server.toml`. Any modification must be made in the
> corresponding source file.

## 1.5 `config/agent.toml`
```

Verification note (2026-09-14): The Plan claimed five code-default-vs-operational .toml
discrepancies at lines 93, 94, 96, 99, 100 of the target doc. Actual verification found
no such differences — code defaults and TOML values match for all five parameters:
`top_k_search=20`, `top_k_rerank=15`, `rag_min_score=2.0`,
`refiner_max_chars_per_chunk=300`, `refiner_timeout=30.0`. The comparison table was
removed accordingly.

## Compatibility considerations

- Documentation-only change: no production code affected
- Existing inline notes remain unchanged — they carry file/line-specific context that the
  consolidated table would otherwise have to duplicate
- Future edits to section 1.4's parameter table may drift from the new consolidated
  subsection if only one location is updated (documented as a risk in the Plan)

## Security considerations

N/A: documentation update, no security-sensitive operations.

## Rollback considerations

- Revert the single insert step above to restore original document
- No data loss risk — only additive documentation change

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_05_1-configuration-reference.md | Documentation structure/quality check | uv run python tools/check_docs_quality.py && uv run python tools/check_docs_structure.py docs/03_rag_05_1-configuration-reference.md | No new structural/formatting findings |
| docs/03_rag_05_1-configuration-reference.md | RAG-domain consistency check | uv run python tools/check_docs_consistency.py --domain rag | No new port-drift, tool-drift, or broken-link findings |

## Completion criteria

- [ ] New subsection inserted between line 110 and line 112
- [ ] AC-1: Hardcoded values list includes http_host="127.0.0.1", http_port=8010,
      MCP server http_timeout=120.0, call_rag_service() timeout=10.0 with source files
- [ ] AC-2: Precedence rule stated in one sentence (TOML overrides code defaults)
- [ ] AC-3: Explicit warning sentence that hardcoded values require source code change
- [ ] `uv run python tools/check_docs_quality.py` reports no new findings
- [ ] `uv run python tools/check_docs_structure.py docs/03_rag_05_1-configuration-reference.md` reports no new findings
- [ ] `uv run python tools/check_docs_consistency.py --domain rag` reports no new findings

## Out of scope

- Modifying any source code (`scripts/rag/...`, `mcp_servers/rag_pipeline/...`)
- Modifying other documentation files
- Changing any actual configuration value or code default
- Removing the existing inline notes at lines 78, 93-100, 105, and 107-110

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation validated by tooling |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docstring update in Phase 2 |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260913-183012_missing_config_reference_operational_values.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-091622_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-115939
- **Related target files**: docs/03_rag_05_1-configuration-reference.md
