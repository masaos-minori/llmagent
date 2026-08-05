# Implementation Procedure: 04_mcp_06_06_verification-methods.md

## Goal

Deduplicate the repeated "operator_action_required / display-only, no auto-restart" note and
consolidate four near-identical degraded-response JSON examples into one compact Markdown table in
`docs/04_mcp_06_06_verification-methods.md`, §"ヘルスプローブレスポンスの例".

## Scope

- In scope: the "## ヘルスプローブレスポンスの例" section only (current lines 49-133 of the target file).
- Out of scope: any other section of this file, any other doc, any source code.

## Assumptions

- The plan's line references (verified against current file: lines 49, 51-63, 65-77, 79-133) still
  match the file as of this writing — confirmed via `grep -n` before writing this document.
- Consolidating the four degraded examples (rag-pipeline-mcp, github-mcp, mdq-mcp, git-mcp) into a
  table does not lose information needed by a reader diagnosing a degraded probe response.
- `shell-mcp` remains the one full degraded JSON example kept verbatim, since it best illustrates
  the general `dependencies`/`details` shape.

## Design decisions

- Keep exactly one full degraded JSON example (`shell-mcp`) plus one healthy example — this is a
  documentation edit, not a schema change, so no code-level design tradeoffs apply; the only
  "design" decision is information architecture (JSON blocks -> table row) per
  `skills/python-design/workflow.md` Step 5 guidance (keep data-model-adjacent descriptions at
  semantic/summary level, avoid redundant exhaustive listings).
- Introduce the note as a single introductory sentence above the table rather than repeating it
  per row, per `rules/coding.md` "Documentation notes" classification: this is an "Accepted current
  specification" case (behavior is correct/intentional), so it is written as plain prose with no
  special framing — not an issue-filed discrepancy.

## Alternatives considered

- Keep all five full JSON blocks and only dedupe the trailing sentence: rejected — plan calls for a
  table to reduce structural repetition (dependencies key / error string / port), not just the
  redundant sentence.
- Drop `shell-mcp`'s full JSON example too and fold everything into the table: rejected — plan
  explicitly requires retaining one full JSON example as a format reference for readers.

## Implementation

### Target file

`docs/04_mcp_06_06_verification-methods.md`

### Procedure

1. Open `docs/04_mcp_06_06_verification-methods.md`.
2. Keep the healthy base-response example (current lines 51-63) unchanged.
3. Keep the `shell-mcp` degraded example (current lines 65-77) unchanged, including its trailing
   explanatory sentence (line 77) — this is the one example that keeps the full sentence since it
   is the reference example, not part of the deduplicated group.
4. For the four remaining degraded examples (rag-pipeline-mcp lines 79-91, github-mcp lines 93-105,
   mdq-mcp lines 107-119, git-mcp lines 121-133): delete the JSON code blocks and their trailing
   per-example sentences (lines 91, 105, 119, 133 specifically, per the plan).
5. Insert one introductory sentence before the new table: "全ての degraded 例について: `/mcp status`
   の `health_reason` に `operator_action_required` として反映される（表示のみ；自動的な再起動は行われない）。"
6. Insert the replacement table (columns: Server, Port, `dependencies` key, Error Message /
   `details`) with the four rows specified in the plan (rag-pipeline-mcp/8010/embed_url/"not
   configured"; github-mcp/8006/github_token/"not_set"; mdq-mcp/8013/db_file/"not found:
   /opt/llm/db/mdq.sqlite" with details `{"service": "mdq-mcp", "database":
   "/opt/llm/db/mdq.sqlite"}`; git-mcp/8014/git/"git not found in PATH").
7. Leave the rest of the file (including "## /v1/tools による検証" and everything after) untouched.

### Method

- Use `Edit` (string replacement) scoped to the exact block spanning the four degraded examples;
  do not touch the healthy or `shell-mcp` blocks.
- Verify post-edit with `grep -n` for the section header and the four server names to confirm the
  table replaced the JSON blocks and no duplicate sentence remains.

### Details

- Current file state (verified via `grep -n` + targeted `Read` of lines 49-137, not full-file read):
  - Line 49: section header `## ヘルスプローブレスポンスの例`.
  - Lines 51-63: healthy example — retain as-is.
  - Lines 65-77: `shell-mcp` (port 8009) degraded example — retain as-is, including line 77's
    sentence.
  - Lines 79-133: four degraded examples for rag-pipeline-mcp, github-mcp, mdq-mcp, git-mcp —
    replace with intro sentence + table.
  - Line 135: `## /v1/tools による検証` — unaffected, marks end of edit region.
- No other doc or source file references need updating; this section is self-contained prose/JSON.

## Compatibility considerations

- Documentation-only change; no API, schema, or behavior compatibility impact.
- Anchor links to `## ヘルスプローブレスポンスの例` are preserved (heading text unchanged).

## Security considerations

N/A — no secrets, tokens, or credentials are introduced; existing examples already use
non-sensitive placeholder values (e.g., `"not_set"`, `"not configured"`).

## Rollback considerations

- Single-file Markdown edit; revert via `git checkout -- docs/04_mcp_06_06_verification-methods.md`
  or `git revert` of the associated commit if issues are found post-merge.
- No migration or data-state rollback needed.

## Validation plan

Per `rules/toolchain.md`, this is a docs-only change so the Python validation sequence (ruff,
mypy, lint-imports, bandit, pytest, diff-cover) does not apply. Validation instead follows the
plan's own validation plan:

| Target File | Testing Strategy | Expected Outcome |
|---|---|---|
| `docs/04_mcp_06_06_verification-methods.md` | Manual review of the restructured section; `grep -n` for the four server names and the section header to confirm the JSON blocks were replaced and no duplicate sentence remains | Section contains exactly 1 healthy example, 1 full degraded example (`shell-mcp`), 1 intro sentence, and the 4-row summary table; no redundant per-example sentence remains |
| repo-wide | `uv run check-mcp-docs` (per `rules/toolchain.md` "MCP documentation consistency") | No new port-drift or broken-link findings introduced by the edit |

## Out of scope

- Any change to `shell-mcp`'s example or the healthy example beyond leaving them untouched.
- Any change to sections other than "## ヘルスプローブレスポンスの例".
- Any source code change (this is a pure documentation edit).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-064310_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-125855
- Related target files: docs/04_mcp_06_06_verification-methods.md
