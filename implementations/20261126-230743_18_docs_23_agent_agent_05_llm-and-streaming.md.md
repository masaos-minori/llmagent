## Goal

Remove the `/set` reference from the reload-boundary paragraph and point to `/reload`, the command that
actually exists (REQ-007 — documentation lists the same command set as the implementation).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: line 50 is the only `/set` reference in the repository, and `/set` has no
  implementation anywhere under `scripts/`; the reloadable set is the `apply_config` list named in the
  same paragraph.
- The paragraph's claim about compression parameters (`llm_compress_temperature`,
  `llm_compress_max_tokens`, not hot-reloadable) is correct and stays.

## Design decisions

- Rewrite the sentence to name only `/reload` (Plan D7); no new command is created to match the
  documentation, because the documentation is the drift.

## Alternatives considered

- Implementing `/set` — rejected: out of scope for this Plan, and the Issue AI Instruction requires the
  documented set to match the implemented set, not the reverse.

## Implementation
### Target file
`docs/23_agent/agent_05_llm-and-streaming.md`
### Procedure

- In the Runtime Parameter Reload Boundary paragraph, replace "reloadable through `/set` or `/reload`"
  with "reloadable through `/reload`".

### Method

- Single-sentence edit; no other `/set` mention exists in the file.

### Details

- No Front Matter, Keywords, or Related Documents change.

### Companion test files

- N/A: documentation gate per rules/tool-gates.md.

## Compatibility considerations

- Users following the retired `/set` path lose the reference; the surviving path is `/reload`.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Documentation gates (`rules/tool-gates.md`): `check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent`, `check_docs_japanese.py`.

## Completion criteria

- The file contains no `/set` reference, and the documentation-set equality check in document 15 passes.

## Out of Scope

- The command index table (document 19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | N/A | — | — | documentation gate |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | documentation gates |

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
- **Requirement ID**: `REQ-007` (documentation lists the implemented command set)
- **Source issue**: `issues/20261119-145309_cliplc011_export-command-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-212234_cliplc011_export-command-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-230743
- **Related target files**: `docs/23_agent/agent_05_llm-and-streaming.md`
