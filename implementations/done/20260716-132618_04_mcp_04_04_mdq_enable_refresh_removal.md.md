# Implementation: docs/04_mcp_04_04_mdq.md (drop `enable_refresh` from field list)

Source plan: `plans/20260716-131759_plan.md`

Note: a fifth distinct change targeting this doc file, alongside the four
other `04_mcp_04_04_mdq.md` docs already created for plans 01, 02, 04, and
05. All five touch different parts of the same 設定フィールド line/doc —
apply all five (see those docs for the full list).

## Goal

Remove `enable_refresh` from the 設定フィールド (config field) list — it
is confirmed dead per the companion `service.py`/`config.toml` docs for
this plan.

## Scope

**In:**
- The 設定フィールド line: remove `enable_refresh` from the
  comma-separated field list.

**Out:**
- `enable_grep` in the same list — stays, unchanged; it remains a real,
  enforced feature gate.
- Every other field name in the same line (already handled by the four
  companion docs for plans 01, 02, 04, 05).
- Any other section of this doc.

## Assumptions

1. This edit must land after (or together with) the companion `service.py`
   doc (removes `self.enable_refresh`) and `config/mdq_mcp_server.toml`
   doc (removes the `enable_refresh` key) — otherwise the doc would omit a
   key that still exists in code/config.
2. Because five separate docs edit the same 設定フィールド line, apply
   each independently (each targets a disjoint field name/substring) and
   re-read the line after each edit to confirm no malformed intermediate
   Markdown/comma-list state.

## Implementation

### Target file

`docs/04_mcp_04_04_mdq.md`

### Procedure

1. Open `docs/04_mcp_04_04_mdq.md`.
2. Locate the 設定フィールド line (content-match, since exact line number
   shifts as companion docs land).
3. Remove `enable_refresh` from the comma-separated field list, leaving
   `enable_grep` and all other remaining field names intact.

### Method

Single-line text edit removing one field name from a comma-separated list.

### Details

- Preserve the doc's existing Markdown formatting conventions.
- Cross-check against the four other same-file companion docs before
  finalizing.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Field removed | `grep -n "enable_refresh" docs/04_mcp_04_04_mdq.md` | 0 matches |
| `enable_grep` intact | `grep -n "enable_grep" docs/04_mcp_04_04_mdq.md` | 1 match, unchanged |
| Doc consistency | `uv run check-mcp-docs` | passes |
