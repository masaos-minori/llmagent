# Implementation: docs/mdq_config_history.md (new)

Source plan: `plans/20260719-212210_plan.md` ("Clarify MDQ parser scope, audit-log policy, and
config documentation"), Design item 3 / Implementation step "Phase 1 — Config history
relocation".

**Existing-doc check:** `ls implementations/ implementations/done/ | grep -F
"mdq_config_history"` and `rg -l "config_history" docs/` both return zero matches — this
filename has no prior implementation doc and the target doc does not yet exist under `docs/`.
No overlap to reconcile; this is a fresh item.

## Goal

Create a new standalone doc, `docs/mdq_config_history.md`, that holds the six historical
removed-config-key `NOTE` blocks currently embedded as comments in
`config/mdq_mcp_server.toml:50-95`, verbatim, so the rationale and removal dates for each
removed key remain discoverable without cluttering the active config file. This document has no
functional effect — it is a documentation relocation, not a behavior change.

## Scope

**In scope:**
- Create `docs/mdq_config_history.md` containing:
  1. A short intro sentence explaining the doc's purpose (historical record of config keys
     removed from `config/mdq_mcp_server.toml`, for anyone who finds a stale reference to one of
     these keys or wonders why it's gone).
  2. The six `NOTE` blocks copied **verbatim** (not paraphrased) from
     `config/mdq_mcp_server.toml:50-95`, one per removed key, preserving exact wording and
     dates:
     - `audit_log_path` (removed 2026-07-13; lines 50-54)
     - `concurrency_limit` (removed 2026-07-13; lines 56-60)
     - `max_search_results` (removed 2026-07-16; lines 62-65)
     - `use_embedding` / `embedding_dims` / `vector_table` / `embedding_model` (removed
       2026-07-16; lines 67-73)
     - `summary_cache_enabled` / `summary_threshold` / `summary_model` (removed 2026-07-16;
       lines 75-82)
     - `enable_refresh` (removed 2026-07-16; lines 84-89)
     - `status` (removed 2026-07-17; lines 91-95)

**Out of scope:**
- Any edit to `config/mdq_mcp_server.toml` itself — covered by the companion doc
  `implementations/20260720-095417_mdq_mcp_server.toml.md` (Phase 1, second half).
- Any change to `scripts/mcp_servers/mdq/*.py` — none of these keys are read by any current
  code (already verified by the plan's Assumptions and by the existing NOTE text itself).
- Any other doc under `docs/` — `docs/04_mcp_04_04_mdq.md`'s own config-field-list parenthetical
  (line 27) already summarizes these removals briefly and is left as-is; no cross-reference edit
  is required there since it does not reproduce the NOTE text itself.

## Assumptions

1. `docs/mdq_config_history.md` does not currently exist (`ls docs/mdq_config_history.md` →
   "No such file or directory", confirmed by direct check during this design cycle).
2. `config/mdq_mcp_server.toml` lines 50-95 currently contain exactly the six `NOTE` blocks
   listed above, confirmed by direct read of the file during this design cycle (line numbers
   match the plan's citations exactly, no drift).
3. `deploy/deploy.sh` does not copy `docs/` at all (per the plan's Assumption 6), so this new
   file requires no `deploy/deploy.sh` edit.
4. This document is for AI/operator reference only — it is not consumed by any code, not linked
   from `routing.md`'s "Docs → task mapping" table (out of scope to add it there; that table
   maps task types to domain-spec docs, not one-off historical-record docs).

## Implementation

### Target file

`docs/mdq_config_history.md` (new file)

### Procedure

1. Create the file with YAML frontmatter matching the convention used by other `docs/*.md`
   files (see `docs/04_mcp_04_04_mdq.md:1-14` for the pattern: `title`, `category`, `tags`,
   `related`).
2. Write a one-paragraph intro stating the doc's purpose and pointing back to
   `config/mdq_mcp_server.toml` as the place where the pointer comment now lives.
3. Add one subsection per removed key (or key group), each containing the verbatim NOTE text
   (reformatted from `#`-prefixed comment lines into plain Markdown prose — same wording, no
   `#` comment markers).
4. Order the subsections chronologically by removal date (2026-07-13 keys first, then
   2026-07-16 keys, then the 2026-07-17 key) to mirror the config file's existing top-to-bottom
   order, so a reader can cross-reference the pointer comment's key-name list against this doc
   in the same sequence.

### Method

Content relocation only — no new facts, no new decisions. Pseudocode for the document
structure (not a literal file dump, since the source content is lengthy and already fully
specified verbatim in `config/mdq_mcp_server.toml:50-95`):

```
---
title: "MDQ Config: Removed Key History"
category: mcp
tags: [mcp, mdq, config, history]
related:
  - 04_mcp_04_04_mdq.md
  - ../config/mdq_mcp_server.toml   # (descriptive only; not a real relative-link target)
---

# MDQ Config: Removed Key History

<intro paragraph: these keys were once part of config/mdq_mcp_server.toml;
 they are documented here instead of as inline comments so the active config
 file stays short and readable>

## `audit_log_path` (removed 2026-07-13)
<verbatim text from config/mdq_mcp_server.toml:50-54>

## `concurrency_limit` (removed 2026-07-13)
<verbatim text from config/mdq_mcp_server.toml:56-60>

## `max_search_results` (removed 2026-07-16)
<verbatim text from config/mdq_mcp_server.toml:62-65>

## `use_embedding`, `embedding_dims`, `vector_table`, `embedding_model` (removed 2026-07-16)
<verbatim text from config/mdq_mcp_server.toml:67-73>

## `summary_cache_enabled`, `summary_threshold`, `summary_model` (removed 2026-07-16)
<verbatim text from config/mdq_mcp_server.toml:75-82>

## `enable_refresh` (removed 2026-07-16)
<verbatim text from config/mdq_mcp_server.toml:84-89>

## `status` (removed 2026-07-17)
<verbatim text from config/mdq_mcp_server.toml:91-95>
```

### Details

- The verbatim text for each section must be copied exactly from the current
  `config/mdq_mcp_server.toml` (read the file fresh at implementation time in case line numbers
  have shifted since this design cycle — see the plan's own "line numbers may have shifted"
  risk).
- Do not summarize or shorten the NOTE text — the whole point of this relocation is to preserve
  the precise rationale and dates without loss, per the plan's stated risk mitigation ("copy the
  six NOTE blocks verbatim, not paraphrased").
- Keep the `#`-comment-style line wrapping (~78-80 col) or reflow to normal prose paragraphs —
  either is acceptable since this is documentation, but reflowing to full sentences (removing
  the mid-word line breaks visible in the raw comment, e.g. "frontmat-\nter" style wraps) improves
  readability; a straight verbatim comment-block quote (in a fenced block) is also acceptable
  as long as no words are altered.

## Validation plan

| Check | Command | Expected outcome |
|---|---|---|
| File created | `ls docs/mdq_config_history.md` | File exists |
| Content completeness | Manual diff-review: compare each subsection's prose against the original `config/mdq_mcp_server.toml:50-95` NOTE text | No rationale, date, or key name lost or altered |
| No source/runtime edits | `git status` | Only `docs/mdq_config_history.md` (and the companion `config/mdq_mcp_server.toml` trim, tracked separately) appear as changed; nothing under `scripts/` |
| Doc consistency | `uv run check-mcp-docs` | Passes (new doc file does not participate in routing/fail-open/toolcount checks, but confirms no regression) |
| Pre-commit | `uv run pre-commit run --all-files` | Passes (Markdown lint / trailing whitespace / frontmatter checks if configured) |
