# Confirm GitHub API key (GITHUB_TOKEN) setup procedure accuracy in docs/02_deployment-part1.md

## Priority
Medium

## Summary
`docs/02_deployment-part1.md` §2.3 describes setting `GITHUB_TOKEN` via `conf.d/github-mcp`, but a repository-wide search finds no reference to a `conf.d` directory anywhere, and `scripts/mcp_servers/github/service_init.py` / `scripts/mcp_servers/cicd/service_init.py` only read `GITHUB_TOKEN` directly via `os.environ.get(...)` — no `conf.d`-based configuration mechanism was found.

## Reason for Change
If this procedure doesn't actually exist as described, a deployer following it would search for a nonexistent configuration file and fail to properly set up GitHub integration, silently leaving GitHub-dependent features (cicd-mcp, github-mcp) non-functional.

## Implementation Intent
Confirm the actual, correct GitHub token setup procedure (environment variable directly, or an OpenRC-style `conf.d` mechanism external to this repository) with the document author or by tracing the actual startup environment configuration, then correct the documented procedure.

## Target Files or Areas
`docs/02_deployment-part1.md` (§2.3)

## Required Changes
- Confirm with the document author (or via the actual service-startup configuration, e.g. an OpenRC init script if one exists outside this repo) how `GITHUB_TOKEN` is actually meant to be set in production.
- Update the documented procedure to match the confirmed actual mechanism (environment variable directly, or an accurately-named/located `conf.d`-equivalent file).

## Acceptance Criteria
The documented GitHub token setup procedure matches a mechanism that is confirmed to actually exist and function.

## Testing Expectations
Not required (documentation-only). If feasible, verify by tracing how `GITHUB_TOKEN` is actually populated in a running deployment.

## Documentation Impact
`docs/02_deployment-part1.md` corrected with the confirmed accurate procedure.

## Out of Scope
Do not implement a new `conf.d`-based configuration mechanism in this issue if one doesn't currently exist — documentation only, reflecting confirmed actual practice.

## AI Implementation Instruction
This requires confirmation beyond what's visible in this repository (possibly an external OpenRC configuration) — if unconfirmable through available context, register it as an explicit open Needs Confirmation item rather than asserting either interpretation as fact.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_deployment.md §6 (通常の確認事項: GitHub操作のAPIキー設定手順)
- Generated at: 2026-08-02
