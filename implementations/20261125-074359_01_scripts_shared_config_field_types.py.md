## Goal

Create the strict type primitives that both the startup builder and `/reload` share, so a
wrong-typed configuration value is rejected identically by both paths (REQ-001, type-rule
composition; REQ-011, structured error text without the raw value).

## Scope
**Release unit**: R1-strict-primitives

## Assumptions
- The primitives must live in `scripts/shared/` because `.importlinter` contract `shared-is-leaf`
  forbids `shared` importing `agent`; `scripts/shared/mcp_config.py` is a `shared` consumer and
  cannot reach an `agent` module (OD-04).
- `scripts/agent/services/typed_validators.py` (row 2) delegates here, so this module must not
  import anything from `agent`, including `agent.services.exceptions`.
- The error vocabulary is defined here and reused by the delegating callers, so the exception type
  raised by this module is the one the command layer catches.

## Design decisions
- One primitive per declared type, each raising the same error type with the field path and the
  violated rule, never the raw value (`AGENTS.md`-style no-value-in-error requirement, REQ-011).
- `bool` is rejected wherever a number or string is declared, and a number is rejected wherever a
  `bool` is declared: `isinstance(v, bool)` is checked before `isinstance(v, int)`.
- `FieldRule` (new) is a small frozen vocabulary (the rule name plus the declared type) used to build the
  error text, so every caller produces the same message shape.

## Alternatives considered
- Keeping the primitives in `agent/services/typed_validators.py` and importing them from `shared` —
  rejected, it breaks `shared-is-leaf`.
- Duplicating the rules in each layer — rejected, that duplication is the AC-1 defect.

## Implementation
### Target file
`scripts/shared/config_field_types.py` (new)

### Procedure
Define the error type, the seven strict primitives, and the `FieldRule` (new) vocabulary; keep the module
leaf-only (no `agent` import).

### Method
- `ConfigFieldTypeError` (new) carries the field path and the violated rule name; its message is
  built from those two and never from the value.
- `strict_bool` (new), `strict_int` (new), `strict_float` (new), `strict_str` (new),
  `strict_str_list` (new), `strict_str_mapping` (new) each take a value and the field path and
  return the typed value or raise `ConfigFieldTypeError` (new).
- `reject_unknown_keys` (new) takes the payload and the declared key set and raises with the key
  name only.

### Details
- Empty and whitespace-only strings are rejected by `strict_str` (new); an empty sequence is rejected by
  `strict_str_list` (new) unless the caller declares the field `allow_empty` (new) (UNK-05 is decided per
  registry entry in row 4, so the primitive takes the flag as an argument rather than deciding).
- Non-string mapping values are rejected element by element, naming the key, not the value.
- `bool` passed to `strict_int` (new) or `strict_float` (new) is rejected even though `bool` is an `int`
  subclass; this is the behavior `typed_validators._get_int` already has and must not regress.

## Compatibility considerations
- `tests/agent/services/test_typed_validators.py` pins the current error text of
  `typed_validators`; the delegating row (2) keeps the message shape by reusing `FieldRule` (new), so the
  existing wording stays valid where the rule name is unchanged.
- No public symbol is renamed; this module is new and only its callers change.

## Security considerations
- Error text must not echo configuration values: `approval_protected_paths`,
  `approval_github_allowed_repos`, and `memory_embed_url` can carry paths and tokens.

## Rollback considerations
- Revert the Phase 1 commit; nothing persists and no service holds state from this module.

## Validation plan
- `uv run pytest tests/shared/test_config_field_types.py -q` (row 25).
- `uv run lint-imports` — `shared-is-leaf` stays intact with the new leaf module.
- `uv run ruff check scripts tests`, `uv run mypy scripts`.

## Completion criteria
- Every primitive rejects the value shapes listed in the Plan's `Newly rejected inputs` for its
  type, and no raised message contains the raw value.
- `lint-imports` reports 6 contracts kept, 0 broken.

## Out of Scope
- Wiring the primitives into the section builders and the MCP parser (rows 13, 14, 15).
- The `allow_empty` (new) decision per registry entry (row 4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | covered by row 25 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | includes `lint-imports` |

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
- **Requirement ID**: REQ-001 (shared strict type rules), REQ-011 (structured config error); AC-1, AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/shared/config_field_types.py`
