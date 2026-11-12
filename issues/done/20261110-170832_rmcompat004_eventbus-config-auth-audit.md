# Simplify EventBus configuration validation, authorization format, and audit records

## Priority
Medium

## Summary
Validate each EventBus configuration rule once with messages that describe the current rules, accept one authorization format read strictly, make admin authorization audit records always carry their generation fields, and remove copied vocabulary and history notes from the EventBus authentication and audit modules.

## Background
- Source: `memo-issue.md` item H-07 (consolidated version), re-checked against current source on 2026-11-10. The credential merge part of the memo (`auth_token` and `admin_token`) is already tracked by `issues/20261109-112952_adrrev010_eventbus-authz-harden.md` and is not repeated here.
- `Explicit in code`, in `scripts/eventbus/config.py`:
  - The requirement that `auth_token` is non-empty is checked in three places: `EventBusConfig.__post_init__`, `_validate_deployment_mode`, and `load_config`.
  - `_validate_token_combinations` counts `auth_token` among the accepted tokens, and `load_config` and `__post_init__` already reject an empty `auth_token`, so the function cannot fail after those checks (`Strongly implied by code`).
  - `_validate_deployment_mode` raises for every host other than `127.0.0.1` and `::1` regardless of any token, yet its message says the bind is "without authentication configured; set auth_token or bind to loopback", so setting a token does not allow the bind.
  - Authorization can be written as `consumer_authorization` (consumer to topics) or `topic_authorization` (topic to consumers), and both are merged by `authorization_baseline_hash`; the loaders in `config.py` and `scripts/eventbus/admin_route.py` accept lists and sets.
- `Explicit in code`, in `scripts/eventbus/auth.py`: `getattr` and `hasattr` defaults read `consumer_authorization`, `topic_authorization`, `consumer_token`, `admin_token`, `auth_token`, and other attributes of the config object; `_ROUTE_ROLE_MAP` and `_CONSUMER_ID_ALLOWLIST` are defined and have no other reference in `scripts/eventbus/`; two "Precedent:" comments point at `scripts/mcp_servers/`.
- `Explicit in code`, in `scripts/eventbus/audit.py`: the module docstring describes the `error_type` vocabularies of the mdq and web_search MCP servers; `previous_generation` and `new_generation` are optional (`NotRequired`) and added to a record only when not `None`; `admin_route.py` passes the same values and also appends `gen:<prev>-><new>` to `detail`; the docstring starts with "Mirrors scripts/mcp_servers/audit.py" and a "Precedent" line.
- `Explicit in code`, in `config/eventbus.toml`: comments labelled REQ-005 and REQ-007, and a comment describing `admin_token` as a separate credential.

## Problem
- Three copies of one check can drift, so the error an operator sees depends on which check fires first; one check (`_validate_token_combinations`) is dead.
- The bind error tells operators to set a token to allow an external bind, which cannot work.
- Two formats for one fact allow contradictory configurations and complicate validation and audit; tolerant `getattr` defaults accept missing or misspelled attributes silently, in the module that enforces authorization.
- Generation fields that appear only sometimes, and the same data stored twice in two shapes, make admin audit records ambiguous; copied vocabulary and "Precedent" notes describe other servers and how the code was written, not what it does.

## Reason for Change
- The current-only policy (`compatrm001`) forbids tolerant fallbacks and duplicate formats; the bind message is the only item that can lead an operator to a wrong action today. No external deadline.

## Implementation Intent
- Each configuration rule is validated once, with messages that describe the current rules.
- Authorization has exactly one format, read strictly; unknown shapes are rejected at load.
- The auth module reads config attributes directly and contains no unused tables.
- Every admin authorization audit record contains both generation fields in one place only, and the audit module documents only the vocabulary the EventBus emits, defined as constants.
- Keep roles, route protection, and the authorization model unchanged.

## Target Files or Areas
- `scripts/eventbus/config.py`, `scripts/eventbus/auth.py`, `scripts/eventbus/audit.py`, `scripts/eventbus/admin_route.py`
- `config/eventbus.toml`
- `tests/eventbus/` (config, auth, admin authorization, and audit tests, for example `test_eventbus_auth.py` and `test_authz_generation_ttl.py`)
- `docs/24_eventbus/` documents that describe the configuration, the authorization format, and the audit record (exact files `Unknown`; find by search)

## Required Changes
- Keep one check for the required token in one place, delete `_validate_token_combinations` if it still cannot fail, and rewrite the non-loopback bind error to say that only loopback addresses are allowed.
- Keep `consumer_authorization` (maintainer decision, 2026-11-10) and remove `topic_authorization` from `config.py`, `auth.py`, `admin_route.py`, and the `eventbus.toml` comments, accept one collection type, and reject anything else at load.
- Replace the `getattr`/`hasattr` reads in `auth.py` with direct attribute access, and delete `_ROUTE_ROLE_MAP` and `_CONSUMER_ID_ALLOWLIST` after a zero-reference search.
- Make `previous_generation` and `new_generation` required for admin authorization actions, and remove the `gen:<prev>-><new>` suffix from `detail`.
- Replace the copied `error_type` vocabulary in `audit.py` with the values the EventBus emits, defined as constants.
- Remove the "Precedent" and "Mirrors ..." notes and the REQ comments from `config/eventbus.toml`.
- Add tests: a config using the removed authorization format fails load; every admin authorization audit record has both generation fields.

## Constraints
- Do not add aliases or compatibility parsing for the removed authorization format (`compatrm001`).
- The audit record shape is observed by operators and tests; the change is intended and must be documented.
- `scripts/eventbus/config.py`, `auth.py`, and `admin_route.py` are also targets of `issues/20261109-112952_adrrev010_eventbus-authz-harden.md`; implement that issue first so the validation clean-up uses its credential decision.
- Maintainer decision (2026-11-10): keep `consumer_authorization`; `topic_authorization` support is removed.

## Acceptance Criteria
- The required-token rule appears once in `scripts/eventbus/config.py`, and a test covers each remaining failure message.
- The bind error contains no instruction to set a token for a non-loopback bind.
- A configuration with the removed authorization format fails load with an explicit error.
- `scripts/eventbus/auth.py` has no `getattr(config, ...)`/`hasattr(config, ...)` default and no unreferenced module-level table.
- Admin authorization audit records contain both generation fields and `detail` has no generation suffix, covered by a test.
- `rg -n "Precedent|Mirrors scripts/|REQ-[0-9]+" scripts/eventbus/audit.py scripts/eventbus/auth.py config/eventbus.toml` returns nothing.
- The EventBus tests and the validation sequence pass.

## Testing Expectations
- Update and run `tests/eventbus/`; add the tests named in Required Changes.
- Run `rules/toolchain.md` validation (ruff, mypy with `--no-namespace-packages`, import-linter, bandit, pytest) and, for document edits, `uv run python tools/check_docs_consistency.py --domain eventbus` and the `docs/` checkers in `routing.md`.

## Documentation Impact
- Documentation must be updated: the EventBus configuration and security documents (authorization format, bind rule, audit record) and, where the decision changes ADR-013 text, ADR-013 with an approval record. Describe intent, boundaries, and failure behavior only.

## Out of Scope
- Merging `auth_token` and `admin_token` (`issues/20261109-112952_adrrev010_eventbus-authz-harden.md`).
- Authorization generation persistence across restarts and the no-op contract of the admin endpoint.
- DLQ and delivery code (`issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md` in this batch).
- Replacing `json` with `orjson` in the baseline hash.

## Dependencies
- Depends on `issues/20261109-112952_adrrev010_eventbus-authz-harden.md` (same files; its credential decision fixes the token key name used here).
- Related, documentation only: `issues/20261109-113152_adrrev014_eventbus-spec-gaps.md` (EventBus configuration specification).
- Blocks the history-comment sweep issue in this batch (`issues/20261110-171040_rmcompat007_history-comment-sweep.md`).

## Unresolved Questions
- Decided (2026-11-10): keep `consumer_authorization`, remove `topic_authorization`.
- `不明`: whether the maintainer wants audit records written before this change to remain readable; this issue only changes new records.
- `Needs confirmation`: whether `_ROUTE_ROLE_MAP` and `_CONSUMER_ID_ALLOWLIST` are referenced outside `scripts/eventbus/` (search found no other reference in `scripts/eventbus/`).
- `Needs confirmation`: the exact `docs/24_eventbus/` files to update.

## AI Implementation Instruction
- Change only the EventBus configuration, auth, audit, admin route, `eventbus.toml`, their tests, and the documents that describe them.
- Do not change roles, route protection, or the credential model; defer the token merge to `issues/20261109-112952_adrrev010_eventbus-authz-harden.md`.
- Keep `consumer_authorization` and remove `topic_authorization`; do not keep both.
- Keep comments and log text in English.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261110-170832
- **Related target files**: `scripts/eventbus/config.py`, `scripts/eventbus/auth.py`, `scripts/eventbus/audit.py`, `scripts/eventbus/admin_route.py`, `config/eventbus.toml`
