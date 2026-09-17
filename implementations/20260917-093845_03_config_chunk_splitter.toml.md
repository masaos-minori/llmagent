## Goal

Add an explicit "unvalidated heuristic, pending performance tuning" marker as TOML comments immediately above `min_chunk = 40`, `max_chunk = 500`, and `chunk_overlap = 50` in `config/chunk_splitter.toml` (lines 5-7) — one shared comment block covering all three, since they were filed as one NC entry (NC-034) and interact as a group. Per REQ-003; AC-1, AC-4.

## Scope

- Add a shared TOML comment block before the three chunk-splitter constants
- No behavior change — comment-only addition

## Assumptions

- The three values remain unchanged — this Plan does not alter any constant value
- The three constants interact as a group (same NC entry NC-034), so a single shared comment block is appropriate
- Prior investigation attempts (`git log -S` on each value: earliest commits 2026-05-29 package reorg, 2026-07-05 config-file split) found no rationale

## Design decisions

- Use a single shared comment block covering all three constants rather than individual markers per constant — the source issue notes they interact as a group and were filed under one NC entry

## Alternatives considered

- Individual markers per constant: rejected because the source issue groups them under NC-034 and notes their interaction
- Placing the marker in a separate docstring or config file: rejected because the source issue requires the marker at the definition site itself

## Implementation

### Target file

`config/chunk_splitter.toml`

### Procedure

Insert a shared TOML comment block immediately above the three constants.

### Method

Edit lines 4-7 region: add a multi-line TOML comment block before the first constant assignment.

### Details

Current state (lines 4-8):
```toml
rag_src_dir = "/opt/llm/rag-src"

min_chunk = 40
max_chunk = 500
chunk_overlap = 50

md_index_enable = false
```

After edit:
```toml
rag_src_dir = "/opt/llm/rag-src"

# Unvalidated heuristic, pending performance tuning — no recorded rationale found
# via git history or originating issues. These three values interact as a group
# (NC-034) and were set without measured justification.
min_chunk = 40
max_chunk = 500
chunk_overlap = 50

md_index_enable = false
```

## Compatibility considerations

N/A: TOML comments are inert to the config loader — no runtime behavior change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

If the comment text proves inaccurate later, the rollback is removing the added comment lines — no config value revert needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| config/chunk_splitter.toml | Manual diff review | `git diff` | Only comment lines added, no value line changed |

## Completion criteria

- [ ] AC-1: A shared "unvalidated heuristic" marker exists above the three chunk-splitter constants at their definition sites
- [ ] AC-4: None of the three constant values were changed (verified by `git diff`)

## Out of scope

- Changing `min_chunk`, `max_chunk`, or `chunk_overlap` values
- Adding tests for these constants
- Editing other constants in this file

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add heuristic marker above min_chunk/max_chunk/chunk_overlap | Pending | — | — | |
| 2 | Run validation sequence (manual diff review) | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260915-200627_rag03_establish-rationale-for-undocumented-chunking-and-crawler-tuning-constants.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-153123_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260917-093845
- **Related target files**: config/chunk_splitter.toml
