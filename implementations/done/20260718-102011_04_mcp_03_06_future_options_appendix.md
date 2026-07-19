## Goal

Implementation steps 1-2 of `plans/20260717-181151_plan.md` (requirement 20): capture the
"Future / deferred design options" subsection content (two evaluated-but-unimplemented
proposals — an `include_disabled=false` query parameter for `/v1/tools`, and a structured
`disabled_code` enum alongside `disabled_reason`) as a ready-to-append Markdown fragment, and
define the conditional procedure for landing it inside
`docs/04_mcp_03_06_tool-runtime-availability-metadata.md` once that file exists. This is
documentation/evaluation only — no source code, tests, or runtime behavior change. Today's
default `/v1/tools` behavior (always return every tool, including disabled ones) must be
explicitly preserved as the baseline assumption.

Note on a prior filename match: `implementations/20260718-101441_04_mcp_03_06_tool-runtime-availability-metadata.md`
also targets `04_mcp_03_06_tool-runtime-availability-metadata.md`, but its Goal is Implementation
step 3 of `plans/20260717-180307_plan.md` (requirement 19) — creating the base file itself
(the `config_dependent`/`enabled`/`disabled_reason` contract spec). That is a different
deliverable from this plan's "Future options" appendix content. This is a **false-positive
filename match**, not an already-implemented duplicate of this plan's step; it is flagged here
rather than silently skipped, per the batch's disambiguation requirement. This new doc uses a
distinct `future_options_appendix` slug specifically to avoid being conflated with that base-file
creation doc in any future filename search.

## Scope

**In scope**:
- The two-option "Future / deferred design options" Markdown subsection text (verbatim, ready to
  paste), matching the Design section of `plans/20260717-181151_plan.md`.
- The conditional procedure: re-check whether `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`
  exists before attempting to append; branch accordingly.
- Confirming the doc-consistency test only needs to run on the branch where an actual edit to an
  existing file happens.

**Out of scope**:
- Creating `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` from scratch — that remains
  requirement 19's deliverable (`plans/20260717-180307_plan.md`,
  `implementations/20260718-101441_04_mcp_03_06_tool-runtime-availability-metadata.md`).
- Any change to `scripts/mcp_servers/**`, `scripts/shared/**`, `scripts/agent/**`, or any test
  file — no FastAPI query parameter, Pydantic field, or dispatch-table change is designed here.
- Registering a new File Index entry in `docs/04_mcp_00_document-guide.md` — this is additive
  content for a file that requirement 19 already plans to register; no new file is introduced by
  this plan.

## Assumptions

1. As of this writing, `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` does not exist
   (verified: `find docs -iname "04_mcp_03_06*"` returns nothing). Verified independently in this
   procedure-doc-writing pass, matching the plan's own Assumption 3.
2. Requirement 19's plan (`plans/20260717-180307_plan.md`) has an implementation procedure doc
   already written (`implementations/20260718-101441_...md`) but the actual base file has not yet
   been created in `docs/` — so this appendix content has no file to attach to yet. This is a
   pre-existing, acknowledged risk in the source plan (see its Risks section), not something this
   procedure doc can resolve.
3. `scripts/` still has zero occurrences of `config_dependent`, `disabled_reason`, or
   `RuntimeToolRegistry` (per the source plan's Assumption 2) — the entire runtime-availability
   contract, including this appendix's proposals, remains unimplemented target design.
4. No `issues/*_unknowns.md` file is needed (the source plan already resolved both its Unknowns
   through analysis, without leaving a blocking unknown).

## Implementation

### Target file

`docs/04_mcp_03_06_tool-runtime-availability-metadata.md` (does not exist yet; conditional edit).

### Procedure

1. Run `find docs -iname "04_mcp_03_06*"` immediately before attempting any edit.
2. **Branch A — file still does not exist** (expected, per Assumption 1): do not create the file.
   The deliverable of this step is the appendix content below, held as a self-contained fragment
   (already fully specified in this doc and in `plans/20260717-181151_plan.md`'s Design section).
   No file write happens in this branch. Record this branch's outcome in the plan's Risks section
   (already done in the source plan — "Base file dependency on requirement 19").
3. **Branch B — file has since been created** (requirement 19 implemented in the meantime): open
   `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`, locate the "Implementation status"
   callout (per that file's planned Design item 7 in `plans/20260717-180307_plan.md`), and insert
   the "Future / deferred design options" subsection (verbatim text below) immediately after it,
   as a new `##`-level section preceding any closing "Related Documents"/"Keywords" boilerplate
   the doc-guide convention appends at file end (matching the pattern of every other
   `04_mcp_*.md` file, e.g. `docs/04_mcp_90_inconsistencies_and_known_issues.md`'s own
   "Related Documents" / "Keywords" tail observed in this batch).
4. In Branch B only: run `uv run pytest tests/test_check_mcp_docs_consistency.py -v` after the
   edit to confirm the doc-consistency checks (`check_routing_authority_v1tools`,
   `check_active_inconsistencies`, etc., per `tests/test_check_mcp_docs_consistency.py:11-23`)
   still pass. No new File Index registration is expected (no new file was added), so no change
   to `docs/04_mcp_00_document-guide.md` is required by this step.

### Method

Manual Markdown authoring (no scripted generation). No production code, no pytest fixtures
beyond the existing consistency test re-run in Branch B.

### Details

Verbatim subsection content to append (Branch B) or hold in reserve (Branch A):

```
## Future / deferred design options

Evaluated per requirement 20 (`requires/done/20260717_20_require.md` once filed) and
`plans/20260717-181151_plan.md`. Neither option below is implemented; both are deferred design
decisions with no dependency from the initial RuntimeToolRegistry migration (requirements 14-19).

### 1. `include_disabled` query parameter

Proposed: `GET /v1/tools?include_disabled=false` as an opt-in filter on tool discovery.

- Default (no query param, or `include_disabled=true`) preserves today's behavior: every tool is
  returned, including disabled ones, each carrying `enabled=false` / `disabled_reason` set.
- Only when a caller explicitly passes `include_disabled=false` are disabled tools omitted from
  the `tools` array in the response.
- Status: unimplemented, no immediate action required.

### 2. `disabled_code` structured field

Proposed: a machine-readable enum companion to the free-text `disabled_reason`, coexisting with
it (never replacing it, never present alone without `disabled_reason`).

Candidate values, mapped to today's `requires_config`-gated servers:

| `disabled_code`             | Server(s)                              |
|------------------------------|-----------------------------------------|
| `EMPTY_ALLOWED_DIRS`         | file read / write / delete              |
| `EMPTY_ALLOWED_REPO_PATHS`   | git (precedence over `READ_ONLY`)       |
| `READ_ONLY`                  | git write tools                         |
| `EMPTY_COMMAND_ALLOWLIST`    | shell (reserved; scoped out of req. 15) |
| `EMPTY_WORKFLOW_ALLOWLIST`   | cicd (reserved; scoped out of req. 15)  |

- `disabled_reason` remains for humans/logs; `disabled_code` is for programmatic dispatch.
- Status: unimplemented, no immediate action required.

Neither option is implemented. Both are deferred design decisions tracked for future evaluation;
the initial RuntimeToolRegistry migration (requirements 14-19) does not depend on either.
```

(This block is pseudocode/prose content for a Markdown doc, not source code — no production
code is introduced by this procedure.)

## Validation plan

- Branch A (file still absent): no automated validation applicable — nothing was written to
  `docs/`. Confirm via `find docs -iname "04_mcp_03_06*"` (expect empty) that Branch A was
  correctly identified before concluding this step.
- Branch B (file exists, edit applied): `uv run pytest tests/test_check_mcp_docs_consistency.py -v`
  must pass. `git diff --stat docs/04_mcp_03_06_tool-runtime-availability-metadata.md` reviewed
  to confirm only the intended subsection was added.
- No ruff/mypy/lint-imports/bandit/full-pytest/diff-cover run — Markdown-only change, `.importlinter`
  and bandit configs do not scan `docs/`.
