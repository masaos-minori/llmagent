## Goal

Record the five-layer coverage for github-mcp in
`docs/22_mcp/mcp_04_01_web-search-file-read-github.md`, including the reason state-based postcondition
verification is not applicable in this Plan (REQ-009, AC-009).

## Scope

- Add one `### Guard and postcondition coverage` subsection to the github-mcp section.
- State the not-applicable reason for postcondition verification and record UNK-02 as a follow-up.
- Leave the web-search-mcp and file-read-mcp sections unchanged: the Plan's target row names github-mcp
  only.

## Assumptions

- The section shape and layer names come from the Plan's Design decision table and the existing
  `docs/22_mcp/mcp_04_05_git.md` sections.
- The github-mcp Audit line at `docs/22_mcp/mcp_04_01_web-search-file-read-github.md:175` is already
  correct and needs no change.

## Design decisions

- Record the guards by name (`_assert_allowed_repo`, `_assert_allowed_path`, `_assert_allowed_branch`,
  `_clamp_per_page`, `_assert_max_file_size`) so the document names the code that enforces each one
  instead of asserting coverage in the abstract.
- State postcondition verification as not applicable in this Plan rather than as absent, and name the
  `push_files` ref-movement verification as the follow-up the Plan records as UNK-02.

## Alternatives considered

- Add coverage lines for all three servers in this file: rejected — the Plan's frozen target row scopes
  this row to github-mcp, and the other two servers have no new facts to record.

## Implementation

### Target file

`docs/22_mcp/mcp_04_01_web-search-file-read-github.md`

### Procedure

1. Insert a `### Guard and postcondition coverage` subsection into the github-mcp section, after its
   Audit line.
2. Add `Common guard`, `Command-specific guard status`, `Postcondition verification`, and `Audit`
   sub-headings inside it, matching the git-mcp document's names.
3. Add the follow-up sentence naming ref-movement verification.

### Method

One short paragraph per layer, each ending with the `(Explicit in code — <path>)` marker the document
already uses.

### Details

- The github-mcp section is `docs/22_mcp/mcp_04_01_web-search-file-read-github.md:141-186`; its Audit
  line is at `docs/22_mcp/mcp_04_01_web-search-file-read-github.md:175`.
- Cite `scripts/mcp_servers/github/github_server.py` as the code evidence for the allowlist guards.
- Record that Layer2 and Layer3 are both written, and that before/after state snapshots are not
  applicable because the GitHub API response carries the resulting state.

## Compatibility considerations

- The document's tool tables and configuration tables are unchanged.
- `docs/91_security/security_02_high-risk-tool-common-policy.md` points at each tool document for its
  coverage; the pointer to this file becomes load-bearing after Plan row 18.

## Security considerations

- The document records enforcement facts only; no token, repository content, or API payload is added.

## Rollback considerations

N/A: revert the commit. A rollback reopens the documentation gap AC-009 closes.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_known_deviation_sync.py`
- `uv run python tools/check_workitem_structure.py --file implementations/20261017-162434_14_docs_22_mcp_mcp_04_01_web-search-file-read-github.md.md`

## Completion criteria

- The github-mcp section states all five layers, with an explicit reason for the not-applicable
  postcondition layer (AC-009).
- The follow-up for ref-movement verification is stated as a follow-up, not as implemented coverage.
- The docs checkers report no findings for this file.

## Out of scope

- Recording coverage for web-search-mcp and file-read-mcp.
- Implementing `push_files` ref-movement verification, which the Plan records as UNK-02.
- Changing github-mcp behaviour.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the github-mcp layer-coverage subsection | Completed | — | 2026-10-17 | REQ-009 |
| 2 | Run the docs checkers | Completed | — | 2026-10-17 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | The procedure's Details bullet cites `scripts/mcp_servers/github/github_server.py` as the code evidence for the allowlist guards. The guards are implemented in `scripts/mcp_servers/github/github_service_security.py` (`_assert_allowed_repo`, `_assert_allowed_path`, `_assert_allowed_branch`, `_clamp_per_page`, `_assert_max_file_size`); `github_server.py` only owns the disabled-tool gate and the shared audit call. The subsection cites both files. | Yes | 20261017-210000 |
| 1 | The procedure names `_assert_max_file_size` against a `max_file_size` limit; the configuration key is `max_file_size_kb` (`scripts/mcp_servers/github/github_models_config.py:34`). The document states the real key. | Yes | 20261017-210000 |

## Work Items Created

- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-009
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-160222_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162434
- **Related target files**: `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`