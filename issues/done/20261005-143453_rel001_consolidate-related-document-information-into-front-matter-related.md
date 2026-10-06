# Consolidate related-document information into front matter related

## Priority
Medium

## Summary
Make the front matter `related:` field the single list of related documents for all non-ADR documents, remove the leftover body `Related Documents` block, state the rule in the governance documents, strengthen the structure checks so that a reintroduced body `Related Documents` section is detected at any heading level, and make the check enforced in CI over the whole `docs/` tree. Contextual links in prose and purpose-specific navigation sections (for example `Reading Order` and `Related ADRs`) stay. The ADR documents are handled by the follow-up issue `rel002` (see Dependencies); this issue keeps the existing ADR exception unchanged.

## Background
The source of this issue is the work instruction in `memo2.md` (repository root). Current state, confirmed by repository inspection (Evidence label: Confirmed by repository evidence):
- All documents under `docs/` (192 Markdown files) carry a front matter `related:` field; three EventBus documents use `related: []`. All 870 `related:` entries across the documents are plain basenames ending in `.md`; none uses a path or an anchor.
- Only documents under `docs/10_adr/` (20 files, including `adr-index.md` and `adr_00_document-guide.md`) carry a body `## Related Documents` section. No non-ADR document has a `## Related Documents` heading, and no non-ADR document has a `Related Docs`, `Related Chapters` or `See Also` heading.
- One non-ADR document has a leftover `### Related Documents` block in the middle of its body: `docs/22_mcp/mcp_06_13_health-reasons-and-error-kinds.md`. Its two entries are identical to the front matter `related:` list, so no link is lost by removing it. The block is followed by a stray `### Keywords` block.
- The current rule is already "front matter `related:` is the single authoritative store; general documents carry no body Related section; ADR documents keep a classified `## Related Documents` block" (`docs/00_governance/governance_02_documentation-metadata.md`, `governance_04_documentation-checks.md` section 8).
- `tools/check_docs_structure.py` rejects `## Related Documents`, `## Related Docs` and `## Related Chapters` in non-ADR documents, but its pattern matches only `## ` headings (fenced code excluded), which is why the `### Related Documents` block above was not detected. It also checks related targets, self-references and duplicates (`check_related_links`).
- CI and local runs differ today: `.github/workflows/governance-docs-consistency.yml` runs the structure check with `continue-on-error: true`, only over `docs/*.md docs/10_adr/*.md` (so subdirectories such as `docs/21_rag` are not covered), with `--schema`. A local run without arguments scans `docs/**/*.md`. `.pre-commit-config.yaml` runs `check_docs_quality.py` and the ADR checks, not `check_docs_structure.py`.
- Rule and tooling touchpoints that mention the body section: `tools/check_docs_structure.py`, `tools/manage_frontmatter.py` (the `merge-related` subcommand merges the body block into `related:`), `tools/check_docs_quality.py` (allowed-heading set), `tools/TOOL_DESCRIPTIONS.md`, `routing.md` (Tools table), `prompts/08_document-sync.md`, governance_02 (the `related` field description) and governance_04 (structure-check description, GV-005 row). No other template, document generation script, README or AI-facing authoring guidance carries the old rule: `templates/` holds only work-item templates and no document generator exists.

## Adversarial Verification
Verified against the current repository state (2026-10-05). Every factual claim below holds:
- `docs/` contains 192 Markdown files; 870 `related:` entries exist, all plain basenames ending in `.md`; none uses a path or anchor.
- Three EventBus documents use `related: []`: `docs/24_eventbus/eventbus_12_health_endpoint.md`, `eventbus_13_replay_endpoint.md`, `eventbus_15_ack_nack_endpoints.md`.
- All 20 files under `docs/10_adr/` carry a `## Related Documents` section; no non-ADR document carries a `## Related Documents`, `## Related Docs`, `## Related Chapters` or `See Also` heading.
- The only non-ADR body Related-style heading is `### Related Documents` at line 68 of `docs/22_mcp/mcp_06_13_health-reasons-and-error-kinds.md`; its two entries equal the front matter `related:` list.
- The adjacent `### Keywords` block (lines 73-76) duplicates the real `## Keywords` section (lines 165-168) verbatim — removing it loses nothing. Resolves the Unresolved Question there.
- `tools/check_docs_structure.py` `_RELATED_HEADING_RE` matches only `^## ` headings, so the `### ` block is not detected; running the tool on the file reports "All checks passed".
- `.github/workflows/governance-docs-consistency.yml` runs the structure check with `continue-on-error: true` over `docs/*.md docs/10_adr/*.md --schema ...`; `.pre-commit-config.yaml` runs `check_docs_quality.py` and the ADR checks but not `check_docs_structure.py`.
- governance_02 states the single-store rule; governance_04 GV-005 row is currently `Warning` (not blocking); `merge-related`, `check_docs_quality.py` allowed-heading set, `TOOL_DESCRIPTIONS.md`, `routing.md`, `prompts/08_document-sync.md` all carry the rule text.

## Problem
A body `Related Documents` block can still appear in a non-ADR document without being detected (one such block exists), because the check matches only second-level headings. The structure check that would catch it is not blocking in CI and does not cover the subdirectories of `docs/`, so local and CI results differ. The `related:` format (basename list) is also not stated as a validated rule even though every existing entry follows it.

## Reason for Change
Make the single-store rule for related-document information explicit and enforceable: remove the remaining duplicate block, detect reintroduction at any heading level, and run the check where it can actually block a change, while keeping every still-needed link.

## Implementation Intent
Treat the work as one coordinated change so that the rule, the tools, the tests and the documents are never left inconsistent. Proceed in this order:
- Survey: for every Markdown file in `docs/`, record whether `related:` exists, whether a body Related-style block exists, whether the two agree, which body-only links exist, whether link targets exist, and self-references and duplicates. Reuse the existing `tools/` checks and `tools/manage_frontmatter.py` rather than writing a new script. The survey above is the starting point and must be re-run before changes.
- Link triage: a link that exists only in a body block is checked before removal. Still-needed links move to `related:`; obsolete or invalid links are deleted; links whose necessity cannot be judged are registered as Needs Confirmation (see `docs/00_governance/governance_03_issue-and-uncertainty-management.md`), not guessed. Ordinary contextual links in prose are not moved or deleted.
- Update the rule statement and tool descriptions first, then the tools and tests, then migrate the one document, so each step leaves the repository passing its own checks.
- Strengthen, do not weaken, the checks: keep the required `related` check, validate the format (a list of basenames ending in `.md`), target existence, self-reference and duplicates, and detect a body `Related Documents` heading at any heading level, ignoring fenced code, in non-ADR documents.
- Make the structure check blocking in CI over `docs/**/*.md` so local and CI runs agree; if the schema variant must stay non-blocking, add a separate blocking step for the structural checks.

## Target Files or Areas
- docs/00_governance/governance_02_documentation-metadata.md
- docs/00_governance/governance_04_documentation-checks.md
- tools/check_docs_structure.py
- tools/manage_frontmatter.py (the `merge-related` subcommand)
- tools/check_docs_quality.py
- tools/TOOL_DESCRIPTIONS.md
- routing.md
- prompts/08_document-sync.md
- tests/tools/test_check_docs_structure.py, tests/tools/test_manage_frontmatter.py
- docs/22_mcp/mcp_06_13_health-reasons-and-error-kinds.md (migration)
- .github/workflows/governance-docs-consistency.yml (and `.pre-commit-config.yaml` only if the owner wants a local gate)

## Required Changes
- Run the survey and record: files changed, files migrated, links added to `related:`, invalid links removed, Needs Confirmation items registered.
- Update governance_02 and governance_04: `related:` is the single related-document list for non-ADR documents; a body `Related Documents` section is not used there; contextual links and purpose-specific navigation sections are allowed; the ADR exception is stated as remaining until `rel002`.
- Update `tools/check_docs_structure.py`: detect a body `Related Documents` (and `Related Docs` / `Related Chapters`) heading at any level in non-ADR documents, ignoring fenced code; validate the `related` format as a list of basenames ending in `.md`; keep target existence, self-reference and duplicate checks; update error messages and the module docstring. Leave the ADR requirement unchanged.
- Update `tools/manage_frontmatter.py` (`merge-related` becomes a documented one-time migration aid or is retired), `tools/check_docs_quality.py`, `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `prompts/08_document-sync.md` so they match the new rule text.
- Update the tests: a reintroduced body block at `##` and `###` levels is reported, a heading inside a fenced code block is ignored, `related: []` is accepted, an invalid `related` format, a missing target, a self-reference and a duplicate are reported.
- Migrate `docs/22_mcp/mcp_06_13_health-reasons-and-error-kinds.md`: remove the body `### Related Documents` block, and the adjacent stray `### Keywords` block only if it duplicates the real Keywords section (otherwise report it). Tidy headings, blank lines and file endings; confirm contextual links remain.
- Update the CI workflow so the structure check runs over `docs/**/*.md`, is blocking, and gives the same result as the local run.

## Constraints
- Do not remove a body-only link without checking its necessity first, and do not move body links into `related:` unconditionally.
- Do not delete ordinary contextual links, `Reading Order` sections or `Related ADRs` sections.
- Do not change the ADR documents or the ADR rules here (see `rel002`); the ADR requirement for `## Related Documents` stays in `tools/check_docs_structure.py` until `rel002`.
- Do not weaken a check to make the migration pass; keep rule text, tools and tests consistent at every commit.
- Keep `related:` a required field; `related: []` stays valid (three existing documents use it).
- Documentation text stays English (`skills/DESIGN.md` Output language).

## Acceptance Criteria
- governance_02 and governance_04 state that `related:` is the only related-document list for non-ADR documents and that a body `Related Documents` section is not used there; the remaining ADR exception and its follow-up are stated.
- No non-ADR document contains a body `Related Documents`, `Related Docs` or `Related Chapters` heading at any level, and the survey and the list of links added to `related:` show that no still-needed link was lost.
- No `related:` entry points to a missing file or to the document itself, appears twice, or uses a path, an anchor or a non-`.md` form.
- `tools/check_docs_structure.py` reports a reintroduced body block at any heading level in a non-ADR document, validates the `related` format, and its tests cover the cases listed under Required Changes.
- `tools/manage_frontmatter.py`, `tools/check_docs_quality.py`, `tools/TOOL_DESCRIPTIONS.md`, `routing.md` and `prompts/08_document-sync.md` contain no stale statement of the rule.
- The CI structure check runs over `docs/**/*.md`, is blocking, and its result matches the local run.
- Links that could not be judged are registered as Needs Confirmation and `uv run python tools/check_needs_confirmation_inventory.py` passes.

## Testing Expectations
- Unit tests for `tools/check_docs_structure.py` and `tools/manage_frontmatter.py` covering the cases above; run `uv run pytest tests/tools`, then ruff, mypy and bandit for the changed tool files per `routing.md` ("Adding a new tool" validation sequence).
- Run: `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_needs_confirmation_inventory.py`, `uv run python tools/check_tool_descriptions_sync.py`, and the domain consistency checks for the touched areas.
- Run the CI command exactly as written in the workflow locally and compare with the default local run; the results must agree.
- Compare the survey output before and after to show that no link was lost.

## Documentation Impact
Yes. The governance rule text (the `related:` single-store rule, allowed contextual and navigation links, the remaining ADR exception) and the tool descriptions change, and one MCP document is migrated. Follow the documentation workflow in `routing.md` (Documentation row) and run the documentation checkers listed under Testing Expectations.

## Out of Scope
- The ADR documents and the ADR rules, including the ADR standard header list, `tools/check_adr_structure.py` and `tools/check_known_deviation_sync.py` (handled by `rel002`).
- Changing contextual links inside ordinary prose, or removing `Reading Order`, `Related ADRs` or other purpose-specific navigation sections.
- Reorganizing or renaming documents, or changing front matter fields other than `related:`.

## Dependencies
- This issue is independent and should land first. The follow-up issue `rel002` (remove the ADR `## Related Documents` block and update the ADR rules and tools together) depends on this issue's strengthened detection and CI step; it is filed as a separate issue.

## Unresolved Questions
- Should the blocking CI structure step also run the `--schema` variant, or should the schema variant stay non-blocking (`continue-on-error`) while a separate blocking step runs the structural checks? Decide when changing the workflow.
- Should a local gate be added to `.pre-commit-config.yaml` (it currently runs `check_docs_quality.py` and the ADR checks but not `check_docs_structure.py`), or is CI enough?
- The stray `### Keywords` block next to the `Related Documents` block in `docs/22_mcp/mcp_06_13_health-reasons-and-error-kinds.md`: is it a duplicate of the real Keywords section? The survey must confirm before removal.

## AI Implementation Instruction
Follow `memo2.md`, limited to the non-ADR scope defined here. Start with the survey; keep each commit self-consistent (rule text, tools and tests first, then the document migration, then CI). Never remove a body-only link without checking it, never weaken a check to pass the migration, and register anything you cannot judge as Needs Confirmation. Do not touch the ADR documents or ADR rules; leave those to `rel002`. Do not change unrelated documents or links.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261005-143453
- **Related target files**: docs/00_governance/governance_02_documentation-metadata.md, docs/00_governance/governance_04_documentation-checks.md, tools/check_docs_structure.py, tools/manage_frontmatter.py, tools/check_docs_quality.py, tools/TOOL_DESCRIPTIONS.md, routing.md, prompts/08_document-sync.md, tests/tools/test_check_docs_structure.py, tests/tools/test_manage_frontmatter.py, docs/22_mcp/mcp_06_13_health-reasons-and-error-kinds.md, .github/workflows/governance-docs-consistency.yml
