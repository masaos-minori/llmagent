## Goal
Thread the live `POST /v1/call_tool` request's `dry_run` value and the module-level
`_cfg.allow_detached_head` setting into `WriteProtectionPipeline.run()`'s call
(`REQ-006`), so Stage 5's `verify_preconditions()` (sibling target-file document
`implementations/20260905-202634_01_...repository_state.py.md`) actually receives
both values from the live path instead of never being able to observe them.

## Scope
- In scope: the `pipeline.run(req.name, handler)` call site at line 266 — passing the
  two new arguments `run()` requires once its own signature is updated (per the
  `repository_state.py` sibling document).
- Out of scope: `verify_preconditions()`/`run()`'s own signatures and bodies
  (`repository_state.py`, separate target file); `config/git_mcp_server.toml`;
  test files.

## Assumptions
- `run()`'s new signature (defined in the `repository_state.py` sibling document)
  accepts `dry_run: bool` and `allow_detached_head: bool` as positional-or-keyword
  parameters after `op`.
- `req` (`CallToolRequest`) has no `.dry_run` attribute directly — the request's
  `dry_run` flag lives in `req.args` (a `dict`), consistent with the existing
  extraction pattern already used at lines 327/340/351
  (`cast(bool, req.args.get("dry_run", False))`) for the individual
  checkout/pull/push request models. The Plan's Implementation intent phrase
  "`req.dry_run`" is shorthand for this value, not a literal attribute access.

## Design decisions
- Extract `dry_run` via `cast(bool, req.args.get("dry_run", False))` at the call site,
  matching the file's existing extraction convention exactly (same pattern already
  used three times in this file) rather than introducing a new helper or a `req.dry_run`
  property.
- Pass `_cfg.allow_detached_head` directly (module-level `_cfg`, already loaded at
  line 60) — no new config plumbing needed, this value already exists and is already
  threaded to `format_checkout()`'s postcondition check (line 330); this document adds
  a second, independent use of the same existing value.

## Alternatives considered
- Adding a `dry_run` property to `CallToolRequest` in `git_models.py`: rejected as
  out-of-scope — `git_models.py` is a Reference File in the Plan (read-only), not an
  Implementation Target File; the existing `req.args.get(...)` extraction pattern is
  sufficient and consistent with every other call site in this same function.

## Implementation
### Target file
`scripts/mcp_servers/git/git_server.py`

### Procedure
1. At line 265-266, before constructing `pipeline`, extract
   `dry_run = cast(bool, req.args.get("dry_run", False))` (or inline the cast directly
   into the `pipeline.run(...)` call — match whichever style keeps the line readable
   given the two other new arguments).
2. Change line 266 from `result = pipeline.run(req.name, handler)` to
   `result = pipeline.run(req.name, handler, dry_run, _cfg.allow_detached_head)`
   (positional order must match `run()`'s new signature exactly, defined in the
   `repository_state.py` sibling document — confirm the parameter order there before
   this edit).

### Method
Direct code edit — one call-site line change plus, if extracted to a local variable,
one new line above it. No codemod/AST tooling needed. Read lines 253-270 immediately
before editing to reconfirm no drift since this document's revalidation (current as
of 2026-09-05).

### Details
```python
dry_run = cast(bool, req.args.get("dry_run", False))
pipeline = WriteProtectionPipeline(pre_state)
result = pipeline.run(req.name, handler, dry_run, _cfg.allow_detached_head)
```
`cast` is already imported in this file (used at lines 197, 253, 324-327, etc.) — no
new import needed.

## Compatibility considerations
- This is the sole external call site of `WriteProtectionPipeline.run()` outside
  `git_service.py` (a Reference File, not modified by this Plan — its own call to
  `pipeline.run(tool_name, ...)` at `git_service.py:234` is a separate, dead-code path
  per the Plan's Design section). `run()`'s new `dry_run`/`allow_detached_head`
  parameters default to `False` (per the `repository_state.py` sibling document's
  Design decisions, revised specifically to avoid breaking this call site) — so
  `git_service.py:234` keeps working with zero edits; this document's call site is the
  only one that needs to pass explicit, non-default values.
- No change to the `POST /v1/call_tool` request/response schema — `dry_run` is already
  a valid `req.args` key (used elsewhere in this same file); no new field is added to
  `CallToolRequest`.

## Security considerations
- `_cfg.allow_detached_head` is read from the same already-loaded, already-trusted
  module-level config (`_cfg = GitConfig.load()`, line 60) used elsewhere in this file
  — no new trust boundary or input validation is introduced.
- `dry_run` is extracted the same way three other dry_run values already are in this
  same function/file — no new parsing or validation logic.

## Rollback considerations
- Single-line (or two-line) change at one call site; revertible via `git checkout` of
  this file, but must be reverted together with the `repository_state.py` signature
  change (both move together — reverting only one breaks the other via a `TypeError`).

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` — new
  `POST /v1/call_tool` dry-run/detached-HEAD tests (tracked in that sibling document)
  must pass against this change.
- `uv run pytest tests/mcp_servers/git/ -v` — full suite, no new failures.
- `uv run ruff check scripts/mcp_servers/git/`, `uv run mypy scripts/mcp_servers/git/`,
  `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`,
  `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- `pipeline.run(...)`'s call at the live `/v1/call_tool` path passes the request's
  actual `dry_run` value and the configured `allow_detached_head` value through to
  Stage 5.
- A dry-run request against a dirty/detached-HEAD repository is no longer rejected by
  Stage 5 (verified by the `test_git_security_compliance.py` sibling document's new
  `TestClient` tests).
- All existing and new tests pass; no new lint/type/security findings.

## Out of scope
- `repository_state.py`'s own signature/body changes — separate target-file document.
- `git_service.py`'s dead-code `pipeline.run()` call — Reference File only; any
  required change there is an additional-target-file discovery, not this document's
  scope.
- `config/git_mcp_server.toml`, test files — separate target-file documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extract `dry_run` from `req.args` and pass it plus `_cfg.allow_detached_head` into `pipeline.run(...)` | Pending | — | — | |
| 2 | Add or update tests per Validation plan (tracked in the `test_git_security_compliance.py` sibling document) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A here — doc update deferred per Plan's Documentation Impact |

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
- **Requirement ID**: REQ-006 (thread req dry_run / _cfg.allow_detached_head into the
  pipeline call)
- **Source issue**: issues/20260902-144909_gitdryrun_align_detached_head_and_dry_run_with_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-191122_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-202634
- **Related target files**: scripts/mcp_servers/git/git_server.py
