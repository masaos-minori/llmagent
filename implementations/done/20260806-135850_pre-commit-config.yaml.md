# Implementation: .pre-commit-config.yaml — Phase 3: wire the suppression-justification hook

## Goal

Wire `tools/check_suppression_justification.py` into `.pre-commit-config.yaml` as a
`local` hook so unjustified `# noqa`/`# type: ignore`/`# nosec` suppressions are caught
automatically at commit time, following the exact shape of the existing `no-compat-stubs`
hook.

## Scope

**In-Scope:**
- Add one new `local` hook entry, `check-suppression-justification` (or equivalent id),
  to `.pre-commit-config.yaml`, calling
  `python -m tools.check_suppression_justification`.
- Match the existing `no-compat-stubs` hook's structure: `language: system`,
  `pass_filenames: false`, and an appropriate `types`/`types_or` restriction (the plan
  specifies `types: [python]`, since suppression comments are Python-only, unlike
  `no-compat-stubs` which also scans `markdown` via `types_or: [python, markdown]`).

**Out-of-Scope:**
- Modifying the existing `no-compat-stubs` or `tool-descriptions-sync` hook entries.
- Any change to hook ordering guarantees beyond appending the new entry (unless the repo's
  existing convention groups related hooks — confirm at implementation time by re-reading
  the full hook list, not assumed here).
- `tox.ini` changes — the plan explicitly keeps this pre-commit-only, not part of
  `tox -e lint`.

## Assumptions

- Current relevant excerpt of `.pre-commit-config.yaml` (lines 30-41):
  ```yaml
        - id: no-compat-stubs
          name: Check for compatibility stubs and shims
          entry: python -m tools.check_no_compat
          language: system
          pass_filenames: false
          types_or: [python, markdown]
        - id: tool-descriptions-sync
          name: Check tools/TOOL_DESCRIPTIONS.md sync
          entry: python -m tools.check_tool_descriptions_sync
          language: system
          pass_filenames: false
          files: ^tools/(.*\.py|TOOL_DESCRIPTIONS\.md)$
  ```
- The new hook only needs to scan Python files (`types: [python]`), since `# noqa`/
  `# type: ignore`/`# nosec` are Python-specific comment conventions — narrower than
  `no-compat-stubs`'s `types_or: [python, markdown]`, per the plan's explicit spec:
  "following the `no-compat-stubs` entry's exact shape (`language: system`,
  `pass_filenames: false`, `types: [python]`)."
- `pass_filenames: false` is required because the underlying tool scans `scripts/` and
  `tests/` internally (matching `check_no_compat.py`'s own default-directory-scan
  behavior when invoked with no file args), not per-changed-file.

## Design decisions

- Reuse the `no-compat-stubs` hook's exact field set (`language: system`,
  `pass_filenames: false`) rather than introducing a new hook style — minimizes review
  friction and keeps `.pre-commit-config.yaml` internally consistent (per plan
  Implementation Steps Phase 3, bullet 3, and plan's Risk Metrics note on
  `.pre-commit-config.yaml`: "new hook must follow the exact existing `local` hook shape
  to minimize review friction").
- Restrict `types` to `[python]` only (not `types_or: [python, markdown]` like
  `no-compat-stubs`) since suppression comments are a Python-syntax concept, not a
  Markdown one.

## Alternatives considered

- Use a `repo:`-hosted hook (e.g. a hypothetical external pre-commit hook repo) instead
  of `local` — rejected: no such external tool exists for this repo-specific convention;
  `local` + `language: system` matches the existing precedent and requires no new
  hook-repo dependency.
- Scope the hook with `files:` (like `tool-descriptions-sync`'s
  `files: ^tools/(.*\.py|TOOL_DESCRIPTIONS\.md)$`) instead of `types: [python]` — not
  chosen because the plan explicitly specifies `types: [python]` for this hook,
  mirroring `no-compat-stubs` rather than `tool-descriptions-sync`.

## Implementation

### Target file
`.pre-commit-config.yaml`

### Procedure
1. Locate the `repos: - repo: local hooks:` list containing `no-compat-stubs` and
   `tool-descriptions-sync` (lines ~30-41 per current content).
2. Append a new hook entry after the existing ones (or in a position consistent with any
   existing grouping convention, confirmed by reading the full file at implementation
   time):
   ```yaml
         - id: check-suppression-justification
           name: Check noqa/type:ignore/nosec suppression justifications
           entry: python -m tools.check_suppression_justification
           language: system
           pass_filenames: false
           types: [python]
   ```
3. Do not implement yet — this is a document-only phase; actual file edit happens at
   `prompts/03_implementation.md` time, once
   `tools/check_suppression_justification.py` exists.

### Method
Direct YAML edit, appending one `local` hook entry — no new pre-commit hook repo
dependency, no changes to `default_language_version` or other global config.

### Details
- Per plan Implementation Steps Phase 3, bullet 3 (verbatim intent): "Wire the new check
  into `.pre-commit-config.yaml` as a `local` hook, following the `no-compat-stubs`
  entry's exact shape (`language: system`, `pass_filenames: false`, `types: [python]`)."
- Per plan Implementation Steps Phase 3, bullet 4 (validation step tied to this file):
  "Run `uv run pre-commit run check-suppression-justification --all-files` to confirm it
  passes against the current (allowlisted) baseline before enabling it for all future
  commits." — this must be run only after both this file's edit AND the
  `tools/check_suppression_justification.py` module exist; sequencing dependency noted
  here for the implementation phase.
- Hook id chosen (`check-suppression-justification`) to read naturally in
  `pre-commit run <id>` invocations and in CI output, consistent with the plan's own
  reference to that exact id in its Validation Plan table.

## Compatibility considerations

- Additive hook entry; does not alter `no-compat-stubs` or `tool-descriptions-sync`
  behavior. Existing `pre-commit run --all-files` invocations will now also run this new
  hook — expected to pass against the allowlisted baseline once
  `tools/check_suppression_justification.py` is implemented with its baseline allowlist
  populated (dependency on that procedure's completion first).

## Security considerations

N/A — CI/tooling configuration only, no runtime security surface.

## Rollback considerations

- Revert is deleting the appended hook block; no other hook entry depends on it.

## Validation plan

- `uv run pre-commit run check-suppression-justification --all-files` — passes against
  the allowlisted baseline (per plan Validation Plan table row for this hook).
- `uv run pre-commit run --all-files` — full gate passes, including the new hook (per
  plan Validation Plan table, "Final gate" row).
- Manually introduce an unjustified suppression in a scratch/test file and re-run the
  hook to confirm it actually fails on new violations (per plan Validation Plan table:
  "fails when a new unjustified suppression is introduced in a scratch test file").

## Out of scope

- `tools/check_suppression_justification.py` implementation — separate procedure.
- `tests/tools/test_check_suppression_justification.py` — separate procedure.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260806-133908_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-135850
- Related target files: .pre-commit-config.yaml
