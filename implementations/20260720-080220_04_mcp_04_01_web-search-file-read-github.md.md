# Implementation Procedure: docs/04_mcp_04_01_web-search-file-read-github.md

Source plan: `plans/20260719-192933_plan.md` ("Validate WebSearchConfig and align search_web input schema")

## Goal

Extend the existing web-search-mcp server-catalog entry to describe the new
config-validation invariants and query-normalization behavior once implemented in
`web_search_models.py` and `web_search_tools.py`, so the doc stays accurate and does
not silently go stale relative to the code.

## Scope

**In scope**
- The `web-search-mcp` section (currently L29-55) of
  `docs/04_mcp_04_01_web-search-file-read-github.md`: the tool-schema table
  (L37-39) and the existing 2026-07-17 note (L48).

**Out of scope**
- Any other server section in this same catalog file (`file-read-mcp`,
  `github-mcp`, etc. — untouched).
- Any other doc file.
- Actually implementing the code this doc describes (see the other four
  `implementations/` docs from this cycle for that).

## Assumptions

1. Per `rules/coding.md`'s "Current behavior" classification table: this update is
   an "Accepted current specification" once the code changes land — it describes
   new intended behavior, not a gap between doc and code, so it is written as plain
   prose in the normal section, not as an "Implementation fix required" issue.
2. This doc update should happen *after* (or together with) the `web_search_models.py`
   and `web_search_tools.py` changes land, so the prose describes shipped behavior,
   not aspirational behavior — sequence this doc's edit last in the implementation
   order.
3. The doc is Japanese-language prose (per the file's existing convention); new
   text should match that convention (this repo's `rules/coding.md` "English only"
   rule applies to code comments/log output, not to this doc's own established
   Japanese narrative content).

## Implementation

### Target file

`docs/04_mcp_04_01_web-search-file-read-github.md`

Current shape (verified by reading the live file):
- L29-55: `## web-search-mcp（ポート 8004）` section.
- L35-39: tools table — single row: `search_web` | `{query: str, max_results?: int}`
  input | result-block output. No mention of length/range bounds today.
- L41-46: config-parameters table — `default_max_results` (default `5`),
  `max_results_limit` (default `20`).
- L48: existing note dated 2026-07-17, describing that these two config keys are
  wired into `SearchRequest.max_results`'s Pydantic `Field` `ge`/`le`/default via
  `WebSearchConfig.load()` at module-import time. Note: this line currently refers
  to the file by its pre-rename name `mcp_servers/web_search/models.py` — the live
  file is `web_search_models.py` (see this plan's revision note); whether to also
  correct that stale filename reference here is a judgment call for whoever
  performs this edit, tracked as a minor pre-existing inconsistency, not part of
  this doc's new content requirement.

### Procedure

1. Extend the tools table (L37-39) or add a follow-up note directly below it,
   documenting the new bounds: `query` must be 1-500 characters (non-empty after
   trimming), `max_results` must be between 1 and the configured
   `max_results_limit` (hard-capped at `HARD_MAX_RESULTS_LIMIT=100` regardless of
   config).
2. Add a new dated note (e.g. `**注記(2026-07-XX):**`, using the actual
   implementation date) directly after the existing L48 note, describing:
   - `WebSearchConfig.from_dict()` now validates the four invariants
     (`default_max_results >= 1`, `max_results_limit >= 1`,
     `default_max_results <= max_results_limit`,
     `max_results_limit <= HARD_MAX_RESULTS_LIMIT`) and raises on violation
     (fail-fast at process/import time).
   - `SearchRequest.query` is now normalized: leading/trailing whitespace is
     trimmed; empty-after-trim or control-character-containing queries are
     rejected.
   - The `search_web` tool's `inputSchema` (in `web_search_tools.py`) now carries
     `minLength`/`maxLength`/`minimum`/`maximum` matching these bounds, sourced
     from the same `_cfg` singleton — so a `max_results_limit` TOML change takes
     effect in `/v1/tools` only after a server restart (same lifecycle as the
     existing L48 note's `_cfg` binding), not immediately.
3. Do not alter the surrounding sections (`## file-read-mcp`, etc.) or the
   document's YAML frontmatter (L1-16).

### Method

This is a documentation-content change; no pseudocode applies. The new note
should be written as plain Japanese prose consistent with the existing L48 note's
register and terminology (e.g. reuse "モジュールインポート時にロードされる",
"フェイルファースト" if introducing the fail-fast concept, matching how L48 already
describes the `_cfg` binding).

### Details

- This edit should be sequenced after the code changes in
  `implementations/20260720-080006_web_search_models.py.md` and
  `implementations/20260720-080040_web_search_tools.py.md` land, so line numbers
  and behavior descriptions can be verified against the final implementation
  rather than the design-time draft.
- `uv run check-mcp-docs` (see `rules/toolchain.md`) checks routing-authority
  language consistency and active-MCP-issue cross-references; re-run it after this
  edit to confirm no doc-consistency regression, even though this specific check
  does not validate prose content changes like this one.
- No `deploy/deploy.sh` change is needed — this is a `docs/` file, not part of the
  `scripts/` copy list.

## Validation plan

Reference commands only (do not run as part of this design-only task; see
`rules/toolchain.md` for the authoritative sequence):

```bash
uv run check-mcp-docs
uv run pre-commit run --all-files
```

Manual review: read the updated `web-search-mcp` section end-to-end and confirm the
new note is consistent with the actual shipped behavior of `web_search_models.py`
and `web_search_tools.py` (cross-check field names, constants, and bound values
against the final code, not just this design doc's Method/Details).
