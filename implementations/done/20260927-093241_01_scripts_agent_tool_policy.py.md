## Goal

Add `\r` (carriage return) to `_METACHAR_RE`'s fail-closed metacharacter set in `scripts/agent/tool_policy.py`, fixing a confirmed security-classification gap where a carriage-return-separated `shell_run` command bypasses the metacharacter check and is misclassified as `RiskLevel.NONE` instead of `HIGH` (REQ-001).

## Scope

In scope: `_METACHAR_RE`'s regex pattern (line 42) only. Out of scope: `_match_executable_identity`/`shlex.split`'s tokenization behavior (standard library behavior, not to be changed) and any other part of `classify_risk`/`_special_case_risk`'s logic (confirmed already correct otherwise).

## Assumptions

- None beyond the Plan's own confirmed evidence (the regex gap and `shlex`'s whitespace treatment of `\r` were both directly confirmed via Read and an empirical Python check).

## Design decisions

- Add `\r` to the existing alternation directly (e.g. `r"...|[\r\n]"` replacing the existing lone `\n` alternative, or `r"...|\r|\n"`), mirroring exactly how `\n` is already handled — minimal, single-character-class addition.

## Alternatives considered

- Rewriting the whole `_METACHAR_RE` pattern for clarity while making this fix: rejected — per `AGENTS.md` Global Rule 5, scope this change to only what the task requires; a broader rewrite is unrelated cleanup.

## Implementation

### Target file

`scripts/agent/tool_policy.py`

### Procedure

1. Re-confirm `_METACHAR_RE`'s exact current pattern via Read (line 42): `re.compile(r"[;|&]|&&|\|\||`|\$\(|<\(|>\(|>>|<<|[<>]|\n")`.
2. Change the trailing `|\n` alternative to `|[\r\n]` (a character class matching either `\r` or `\n`), so the full pattern becomes `r"[;|&]|&&|\|\||`|\$\(|<\(|>\(|>>|<<|[<>]|[\r\n]"`.

### Method

Single-character-class edit to one regex literal — no other code change.

### Details

- Before: `_METACHAR_RE = re.compile(r"[;|&]|&&|\|\||`|\$\(|<\(|>\(|>>|<<|[<>]|\n")`.
- After: `_METACHAR_RE = re.compile(r"[;|&]|&&|\|\||`|\$\(|<\(|>\(|>>|<<|[<>]|[\r\n]")`.
- Verify empirically after the edit: `_METACHAR_RE.search("cat\r/etc/passwd")` should now match (truthy), causing `_has_metacharacters` to return `True` and `_special_case_risk` to return `RiskLevel.HIGH` for this command, before ever reaching `shlex.split`/prefix matching.

## Compatibility considerations

- This is a security-hardening change, not a behavior-narrowing one for any legitimate command: a genuine command argument containing a literal `\r` (already an unusual case) will now classify as `HIGH` rather than matching a safe prefix — this is the intended, safer fail-closed behavior, consistent with how `\n` is already handled.

## Security considerations

- This is the fix for a confirmed command-injection-style evasion technique (carriage-return substituted for a space/newline to bypass the metacharacter fail-closed check while `shlex` still treats it as whitespace, allowing a smuggled dangerous command to match an approved safe prefix). Restores the intended fail-closed behavior; do not relax this test's expectation to match the pre-fix (vulnerable) state.

## Rollback considerations

- `git revert` the commit, or manually restore the regex to its prior (vulnerable) form. Given the security nature of this fix, a rollback should only be performed with explicit awareness that it reintroduces the confirmed evasion technique.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/tool_policy.py` | Unit | `uv run pytest tests/agent/test_tool_policy.py -q` | All tests pass, including both previously-failing carriage-return tests; no regression in other risk-classification tests (space/whitespace/quote handling) |

## Completion criteria

- `uv run pytest tests/agent/test_tool_policy.py::TestPrefixCollision -q` passes (both carriage-return tests return `"high"`).
- `uv run pytest tests/agent/test_tool_policy.py -q` (full file) passes with no regression in other currently-passing risk-classification tests (space/whitespace/quote handling for the safe-prefix path).

## Out of scope

- Any other eventbus/agent/mcp_servers/shared test file tracked under a separate Plan/issue.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: existing `TestPrefixCollision` carriage-return tests already cover this fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | If a security design doc describes `_METACHAR_RE`'s exact character set, update it to include `\r` — confirm exact doc path at implementation time; otherwise N/A: internal implementation detail |

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
- **Requirement ID**: REQ-001: add `\r` to `_METACHAR_RE`
- **Source issue**: issues/20260927-075257_agent006_tool_policy-carriage-return-command-misclassified-as-risk-none.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-085129_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-093241
- **Related target files**: scripts/agent/tool_policy.py
