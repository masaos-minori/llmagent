# Implementation: Deploy verification for fail_open and eventbus no-op field removal (Phase 5)

## Goal

Confirm that removing `allowed_repos_mode` (Phase A) and the eventbus no-op config fields (Phase B) requires no `deploy/deploy.sh` copy-list changes, and define the operational precautions needed before deploying Phase B's stricter startup validation (which can now cause the Event Bus to refuse to start).

## Scope

**In:**
- Verify `deploy/deploy.sh` needs no copy-list update — Phases A and B only modify existing files (`config/github_mcp_server.toml`, `config/eventbus.toml`, and files under `scripts/`), both of which are already copied wholesale (`cp` for the two TOML files individually, `rsync` for all of `scripts/`)
- Define the pre-deploy check for Phase B: confirm the target deployment's `/opt/llm/config/eventbus.toml` does not set `poll_interval_ms` or `offset_checkpoint_interval` before deploying the new code, since deploying without checking would leave the Event Bus refusing to start until the operator edits the TOML
- Confirm no CHANGELOG file exists in this repository (verified: `find . -maxdepth 1 -iname "CHANGELOG*"` returns nothing) — the "Note (YYYY-MM-DD): X was removed" annotations added directly to the affected `docs/*.md` files in Phases A-4 and B-3 are this project's equivalent mechanism, and are sufficient; no separate changelog file needs to be created

**Out:**
- No new environment variables, ports, or MCP server registrations are introduced by Phase A or B — nothing to add to `config/agent.toml`'s `[mcp_servers]` section or to `rules/env.md`

## Assumptions

1. All changes across Phases A-1 through B-3 modify only pre-existing files; no file under `scripts/` or `config/` is added or removed — to be confirmed at implementation time via `git status --porcelain scripts/ config/ | grep -v "^ M"` (expect no output).
2. The GitHub MCP server (`github-mcp`) does not need a similar "startup error on stray key" treatment for `allowed_repos_mode` the way eventbus's fields do — since `GitHubConfig.from_dict()` uses `_get_str(d, "allowed_repos_mode", "fail_closed")` only to *read* the key if present, and after Phase A-1 that line is deleted entirely, a stray `allowed_repos_mode` key left in `github_mcp_server.toml` will simply be silently ignored (not read at all), not rejected. This is a deliberate asymmetry from Phase B's approach: the user's approved plan only specified a hard-error requirement for item B (eventbus), not item A (github). If symmetric behavior is desired, that would be a follow-up decision requiring separate confirmation — not assumed here.

## Implementation

### Target file

`deploy/deploy.sh` (verification only, no expected edits)

### Procedure

1. After Phases A-1 through B-3 are implemented, diff the full list of touched files against `deploy/deploy.sh`'s copy list; confirm every touched file (`scripts/mcp/github/models_config.py`, `scripts/mcp/github/service_security.py`, `scripts/agent/security_audit_config.py`, `scripts/agent/repl_health.py`, `scripts/shared/production_config_validator.py`, `config/github_mcp_server.toml`, `scripts/eventbus/config.py`, `config/eventbus.toml` if edited) is already covered by the existing `rsync`/`cp` lines, with no additions or removals needed.
2. Before deploying Phase B to production: run `grep -n "poll_interval_ms\|offset_checkpoint_interval" /opt/llm/config/eventbus.toml` against the live deployment's config file (not this repository's copy) to confirm neither key is set; if either is present, remove it from the live TOML as part of the same deploy step, before restarting the Event Bus service.
3. Before deploying Phase A to production: no equivalent pre-check is required for `github_mcp_server.toml`, since (per Assumption 2) a stray `allowed_repos_mode` key is silently ignored rather than rejected — however, operators should still be advised via the doc notes (Phase A-4) to remove it for clarity.
4. Confirm the "Note (2026-07-10)" style doc annotations added in Phases A-4 and B-3 are present before considering the work complete — these serve as this project's changelog equivalent.

### Method

Verification-only step — no source code is produced by this document; it records the deployment checklist for `plans/20260710-122146_plan.md`'s "Phase 5" section.

### Details

- This mirrors the deploy-verification pattern already used in the prior backward-compat removal cycle (`implementations/done/20260710-103755_backcompat_removal_deploy_verification.md`), adapted to this cycle's two items.
- The asymmetry noted in Assumption 2 (eventbus hard-fails on stray keys, github-mcp silently ignores them) reflects the user's explicit, differentiated approval for each item — B was approved for "起動時エラーにする" (make it a startup error), A's approval was scoped only to "fail_open モードを完全削除" (remove the mode entirely) without a parallel stray-key hard-error requirement.

## Validation plan

```bash
# Confirm no file additions/removals require a deploy.sh copy-list change
git status --porcelain scripts/ config/ | grep -v "^ M"   # expect no output

# Pre-deploy check against the live eventbus config (run on the target host, not in this repo)
grep -n "poll_interval_ms\|offset_checkpoint_interval" /opt/llm/config/eventbus.toml || echo "clean"
```

Expected outcome: no unmodified-copy-list drift; the live `eventbus.toml` (when this is actually deployed) contains neither removed key before the new code is started.
