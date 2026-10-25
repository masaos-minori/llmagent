# Audit `args_preview` cap implementation procedure (docs)

**Stage:** Implementation Procedure
**Created:** 2026-10-25 00:28 UTC
**Status:** Draft for execution
**Owning Plan:** `plans/done/20261024-221315_args-preview-is-written-to-the-audit-log-unbounded.md` (`Frozen`)
**Owning Requirement:** `REQ-006`
**Issue:** `issues/20261024-124138_tool005-args-preview-is-written-to-the-audit-log-unbounded.md`
**Target file (row 3 of 3):** `docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md`

## Goal

- State the `args_preview` size cap in the chapter that owns agent-side audit events: cap value,
  envelope shape, and the mask-before-bound ordering (REQ-006, `AC-5`).
- Make the cap number discoverable so the Issue's "undocumented behavior is not acceptable" constraint is
  satisfied, and record the agent-side-only boundary so readers do not assume MCP-side records are
  bounded.

## Scope

- One bullet appended to the `## Key Constraints` section (currently `:46-50`), immediately after the
  existing bullet "Calling writing functions for `tool_approval` / `tool_exec` outside of a workflow
  context will result in an assertion error." (`:50`).
- Resolution of the plan's conditional second edit: the chapter contains no audit-log size-control or
  rotation text (`grep -in "audit.log|truncat|preview|rotation|size"` matches only the troubleshooting
  line `:70`), verified 2026-10-25 — so nothing is added elsewhere in this file.

## Assumptions

- Row 1 (`scripts/agent/tool_audit.py`) has landed: the doc names `AUDIT_ARGS_PREVIEW_MAX_CHARS` (new)
  and the envelope as code facts, so the doc edit must follow the code to avoid a stale claim.
- Doc content is English per `skills/DESIGN.md` Output language; front matter and section headings stay
  unchanged (no category/title change, so the docs structure checker sees no new section to validate).
- The exact value 1500 is stated alongside the constant name: if the owner later revises the constant,
  this bullet is the paired doc update point (plan Risks mitigation "the number is discoverable").

## Design decisions

- `DR-101`: Single bullet in `Key Constraints` rather than a new subsection — `Key Constraints` already
  owns the event-format facts (`:48` JSON-lines format, `:50` the two writers), the chapter is
  high-churn (13 commits/30d), and the plan's Risks mitigation prescribes a "single subsection edit".
- `DR-102`: The bullet carries all four contract facts in one entry (cap quantity, envelope shape,
  mask-before-bound ordering, agent-side-only boundary) instead of scattering them across Operational
  Notes — one grep-hit location for the whole contract.
- `DR-103`: `docs/22_mcp/mcp_06_05_reading-audit-logs.md` is left unmodified: its jq/grep examples filter
  on `event`/`tool`, never on `args_preview` sub-keys (plan `Reference Files`, verified 2026-10-24), so
  no cross-reference is required by the docs gates.

## Alternatives considered

- New `### Preview size cap` subsection under `Operational Notes` — **rejected**: duplicates facts already
  owned by `Key Constraints` and enlarges the diff in a high-churn chapter; `DR-101` covers the same
  content with one line each.
- Documenting the cap in `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` — **rejected**:
  that chapter covers retention/rotation only, which is out of scope (plan `Documentation Impact`); the
  Issue's original pointer to `docs/41_db/` or `docs/40_shared/` was corrected by verification to
  `agent_10_02`.

## Implementation

### Target file

`docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md`

Modify (one bullet appended to `Key Constraints`).

### Procedure

1. Confirm row 1 is merged in the deployed working tree (`AUDIT_ARGS_PREVIEW_MAX_CHARS` (new) exists in
   `scripts/agent/tool_audit.py`) so the doc's claims are live facts, not pending ones.
2. Insert the new bullet after the `Key Constraints` bullet ending "...assertion error." (`:50`), before
   the section break preceding `## Operational Notes` (`:52`).
3. Insert exactly the text under Method below (single bullet, two wrapped lines per the file's existing
   line-wrapping style).
4. No other edit in this file; confirm `docs/22_mcp/mcp_06_05_reading-audit-logs.md` stays untouched.
5. Run the docs gates from the plan Validation plan (see below) and the stale detector on this procedure
   doc; the plan's `AC-5` exit condition is "cap is stated in `agent_10_02` and the docs gates report no
   findings".

### Method

New `Key Constraints` bullet, exact final text:

```markdown
- Agent-side `tool_approval` / `tool_exec` events cap `args_preview` at `AUDIT_ARGS_PREVIEW_MAX_CHARS = 1500`
  (chars of serialized preview JSON, `scripts/agent/tool_audit.py`): containers at or below the cap
  are stored unchanged; larger ones are replaced by `{"preview": <serialized prefix>, "truncated": true}`.
  Bounding runs after masking, so a truncated prefix may contain `"***"` values and must be read as
  structurally reduced, not as absent arguments. MCP-side audit records are not bounded by this cap.
```

### Details

- Wording mirrors the frozen contracts: "at or below the cap ... unchanged" matches the row-1 `DR-103`
  pass-through (`<=`), and `"truncated": true` matches the envelope emitted above the cap.
- "Serialized prefix" states the char-count policy (chars of the `_json_dumps` output string) without
  naming the internal serializer, keeping the doc implementation-lean while staying exact.
- The "read as structurally reduced" sentence is the plan Risks mitigation for the security-review
  concern (truncation mistaken for absent arguments) — required by REQ-006's "truncation applies after
  masking".
- The last sentence encodes the documented boundary from plan Risks (shared `audit.log` MCP-side
  records unbounded), so readers of the shared log know which events the cap governs.

## Compatibility considerations

- Chapter title, category, front matter, and all existing bullets are unchanged; only one list item is
  added, so `check_docs_structure.py` sees the same section set.
- `AC-4` integration suites and reader-facing usage examples in `mcp_06_05` consume no `args_preview`
  sub-keys (plan `Reference Files`), so no other doc or test needs a wording follow-up.
- The file is rsynced by `deploy.sh` per plan `Affected areas`; doc sync rides the standard deploy step.

## Security considerations

- The bullet is the doc half of the mask-before-bound security mitigation: it instructs reviewers to
  treat `truncated` rows as structurally reduced rather than argument-free (plan Risks).
- No secrets, paths, or production log excerpts are added to the doc.

## Rollback considerations

- Revert is a one-bullet deletion; no cross-reference in another chapter depends on it (`mcp_06_05`
  untouched, verified 2026-10-25).
- If row 1 is reverted, this bullet must be reverted in the same change — otherwise the doc claims a cap
  that the code no longer enforces (stale-doc failure mode the stale detector would flag).

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Docs gates (plan Validation plan row 5) | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py "docs/**/*.md"`; `uv run python tools/check_docs_content_policy.py` | No findings |
| AC-5 spot check | `grep -n "AUDIT_ARGS_PREVIEW_MAX_CHARS" docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md` | Exactly the new bullet matches |
| Cross-file consistency | `grep -rn "args_preview" docs/` | Only this chapter matches (was empty before this row; the new bullet becomes the single doc-side mention) |
| Stale detector | `uv run python tools/stale_detector.py implementations/20261025-002808_03_docs_23_agent_agent_10_02_operations-and-observability-audit-and-otel.md.md` | Not stale (row 1 landed first) |

## Completion criteria

- REQ-006 / `AC-5`: `agent_10_02` states the cap value, the envelope shape, and the mask-before-bound
  ordering; docs gates report no findings.
- The agent-side-only boundary is stated (plan Risks mitigation satisfied).
- No other doc file changed (`mcp_06_05` explicitly left unmodified).

## Out of Scope

- Retention/rotation text (`docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`) and MCP-side
  record bounding (plan `Scope`).
- Editing `docs/22_mcp/mcp_06_05_reading-audit-logs.md` (verified non-consumer of `args_preview`
  sub-keys).
- Any config-key story: the cap is a module constant, and the doc says so by naming the constant.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm row 1 landed (Phase 3 precondition) | Completed | 20261024-233411 | 20261024-233411 | `AUDIT_ARGS_PREVIEW_MAX_CHARS` + `_bounded_preview` live in `scripts/agent/tool_audit.py` with row-2 tests green |
| 2 | Key Constraints bullet (`DR-101`, `DR-102`) | Completed | 20261024-233411 | 20261024-233411 | Exact Method text inserted after the assertion-error bullet (now `:51`); `mcp_06_05` untouched |
| 3 | Docs gates + AC-5 checks | Completed | 20261024-233411 | 20261024-233411 | `check_docs_quality` / `check_docs_structure` / `check_docs_content_policy` / `check_docs_consistency --domain agent` all exit 0; AC-5 grep matches only the new bullet; `grep -rn "args_preview" docs/` shows this chapter as the single mention; stale detector: not stale |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | N/A |

**Reconcile note (2026-10-25):** the source fixes for this procedure landed on `origin/master` from a separate session (fix commit `73d714609`, archive commit `e6c0d6eef`). A second session independently re-executed and fully validated the same procedure on the pre-reset tree; `origin/master` was then adopted as canonical and the source state re-confirmed there with targeted tests.

## Traceability

- **Owning plan**: `plans/done/20261024-221315_args-preview-is-written-to-the-audit-log-unbounded.md` —
  row 3 of the `Implementation Target Files` table; plan `Implementation steps` Phase 3.
- **Source issue**: `issues/20261024-124138_tool005-args-preview-is-written-to-the-audit-log-unbounded.md`
  (documentation constraint: cap in a constant/config **and** documented).
- **Plan requirements covered**: `REQ-006` (`AC-5`).
- **Local design decisions**: `DR-101`..`DR-103` operationalize the plan `Documentation Impact` entry and
  the plan Risks mitigations (discoverable number; documented agent-side boundary).
- **Cross-row dependencies**: this row runs **after** row 1 (doc must describe landed code) and after
  row 2 (the tests pin the exact wording mirrored by `DR-101` of the row-2 procedure); completion of all
  three rows closes the plan's Execution status step 3.
