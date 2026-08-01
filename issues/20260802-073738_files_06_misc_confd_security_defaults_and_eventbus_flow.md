# Complete conf.d/ security-default documentation and replace eventbus file listing with failure/recovery flow in docs/01_overview-files-06-misc.md

## Priority
High

## Summary
`docs/01_overview-files-06-misc.md` documents only `github-mcp` under `conf.d/`, omitting `cicd-mcp`, `git-mcp`, and `web-search-mcp` (4 files actually exist). Critically, `git-mcp`'s security defaults are undocumented: `allowed_repo_paths` empty means fail-closed (all repository access denied), and `read_only=true` is the default (confirmed by direct source reading). Separately, the eventbus file listing (`broker.py`/`offsets.py`/`dlq.py`/`replay_route.py`, ~lines 27-45) is a bare filename enumeration that doesn't convey the failure/recovery flow.

## Reason for Change
Omitting `git-mcp`'s fail-closed/read-only security defaults risks an implementer misunderstanding `allowed_repo_paths` configuration and unintentionally granting broader write access than intended — a security-relevant documentation gap. The eventbus filename listing conveys no operational understanding of what happens when message delivery fails.

## Implementation Intent
Document all 4 `conf.d/` configuration files, explicitly calling out `git-mcp`'s fail-closed and read-only defaults. Replace the eventbus filename listing with a description of the failure → DLQ → replay recovery flow.

## Target Files or Areas
`docs/01_overview-files-06-misc.md`

## Required Changes
- Add `cicd-mcp`, `git-mcp`, `web-search-mcp` to the `conf.d/` description (currently only `github-mcp` is documented).
- Explicitly document `git-mcp`'s security defaults: `allowed_repo_paths` empty → fail-closed (denies all repository access); `read_only=true` is the default.
- Confirm whether the 3 missing `conf.d/` entries were an intentional omission or an oversight before finalizing (per this review, evidence suggests oversight, but confirm before asserting).
- Replace the eventbus file listing (~lines 27-45) with prose describing the recovery flow: failed message delivery → DLQ (`dlq.py`) → replay via `replay_route.py`'s endpoint.

## Acceptance Criteria
All 4 `conf.d/` configuration files are documented; `git-mcp`'s fail-closed/read-only security defaults are explicit; the eventbus section describes the failure/recovery flow rather than only listing filenames.

## Testing Expectations
Not required (documentation-only). Manually verify the `git-mcp` security defaults by reading its actual `conf.d/git-mcp` config and corresponding server code before finalizing wording.

## Documentation Impact
`docs/01_overview-files-06-misc.md` updated with security-relevant configuration detail and an eventbus recovery-flow description.

## Out of Scope
Do not change any `conf.d/` configuration values or eventbus source code in this issue — documentation only. Per project policy (AGENTS.md Global Rule 8), do not implement any eventbus-related code changes as part of this documentation issue.

## AI Implementation Instruction
Verify the `git-mcp` fail-closed/read-only defaults directly against the actual config file and server code before writing — this is security-relevant content and must not be asserted without verification.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §4 強化候補 (conf.d/), §3 要約候補 item 4 (eventbus), §5 例5, §6A (conf.d/記載漏れ)
- Generated at: 2026-08-02
