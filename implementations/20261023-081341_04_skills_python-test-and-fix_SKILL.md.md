## Goal

Add one bullet to `skills/python-test-and-fix/SKILL.md`'s `Core Testing Rules` stating the wiring-guard requirement and the prohibition on asserting mock state the test assigned (REQ-008).

## Scope

Only `skills/python-test-and-fix/SKILL.md`. One bullet added to the existing `Core Testing Rules (Strictly Enforced for AI)` list; no reformatting of the rest of the file. The paired paragraph in `skills/python-test-and-fix/workflow.md` is covered by row 5. No production file under `scripts/` changes.

## Assumptions

- The rule is routed into the skill by `routing.md:14-15`, which sends all test work to `skills/python-test-and-fix/`, so this is the durable home for the rule.
- Line numbers below are current-HEAD values from `skills/python-test-and-fix/SKILL.md`.

## Design decisions

- **One bullet, existing form.** The rule is added as a single list item in the enforced-rules section, matching the `**Lead-in**:` bold-prefix + colon + description form of the surrounding bullets. It states both halves of REQ-008: a `__init__`-constructed, post-startup-rebound component MUST have a wiring-level guard test, and a test MUST NOT assert on state the test itself assigned to a mock.
- **Placement next to the mock-cleanliness bullet.** The mock-state half pairs naturally with the existing "Ensure Mock Cleanliness" bullet, so the new item sits between it and "No Tool Hallucination".

## Alternatives considered

- A separate top-level section or a `workflow.md`-only note — rejected: REQ-008 requires the rule in the *enforced* Core Testing Rules, and `routing.md` routes test work here, so a rule outside this list is not loaded where enforcement happens.
- Two separate bullets — rejected: REQ-008 asks for one bullet; the two halves share one rationale (a self-asserting mock hides wrong wiring) and read better as a single scoped rule.

## Implementation

### Target file

`skills/python-test-and-fix/SKILL.md`

### Procedure

1. Insert one bullet into the `Core Testing Rules (Strictly Enforced for AI)` list, after the "Ensure Mock Cleanliness" bullet and before the "No Tool Hallucination" bullet. Match the existing bullet form exactly.
2. Verify the skill still parses and its references are intact: `uv run python tools/check_skills_references.py`.

### Method

Insert this bullet (exact text) immediately after the `Ensure Mock Cleanliness` line and before the `No Tool Hallucination` line:

````markdown
- **Wiring-Guard and Mock-State Prohibition**: A component constructed in `__init__` and rebound after startup (e.g. `AgentREPL`'s shutdown event, set via `set_shutdown_event`) MUST have a wiring-level guard test that runs the real constructor and asserts the production handoff; and a test MUST NOT assert on state the test itself assigned to a `MagicMock` — asserting self-assigned mock state hides the very defect (wrong or missing wiring) this rule exists to catch.
````

### Details

The insertion point is between the current `Ensure Mock Cleanliness` bullet and the `No Tool Hallucination` bullet (`SKILL.md:22`→`:23`). The rule is scoped to *state the test itself assigned to a mock* and to *components constructed in `__init__`*, not to interaction assertions in general — many suite tests legitimately assert mock call state, and this rule must not contradict them (see the Plan's Risks).

## Compatibility considerations

N/A: skill-documentation change only; no code, no new dependency.

## Security considerations

N/A: no credential, permission, or I/O boundary touched.

## Rollback considerations

N/A: revert the commit; the change is a single inserted bullet.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| bullet present, correctly formed | read + structure | `uv run python tools/check_skills_references.py` | Passes; references intact |
| no drift in the rest of the file | diff review | `git diff skills/python-test-and-fix/SKILL.md` | Only the one bullet added |

## Completion criteria

- The `Core Testing Rules` list contains one new bullet stating both the wiring-guard requirement and the mock-state prohibition, in the section's existing form (AC-8).
- `uv run python tools/check_skills_references.py` passes (AC-8).
- `git diff` shows only the one inserted bullet; no other lines changed.

## Out of Scope

`skills/python-test-and-fix/workflow.md` (row 5); the `SKILL.md` Task Routing / Phase overview tables; any `scripts/` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the wiring-guard / mock-state bullet to `Core Testing Rules` | In Progress | — | — | Order-independent; safe at HEAD |
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
| WI-01 | Step 1 / REQ-008 | Rule wording | Open | implementer | confirm the rule does not contradict existing mock-call assertions |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-008
- **Source issue**: `issues/done/20261021-093421_repl003_repl-shutdown-behavior-untested-in-real-wiring.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-043008_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-081341
- **Related target files**: `skills/python-test-and-fix/SKILL.md`
