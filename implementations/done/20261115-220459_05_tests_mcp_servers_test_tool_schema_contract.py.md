## Goal

Add an exact-equality parity assertion between `TOOL_LIST` `is_write=True` entries
and `ALL_SIDE_EFFECTING_TOOLS` (with explicitly named approved exceptions only) to
`tests/mcp_servers/test_tool_schema_contract.py`, so a future omission fails in CI
rather than at runtime. (`REQ-005`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The existing `test_tool_name_coverage_matches_tool_constants()` (lines 51-58)
  already imports every `TOOL_LIST` module and iterates its entries; reuse that
  pattern.
- `ALL_SIDE_EFFECTING_TOOLS` is defined in `shared/tool_constants.py` (row 01).
- Some side-effecting tools may legitimately carry `is_write=False` in their
  schema (for example delete or execute tools), and vice versa; those are the
  "approved exceptions" and must be enumerated explicitly by inspecting the real
  `is_write` flags.

## Design decisions

- Add a new test function (do not modify the existing coverage test) that builds
  the set of tool names with `is_write=True` across all `TOOL_LIST` modules and
  asserts its symmetric difference with `ALL_SIDE_EFFECTING_TOOLS` is a subset of
  a small, reviewed, explicitly-named approved-exceptions set.

## Alternatives considered

- **A separate new test file.** Rejected: the plan adds to the existing file that
  already iterates every `TOOL_LIST` module, keeping the schema-contract checks
  together.

## Implementation
### Target file
`tests/mcp_servers/test_tool_schema_contract.py`

### Procedure
1. Import `ALL_SIDE_EFFECTING_TOOLS` from `shared.tool_constants`.
2. Add `test_is_write_matches_side_effect_classification()`:
   - Build `is_write_tools = {t["name"] for module in _TOOL_LIST_MODULES for t in module if t.get("is_write")}`.
   - Define `APPROVED_EXCEPTIONS` (new) as an explicitly named set of tool names whose
     `is_write` flag diverges from the side-effect classification. Derive this
     set by inspecting each `TOOL_LIST` entry's real `is_write` flag and listing
     every name in the symmetric difference with `ALL_SIDE_EFFECTING_TOOLS`.
   - Assert `{name for name in (is_write_tools ^ ALL_SIDE_EFFECTING_TOOLS)} <= APPROVED_EXCEPTIONS`, with a message naming the unexpected diff.
3. Do not alter `test_all_tools_pass_schema_v2_contract()` or
   `test_tool_name_coverage_matches_tool_constants()`.

### Method
Place the new function after the existing coverage test. Keep the
`importlib`-based module iteration already used in the file.

### Details

- The parity catches both directions: a tool marked `is_write=True` but missing
  from the canonical set (silent bypass) and a canonical member not marked
  `is_write=True`.
- `APPROVED_EXCEPTIONS` (new) must stay minimal and reviewed; adding a name hides a
  real divergence, so each entry needs a one-line reason.
- `config/mcp_dedup.toml` retry classes are a related but separate dimension;
  the plan's broader parity across retry classes is out of scope for this
  function unless the implementer extends it deliberately.

## Compatibility considerations

Test-only addition; does not change `scripts/` behavior.

## Security considerations

This test is the CI guard that prevents a side-effecting tool from silently
bypassing dedup/idempotency (ADR-004). Keep `APPROVED_EXCEPTIONS` (new) minimal.

## Rollback considerations
N/A: revert the commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected |
|---|---|---|---|
| `tests/mcp_servers/test_tool_schema_contract.py` | Unit: parity holds with only approved exceptions | `uv run pytest tests/mcp_servers/test_tool_schema_contract.py` | parity test passes; no unexpected symmetric difference |

## Completion criteria

- The parity test exists and passes with `ALL_SIDE_EFFECTING_TOOLS`.
- `APPROVED_EXCEPTIONS` (new) lists exactly the reviewed `is_write` divergences.

## Out of Scope

- Changing any `is_write` value in a `TOOL_LIST`.
- Editing `tool_constants.py`, `dispatch.py`, `http_transport.py`, `tool_policy.py` (rows 01-04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `is_write` vs canonical-set parity assertion | Completed | 20261116-071355 | 20261116-071355 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261116-071355 | 20261116-071355 |  |

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
- **Requirement ID**: `REQ-005` (CI parity test between `is_write` and the canonical set)
- **Source issue**: `issues/20261111-163800_sideeffect001_side-effect-classification-central.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-052032_sideeffect001_side-effect-classification-central.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-220459
- **Related target files**: `tests/mcp_servers/test_tool_schema_contract.py`