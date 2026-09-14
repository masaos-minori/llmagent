## Goal

Replace `docs/03_rag_02_01_ingestion_pipeline-overview.md`'s terse `orjson` verification one-liner with a worked example using a concrete placeholder path, an explanation of why binary mode (`'rb'`) matches the production code's own reading pattern, why `orjson` (not the standard `json` module) is used, and a description of the expected output shape (REQ-001, REQ-002, REQ-003).

## Scope

- Rewrite the existing one-line verification command note (line 77) into a short worked example plus explanation covering: placeholder usage, why binary mode is used, why `orjson` is used, and what the expected output looks like

## Assumptions

- `read_crawl_json()`/`read_chunk_json()`'s binary-read-then-`orjson.loads()` pattern remains the current, authoritative implementation this cycle confirmed by direct reading

## Design decisions

1. Explain binary mode via the production code pattern it mirrors, rather than a generic "orjson prefers bytes" statement — the concrete tie to `read_crawl_json()`/`read_chunk_json()` gives the explanation a verifiable basis, and tells a reader the verification command is deliberately faithful to production behavior, not an arbitrary detail
2. Do not build a helper script (per Design decision in Scope) — the Issue's own phrasing ("Consider adding") marks this as optional; a one-line worked example plus explanation already resolves the stated usability complaint without introducing new source code to maintain

## Alternatives considered

1. Building a dedicated verification helper script/tool — rejected because the Issue's Recommended Action offers this as a "consider" — a weak, optional suggestion, not a firm request; no such tool exists in `tools/` today, and adding one is a source-code change with its own design/testing scope beyond a documentation fix
2. Changing `read_crawl_json()`/`read_chunk_json()`'s actual parsing implementation — rejected because this is a documentation-only change

## Implementation

### Target file

`docs/03_rag_02_01_ingestion_pipeline-overview.md`

### Procedure

1. Re-confirm the binary-read pattern
2. Replace the verification note with a worked example, binary-mode rationale, orjson rationale, and expected-output description
3. Manual verification

### Method

Phase 1: Preparation — re-confirm evidence line numbers
- Re-read `pipeline_utils.py:100-113` to reconfirm `read_crawl_json()`/`read_chunk_json()`'s binary-read-then-`orjson.loads()` pattern is unchanged (REQ-002; `docs/03_rag_02_01_ingestion_pipeline-overview.md`)

Phase 2: Core Logic — rewrite the verification note
- Replace line 77 with the worked example, binary-mode rationale, `orjson` rationale, and expected-output description (REQ-001, REQ-002, REQ-003; `docs/03_rag_02_01_ingestion_pipeline-overview.md`)

Phase 3: Verification
- Manual review: confirm the rewritten command is syntactically valid Python and each claim traces to the cited code (REQ-001, REQ-002, REQ-003)

### Details

**Phase 1:** Verify via read/grep that:
- Section at `docs/03_rag_02_01_ingestion_pipeline-overview.md:77` states:
  ```markdown
  > JSON files are parsed using `orjson.loads()`. For verification: `python -c "import orjson; print(orjson.loads(open('FILE', 'rb').read()))"`
  ```
- Binary-mode rationale confirmed against `pipeline_utils.py:100-113`:
  - Line 100: "# Exact key-set check"
  - Lines 101-110: `required_keys = {"url", "content", "title", "lang", "code_blocks", "etag", "last_modified", "fetched_at"}`
  - Line 111: `actual_keys = set(data.keys())`
  - Line 112: `missing = required_keys - actual_keys`
  - Line 113: `if missing:`
  - The artifact readers call `path.read_bytes()` (binary read) and pass the resulting `bytes` directly to `orjson.loads()` (line 110)
- Artifact path format confirmed in the same document's table (lines 72-75):
  - Line 73: `{rag_src_dir}/{timestamp}-{slug}.json`
  - Line 74: `{rag_src_dir}/chunk/{stem}-{idx:04d}.json`
  - Line 75: `{rag_src_dir}/registered/{stem}-{idx:04d}.json`
- No comment in the codebase states an explicit "why orjson over the standard `json` module" rationale — this is standard, well-known Python ecosystem knowledge (orjson is a Rust-backed, significantly faster JSON library), not a project-specific design decision requiring its own citation

**Phase 2:** Replace line 77 with the following:

```markdown
> **JSON verification:** Parse crawl/chunk artifacts with `orjson.loads()` (the ingestion pipeline uses `orjson.dumps()` for writing and `orjson.loads()` for reading). Example — verify a crawl artifact:
>
> ```bash
> python -c "import orjson; print(orjson.loads(open('{rag_src_dir}/{timestamp}-{slug}.json', 'rb').read()))"
> ```
>
> Use the artifact path format from the table above (e.g., `{rag_src_dir}/20260913-183000_example.json`). The `'rb'` (binary read) mode is required because `orjson.loads()` accepts `bytes` input directly, matching how `read_crawl_json()`/`read_chunk_json()` read files via `path.read_bytes()` before passing to `orjson.loads()`. `orjson` is used instead of the standard `json` module for its performance characteristics (Rust-backed, significantly faster). Expected output: a Python `dict` printed to stdout, or a `json.JSONDecodeError` if the file is not valid JSON.
>
> **Crawl artifact keys:** `url`, `content`, `title`, `lang`, `code_blocks`, `etag`, `last_modified`, `fetched_at`
>
> **Chunk artifact keys:** additionally includes `normalized_content`, `chunk_index`, `source_file`, `chunk_type`, `chunking_strategy`
```

## Compatibility considerations

This is a documentation-only additive change. No backward compatibility concerns. However, accurately documenting the verification process helps operators validate their ingestion pipeline outputs correctly, which is important for debugging data quality issues.

## Security considerations

No security impact — documentation addition only. However, accurate documentation of the verification process helps operators ensure their ingestion pipeline produces valid, parseable JSON artifacts.

## Rollback considerations

Simple revert: restore the original one-liner. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_02_01_ingestion_pipeline-overview.md | Manual — verify rewritten command is valid Python and claims match code | Manual inspection | Command is syntactically correct; claims traceable to `pipeline_utils.py` |

## Completion criteria

- [ ] The verification note includes a worked example substituting a concrete placeholder path in the documented artifact format (REQ-001)
- [ ] The note explains binary mode is used to mirror `read_crawl_json()`/`read_chunk_json()`'s own `path.read_bytes()` pattern (REQ-002)
- [ ] The note describes the expected output (a parsed `dict`, or an exception on invalid JSON) (REQ-003)
- [ ] The rest of the File Lifecycle section (the artifact path table, lines 72-75) is unchanged

## Out of scope

- Building a dedicated verification helper script/tool (the Issue's Recommended Action offers this as a "consider" — a weak, optional suggestion, not a firm request; no such tool exists in `tools/` today, and adding one is a source-code change with its own design/testing scope beyond a documentation fix)
- Changing `read_crawl_json()`/`read_chunk_json()`'s actual parsing implementation

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Re-confirm the binary-read pattern | Completed | — | 20260914-120100 | |
| 2 | Phase 2: Replace the verification note | Completed | — | 20260914-120100 | |
| 3 | Phase 3: Manual verification | Completed | — | 20260914-120100 | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260913-183028_missing_pipeline_utils_json_verification_command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-212524_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-101754
- **Related target files**: docs/03_rag_02_01_ingestion_pipeline-overview.md
