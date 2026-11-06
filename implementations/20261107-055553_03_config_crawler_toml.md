## Goal

- Make the `config/crawler.toml` NOTE comment truthful after the code fallback becomes 200 (REQ-003: comment
  no longer claims a 500 code default; rationale caveat kept).

## Scope
**Release unit**: fallback alignment

- Comment-only edit in the same release unit as the seq01 literal change: once the code fallback is 200, the
  comment's "500 in code" claim becomes false. The deployed value line is not touched.

## Assumptions

- No test reads the comment (Plan row evidence); AC-004 is checked by inspection in Phase 3.

## Design decisions

- Restate the same NOTE with the corrected values, keeping the "no measured justification" caveat intact.

## Alternatives considered

- Deleting the NOTE comment entirely: rejected — its rationale-tracking purpose (nc035 governance) is still
  needed; the Plan requires keeping it truthful.

## Implementation
### Target file
`config/crawler.toml`

### Procedure
- Replace the NOTE line (currently line 22) and only that line.

### Method
- Before: `# NOTE: max_pages default (500 in code, 200 in TOML) also lacks measured justification`
  After: `# NOTE: max_pages default (200 in both code and TOML) also lacks measured justification`

### Details
- The adjacent value line `max_pages = 200` (currently line 23) MUST NOT change (AC-004 pins it).

## Compatibility considerations

- N/A: comment-only change; TOML parsing and deployed behavior unaffected.

## Security considerations

- N/A: comment-only change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `grep -n "max_pages" config/crawler.toml` — value line still `max_pages = 200`; no "500 in code" text
  remains (AC-004).
- Full-suite gates for the whole Plan run once, documented in the seq01 document.

## Completion criteria

- AC-004: `max_pages = 200` unchanged; the comment no longer states a 500 code default; the rationale caveat
  is preserved.

## Out of Scope

- Any change to the value line or any other config key (`max_depth`, `skip_nofollow`, ...).
- The code fallback change itself (seq01 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the NOTE comment line in config/crawler.toml per Method (Plan Phase 2, REQ-003) | Pending | — | — | Release unit "fallback alignment": land with the seq01 literal change |
| 2 | Verify per Validation plan: grep shows value line unchanged and no "500 in code" claim | Pending | — | — | |

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
- **Requirement ID**: REQ-003 (config comment kept truthful about the code default)
- **Source issue**: issues/done/20261106-110944_ragfix002_orchestrator-max-pages-default.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-052809_ragfix002_orchestrator-max-pages-default.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-055553
- **Related target files**: config/crawler.toml
