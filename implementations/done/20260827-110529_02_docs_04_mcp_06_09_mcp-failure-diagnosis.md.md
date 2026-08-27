## Goal

Add the missing subprocess-vs-persistent recovery-expectation contrast to
`docs/04_mcp_06_09_mcp-failure-diagnosis.md`'s "`ensure_ready` behavior during tool
dispatch" section (REQ-002), per `plans/20260826-114325_plan.md`.

## Scope

- In scope: the "`ensure_ready` behavior during tool dispatch" section (lines
  51-74) of this one document.
- Out of scope: any other section of this document; any code change.

## Assumptions

- `_ServerLifecycleRouter.ensure_ready()` (`scripts/agent/factory.py`, verified
  2026-08-27 around lines 128-142) returns immediately (no-op) whenever
  `cfg.transport != TransportType.HTTP or cfg.startup_mode !=
  StartupMode.SUBPROCESS` — i.e., for any persistent-mode server, this is the entire
  recovery attempt: none.
- No other code path in `scripts/agent/` attempts to restart a persistent-mode
  server (confirmed by this Plan's own Design section verification, not
  independently re-searched by this procedure beyond the `ensure_ready()` read
  above).

## Design decisions

- State the contrast as a direct addition to the existing section rather than a new
  subsection — the section already describes subprocess-mode's reactive recovery in
  detail (lines 51-70); the persistent-mode contrast is a short, adjacent addition,
  not a topic requiring its own heading.
- Name the concrete code condition (`cfg.transport != TransportType.HTTP or
  cfg.startup_mode != StartupMode.SUBPROCESS` → no-op) so the claim is evidence-
  labeled, per this repository's convention, not just asserted in prose.

## Alternatives considered

- Adding a new top-level "Recovery Expectations by Startup Mode" section was
  considered and rejected — REQ-002 targets the existing `ensure_ready` section
  specifically, and the content fits there without duplicating the surrounding
  subprocess-mode explanation.

## Implementation
### Target file
`docs/04_mcp_06_09_mcp-failure-diagnosis.md`

### Procedure
1. Locate the "`ensure_ready` behavior during tool dispatch" section (verified at
   lines 51-74 as of 2026-08-27).
2. Add a short paragraph or bullet stating persistent-mode servers get zero
   automatic recovery, contrasted with subprocess-mode's reactive recovery already
   described in this section.
3. Run `uv run python tools/check_docs_quality.py` and
   `uv run python tools/check_docs_structure.py
   docs/04_mcp_06_09_mcp-failure-diagnosis.md`.

### Method
Direct text addition (Edit tool) — one new paragraph/bullet within the existing
section; no restructuring.

### Details
Current section content (verified 2026-08-27): describes `ensure_ready()`'s
subprocess-mode reactive recovery (lines 56-68, including the code excerpt comment
"In agent/factory.py `_ServerLifecycleRouter.ensure_ready()`:" at line 56, and the
watchdog-removal cross-reference at line 68), an "Implementation Note" (line 70), and
"Appropriate cases for restart" (line 74). Insert a new paragraph after line 68's
watchdog-removal sentence (or as a new bullet immediately following it) stating:
persistent-mode (non-HTTP-subprocess) MCP servers receive **no** automatic recovery
of any kind — `ensure_ready()` returns immediately for them
(`cfg.transport != TransportType.HTTP or cfg.startup_mode != StartupMode.SUBPROCESS`)
— so recovery for a crashed persistent-mode server depends entirely on external
process supervision (see
`04_mcp_06_16_pre-production-fail-open-checklist.md`'s restart-policy requirement).
This explicitly contrasts with subprocess-mode's reactive-on-next-dispatch recovery
already described above in the same section.

## Compatibility considerations

- Documentation-only; no runtime behavior, code path, or public interface is
  affected.

## Security considerations

- N/A: informational addition; does not change or claim to change any enforced
  behavior.

## Rollback considerations

- Single-paragraph addition revert via `git diff`/`git checkout -- <path>`; no other
  document or code depends on this addition (the checklist doc it cross-references,
  REQ-003, is a separate target file in this same pass — verify that file's final
  section heading/anchor before finalizing this cross-reference wording).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_06_09_mcp-failure-diagnosis.md` | Doc quality check | `uv run python tools/check_docs_quality.py` | Passes |
| `docs/04_mcp_06_09_mcp-failure-diagnosis.md` | Doc structure check | `uv run python tools/check_docs_structure.py docs/04_mcp_06_09_mcp-failure-diagnosis.md` | Passes |

## Completion criteria

- The "`ensure_ready` behavior during tool dispatch" section explicitly states that
  persistent-mode servers receive no automatic recovery of any kind, distinct from
  subprocess-mode's reactive recovery already described.

## Out of scope

- Any other section of this document.
- Any code change.
- `docs/04_mcp_06_16_pre-production-fail-open-checklist.md` itself (separate target
  file, REQ-003, in this same pass).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add subprocess-vs-persistent contrast paragraph to the `ensure_ready` section | Completed | — | — | Added persistent-mode zero-recovery statement contrasting with subprocess-mode reactive recovery |
| 2 | Run `check_docs_quality.py` and `check_docs_structure.py` | Completed | — | — | Pre-existing issues only (missing front matter, broken link); no new findings from this edit |

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
- **Requirement ID**: REQ-002
- **Source issue**: `issues/20260821_04_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-114325_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-110529
- **Related target files**: `docs/04_mcp_06_09_mcp-failure-diagnosis.md`
