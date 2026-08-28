# MCP-004: Git write-tool approval risk hierarchy — close remaining defense-in-depth and verification gaps

## Priority
Medium

## Summary
`MCP-004` was originally reported as: Git write tools are classified `WRITE_DANGEROUS` but the
actual approval prompt falls back to the default `MEDIUM` (`y/N`), skipping the stronger
full-word confirmation expected for that tier. Code and config inspection confirms this specific
mismatch is **already fixed**: `config/agent.toml`'s `[approval_risk_rules]` sets
`git_checkout`/`git_pull`/`git_push = "high"`, `_prompt_user_approval()` already requires the
full word `"yes"` for `RiskLevel.HIGH`, and `check_approval()` already records every decision via
`audit_approval()`. `docs/adr/ADR-012-...md`'s Known Deviations section still lists this as an
open deviation, which is stale relative to `docs/04_mcp_90_inconsistencies_and_known_issues.md`'s
own `MCP-004` entry (`Status: resolved`). What remains open, confirmed by reading the current
implementation, is narrower: no floor prevents the `"high"` override from later being weakened in
config, no test exercises the real `config/agent.toml` file through the actual approval flow, and
the approval-screen preview for git tools falls back to a generic JSON dump rather than a
purpose-built preview naming the repository/branch being acted on.

## Background
`MCP-004` is tracked in `docs/04_mcp_90_inconsistencies_and_known_issues.md`, already `resolved`
per its own Resolution Notes (citing `REQ-006` and `tests/agent/test_tool_policy_comprehensive.py`).
`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`'s Known Deviations section still
lists `MCP-004` as open — the same kind of staleness already found and tracked for `GIT-001`/
`GIT-002` in a separate issue (`DOC-005`); ADR-012's Known Deviations section appears to need a
broader refresh across multiple entries, though only `MCP-004` is addressed here per this issue's
scope. `config/agent.toml`'s `approval_risk_rules`/`tool_safety_tiers` sections and
`scripts/agent/tool_policy.py`/`tool_approval.py` implement the current approval-risk pipeline.

## Problem
Confirmed by reading `config/agent.toml`, `scripts/agent/tool_policy.py`,
`scripts/agent/tool_approval.py`, and `tests/agent/test_tool_policy_comprehensive.py`:

**Already resolved (contrary to the original report and ADR-012's stale Known Deviations entry):**
- `config/agent.toml` lines 201-203 set `git_checkout = "high"`, `git_pull = "high"`,
  `git_push = "high"` under `[approval_risk_rules]`; lines 281-283 confirm `WRITE_DANGEROUS` tier
  classification for the same three tools.
- `tool_approval.py::_prompt_user_approval()` requires the literal word `"yes"` for
  `RiskLevel.HIGH` (`"  Execute? [yes/no]: "`), vs. a single-letter `y/N` prompt otherwise.
- `check_approval()` calls `audit_approval(ctx, tool_name, risk, args, decision)` on every code
  path — preflight denial, gitops-push-blocked denial, dry-run-error denial, auto-approval
  (`RiskLevel.NONE`), and the final approved/denied decision — so approval outcomes are already
  recorded.

**Confirmed still open:**
- **No floor prevents downgrading below `HIGH`.** Nothing in
  `shared/production_config_validator.py` or elsewhere rejects a config that sets
  `git_checkout`/`git_pull`/`git_push` to `"medium"` or `"low"`, or that simply omits the
  override (reverting to the `WRITE_DANGEROUS` tier's `MEDIUM` fallback). The current correct
  behavior depends entirely on the current config content persisting unchanged.
- **The existing test verifies the mapping function, not the shipped config through the real
  flow.** `test_git_checkout_pull_push_resolve_to_high_risk`
  (`tests/agent/test_tool_policy_comprehensive.py`) constructs a synthetic `cfg` object with its
  own `approval_risk_rules` dict and calls `classify_risk()` directly — it does not load the
  actual `config/agent.toml` or exercise `check_approval()`/`_prompt_user_approval()`'s full-word
  requirement end-to-end. A regression that only breaks the real config file (e.g., a typo, a
  merge that drops the override) would not be caught by this test.
- **The approval-screen preview for git tools is generic, unlike other tool categories.**
  `tool_result_formatter.py::build_preview()` has dedicated cases for `write_file`/`edit_file`,
  `delete_file`/`delete_directory`/`create_directory`, `move_file`, `shell_run`, and
  `github_*`, but no case for `git_*` tools — they fall through to
  `_json_dumps(args)[:300]`, a raw truncated JSON dump rather than a purpose-built preview
  naming the repository path and target branch/remote the way, e.g., `move_file`'s
  `"{source} → {destination}"` preview does.

**Not yet investigated (see Unresolved Questions):**
- Whether `args` used at approval time can differ from `args` actually executed (argument
  immutability between approval and execution).
- Whether any approval decision is ever reused across multiple tool calls without a fresh prompt.

## Reason for Change
The core, actively-exploitable mismatch this Known Issue originally reported — Git write tools
silently approved with the weaker `y/N` prompt despite being documented as `WRITE_DANGEROUS` — is
already fixed and covered by a passing test. Priority is set to Medium rather than treating this
as an active vulnerability: what remains is defense-in-depth (preventing an accidental future
downgrade), verification completeness (testing the real shipped config, not just the mapping
function), and an approval-screen quality gap (a specific-enough preview for the operator to
recognize what they are approving) — all worth closing, but none currently causing incorrect
approval behavior in production.

## Implementation Intent
Address the three confirmed-open items independently; each is small and does not depend on the
others:

1. **Config floor.** Add a check (in `shared/production_config_validator.py` or the config
   loader) that rejects — or at minimum warns loudly at startup on — an `approval_risk_rules`
   value for `git_checkout`/`git_pull`/`git_push` that resolves below `HIGH`, or their absence
   combined with a `tool_safety_tiers` entry lower than `WRITE_DANGEROUS`. Decide fail-fast vs.
   fail-open per this project's existing Environment Profile failure policy (`ADR-004`) rather
   than inventing new behavior here.
2. **Real-config verification test.** Add a test that loads the actual `config/agent.toml` (not a
   synthetic `cfg`) and asserts `classify_risk()` resolves `git_checkout`/`git_pull`/`git_push` to
   `HIGH`, and/or an integration-level test exercising `check_approval()`'s full-word-`"yes"` path
   for these three tools against the real config.
3. **Git-specific approval preview.** Add a `git_*` case to `build_preview()` naming the
   repository path and, where present, the target branch/remote — following the existing
   per-category pattern (`move_file`'s `"{source} → {destination}"`, `_preview_file_path()`, etc.)
   rather than introducing a new preview mechanism.

Investigate, but do not assume the answer to, the two Unresolved Questions below before deciding
whether items 6/7 from the original proposal require any code change.

## Target Files or Areas
- `config/agent.toml` (`[approval_risk_rules]`, `[tool_safety_tiers]` — reference only; already
  correct)
- `shared/production_config_validator.py` (or wherever config validation runs — target for the
  new floor check)
- `scripts/agent/tool_policy.py` (`classify_risk()`, `_TIER_TO_RISK` — reference for how the floor
  check should reason about resolved risk)
- `scripts/agent/tool_approval.py` (`check_approval()`, `_prompt_user_approval()` — reference;
  confirm argument-immutability question here if investigated)
- `scripts/agent/tool_result_formatter.py` (`build_preview()` — add the `git_*` preview case)
- `tests/agent/test_tool_policy_comprehensive.py` (existing synthetic-config test; add the
  real-config test alongside it, not as a replacement)
- `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` (Known Deviations — `MCP-004` entry
  needs correcting regardless of this issue's other outcomes)

## Required Changes
- Implement the config floor check for `git_checkout`/`git_pull`/`git_push`'s effective risk
  (item 1 above).
- Add a test that verifies the real `config/agent.toml` resolves these three tools to `HIGH`
  through the actual approval-risk pipeline (item 2 above).
- Add a git-specific case to `build_preview()` (item 3 above).
- Update `ADR-012`'s Known Deviations entry for `MCP-004` to reflect the resolved core behavior
  and the narrower remaining scope this issue tracks.
- Investigate and record findings for the two Unresolved Questions (argument immutability,
  approval reuse) before deciding whether they require further code changes.

## Constraints
- Do not change the currently-correct `config/agent.toml` values for
  `git_checkout`/`git_pull`/`git_push` — they are already `"high"` and must remain so.
- Follow this project's existing Environment Profile fail-fast/fail-open policy (`ADR-004`) for
  the new config floor check rather than defining a new failure model specific to this check.
- Do not change `_prompt_user_approval()`'s existing full-word-`"yes"` behavior for `HIGH` — it is
  already correct.

## Acceptance Criteria
- A config that would resolve `git_checkout`/`git_pull`/`git_push` below `HIGH` is rejected or
  loudly flagged at startup/validation time, per the chosen fail-fast/fail-open policy.
- A test exercising the real `config/agent.toml` (not only a synthetic `cfg`) confirms these
  three tools resolve to `HIGH` through the actual risk-classification path.
- `build_preview()` shows a git-specific preview (repository path, branch/remote where
  applicable) for `git_*` tools instead of falling through to the generic JSON-dump case.
- `ADR-012`'s Known Deviations `MCP-004` entry and `docs/04_mcp_90_inconsistencies_and_known_issues.md`'s
  `MCP-004` Resolution Notes reflect the corrected, narrower scope.
- The two Unresolved Questions have recorded findings (confirmed safe, or a follow-up issue filed
  if a gap is found).

## Testing Expectations
Unit test for the new config floor check (accepts `"high"`, rejects/warns on `"medium"`/`"low"`/
absent-override-with-low-tier). New or extended test loading the real `config/agent.toml` through
`classify_risk()`/`check_approval()`. Unit test for the new `build_preview()` git case. Regression
run of `tests/agent/test_tool_policy_comprehensive.py` and `tests/agent/test_tool_approval_risk.py`.

## Documentation Impact
Yes. `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`'s Known Deviations `MCP-004`
entry must be corrected — it currently describes the already-fixed core mismatch as if still
open. `docs/04_mcp_90_inconsistencies_and_known_issues.md`'s `MCP-004` entry should note the
narrower remaining scope (config floor, real-config test, preview quality) rather than being
silently left as-is once this issue's items are addressed.

## Out of Scope
- Re-fixing the core `HIGH`-tier/full-word-confirmation behavior — already correct.
- Re-implementing approval-outcome audit recording — already implemented via `audit_approval()`.
- A general audit of every other stale entry in `ADR-012`'s Known Deviations section — only
  `MCP-004` is corrected here; a broader refresh, if warranted, should be its own issue.
- Extending the git-specific preview work to any tool category other than `git_*`.

## Dependencies
- Related: `ADR-012` (Known Deviations correction for `MCP-004`), `DOC-005` (parallel
  Known-Deviations staleness correction for `GIT-001`/`GIT-002` — same underlying pattern, tracked
  separately), `ADR-004` (Environment Profile fail-fast/fail-open policy the new config floor
  check should follow).

## Unresolved Questions
- Whether `args` used at approval time (`check_approval(ctx, tool_name, args)`) can differ from
  the `args` actually passed to git command execution afterward — i.e., whether there is any
  window for argument mutation between approval and execution. Needs tracing through
  `tool_preparation.py`/`tool_runner.py`'s `PreparedToolCall` handling before concluding whether
  this is already safe or needs an explicit immutability guarantee.
- Whether any approval decision is reused across multiple tool calls without a fresh prompt (the
  original proposal's "承認の使い回しを制限"). No caching/reuse mechanism was found in
  `tool_approval.py`/`tool_policy.py` during this issue's investigation, which suggests each call
  already gets an independent prompt — but this should be confirmed by tracing
  `run_approval_checks()`'s call pattern rather than assumed from an absence of matching grep
  results.

## AI Implementation Instruction
Do not re-implement the `HIGH`-tier override, the full-word-`"yes"` prompt, or approval-outcome
audit recording — all three are already correct; re-confirm this by reading
`config/agent.toml` lines ~200-203/280-283, `tool_approval.py::_prompt_user_approval()`, and
`check_approval()`'s `audit_approval()` calls before starting, since re-implementing already-working
behavior risks introducing a regression. Investigate the two Unresolved Questions by tracing code
rather than assuming an answer either way. Implement the three Required Changes independently and
update `ADR-012`'s `MCP-004` Known Deviations entry as part of the same change.
