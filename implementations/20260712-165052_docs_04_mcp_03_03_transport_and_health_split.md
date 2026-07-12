# Implementation Procedure: docs/04_mcp_03_03_transport-and-health.md size-limit split

Source plan: `plans/20260712-163522_plan.md`, Implementation steps 1-8

## Goal

Split `docs/04_mcp_03_03_transport-and-health.md` (8721 bytes, over the 8192-byte limit enforced
by `tools/validate_docs_structure.py`) into `-part1.md`/`-part2.md`, and update every referring
file so no broken links remain.

## Scope

**In scope:**
- Creating `docs/04_mcp_03_03_transport-and-health-part1.md` and `-part2.md`.
- Deleting `docs/04_mcp_03_03_transport-and-health.md`.
- Updating 7 referring files: `docs/04_mcp_00_document-guide.md`,
  `docs/04_mcp_02_01_endpoints-and-transport.md`, `docs/04_mcp_02_03_audit-logging-and-errors.md`,
  `docs/04_mcp_03_01_dispatch-and-routing.md`, `docs/04_mcp_03_02_tool-registry.md`,
  `docs/04_mcp_03_04_tool-call-tracing-and-watchdog.md`,
  `docs/04_mcp_03_05_lifecycle-and-new-server.md`.

**Out of scope:**
- Any technical/body content change beyond what the split mechanically requires (no rewriting of
  prose).
- The front-matter dead-reference cleanup itself — that is a **prerequisite**, implemented by
  `implementations/20260712-164711_docs_front_matter_dead_reference_cleanup.md` (part of the
  `docs/04_mcp_03_routing_lifecycle_and_execution.md` dead-reference group, which includes this
  file). **Do not start this task until that cleanup has been applied to
  `docs/04_mcp_03_03_transport-and-health.md`'s front matter** (its `source:` field currently
  still lists the dead `04_mcp_03_routing_lifecycle_and_execution.md` — reconfirm with
  `grep -n "^source:" -A1 docs/04_mcp_03_03_transport-and-health.md` before starting; if the dead
  reference is still present, apply that cleanup step to this one file first).

## Assumptions

1. The file's current H2 structure (reconfirm with `grep -n "^## " docs/04_mcp_03_03_transport-and-health.md`
   before editing) is: `## HttpTransport (...)` (line 20), `## McpServerHealthRegistry (...)`
   (line 37), `## エンドツーエンドのツール呼び出し追跡` (line 79), `## Related Documents` (line
   122), `## Keywords` (line 130).
2. Splitting at the boundary between line 78 (`---` divider) and line 79 (start of
   `## エンドツーエンドのツール呼び出し追跡`) produces part1 ≈ 6457 bytes (lines 1-78, plus a new
   front matter block and H1) and part2 ≈ 2264 bytes (lines 79-139, plus a new front matter block
   and H1) — both comfortably under 8192 bytes.
3. The anchor `#end-to-end-tool-call-tracing` used by
   `docs/04_mcp_02_01_endpoints-and-transport.md:65` may already be a dangling/non-resolving
   anchor (the target heading is pure Japanese text; GitHub-style anchor slugs preserve Unicode
   characters rather than transliterating to English) — this is a **pre-existing** issue,
   independent of the split. This task only redirects the filename portion of the link to the
   correct half; it does not attempt to fix the anchor's resolvability.

## Implementation

### Target files

- New: `docs/04_mcp_03_03_transport-and-health-part1.md`
- New: `docs/04_mcp_03_03_transport-and-health-part2.md`
- Deleted: `docs/04_mcp_03_03_transport-and-health.md`
- Edited: the 7 referring files listed in Scope.

### Procedure

1. Confirm the front-matter prerequisite (see Out of scope note above) is satisfied.
2. Read the full current content of `docs/04_mcp_03_03_transport-and-health.md`.
3. Create `docs/04_mcp_03_03_transport-and-health-part1.md`:
   - Front matter: `title: "HttpTransport, McpServerHealthRegistry, and Tracing Correlation Keys (Part 1)"`,
     same `category`/`tags` as the original, `related:` = the original's `related:` list minus the
     dead entry (already removed by the prerequisite cleanup), `source:` =
     `04_mcp_03_03_transport-and-health-part1.md` (self-reference, per the
     `03_rag_02_02_ingestion_pipeline-crawler-part1.md` precedent of using part1's own filename as
     the `source:` for both halves).
   - Body: H1 heading (reuse or adapt the original H1) + `## HttpTransport (...)` section +
     `## McpServerHealthRegistry (...)` section (original lines 20-76), followed by
     `## Related Documents` and `## Keywords` sections (new, see step 5).
4. Create `docs/04_mcp_03_03_transport-and-health-part2.md`:
   - Front matter: `title: "... (Part 2)"`, same `category`/`tags`, same `related:` list,
     `source:` = `04_mcp_03_03_transport-and-health-part1.md` (part1's filename, matching the
     shared-source convention).
   - Body: H1 heading (Part 2 variant) + `## エンドツーエンドのツール呼び出し追跡` section
     (original lines 79-118, including `### 相関キー` and `### 成功パスの例`), followed by
     `## Related Documents` and `## Keywords`.
5. For both new files' `## Related Documents` section, list the same files the original's
   `## Related Documents` listed (lines 122-128), plus a cross-reference from part2 to part1 (and
   vice versa) so a reader landing on either half can find the other.
6. Delete `docs/04_mcp_03_03_transport-and-health.md`.
7. Update `docs/04_mcp_02_01_endpoints-and-transport.md:65`: change the link target from
   `04_mcp_03_03_transport-and-health.md#end-to-end-tool-call-tracing` to
   `04_mcp_03_03_transport-and-health-part2.md#end-to-end-tool-call-tracing` (filename only; leave
   the anchor text unchanged per Assumption 3).
8. Update `docs/04_mcp_02_03_audit-logging-and-errors.md:60`: change the link target from
   `04_mcp_03_03_transport-and-health.md#httptransport` to
   `04_mcp_03_03_transport-and-health-part1.md#httptransport`.
9. Update `docs/04_mcp_00_document-guide.md:76`: expand the compact `_03` link in the index table
   to two links, one for each part, following the file's existing compact-notation style (e.g.
   `[_03a](04_mcp_03_03_transport-and-health-part1.md)/[_03b](...part2.md)` or similar — match
   whatever bracket/label convention the surrounding table cells already use; read the full line
   before editing to preserve the exact style).
10. Update the front matter `related:` and body `## Related Documents` list in each of
    `docs/04_mcp_03_01_dispatch-and-routing.md`, `04_mcp_03_02_tool-registry.md`,
    `04_mcp_03_04_tool-call-tracing-and-watchdog.md`, `04_mcp_03_05_lifecycle-and-new-server.md`:
    replace the single `04_mcp_03_03_transport-and-health.md` entry with two entries (part1 and
    part2) in both the front-matter list and the body list.
11. Run the `grep` residual-reference check (see Validation plan) to confirm no exact-match
    `04_mcp_03_03_transport-and-health.md` string remains anywhere under `docs/`.

### Method

No code is involved; this is pure Markdown file creation/deletion/editing. Use `Read` to capture
full original content before splitting, `Write` for the two new files, `Edit` for the 7 referring
files, and `Bash`(`git rm`) or direct deletion for the original file.

### Details

- Preserve all technical prose verbatim within each half — no rewording.
- Match the front-matter YAML style (indentation, key order) of an already-split sibling, e.g.
  `docs/04_mcp_03_01_dispatch-and-routing.md`, for consistency.
- Do not fix the `#end-to-end-tool-call-tracing` anchor's underlying resolvability — flagged in
  Assumption 3 as pre-existing and out of scope.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Size limit | `uv run python tools/validate_docs_structure.py` | No size-exceeded error for either new file; overall `All checks passed` |
| RAG doc consistency | `uv run python tools/check_docs_consistency.py` | Passed |
| MCP doc consistency | `uv run python tools/check_mcp_docs_consistency.py` | No new failures beyond the two pre-existing/unrelated warnings (server-catalog-not-found — fixed by a separate plan; is_error=True false positive — accepted, no action) |
| No residual old filename | `grep -rn "04_mcp_03_03_transport-and-health\.md" docs/` | Zero matches (only `-part1.md`/`-part2.md` suffixed strings should appear anywhere) |
| Content completeness | Manual diff: concatenate part1+part2 bodies and compare against the original file's body (excluding front matter/H1 duplication) | No prose lost or duplicated |
