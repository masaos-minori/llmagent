# Implementation Procedure: docs/03_rag_90_inconsistencies_and_known_issues-part2.md

Source plan: `plans/20260712-162509_plan.md`

## Goal

Replace the OPEN-02 entry (documented as unresolved) with a short resolved-note, since
`fmt_delete_document()` already invalidates the semantic cache in the current codebase.
Leave OPEN-01 untouched.

## Scope

**In scope:**
- `docs/03_rag_90_inconsistencies_and_known_issues-part2.md` lines 46-66 (the `### OPEN-02:` heading
  and its full body) only.

**Out of scope:**
- OPEN-01 (lines 29-42) — must remain byte-for-byte identical.
- `scripts/mcp_servers/rag_pipeline/service.py` / `document_manager.py` — no code change; the fix
  described here is already implemented, this task only updates stale documentation.
- The empty `## 未解決の課題` section (line 70) — pre-existing, unrelated to this task.
- front matter, `## Related Documents`, `## Keywords` sections.

## Assumptions

1. `scripts/mcp_servers/rag_pipeline/service.py`'s `fmt_delete_document()` still calls
   `self._pipeline_or_raise().invalidate_cache()` at lines 210-213 as of this writing — reconfirm
   with a direct read immediately before editing, since no code changes are expected between
   planning and implementation.
2. The resolved-note must be wrapped in **fullwidth** parentheses `（`/`）` (not ASCII `(`/`)`),
   matching the `UNDOC-02` precedent in `docs/05_agent_90_inconsistencies_and_known_issues.md`
   lines 40-47 exactly. This was a defect caught during plan review — verify it is honored.

## Implementation

### Target file

`docs/03_rag_90_inconsistencies_and_known_issues-part2.md`

### Procedure

1. Open the file and locate the `## キャッシュ無効化` section (line 27 as of planning time).
   Confirm OPEN-01 (`### OPEN-01: ...`) is present and ends with a `---` divider before OPEN-02
   begins.
2. Replace the entire OPEN-02 block — from `### OPEN-02: \`delete_document()\`はセマンティック
   キャッシュを無効化しない` through its last `**Recommended action:**` line — with a single
   heading-less italic paragraph (see Method below). Do not add a new `###` heading for it; the
   replacement is prose only, matching the `UNDOC-02` precedent style (a note under an existing
   heading, not its own subsection).
3. Do not touch anything before the `### OPEN-02:` line or after its final line (the following
   `---` divider that separates the `## キャッシュ無効化` section from `## 未解決の課題` stays
   as-is).
4. Re-read the whole file after editing to confirm no stray blank lines or duplicate `---`
   dividers were introduced.

### Method

Replacement text (verbatim, note the fullwidth wrapping parentheses):

```
*（OPEN-02「delete_document()はセマンティックキャッシュを無効化しない」は解決済み。
scripts/mcp_servers/rag_pipeline/service.py の fmt_delete_document()(210〜213行)が
削除成功時に self._pipeline_or_raise().invalidate_cache() を呼び出しており、
このエントリが指摘していたギャップはもはや存在しない。）*
```

### Details

- Use the `Edit` tool with `old_string` spanning the exact current OPEN-02 block (from
  `### OPEN-02:` through the final `あるいは、呼び出し元が別途キャッシュ無効化を行う必要がある
  旨をドキュメント化する。` line) and `new_string` as the replacement paragraph above.
- Do not use `replace_all`; this string should be unique in the file.
- Verify the surrounding `---` dividers: exactly one `---` must separate OPEN-01 from the new
  note, and exactly one `---` must separate the new note from `## 未解決の課題`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| RAG doc consistency | `uv run python tools/check_docs_consistency.py` | `All checks passed` |
| OPEN-01 unchanged | `git diff docs/03_rag_90_inconsistencies_and_known_issues-part2.md` | Only the OPEN-02 block is in the diff; OPEN-01's lines show no changes |
| Grep spot-check | `grep -n "OPEN-01\|OPEN-02" docs/03_rag_90_inconsistencies_and_known_issues-part2.md` | OPEN-01 heading line still present; OPEN-02 heading line no longer present (replaced by the prose note) |
