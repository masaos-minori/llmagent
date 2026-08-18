# Unify `[DENIED]`/`read_only` guard-denial message formatting into a structured error-code scheme

## Priority
Low

## Summary
`scripts/mcp_servers/git/git_service.py`'s 10 `git_*` handlers each return ad hoc,
human-readable `[DENIED]`/`read_only=true` strings on security-guard denial (from
`git_security.py`'s `_check_repo_path`/`_check_write`), rather than a structured, machine-parsable
error code.

## Reason for Change
Found during a `prompts/04_refactor.md` cycle on `git_service.py` (2026-08-14). Not implemented
there because changing these message formats would alter visible output that existing tests
pattern-match on and that MCP clients may parse/display verbatim — a structured error-code
scheme is a genuine behavior change (new response shape), not a pure refactor, and requires
product-level design input (what should the structured shape look like?) rather than being an
implementation detail an isolated refactor cycle can decide unilaterally.

## Implementation Intent
This needs a design decision before any implementation: should denial responses carry a
structured `error_code` field alongside (or instead of) the current human-readable string? If
so, define the enum of codes (e.g. `PATH_NOT_ALLOWED`, `READ_ONLY_MODE`) and the exact response
shape change, then write a full before/after characterization-test rewrite for every guard-denial
message across `git_service.py` (and, if unified repo-wide, the equivalent guards in
`file/{delete,read,write}_service.py`) before implementing.

## Target Files or Areas
- `scripts/mcp_servers/git/git_security.py` (guard implementations)
- `scripts/mcp_servers/git/git_service.py` (10 handlers consuming guard results)
- `tests/mcp_servers/git/test_mcp_git.py` (existing guard-denial message assertions)
- Unknown: whether this should extend to `scripts/mcp_servers/file/*_service.py`'s analogous
  guards (not decided; a maintainer should scope this before implementation starts)

## Required Changes
- Design review: decide the target structured shape (or explicitly decide not to change the
  format and close this issue as "no action").
- If proceeding: full characterization-test rewrite for every guard-denial message currently
  produced, asserting the *new* expected shape, before touching implementation code.
- Update `_check_repo_path`/`_check_write` and all 10 `git_*` handlers to use the new shape.

## Acceptance Criteria
- A maintainer-approved target shape exists and is documented in this issue (or a linked design
  note) before implementation begins.
- All existing and new tests assert the agreed-upon final message/response shape.
- No unintended change to which conditions trigger a denial (only the message format changes).

## Testing Expectations
Full characterization-test rewrite for guard-denial paths in `tests/mcp_servers/git/
test_mcp_git.py`; full `tests/mcp_servers/git/` and `tests/mcp_servers/file/` regression runs if
extended repo-wide.

## Documentation Impact
Update any `docs/04_mcp_*` file documenting the exact denial-message format if one exists.

## Out of Scope
- Do not implement any format change without a documented, maintainer-approved target shape
  first (this is a design decision, not a refactor).
- Do not weaken or reorder the underlying guard logic itself — only the resulting message shape
  is in scope for discussion.

## AI Implementation Instruction
Treat this as blocked on a design decision. Do not write implementation code until the target
error-code/response shape is explicitly approved and recorded in this issue or a linked
`plans/` entry, per `rules/coding.md`'s explicit sign-off gates for security-adjacent changes.
