# Implementation: docs/03_rag_90_inconsistencies_and_known_issues.md

## Goal

Create a structured catalog of all known inconsistencies, bugs, open questions, and
spec conflicts identified during the documentation restructuring analysis.

## Scope

- Content from: `03_spec_rag.md` section 13 (未解決事項・既知問題)
- Content from: `05_ref-rag.md` section 1.1 (use_rrf note)
- Content from: plan Unknowns section (additional analysis findings)
- Output: `docs/03_rag_90_inconsistencies_and_known_issues.md`
- Must contain 14+ critical issues as analyzed in the plan

## Assumptions

- Each issue uses the format: Type / Impact scope / Description / Current safe interpretation
  / Recommended action / Notes for AI reference
- Types: BUG (code defect), SPEC_CONFLICT (contradictory documentation),
  OPEN_QUESTION (undefined behavior), DOC_INCONSISTENCY (naming/terminology mismatch)

## Implementation

### Target file

`docs/03_rag_90_inconsistencies_and_known_issues.md`

### Procedure

Write the following issues in this order:

**Implementation Bugs:**
1. BUG-1: `chunking_strategy` field lost in `_read_chunk_json()` (ingester.py:94)
2. BUG-2: `normalized_content` hardcoded to None in ingester (ingester.py:255)
3. BUG-3: `chunk_index` always 0 due to `idx=0` dead code (ingester.py:257-260)
   - Note: BUG-1/2/3 share root cause: `dataclasses.asdict(read_json_file(path))` drops unknown fields
   - Fix: change `_read_chunk_json()` to `orjson.loads(path.read_bytes())`

**Spec Conflicts:**
4. `use_rrf=False` never takes effect: FusionStage ignores the flag; `_dedup_hits` is dead code
5. Stage count discrepancy: `03_spec_rag.md` says "4段階", `03_rag-ingestion-run.md` says "3ステップ"
   - Preferred: "3 scripts / 4 processing phases"

**Document Inconsistencies:**
6. Module name: ref files say `web_crawler.py`; run files say `crawler.py` (actual: `crawler.py`)
7. Module name: ref file says `rag_ingester.py`; run files say `ingester.py` (actual: `ingester.py`)

**Open Questions:**
8. External RAG service authentication/error handling undefined when `rag_service_url` is set
9. MDQ vs RAG boundary: migration criteria undefined (see `04_mcp-mdq.md`)
10. `test_ingester.py` missing: DB write behavior and `chunking_strategy` reflection untested
11. `chunks_fts` trigger for `normalized_content=None` (English/code): verify COALESCE behavior
12. `use_refiner=True` edge cases: behavior when refiner returns empty string
13. `_augment_http()` fallback: condition that triggers in-process fallback not documented
14. `SemanticCache` prune policy: FIFO described; verify behavior under concurrent access

### Method

For each issue, use this structure:
```
### [TYPE-N] Short title

- **Type:** BUG | SPEC_CONFLICT | OPEN_QUESTION | DOC_INCONSISTENCY
- **Impact scope:** (affected files/modules)
- **Description:** (what the problem is)
- **Current safe interpretation:** (what to assume when uncertain)
- **Recommended action:** (fix or investigation needed)
- **Source reference:** (where found)
- **Notes for AI reference:** (guidance for AI reading this doc)
```

## Validation plan

- File exists at `docs/03_rag_90_inconsistencies_and_known_issues.md`
- Exactly 14 or more distinct issues
- BUG-1/2/3 with shared root cause explanation
- use_rrf spec conflict documented
- Stage count discrepancy documented
- Both module naming inconsistencies documented
