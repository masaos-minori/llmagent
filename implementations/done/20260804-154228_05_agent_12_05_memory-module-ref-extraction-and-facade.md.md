# Implementation Procedure: Fix stale `EmbeddingClientConfig` field list at docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md:67

## Goal

Correct `docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md:67` so the documented
`EmbeddingClientConfig` field list matches the actual dataclass in
`scripts/agent/memory/embedding_client.py`, by removing the two non-existent fields
`query_prefix="query: "` and `embed_dim=384`.

## Scope

**In scope:**
- Edit line 67 of `docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md` only.

**Out of scope:**
- `scripts/agent/memory/embedding_client.py` (read-only reference; confirmed correct, not modified).
- Any other line/section of the target doc, or any other `docs/*.md` file (their unrelated
  `embed_dim` references, e.g. `MemoryStore`/`memory_embed_dim`, are accurate as-is).

## Assumptions

1. `EmbeddingClientConfig` currently has exactly six fields — verified directly at
   `scripts/agent/memory/embedding_client.py:31-39`: `embed_url: str = ""`,
   `timeout: float = 5.0`, `max_retries: int = 2`, `circuit_open_after: int = 3`,
   `circuit_reset_sec: float = 60.0`, `local_only: bool = False`. No `query_prefix` or
   `embed_dim` field exists.
2. Line 67 of the target doc, verified via `grep -n "EmbeddingClientConfig"`, currently reads:
   `` `EmbeddingClientConfig`: embed_url, timeout=5.0, max_retries=2, circuit_open_after=3, circuit_reset_sec=60.0, query_prefix="query: ", embed_dim=384, local_only=False。 ``
   — a single line, only one match in the file.
3. This is a pure documentation correction under `rules/coding.md`'s "Documentation fix
   required" category (doc is wrong, code is right) — fix the doc directly, no issue filing
   needed.

## Design decisions

- Edit only the stale substring on line 67 (removing `, query_prefix="query: ", embed_dim=384`),
  preserving the surrounding Japanese sentence, backtick-code formatting, and trailing `。`,
  rather than rewriting the whole line or paragraph — minimizes diff surface and review risk.
- Treat this as a targeted content fix, not a structural doc change — no heading, table, or
  section reorganization is warranted for a single stale field list.

## Alternatives considered

- Rewrite line 67 as a Markdown table (matching the `EmbeddingClient` method table style used
  just above it in the same file) — rejected: expands scope beyond the stale-field fix this
  plan authorizes, and the plan's Design section explicitly specifies a single-line text
  replacement.
- Leave a "Current behavior" note explaining the historical `query_prefix`/`embed_dim` fields
  instead of deleting them — rejected: per `rules/coding.md`'s classification table, this is
  "Documentation fix required" (stale text), not a case warranting an inline discrepancy note;
  the fields simply no longer exist in code.

## Implementation

### Target file

`docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md`

### Procedure

1. Re-confirm `EmbeddingClientConfig`'s current field set in
   `scripts/agent/memory/embedding_client.py` at implementation time (guards against
   intervening changes since this procedure was written).
2. Edit line 67 of the target doc, replacing the stale field list with the corrected one.
3. Grep the target doc and wider `docs/` tree for `query_prefix` and `embed_dim` to confirm no
   remaining `EmbeddingClientConfig`-related stale matches (unrelated `embed_dim` hits tied to
   `MemoryStore`/`memory_embed_dim` are expected and out of scope).
4. Review `git diff docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md` to confirm
   only line 67 changed.

### Method

Direct text replacement on a single Markdown line — no code, no template, no generation script
involved.

### Details

Replace:
```
`EmbeddingClientConfig`: embed_url, timeout=5.0, max_retries=2, circuit_open_after=3, circuit_reset_sec=60.0, query_prefix="query: ", embed_dim=384, local_only=False。
```
with:
```
`EmbeddingClientConfig`: embed_url, timeout=5.0, max_retries=2, circuit_open_after=3, circuit_reset_sec=60.0, local_only=False。
```

## Compatibility considerations

N/A — documentation-only change; no public API, schema, or runtime interface is affected. Not
deployed (`deploy/deploy.sh` only copies `scripts/` production files, not `docs/`).

## Security considerations

N/A — no code, secrets, or configuration involved; plain Markdown text edit.

## Rollback considerations

Trivial single-line revert via `git checkout -- docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md`
or `git revert` of the introducing commit; no migration or data-state implications.

## Validation plan

| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| Line 67 | Manual re-read | `sed -n '67p' docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md` | Lists exactly the 6 current fields, no `query_prefix`/`embed_dim` |
| Whole file | No unintended edits | `git diff docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md` | Only line 67 changed |
| Repo-wide safety check | No stale references remain | `rg -n "query_prefix|embed_dim" docs/` | Zero `query_prefix` matches; only pre-existing unrelated `embed_dim` references remain |
| Source dataclass | Unchanged | `git diff scripts/agent/memory/embedding_client.py` | No output (file untouched) |

No automated tests, lint, type-check, or coverage gates apply — documentation-only change.

## Out of scope

- Any change to `scripts/agent/memory/embedding_client.py`.
- Any change to other lines/sections of the target doc, or to any other `docs/*.md` file.
- Adding a "Current behavior" discrepancy note (not applicable — this is a stale-text fix, not
  a code/doc behavioral mismatch to annotate).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-140117_plan.md
- Source implementation procedure: N/A
- Generated at: 20260804-154228
- Related target files: 05_agent_12_05_memory-module-ref-extraction-and-facade.md
