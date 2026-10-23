## Goal

Add one paragraph to `skills/python-test-and-fix/workflow.md`'s `Test structure` section requiring a fixture that repairs wiring to be paired with a wiring-level test, using `_make_bare_repl` as the worked counter-example (REQ-008).

## Scope

Only `skills/python-test-and-fix/workflow.md`. One paragraph appended to the existing `Test structure` section; no reformatting of the rest of the file. The paired rule bullet in `skills/python-test-and-fix/SKILL.md` is covered by row 4. No production file under `scripts/` changes.

## Assumptions

- The `Test structure` section currently states only the file-layout mirror rule (`:26-54`), which is the same rule the deleted `test_signal_handler_race.py` violated; the new paragraph adds the wiring-pairing rule alongside it.
- Line numbers below are current-HEAD values from `skills/python-test-and-fix/workflow.md`.

## Design decisions

- **One paragraph, existing form.** The paragraph is appended at the end of the `Test structure` section, after the "When finding or adding a test, mirror..." paragraph, in the section's plain-prose form. It names `_make_bare_repl` as the worked example and points to the enforced rule in `SKILL.md`.
- **Counter-example framing.** `_make_bare_repl` repairs wiring, so it is presented as the case that *must* be paired with a guard — the paragraph states the pairing requirement, not just the mirror rule.

## Alternatives considered

- Adding the paragraph to a different section (e.g. Step 13) — rejected: REQ-008 places it in `Test structure`, and that is where a reader looking for test-structure guidance expects it.
- A bullet or code block — rejected: the section is prose; a paragraph matches its existing form.

## Implementation

### Target file

`skills/python-test-and-fix/workflow.md`

### Procedure

1. Append one paragraph at the end of the `Test structure` section, after the "When finding or adding a test, mirror the target module's path under `scripts/` (or `tools/`), not a flat `tests/test_<module>.py` layout." paragraph. Match the section's plain-prose form.
2. Verify the skill still parses and its references are intact: `uv run python tools/check_skills_references.py`.

### Method

Append this paragraph (exact text) immediately after the final "When finding or adding a test..." paragraph of the `Test structure` section:

````markdown
A fixture that repairs production wiring must be paired with a wiring-level test. `_make_bare_repl` (`tests/agent/test_repl.py`) bypasses `AgentREPL.__init__` (`AgentREPL.__new__` plus a hand-supplied shutdown event) so its doubles stand in for config, terminal, LLM and MCP services; because it supplies what `__init__` does not, it must be paired with `TestWiringGuard`, which runs the real constructor and asserts one `asyncio.Event` is held across the objects that own it. Every wiring-repairing fixture in the suite carries such a paired guard and names it in its docstring — see the wiring-guard and mock-state rule in `SKILL.md`.
````

### Details

The insertion point is the last paragraph of the `Test structure` section (`workflow.md:54`). The paragraph references `TestWiringGuard` (the guard this Plan adds, row 1) and the `SKILL.md` rule (row 4); both are in-scope for this Plan, so the cross-reference is valid once rows 1 and 4 land.

## Compatibility considerations

N/A: skill-documentation change only; no code, no new dependency.

## Security considerations

N/A: no credential, permission, or I/O boundary touched.

## Rollback considerations

N/A: revert the commit; the change is a single appended paragraph.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| paragraph present, correctly formed | read + structure | `uv run python tools/check_skills_references.py` | Passes; references intact |
| no drift in the rest of the file | diff review | `git diff skills/python-test-and-fix/workflow.md` | Only the one paragraph added |

## Completion criteria

- The `Test structure` section contains one new paragraph pairing a wiring-repairing fixture with a wiring-level test, naming `_make_bare_repl` and pointing to the `SKILL.md` rule (AC-8).
- `uv run python tools/check_skills_references.py` passes (AC-8).
- `git diff` shows only the one appended paragraph; no other lines changed.

## Out of Scope

`skills/python-test-and-fix/SKILL.md` (row 4); the `Test structure` file-layout mirror rule and code block; any `scripts/` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the fixture-pairing paragraph to `Test structure` | In Progress | — | — | Order-independent; safe at HEAD |
| 2 | Add/update tests per Validation plan | N/A | — | — | doc-only rule, no test |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. `check_skills_references.py` | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | In Progress | — | — | this row |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-01 | Step 1 / REQ-008 | Cross-reference | Open | implementer | confirm `TestWiringGuard` exists before publishing the reference |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-008
- **Source issue**: `issues/done/20261021-093421_repl003_repl-shutdown-behavior-untested-in-real-wiring.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-043008_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-081341
- **Related target files**: `skills/python-test-and-fix/workflow.md`
