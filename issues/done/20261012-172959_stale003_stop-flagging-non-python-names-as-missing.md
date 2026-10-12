# Stop flagging non-Python names as missing

## Priority
Medium

## Summary
`tools/stale_detector.py` checks every backticked, identifier-shaped token of a procedure against the `.py` files of the repository and reports `symbol_missing` when the token appears in none. Several kinds of names can never appear in a `.py` file even though they are cited correctly: configuration keys and database table names, lint rule codes, built-in exception names, sibling-procedure numbers, and documentation chapter ids. About 3.6% of the archived procedures cite at least one of them, and each such citation aborts the cycle until a person approves an exception. Make the detector recognize these classes instead of reporting them.

## Background
- `code-implementation` Step 3 aborts a procedure on any detector mismatch and forbids correcting the procedure and continuing.
- The detector's symbol check (`_check_symbol_refs`) skips tokens that are not identifier-shaped, tokens in a small allowlist, and tokens that fail a minimum shape test; a token that passes is looked up in the target file and then in every `.py` file of the repository (`_symbol_present_somewhere`).
- `plans/done/20261012-132739_plan.md` (stale001) handled two other classes: prose mistaken for an import, and names that the procedure itself creates (the `(new)` marker). It recorded as Unknown UNK-03 that further classes might exist. Its changes were still uncommitted when this issue was written.
- During the stale001 follow-up work, procedures written for other issues hit three of the classes below in practice: a `mypy` setting name (`warn_return_any`), the built-in exception `LookupError`, and a sibling-procedure reference (`_02`); each had to be reworded or approved as an exception. `LookupError` was reported only because no `.py` file used it at that moment; `scripts/agent/startup_prompt_setup.py` now does, so it is no longer reported today, which shows that built-in names pass or fail by accident.

## Problem
Method: for every backticked token of the archived procedures (`implementations/done/*.md`, 6053 files) that has the detector's identifier shape and appears in no tracked `.py` file, classify why. Only classes that are independent of the repository's history are counted, because a token that was removed later is genuinely stale and cannot be told apart from a false positive in an archived procedure. All counts are measured on the current repository.
- Configuration keys, database table names, and tool settings that exist in `config/`, `conf.d/`, `schemas/`, `deploy/`, `init.d/`, or `pyproject.toml` but in no `.py`: 27 distinct tokens in 111 procedures. Examples: `tool_results` (a table created in `deploy/init_db.sh`; 39 procedures), `concurrency_limit`, `enable_refresh`, `embedding_model`, `vector_table` (keys in `config/mdq_mcp_server.toml`), `healthcheck_mode` and `HealthcheckMode` (`config/agent.toml`), `asyncio_mode` (`pyproject.toml`).
- Documentation chapter ids such as `agent_10`, `governance_04`: 58 distinct tokens in 66 procedures. They are prefixes of existing `docs/` file names, not code.
- Built-in and dunder names such as `DeprecationWarning`, `MemoryError`, `StopIteration`, `__slots__`, `__init_subclass__`: 6 tokens in 15 procedures. `LookupError` is a further example that was reported in practice while no `.py` file used it; it passes today only because `scripts/agent/startup_prompt_setup.py` happens to name it.
- Lint and type-checker rule codes such as `RUF100`, `F841`, `I001`: 3 tokens in 7 procedures.
- Sibling-procedure numbers such as `_01`, `_02`, `_10`, written to refer to another procedure of the same plan: 9 tokens in 20 procedures.
- Union of the five classes: 215 of 6053 procedures (3.6%).
- Evidence (`Explicit in code`): none of these can be satisfied by the `.py`-only lookup, so the abort is independent of whether the procedure is correct.
- Examined and excluded: `line_out_of_bounds` findings (66 in a sample of 300 procedures) concern 11 files whose target was split or shortened after implementation; they are genuine staleness. The large remaining group of absent tokens (about 1690 procedures) is dominated by names that a procedure creates (handled by the `(new)` marker) or that were removed later (genuinely stale), so it is not part of this issue.

## Reason for Change
- Each false abort costs a person an exception decision for a correct procedure; at 3.6% of procedures the gate teaches authors to avoid citing configuration, rule codes, and built-ins, or to bypass it.
- The five classes are deterministic: each can be recognized without guessing, and without hiding genuinely stale names.

## Implementation Intent
Handle each class by the narrowest rule that cannot mask a stale Python symbol:
- Rule codes and sibling numbers: skip tokens that match their fixed shapes (a short run of capital letters followed by digits; an underscore followed only by digits).
- Built-in and dunder names: skip names defined by the `builtins` module and names written between double underscores.
- Configuration keys and table names: when the token is absent from every `.py` file, also accept it if it appears in the configuration-like files named above (`config/`, `conf.d/`, `schemas/`, `deploy/`, `init.d/`, `pyproject.toml`, `tox.ini`). Do not search `docs/`, `plans/`, `issues/`, or `implementations/`, which keep the names of removed code and would hide genuine staleness.
- Documentation chapter ids: skip a token that is a prefix of an existing `docs/` file name, rather than a broad pattern that could match a real identifier such as a numbered step name.
Keep every rule independently testable and keep the abort policy unchanged.

## Target Files or Areas
- `tools/stale_detector.py` (`_check_symbol_refs`, `_symbol_present_somewhere`, the skip rules)
- `tests/tools/test_stale_detector.py`
- `tools/TOOL_DESCRIPTIONS.md` (the `stale_detector.py` entry)
- `templates/implementation-procedure.md` — only if the author guidance needs a note about names the detector now recognizes (Unresolved Questions)

## Required Changes
- Add the five recognition rules above, each as a small, separately tested function or constant.
- Extend the repository-wide presence check to the configuration-like locations only.
- Add tests for each class using the exact tokens listed under Problem, plus a negative test per class showing that a similar name that is a real stale Python symbol is still reported.
- Update the tool description.

## Constraints
- Do not weaken detection of genuinely stale Python symbols: a cited class, function, or constant that is absent from every `.py` file and from the configuration-like files must still be reported.
- Do not search documentation or archived work items to decide that a name exists.
- Keep the detector regex-based and dependency-free; the lookups use the file system only.
- Keep runtime acceptable: the current symbol lookup rescans every `.py` file per missing token (about 1.2 s per procedure in a measurement of 300 archived procedures); the new configuration lookup must not make that noticeably worse (cache the file reads per run).
- Do not change the abort-on-any-mismatch policy.

## Acceptance Criteria
- A backticked configuration key or table name that appears only in the configuration-like locations is not reported; the same name absent from them and from every `.py` is still reported.
- A rule code, a sibling-procedure number, a built-in name (including `LookupError`), and a dunder name are not reported.
- A documentation chapter id that is the prefix of an existing `docs/` file name is not reported; a similar token that matches no file name is still reported.
- Re-running the measurement described under Problem over the archived procedures shows zero tokens of the five classes among the reported `symbol_missing` findings, and the existing detector tests pass unchanged.
- Verdicts of the detector on a sample of archived procedures change only where a token of these classes was the reason for a `symbol_missing` finding.
- `uv run python tools/check_tool_descriptions_sync.py` reports no issues.

## Testing Expectations
- Unit tests per class and per negative case in `tests/tools/test_stale_detector.py`, using a temporary directory with a small configuration file and a small docs tree.
- Before and after comparison of verdicts on a sample of archived procedures (for example 60), expecting differences only for the targeted tokens.
- Run `uv run pytest tests/tools/test_stale_detector.py`, `uv run ruff check tools tests/tools`, `uv run mypy tools/stale_detector.py`.

## Documentation Impact
- Yes: the `stale_detector.py` entry of `tools/TOOL_DESCRIPTIONS.md` must list what is recognized. A note in `templates/implementation-procedure.md` is only needed if authors should know (Unresolved Questions). No `docs/*.md` change is expected.

## Out of Scope
- New target files that do not exist yet (tracked separately in the sibling issue `stale002`).
- Names that a procedure creates (handled by the `(new)` marker from stale001) and genuinely stale references.
- Widening which line-leading imports are checked (stale001 UNK-02).
- A reusable measurement tool: the classification above was a one-off analysis; adding it to `tools/` is a separate decision.

## Dependencies
- Depends on stale001 (`plans/done/20261012-132739_plan.md`) being committed: it shares `tools/stale_detector.py` and its test file.
- Sibling issue `stale002` (new target files) touches the same file and tests; the two are independent and can be done in either order, but the second one rebases onto the first.

## Unresolved Questions
- Whether configuration words should also be searched in other locations (for example `rules/` or `templates/`); the measured classes need only the locations listed. Widen only with evidence.
- Whether a small documentation note for authors is warranted, since the recognized classes need no author action.
- Whether a name that exists only in configuration should instead be reported as a warning-level finding; the detector currently has only the stale/not-stale verdict, so this would be a larger change.
- The counts are measured on the current repository, so they will drift; the acceptance measurement should be re-run when planning starts.

## AI Implementation Instruction
- Change only the files listed under Target Files or Areas; do not edit archived procedures.
- Keep every existing detector test passing without edits; add tests rather than relaxing them.
- Do not widen the lookup to documentation or work-item directories, and prove with a negative test that a genuinely stale Python name is still reported.
- Stop and report open questions instead of choosing a broader pattern for documentation ids.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-132739_plan.md
- **Source implementation procedure**: implementations/done/20261012-170854_01_tools_stale_detector.py.md
- **Generated at**: 20261012-172959
- **Related target files**: tools/stale_detector.py, tests/tools/test_stale_detector.py, tools/TOOL_DESCRIPTIONS.md, templates/implementation-procedure.md
