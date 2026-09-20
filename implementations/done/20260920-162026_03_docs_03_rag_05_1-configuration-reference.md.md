## Goal
Remove the four code-fallback-vs-operational-value comparison cells in
`docs/03_rag_05_1-configuration-reference.md`'s `## 1.4 config/rag_pipeline_mcp_server.toml`
table (lines 93, 94, 96, 99 — `top_k_search`, `top_k_rerank`, `rag_min_score`,
`refiner_max_chars_per_chunk`), per `REQ-003` (Plan `plans/20260920-155829_plan.md`),
so `tools/check_docs_content_policy.py` reports no finding at these four locations,
while the code-default-vs-operational-value divergence remains documented.

## Scope
In scope: the four flagged table cells' `Default` column content only. Out of scope:
every other row of this table (`sqlite_busy_timeout_ms`, `llm_url`, `embed_url`, etc.,
none of which were flagged), the rest of this file's sections (e.g. `## 1.1`-`## 1.3`,
`## Hardcoded Values`), and any other `docs/*.md` file.

## Assumptions
The four findings (lines 93, 94, 96, 99) and the file's exact current content
(re-verified via Read during this document's creation) have not shifted since the Plan
was frozen — no commit has touched this file since.

## Design decisions
Step 3a's verification found that this file already contains, at lines 107-110 (the
existing `## Implementation Supplements (Current behavior)` section), a prose
explanation of exactly the divergence the four flagged cells restate: "the following
parameters — `top_k_search`, `top_k_rerank`, `rag_min_score`, and
`refiner_max_chars_per_chunk` — have different default values in
`RagPipelineConfig`... compared to what is written in the operational
`config/rag_pipeline_mcp_server.toml`... As long as values exist in the `.toml` file,
the code defaults are ignored." This corrects the Plan's `REQ-003` wording ("add one
prose sentence") — no new sentence needs to be authored from scratch; the canonical
divergence statement already exists. Simplify each flagged cell's `Default` column to
the code default value alone (dropping the `(code default; operational config uses
N)`/`(operational config value)` parenthetical), and add a single forward-reference
sentence immediately after the table pointing to the existing "Implementation
Supplements" section, rather than duplicating its content inline.

## Alternatives considered
- Author a brand-new explanatory sentence per the Plan's literal wording, ignoring the
  existing "Implementation Supplements" section: rejected — this would create a second,
  independent statement of the same fact, reintroducing exactly the multi-place-sync
  duplication risk this policy targets (the same failure mode Background describes for
  the per-role-token fields elsewhere in this cleanup effort).
- Show only the operational value (drop the code default entirely): rejected — the code
  default is itself meaningful (it is what applies if the `.toml` key is ever removed,
  per line 109's own caveat: "be aware of this difference if deleting or simplifying
  the `.toml` file"); removing it would lose that warning's referent.

## Implementation
### Target file
`docs/03_rag_05_1-configuration-reference.md`

### Procedure
1. Read lines 80-113 to confirm current content matches the Plan's recorded evidence,
   including the existing `## Implementation Supplements` section at lines 107-110.
2. In the `## 1.4` table, edit exactly four `Default` column cells:
   - Line 93 (`top_k_search`): `` `5` (code default; operational config uses `20`) `` →
     `` `5` ``
   - Line 94 (`top_k_rerank`): `` `10` (code default; operational config uses `15`) ``
     → `` `10` ``
   - Line 96 (`rag_min_score`): `` `0.0` (code default; operational config uses `2.0`)
     `` → `` `0.0` ``
   - Line 99 (`refiner_max_chars_per_chunk`): `` `800`(code default; operational config
     uses `300`) `` → `` `800` ``
3. Immediately after the table (currently followed by the `**Note (2026-07-13):**
   ...call_rag_service()...` paragraph at line 105), add one sentence pointing to the
   `## Implementation Supplements` section below for the current operational values of
   these four parameters, which may differ from the code defaults shown above.
4. Leave the existing `## Implementation Supplements (Current behavior)` section
   (lines 107-110) and every other row/section of this file unchanged — it already
   states the divergence and its operational-vs-code-default rationale.

### Method
Two localized `Edit` calls: one covering the four cell edits in the `## 1.4` table
(step 2, `replace_all` is not appropriate here since each cell's operational value
differs — apply as one Edit per distinct cell text, or a single Edit spanning lines
93-99 if contiguous enough to match as one block), and one inserting the
forward-reference sentence (step 3). Do not touch lines 107-110 or any other section.

### Details
Do not delete or reword the existing `## Implementation Supplements` paragraph — it is
the canonical, already-present statement of this exact divergence and is what the new
forward-reference sentence points to. The forward-reference sentence added in step 3
must not restate the four parameter names' specific values (that restatement is exactly
what this cleanup removes) — it states only that a divergence exists and where to read
about it.

## Compatibility considerations
`N/A: documentation-only change, no code, public interface, or data format is affected`.

## Security considerations
`N/A: no security-relevant content is touched`.

## Rollback considerations
Revert via `git checkout` on this one file. The cell edits and the forward-reference
sentence are both reversible independently of the other three Plan rows' files.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` — confirm zero findings for
  `docs/03_rag_05_1-configuration-reference.md` (Plan `AC-3`).
- `uv run python tools/check_docs_quality.py`, scoped to this file — confirm no new
  warning is introduced.
- `uv run python tools/check_docs_structure.py docs/03_rag_05_1-configuration-reference.md`
  — confirm it passes.
- `uv run python tools/check_docs_consistency.py --domain rag` — confirm no new drift
  finding, and that the four simplified `Default` cells still match
  `RagPipelineConfig`'s actual code defaults (this checker cross-references
  `config/agent.toml`/`scripts/`, not this specific `.toml`, so this is a manual
  spot-check, not something the tool itself verifies for this file).

## Completion criteria
None of the four cells restates both a code default and an operational value in the
same cell; a single sentence after the table points readers to the existing
"Implementation Supplements" section for the divergence; that section itself is
unchanged; `check_docs_content_policy.py` reports zero findings for this file.

## Out of scope
- Every other row of the `## 1.4` table and every other section of this file (see
  Scope) — not flagged, not part of `REQ-003`.
- Any other `docs/*.md` file — see the Plan's other three target-file rows, each with
  its own implementation procedure document.
- Extending `check_docs_content_policy.py`'s detection rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-165829 | 20260920-165829 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260920-165829 | 20260920-165829 | N/A: documentation-only, no automated test beyond the doc checkers already listed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-165829 | 20260920-165829 | Scoped to the doc checkers in Validation plan, not the full Python toolchain (no `scripts/` change) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-165829 | 20260920-165829 | N/A: this document IS the documentation change |

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
- **Requirement ID**: `REQ-003` — remove the code-fallback-vs-operational-value comparison cells
- **Source issue**: issues/20260920-154305_dcp009_rag-docs-content-policy-cleanup-batch-2.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-155829_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-162026
- **Related target files**: docs/03_rag_05_1-configuration-reference.md