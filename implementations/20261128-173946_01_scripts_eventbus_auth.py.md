## Goal
- Add one publish-if-current function to `scripts/eventbus/auth.py` that both authorization writers use (`REQ-001` conditional publication; `REQ-004` no behavior change for uncontended requests).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `scripts/eventbus/auth.py` only. The two writers are procedures 02 and 03; the tests are procedures 02 (companion) and 05.

## Assumptions
- Verified at the Plan's evidence revision (`tools/check_evidence_freshness.py check`: 23 unchanged, 0 changed).
- Sequencing (Step 2 overlap judgment): the admin TTL-precedence Plan (adrr001) is archived but its procedures are not yet executed; they edit `scripts/eventbus/admin_route.py`, `tests/eventbus/test_admin_topics_authorization.py`, and the ADR-013 Decision Detail 12. `plan_dependency_order.py` reports this Plan ready because adrr001 left `plans/`, but its procedures MUST be implemented first; re-read the target before editing. Line numbers are deliberately not cited.
- `publish_generation` stays unchanged and unconditional: `build_and_publish_generation` uses it for the startup baseline.
- Module size: `scripts/eventbus/auth.py` is 15636 B against the 24576 B gate; the addition is under 1 KB.

## Design decisions
- Name and signature: `publish_generation_if_current` (new) `(expected: AuthzGeneration | None, new_generation: AuthzGeneration) -> bool`. It compares `_CURRENT_GENERATION is expected`; on a match it assigns and returns `True`, otherwise it returns `False` and publishes nothing.
- The compare and the assignment contain no `await`, so the function is atomic on the event loop; the docstring states this property and that the function is process-local (ADR-013 Decision Detail 16).

## Alternatives considered
- An `asyncio.Lock` around the writers (rejected: the sweep's synchronous path is not covered and the invariant stays implicit).
- Comparing generation numbers instead of identity (rejected: the existing abort test publishes a different object and identity is the stricter check).

## Implementation
### Target file
`scripts/eventbus/auth.py`

### Procedure
1. Add `publish_generation_if_current` (new) directly after `publish_generation`, using the same `global _CURRENT_GENERATION` pattern.
2. Give it a docstring whose first line is a one-sentence summary (the generated reference uses it), followed by the atomicity and process-local notes.

### Method
- Parameter `expected` is `None` only before the baseline is published; the function treats `None` like any other value (a match means the module global is also `None`).
- Do not change `publish_generation`, `current_generation`, or `build_and_publish_generation`.

### Details
- Type hints are required (`mypy`); no new imports are needed because `AuthzGeneration` is defined in this module.

## Compatibility considerations
- Additive: no existing symbol changes; the generated reference output changes (procedures 06 and 07).

## Security considerations
- No credential handling; the compare-and-swap prevents a stale writer from overwriting a newer generation, which is the intended hardening.

## Rollback considerations
- Revert the commit; the function has no persisted effect.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/eventbus/auth.py` | Unit (tests added by procedure 05) | `uv run pytest tests/eventbus/test_authz_generation_ttl.py tests/eventbus/test_eventbus_auth.py -q` | Pass |
| `scripts/eventbus/auth.py` | Static | `uv run ruff format scripts/eventbus/auth.py`, `uv run ruff check scripts/eventbus/auth.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -c pyproject.toml scripts/eventbus/auth.py` | Clean |

## Completion criteria
- `publish_generation_if_current` (new) exists with the semantics above and a docstring; `publish_generation` is unchanged; static checks pass.

## Out of Scope
- Writer changes (procedures 02 and 03), tests (procedure 05), generated output (procedures 06 and 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `publish_generation_if_current` (new) to `scripts/eventbus/auth.py` | Pending | — | — | |
| 2 | Add or update tests per Validation plan (owned by procedure 05) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (publish-if-current function), `REQ-004` (uncontended behavior unchanged)
- **Source issue**: issues/20261125-103308_adrr002_authz-publication-invariant.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261128-172526_adrr002_authz-publication-invariant.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-173946
- **Related target files**: `scripts/eventbus/auth.py`
