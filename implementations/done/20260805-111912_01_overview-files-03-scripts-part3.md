# Implementation Procedure: 01_overview-files-03-scripts-part3.md

## Goal

Add "変更時の注意点" (cautions when changing) coverage to
`docs/01_overview-files-03-scripts-part3.md` for two identified coupled-change risks
that are not currently documented anywhere in this file:
- `workflow/`: `idempotency_ops.py` and `attempt_ops.py` coupling around `attempts`
  table INSERTs.
- `services/`: `config_dataclasses.py` coupling with `config_builders.py` and
  `services/config_validators.py` for `AgentConfig` field changes.

## Scope

- In scope: adding cautions content to `docs/01_overview-files-03-scripts-part3.md` for
  the `workflow/` and `services/` directories described in the plan.
- Out of scope: modifying source code; modifying the file-structure code fence's
  existing file listing/comments; modifying any other part-N doc.

## Assumptions

- Changes to the `attempts` table schema or creation logic must be synchronized between
  `idempotency_ops.py` and `attempt_ops.py` (plan assumption, not re-verified by reading
  file internals in this document-only phase).
- Configuration changes involving `AgentConfig` fields often require simultaneous
  updates across `config_dataclasses.py`, `config_builders.py`, and
  `services/config_validators.py` (plan assumption).
- Both directories (`services/` and `workflow/`) are documented within a single
  continuous fenced code block (lines 26-64 of the current file) that lists the
  deployed directory tree — see Design decisions below for how this affects placement.

## Design decisions

- **Consolidate into one "### 変更時の注意点" section**, placed after the closing code
  fence (after current line 64), containing both bullets (services/ coupling first,
  then workflow/ coupling, matching top-to-bottom tree order: `services/` appears before
  `workflow/` in the tree). Rationale: the plan's phrasing ("locate the X tree, add a
  section below it") cannot be applied literally to each directory in isolation, because
  both directories share one fenced code block — inserting a Markdown heading between
  `services/` and `workflow/` would split that fence and break rendering. This matches
  the established precedent in `docs/01_overview-files-03-scripts-part1.md`, where one
  "変更時の注意点" section follows two preceding tables (エージェント REPL パッケージ table
  and メモリサブパッケージ table) rather than one section per table.
- Keep bullet wording terse and consistent with part1's existing cautions style (one
  sentence per bullet, filenames backtick-quoted, ending with a short reason clause).

## Alternatives considered

- Splitting the single code fence into two fences (one for `services/`, one for
  `workflow/`) with a "### 変更時の注意点" subsection after each — rejected: this would be
  a structural rewrite of the existing tree listing beyond the plan's stated scope
  ("Out of scope: unrelated refactoring... broad formatting-only rewrites" per the
  plan-to-implementation-procedure workflow), and diverges from the one-consolidated-
  section precedent already used in part1.
- Adding two separate "### 変更時の注意点" headings back-to-back after the fence (one
  labeled for `services/`, one for `workflow/`) — considered acceptable as a minor
  variant; either this or the single consolidated section satisfies the plan intent.
  Left as an implementer's choice at Method/Details level; default to the single
  consolidated section for consistency with part1.

## Implementation

### Target file

`docs/01_overview-files-03-scripts-part3.md`

### Procedure

1. Open `docs/01_overview-files-03-scripts-part3.md`.
2. Locate the end of the file-structure code fence (closing ``` ``` at current line 64).
3. Immediately after the fence and before the `## Related Documents` section (current
   line 66), insert a new `### 変更時の注意点` heading.
4. Add bullet 1 (services/ coupling): coupling between `config_dataclasses.py`,
   `config_builders.py`, and `services/config_validators.py` — changes to `AgentConfig`
   fields require synchronized updates across all three.
5. Add bullet 2 (workflow/ coupling): coupling between `idempotency_ops.py` and
   `attempt_ops.py` — both touch `attempts` table INSERTs and must stay in sync on
   schema/creation-logic changes.
6. Do not alter the existing tree listing (lines 26-64) or the `## Related Documents` /
   `## Keywords` sections.

### Method

Direct manual Markdown edit (one new section, two bullets). No script or automation
required.

### Details

- Confirmed via grep that `docs/01_overview-files-03-scripts-part3.md` currently has no
  "変更時の注意点" section (only `## Related Documents` and `## Keywords` follow the file
  tree).
- The `services/` subtree is listed at lines 27-45 (includes `config_validators.py` at
  line 43 — note: filename in the tree is `config_validators.py`, referenced elsewhere as
  `services/config_validators.py`; use the plan's fully-qualified form
  `services/config_validators.py` in the new bullet to disambiguate from any
  identically-named file in another package).
- The `workflow/` subtree is listed at lines 52-63, including `attempt_ops.py` (line 59)
  and `idempotency_ops.py` (line 60).
- `config_dataclasses.py` and `config_builders.py` are not part of this file's tree
  listing (they live under `scripts/agent/` directly, documented in part1/part2) — the
  new bullet references them by name only, consistent with how part1's existing caution
  bullets reference files outside the immediately-preceding table (e.g. part1 line 69
  references `repository_gateway.py`, which is also not in the same table it follows
  immediately).

## Compatibility considerations

- N/A — documentation-only change.

## Security considerations

- N/A — no security-sensitive content.

## Rollback considerations

- Trivial revert: `git checkout -- docs/01_overview-files-03-scripts-part3.md` or revert
  the single commit adding the section. No downstream artifacts depend on this doc's
  exact section layout.

## Validation plan

- Manual review (covers plan Phase 3 "Verification"): confirm the new section matches
  the Markdown style used in part1's "変更時の注意点" section (heading level, bullet
  format).
- Confirm no boilerplate/speculative cautions were added beyond the two specifically
  identified couplings (per plan's stated risk/mitigation).
- Confirm the code fence was not broken (fence still opens/closes correctly, tree
  content unchanged).

## Out of scope

- Any change to source code under `scripts/agent/services/` or `scripts/agent/workflow/`.
- Any change to `docs/01_overview-files-03-scripts-part1.md` (handled by a separate
  procedure document), `part2.md`, `part4.md`, `part5.md`.
- Splitting or reformatting the existing file-structure code fence.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260803-141200_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-111912
- Related target files: 01_overview-files-03-scripts-part3.md
