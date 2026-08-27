## Goal

Remove the stale `embedding_dims`-config-key claim (2 occurrences) in
`docs/03_rag_05_5-constraints-reference.md` (REQ-004), per
`plans/20260826-151220_plan.md`.

## Scope

- In scope: the "Embedding dimensions" constraint row (verified at line 22 as
  of 2026-08-27) and the "Crawl depth and max pages" note's `embedding_dims`
  line-number reference (verified at line 29 as of 2026-08-27).
- Out of scope: the rest of the "Crawl depth and max pages" note (its
  `crawler.toml` values and "Line number references are deprecated" guidance —
  still accurate, do not alter).

## Assumptions

- `config/agent.toml`/`config/ingester.toml` have no `embedding_dims` key
  (re-verified 2026-08-27).
- Line 29's mention of `embedding_dims` is incidental (used only as an example
  of a deprecated line-number reference, within an unrelated note about crawl
  depth/max pages defaults) — it does not itself assert a current config
  behavior claim requiring the same correction as line 22, but it does still
  reference a key that no longer exists, so it should be updated to avoid
  perpetuating the reference.

## Design decisions

- Line 22: replace "384 (`config/agent.toml:embedding_dims`, and
  `config/ingester.toml:embedding_dims`)" with a reference to the fixed code
  constant, per REQ-004's sourcing rule.
- Line 29: the note's own point is that "line number references are
  deprecated" — the specific example given happens to be `embedding_dims`'s
  former line number; since `embedding_dims` no longer exists as a config key
  at all, replace this illustrative example with a still-valid one (any
  current `config/agent.toml` key) rather than leaving a reference to a
  now-nonexistent key as the example.

## Alternatives considered

- Leaving line 29 unchanged (since it is "historical" framing about a
  deprecated referencing style) was considered and rejected — the note's
  illustrative example itself references a key that no longer exists, which
  could confuse a reader trying to verify the example against current
  `config/agent.toml`; using a still-valid example preserves the note's
  pedagogical point without the stale reference.

## Implementation
### Target file
`docs/03_rag_05_5-constraints-reference.md`

### Procedure
1. Re-confirm current line numbers for both occurrences immediately before
   editing (verified at lines 22 and 29 as of 2026-08-27).
2. Rewrite line 22's "Embedding dimensions" row per Method/Details.
3. Rewrite line 29's illustrative example per Method/Details.
4. Run `.venv/bin/python3 tools/check_docs_consistency.py --domain rag` and
   confirm no new warning/error.

### Method
Direct text edits (Edit tool) — one table row, one illustrative-example clause
within a note.

### Details
Current text (verified 2026-08-27):
- Line 22: `| Embedding dimensions | 384
  (\`config/agent.toml:embedding_dims\`, and
  \`config/ingester.toml:embedding_dims\`). float32 little-endian BLOB |`
- Line 29: `- Crawl depth and max pages: Explicit in code, but operational
  values in \`config/crawler.toml\` differ from code defaults. Previous
  versions stated "\`config/agent.toml:43\`", "max 6 hops", and "max 500
  pages", but in the current \`config/agent.toml\`, \`embedding_dims\` is on
  line 17, and actual \`config/crawler.toml\` values are \`max_depth=3\` and
  \`max_pages=200\`. Line number references are deprecated; use
  section-based references instead.`

Replace line 22 with:
```
| Embedding dimensions | Fixed code-level constant (`scripts/db/store_protocols.py::get_embedding_dims()`), not config-driven. float32 little-endian BLOB |
```
Replace line 29's `, but in the current \`config/agent.toml\`,
\`embedding_dims\` is on line 17,` clause with a still-valid illustrative
example (e.g. a key that genuinely exists in current `config/agent.toml` at a
specific line, or simply drop the specific-key illustration and keep the
general "line numbers shift, use section-based references instead" point) —
verify one current, stable example key/line before choosing a replacement, or
omit the specific-key illustration entirely if none is clearly stable.

## Compatibility considerations

- Documentation-only; no runtime behavior, config schema, or public interface
  is affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Two-occurrence text revert via `git diff`/`git checkout -- <path>`;
  independent of the other 14 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_05_5-constraints-reference.md` | Manual diff | `git diff <path>` | No config-key claim remains; deprecated-line-number-reference note's example no longer cites a nonexistent key |
| `docs/03_rag_05_5-constraints-reference.md` | Doc consistency check | `.venv/bin/python3 tools/check_docs_consistency.py --domain rag` | No new warning/error beyond baseline |

## Completion criteria

- Neither occurrence states `embedding_dims` is a `config/agent.toml`/
  `config/ingester.toml` key.

## Out of scope

- The rest of the "Crawl depth and max pages" note (crawler.toml values,
  general deprecation guidance).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line numbers for both occurrences | Completed | — | — | Verified at lines 22 and 29 |
| 2 | Rewrite the "Embedding dimensions" row | Completed | — | — | Config-key claim removed |
| 3 | Rewrite the illustrative example in the crawl-depth note | Completed | — | — | Replaced nonexistent `embedding_dims` reference with valid `embed_url` (line 10) |
| 4 | Run `check_docs_consistency.py --domain rag` | Completed | — | — | Pre-existing warnings only; no new findings |

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
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20260821_10_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-151220_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-112854
- **Related target files**: `docs/03_rag_05_5-constraints-reference.md`
