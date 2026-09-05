## Goal

Decide and implement how `check_port_drift()`/`check_port_range_claim()`
should change under the new docs/ content policy — deprecate, narrow to an
exempt file set, or keep pending a documented exemption list (REQ-003,
REQ-005, REQ-006).

## Scope

- In-scope: this file's `check_port_drift()` and `check_port_range_claim()`
  functions only.
- Out-of-scope: `docs/00_governance_04_documentation-checks.md`'s
  description update (`implementations/20260905-113050_02`); rewriting any
  `docs/*.md` file's content; removing port-number verification for
  `rules/env.md` (out of this policy's scope entirely, and outside
  `docs/*.md` to begin with).

## Assumptions

- **Blocking precondition (Plan Phase 1)**: this row's decision depends on
  two sibling Plans landing first — `docscope1`
  (`plans/done/20260905-101850_plan.md`, `skills/DESIGN.md` five
  remove-category definitions) and `docscope2`
  (`plans/done/20260905-102139_plan.md`, `tools/check_docs_content_policy.py`
  and its violation inventory from a corpus run). Re-verified this cycle:
  neither has been executed yet — `skills/DESIGN.md` still does not contain
  the remove-category definitions (`grep -n "remove-categor" skills/DESIGN.md`
  returns no match), and `tools/check_docs_content_policy.py` does not yet
  exist (its own implementation procedure,
  `implementations/20260905-112812_01`, is generated but not executed). Do
  not execute Implementation > Method against source until both preconditions
  are met.
- Per the source Plan's provisional, evidence-based reading (subject to
  re-verification once the actual violation inventory lands): since no
  `docs/*.md` content has been migrated away from stating port numbers as of
  this cycle, option (c) — keep pending a documented, explicit exemption
  list — is the only option whose precondition is currently satisfiable.
  This is not a final decision; it must be re-confirmed against the actual
  `docscope2` violation inventory before this row's Method is executed.

## Design decisions

If option (c) is confirmed: no functional code change to
`check_port_drift()`/`check_port_range_claim()` is required — both functions
remain exactly as-is; only the rationale is recorded (in
`implementations/20260905-113050_02`'s target file). If the actual violation
inventory instead supports option (a) or (b), this row's Method changes
accordingly (see Details) — the choice is made at Method-execution time, not
fixed here.

## Alternatives considered

Implementing option (a) (deprecate) preemptively, on the assumption that most
port-stating docs will eventually be migrated — rejected: deprecating before
confirming via the actual violation inventory that no `docs/*.md` file still
legitimately states a port number would silently stop catching real
port-configuration drift in files that still do (per Plan Risks).

## Implementation

### Target file

`tools/check_docs_consistency.py`

### Procedure

1. Confirm both sibling Plans (`docscope1`, `docscope2`) have landed before
   proceeding — re-verify against their actual landed text/inventory, not
   the Plan-time snapshot (per source Plan Assumptions).
2. Re-read `docscope2`'s landed violation inventory for how many `docs/*.md`
   files and port references are affected.
3. Confirm or correct this row's provisional reading (option (c)) against
   that inventory.
4. Implement the confirmed option:
   - **Option (c) (provisional default)**: no code change to either
     function — proceed directly to
     `implementations/20260905-113050_02`'s rationale recording.
   - **Option (a) (deprecate)**: only if the inventory confirms no
     remaining `docs/*.md` file legitimately states a port number — remove
     or no-op both functions' call sites in this file's `main` flow (lines
     733 and 749, re-confirmed present this cycle), retaining the function
     definitions with a deprecation docstring rather than deleting them
     outright (per `rules/coding.md` Deprecation policy: removed the next
     time an unrelated Plan touches this file, provided a zero-caller
     re-check still holds).
   - **Option (b) (narrow)**: only if the inventory confirms a small,
     enumerable exempt file set — add a file-path allowlist/denylist
     parameter to both functions, scoping their scan to only the
     non-exempt files.

### Method

Direct `Edit` — outcome depends entirely on which option Procedure step 3
confirms; for the provisional option (c) outcome, no source-code edit is
made to this file at all (this row's Execution Status would then record "No
change needed — option (c) confirmed" rather than a diff).

### Details

`check_port_drift()` (line 248, re-confirmed present) and
`check_port_range_claim()` (line 599, re-confirmed present) are both called
from this file's domain-consistency `main` flow (lines 733 and 749,
re-confirmed present this cycle: `all_issues.extend(check_port_drift(docs_dir,
files, repo_root))` and `all_issues.extend(check_port_range_claim(docs_dir,
files, repo_root))`). Whichever option is confirmed, `rules/env.md` must
never lose port-number verification (REQ-005) — trivially satisfied
regardless of option, since `rules/env.md` is outside `docs/*.md` and was
never in either function's scan scope to begin with (re-confirmed via this
Plan's own Reference Files row for `rules/env.md`).

## Compatibility considerations

No public/runtime-facing interface change regardless of option: the CLI's
`--domain` entry points and flags are unaffected — only these 2 of 13
per-domain checks' internal behavior/scope changes, and only if option (a)
or (b) is confirmed (option (c) makes no code change at all).

## Security considerations

N/A — no security-sensitive logic in either function; no new subprocess,
credential, or untrusted-input handling introduced by any of the three
possible outcomes.

## Rollback considerations

If option (c) is confirmed, there is nothing to roll back (no code change
made). If option (a) or (b) is implemented and later found wrong, revert via
`git revert` — no other file depends on either function's current behavior
beyond this file's own `main` flow.

## Validation plan

- `uv run pytest tests/tools/` (new tests, per
  `implementations/20260905-113050_02`... — actually per this Plan's own test
  row requirement, added under `tests/tools/` reflecting whichever option is
  confirmed) — pass.
- `uv run ruff check tools/check_docs_consistency.py` — clean.
- `uv run mypy tools/check_docs_consistency.py` — clean.

## Completion criteria

- The confirmed option (deprecate / narrow / keep pending) is implemented
  (or, for option (c), confirmed as requiring no code change) — not left
  silently inconsistent with the new policy.
- `rules/env.md` retains port-number verification status quo (i.e., remains
  untouched by either function, as it always was).

## Out of scope

Rewriting any `docs/*.md` file's port-number content. Deciding the fate of
any other check in this file (schema drift, config-key presence, tool-name
drift, etc.).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked pending sibling Plans `docscope1` (`plans/done/20260905-101850_plan.md`) and `docscope2` (`plans/done/20260905-102139_plan.md`) landing — re-confirmed neither has landed this cycle |
| 2 | Add or update tests per Validation plan | Pending | — | — | New tests only, per Plan REQ-006 correction — no prior test suite exists to update |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: documentation update is a separate row, `implementations/20260905-113050_02` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Sibling Plans `docscope1` and `docscope2` not yet implemented — the option choice (deprecate/narrow/keep pending) cannot be finalized without `docscope2`'s actual violation inventory | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-005, REQ-006
- **Source issue**: issues/done/20260903-200135_docscope3_reconcile-port-drift-checks-with-new-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-102436_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-113050
- **Related target files**: tools/check_docs_consistency.py
