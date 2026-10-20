# Track compatibility exceptions and obsolete symbols in a manifest with owner and expiry

## Priority
Medium

## Summary
Replace the hard-coded file allowlist in `tools/check_compat_shims.py` with a manifest in which every exception carries a reason, an owner, and an expiry date, and extend the manifest to name symbols that remain in source but are no longer a current path. An expired entry must produce a clear CI failure.

## Background
- Source: an investigation of the design documents dated 2026-10-20 that listed backward-compatibility features. It read documents only; the facts below were re-checked against the current tool and tests on 2026-10-20.
- `tools/check_compat_shims.py` detects leftover compatibility text with a dictionary of regular-expression patterns, most of them names that were removed from the code, and an optional `--check-removed-names` mode for documentation. (Explicit in code)
- Its exceptions are `DEFAULT_ALLOWLIST`, a hard-coded set of about twenty-five file paths, each with a one-line comment explaining why the file may contain a pattern. An alternative allowlist can be supplied as a file with one path per line. There is no owner, no expiry, and no per-entry reason field that the tool can read. (Explicit in code)
- The tool does not track a symbol that still exists in source but is no longer the current path. The documentation describes this case as requiring a context-aware check and as "not yet implemented (follow-up)". (Documentation only, consistent with the code)
- `vulture` is a development dependency, but no repository gate or baseline file for dead or obsolete code was found. (Explicit in code: searched `pyproject.toml`, `tox.ini`, `.pre-commit-config.yaml`, and the CI workflows)
- The backward-compatibility CI workflow runs `check_compat_shims.py --check-removed-names`, and the tool has about forty tests in `tests/tools/test_check_compat_shims.py`. (Explicit in code)

## Problem
An exception can be added to the allowlist and never reviewed again; nothing says who added it, why it is still needed, or when it should go. Obsolete symbols that remain in source are invisible to the tool, so the only record of them is prose that goes stale when the symbol is deleted.

## Reason for Change
A compatibility exception without an owner and an end date becomes permanent by default. Making the reason, owner, and expiry mandatory and machine-checked turns each exception into a tracked decision and gives cleanup work a deadline that CI enforces.

## Implementation Intent
- Introduce one manifest as the single record of compatibility exceptions and tracked obsolete symbols; the existing path allowlist becomes entries of that manifest, each with a reason carried over from its current comment.
- Make reason, owner, and expiry mandatory fields; reject an entry that lacks one.
- An entry past its expiry fails the check with a message that names the entry and its owner. Whether the failure is blocking in every environment is a decision for the owner (see Unresolved Questions).
- Track obsolete symbols that remain in source by name and file, so the tool can verify that each still exists and has the expected callers, and can report a manifest entry whose symbol is gone.
- Keep the current pattern detection and the `--check-removed-names` behavior unchanged.

## Target Files or Areas
- `tools/check_compat_shims.py` (load the manifest, validate fields, check expiry, check tracked symbols)
- A new manifest file under `config/` (location and format to be fixed in the plan; follow the existing configuration conventions)
- `tests/tools/test_check_compat_shims.py` (tests for the manifest validation, expiry, and symbol tracking)
- `tools/TOOL_DESCRIPTIONS.md` and `docs/00_governance/governance_04_documentation-checks.md` (describe the new behavior)
- `.github/workflows/backward-compat-check.yml` and `.pre-commit-config.yaml` (only if the invocation changes)

## Required Changes
- Define the manifest format with mandatory reason, owner, and expiry date, and a way to name a tracked symbol (module path and name).
- Migrate every entry of `DEFAULT_ALLOWLIST` into the manifest with a reason, an owner, and an expiry date supplied by the owner; do not invent owners or dates.
- Make the tool read the manifest, reject an entry missing a mandatory field, and fail with a clear message for an expired entry.
- Add tracked-symbol support: verify that a listed symbol still exists in the named file, and report a listed symbol that no longer exists so the entry can be removed.
- Keep the optional custom allowlist path working or remove it with its test, as the plan decides.
- Add tests for each rule, update `tools/TOOL_DESCRIPTIONS.md`, and update the check description in `governance_04`.

## Constraints
- Do not change the existing pattern set or what `--check-removed-names` reports.
- The tool must keep running without network access and without importing project code that needs a deployed environment.
- No entry may be created without an owner-supplied owner and expiry date.
- Follow `rules/coding.md` and the `AGENTS.md` rule that a new or changed tool is validated with ruff, mypy, bandit, and a smoke run against real repository data.
- Documentation follows the docs content policy and is written in English.

## Acceptance Criteria
- The manifest exists, every former `DEFAULT_ALLOWLIST` entry is present with reason, owner, and expiry, and the tool no longer carries a hard-coded path list.
- An entry missing reason, owner, or expiry makes the tool fail with a message naming the entry.
- An expired entry makes the tool fail with a message naming the entry and its owner.
- A tracked symbol that no longer exists is reported.
- The existing tests for pattern detection still pass, and new tests cover each new rule.
- `uv run python tools/check_compat_shims.py` and `uv run python tools/check_compat_shims.py --check-removed-names` pass on the repository, and `uv run python tools/check_tool_descriptions_sync.py` passes.

## Testing Expectations
- Unit tests in `tests/tools/test_check_compat_shims.py` for field validation, expiry, and symbol tracking, including a fixture manifest.
- `uv run ruff format` and `uv run ruff check` on the changed tool, `uv run mypy tools/check_compat_shims.py` with the path passed explicitly, `uv run bandit tools/check_compat_shims.py`, and a smoke run against the real repository.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, and `uv run python tools/check_docs_content_policy.py --strict` for the documentation changes.

## Documentation Impact
Yes. Describe the manifest and the expiry rule in the check description of `governance_04` and in `tools/TOOL_DESCRIPTIONS.md` (intent, constraints, failure behavior). Do not list the manifest entries in documentation.

## Out of Scope
- Deleting any obsolete symbol or compatibility stub (tracked in `compat003`, `compat004`, `compat005`).
- Changing the pattern dictionary or adding new removed-name patterns.
- Dead-code detection in general or enabling `vulture` as a gate.
- The review checklist for new compatibility code (`compat010`).

## Dependencies
- Related: `compat005` removes `read_json_file`, whose documentation example is the stated reason for the symbol-tracking part; the two touch the same governance text and the same tool comment and should be merged in a consistent order.
- Sibling-issue check: no open issue under `issues/` touches `tools/check_compat_shims.py` or its tests.

## Unresolved Questions
- Who is the owner and what is the expiry date for each current allowlist entry? (Needs confirmation; only the owner can supply these)
- Should an expired entry fail CI immediately, or fail only on the default branch or after a grace period? (Needs confirmation)
- Where should the manifest live, and in which format, to match the repository's configuration conventions? (Needs confirmation)
- Should tracked symbols be verified only for existence, or also for the absence of callers outside tests?

## AI Implementation Instruction
- Change only the tool, its tests, the new manifest, and the documentation listed; do not alter the existing pattern set or detection logic.
- Do not invent owners or expiry dates; if the owner has not supplied them, stop and report the open question.
- Keep each rule small and covered by its own test.
- Run the validation sequence for tools from `routing.md` before finishing, including the tool description sync check.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261020-123232
- **Related target files**: `tools/check_compat_shims.py`, `tests/tools/test_check_compat_shims.py`, `tools/TOOL_DESCRIPTIONS.md`, `docs/00_governance/governance_04_documentation-checks.md`, `.github/workflows/backward-compat-check.yml`, `.pre-commit-config.yaml`
