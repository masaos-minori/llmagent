# Unify the MCP authentication contract across ADR-002, ADR-007, ADR-013, and ADR-017

## Priority
High

## Summary
ADR-002, ADR-007, ADR-013, and ADR-017 describe MCP token handling differently. Make ADR-017 the only definition of token supply, validation, and failure, and make the other ADRs refer to it.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-H01`; merged from ADRCHK-H01, ADRCHK-M02 (review findings H1, H6, M1, M20)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
ADR-002 INV-04 says the Agent starts without MCP-specific secrets, while ADR-017 and ADR-007 INV-09 say startup aborts when an enabled server has an empty `auth_token`. ADR-007 says tokens come from an environment variable or secret file, and ADR-013 says tokens are stored as a plain string in configuration. The code resolves `${ENV:MCP_*_AUTH_TOKEN}` references and has no secret-file path (`Documentation only` for the ADR side; the loading claim needs confirmation, see Required Changes).

## Reason for Change
- The startup rule contradicts itself. `scripts/agent/startup_validation.py` adds a fatal `mcp_auth` result for each enabled server without a token, so the code follows ADR-017. A reviewer who applies ADR-002 could approve removing the check.
- The supply mechanism is described three ways. Readers who rely on ADR-007 or ADR-013 may provision secrets in a way the code does not read, so startup fails in production.
- The ADR-017 wording is wrong in two places: Negative Consequences cites INV-03 where the `require_auth_token()` rule is INV-02, and the ADR-007 failure policy and the test name `any_server_missing_token` ignore the disabled-server exclusion that ADR-017 and the code apply.

## Implementation Intent
- ADR-017 is the only document that defines how MCP tokens are supplied, validated, and failed.
- ADR-002 INV-04 is limited to server-owned settings and names the connection token as the exception owned by ADR-017.
- ADR-007 and ADR-013 refer to ADR-017 instead of restating the rule, so the rule cannot drift again.

## Target Files or Areas
- `docs/10_adr/adr_02_01_002_platform-config-isolation.md`
- `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`
- `docs/10_adr/adr_02_03_017_mcp-authentication.md`
- `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
- `docs/10_adr/adr_01_index.md`

## Required Changes
- (no decision needed) Confirm the token loading in `config/agent.toml`, `config/*_mcp_server.toml`, and `scripts/mcp_servers/server.py`, and record the evidence in the PR.
- (no decision needed) Fix the INV reference in the ADR-017 Negative Consequences section.
- (no decision needed) Reduce ADR-007 item 10 and its Implementation References to a reference to ADR-017, and add the disabled-server exclusion to the ADR-007 failure policy wording.
- (no decision needed) Describe ADR-013 token storage as a `${ENV:...}` reference resolved at load time.
- (decision) Amend ADR-002 INV-04 (recommended), or record a formal exception in ADR-002. Update the Index matrix row if the wording changes.

## Constraints
- The INV-04 amendment is a decision change; prepare it as a proposal and do not merge it before the maintainer approval record exists.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- No ADR says the Agent starts without an MCP token while another ADR requires one.
- Only ADR-017 defines token supply, and no ADR mentions secret files.
- `uv run python tools/check_adr_authority.py` and `uv run python tools/check_adr_reference.py` pass.

## Testing Expectations
Documentation-only. Run `tools/check_adr_authority.py`, `tools/check_adr_reference.py`, `tools/check_adr_structure.py`, and the docs checkers listed in `routing.md`. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. The five ADR files above change; document supply, validation, failure, and the disabled-server exclusion once, in ADR-017.

## Out of Scope
- Changing `scripts/agent/startup_validation.py` or token-loading code.
- Hot-reload behavior of the config (see the hot-reload validation issue).

## Dependencies
- `issues/20261117-123011_adrchk011_adr-approval-governance.md` blocks the INV-04 decision task (pending-amendment form).

## Unresolved Questions
- The token-loading claim is taken from the review and is `Needs confirmation` until the first Required Change runs.

## AI Implementation Instruction
- Prepare the INV-04 wording as a proposal and stop before merging; never write approval text.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123001
- **Related target files**: `docs/10_adr/adr_02_01_002_platform-config-isolation.md`; `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`; `docs/10_adr/adr_02_03_017_mcp-authentication.md`; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`; `docs/10_adr/adr_01_index.md`
