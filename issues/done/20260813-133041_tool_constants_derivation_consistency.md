# Unify TOOLS/READ/WRITE derivation direction across tool groups in tool_constants.py

## Priority
Low

## Summary
In `scripts/shared/tool_constants.py`, different tool groups derive their frozensets in
inconsistent directions: `CICD_*`/`RAG_*` derive `READ` as `TOOLS − WRITE`, while
`GIT_*`/`GITHUB_*` derive `TOOLS` as `READ | WRITE (| DANGEROUS)`. Both directions are
currently correct (existing tests assert the union/disjointness invariants hold either way),
but the inconsistency makes the file harder to reason about and invites a copy-paste slip in
future edits.

## Reason for Change
Found during a behavior-preserving refactor cycle on `scripts/shared/tool_constants.py`
(2026-08-13). Not changed there because this file holds the `WRITE_TOOLS`/`READ_TOOLS`/
`DELETE_TOOLS`-style classification sets consulted by MCP routing logic
(`tool_executor.py`/`route_resolver.py`) — the refactor's special-case constraint forbade any
change to set membership or classification semantics, and manually re-deriving one group's
direction to match another risks a silent membership change disguised as a consistency fix
(Evidence label: Explicit in code — both derivation directions are directly visible in the
source; the union/disjointness invariants are Verified by test in
`tests/shared/test_tool_constants.py`).

## Implementation Intent
Pick one canonical derivation direction (either "derive READ as TOOLS minus WRITE" or "derive
TOOLS as READ union WRITE") and apply it consistently across all tool groups
(`CICD_*`, `RAG_*`, `GIT_*`, `GITHUB_*`, and any others in the file). This must be a **pure
consistency change with zero membership change** — the existing invariant tests in
`tests/shared/test_tool_constants.py` are the acceptance check, not a description of what to
build.

## Target Files or Areas
- `scripts/shared/tool_constants.py`

## Required Changes
- Record the current membership of every exported frozenset (e.g. via a one-off script printing
  sorted members) before touching anything, as a byte-for-byte comparison baseline.
- Re-derive each group's constants in the chosen consistent direction.
- Re-run the recorded-membership comparison after the change — every frozenset's membership must
  be identical to the baseline.

## Acceptance Criteria
- All exported frozensets in `tool_constants.py` have byte-for-byte identical membership before
  and after (verified by the recorded-baseline comparison, not just by existing tests passing).
- `tests/shared/test_tool_constants.py` and `tests/shared/test_tool_registry.py` pass unchanged.
- Derivation direction is consistent across all tool groups in the file.

## Testing Expectations
Run `tests/shared/test_tool_constants.py` (all union/disjointness invariant tests) and
`tests/shared/test_tool_registry.py` before and after. Additionally, write a temporary
membership-comparison check (can be discarded after use) — this is the primary safeguard against
an accidental classification change, since the existing tests check invariants, not exact
membership.

## Documentation Impact
None expected — this is an internal consistency cleanup with no external contract change.

## Out of Scope
- Do not change which tools belong to which classification set.
- Do not touch `route_resolver.py`, `tool_executor.py`, or `config/agent.toml` tool_names as
  part of this cleanup.

## AI Implementation Instruction
This is a special-case file per `prompts/04_refactor.md`/`workflow.md` (MCP routing
classification data). Before making any change, dump every exported frozenset's sorted members
to a file as a baseline. After the change, diff the new dump against the baseline — it must be
empty. If it is not empty, stop and do not proceed; that would mean a real classification change
occurred, which is explicitly out of scope for this issue.
