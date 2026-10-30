## Goal

Add an operational note to `docs/90_deployment/deployment_01_deployment.md` documenting the `REQ-001` missing-binary pre-flight: an empty or missing `/opt/llm/bin/agent` now fails fast with rebuild/redeploy recovery guidance at agent startup, and `/opt/llm/DEPLOYED_REV` is written only after a successful, binary-gated deploy.

## Scope

Modifies `docs/90_deployment/deployment_01_deployment.md` only: inserts one paragraph into section 2.6 ("Compiled Artifacts (`NUITKA --onefile`)"), immediately after the sentence on line 250 ("A missing config directory or dictionary fails startup with an explicit error naming the path."). No other section, table, or auto-generated block is touched.

## Assumptions

- Section 2.6 currently ends its runtime-failure description at line 250, followed by the "**MCP server launch.**" note at line 252; the new note fits that same bold-label-note style and theme.
- The actual pre-flight check is added to `deploy/start_agent.sh` by the seq 01 procedure; this note only documents the resulting operator-facing behavior.
- The doc is a `Reference`-class guide whose existing notes use the `**Label.** sentence.` pattern (e.g. "MCP server launch.", "Build, freshness, and rollback.").
- Added body text must be English (`check_docs_content_policy.py`).

## Design decisions

- **One paragraph, inline in section 2.6.** The missing-binary pre-flight is a runtime behavior of the compiled-artifact launch described here, so it belongs in section 2.6 rather than a new subsection (which would fragment the section and add a heading the doc's H1/section structure does not expect).
- **Fold-in to preserve the size ceiling.** The target file sits exactly at its `check_docs_structure.py` ceiling (25861 bytes; see Risks). The note is therefore introduced by tightening an equivalent amount of existing prose in section 2.6 (net-zero growth), not by unconditionally appending. See Details.
- **State both `REQ-001` facts.** The note covers (a) the fail-fast with recovery commands and (b) that `/opt/llm/DEPLOYED_REV` reflects only a successful binary-gated deploy, matching the plan's row-3 intent.

## Alternatives considered

- **New subsection 2.6a.** Rejected: adds a heading and structural weight for a single operator note; the doc's sectioning does not call for it.
- **Append after line 252 (after "MCP server launch.").** Rejected: the binary pre-flight is thematically adjacent to the line-250 runtime-failure sentence, not to the MCP `cmd` note.
- **Expand the existing line-250 sentence alone.** Rejected: the binary pre-flight is a distinct concern from the config-directory/dictionary failure it describes; a separate bold-label note keeps each concern scannable.

## Implementation

### Target file

`docs/90_deployment/deployment_01_deployment.md`

### Procedure

1. Open section 2.6 and locate line 250.
2. Insert the note below as a new paragraph directly after the line-250 sentence (before the "**MCP server launch.**" note at line 252).
3. Tighten an equivalent amount of existing section-2.6 prose so the file size does not exceed 25861 bytes (see Details).
4. Run the doc checkers (see Validation plan).

### Method

Insert this paragraph after the sentence on line 250:

```text
**Missing binary pre-flight.** `deploy/start_agent.sh` verifies `/opt/llm/bin/agent` exists and is executable before launch; a missing or non-executable binary aborts startup with an actionable rebuild/redeploy message (`deploy/build_binaries.sh` to rebuild from current source, then `deploy/deploy.sh` to deploy) instead of a bare bash ENOENT. Because the binary gate runs before the revision record is written, `/opt/llm/DEPLOYED_REV` records only a successful, binary-gated deploy.
```

### Details

- **Size ceiling (required handling).** `tools/check_docs_structure.py` caps `deployment_01_deployment.md` at 25861 bytes (`SIZE_EXCEPTIONS`), which equals its current size; any net-positive growth fails the checker (routing.md, "When to run which tool"). To keep it green after adding the ~500-byte note, do **one** of the following:
  - **Preferred — net-zero rewrite.** Tighten ~500 bytes of existing, still-accurate prose in section 2.6 (for example compress verbose sentences in the "Build, freshness, and rollback." paragraph at line 254) while preserving every documented fact. Verify the final size is `<= 25861`.
  - **Alternative — raise the ceiling.** If no prose can be trimmed without losing information, raise the `deployment_01_deployment.md` entry in `tools/check_docs_structure.py`'s `SIZE_EXCEPTIONS` by a dated justification comment (matching the established pattern in that file). This is a deliberate policy change and should be confirmed with the doc owner before landing.
- Do not edit the auto-generated DB Path Reference block (lines 350-359) or the front matter.
- Keep all added text in English.

## Risks

- **Size-ceiling violation.** Adding the note without offsetting prose pushes the file past 25861 bytes and fails `check_docs_structure.py`. The net-zero rewrite (or an owner-approved ceiling raise) is a required step, not optional.
- **Information loss.** Over-compressing section 2.6 to fit the note could drop a documented fact. Preserve every existing fact; only shorten wording.

## Compatibility considerations

N/A: documentation-only change; no runtime, API, or deployment-behavior change.

## Security considerations

N/A: no security-relevant change; the note documents existing fail-fast behavior.

## Rollback considerations

N/A: revert the commit that adds the note.

## Validation plan

- `uv run python tools/check_docs_structure.py docs/90_deployment/deployment_01_deployment.md` — passes (size `<= 25861`, front matter, headings, links).
- `uv run python tools/check_docs_quality.py docs/90_deployment/deployment_01_deployment.md` — no findings.
- `uv run python tools/check_docs_content_policy.py docs/90_deployment/deployment_01_deployment.md` — no findings (English body text).

## Completion criteria

- The section 2.6 note documenting the `REQ-001` missing-binary pre-flight and the `/opt/llm/DEPLOYED_REV`-after-binary-gate relationship is present and accurate.
- `check_docs_structure.py`, `check_docs_quality.py`, and `check_docs_content_policy.py` all pass on the file.

## Out of Scope

- The actual `deploy/start_agent.sh` check (seq 01) and the test (`tests/deploy/test_start_agent_preflight.py`, seq 02).
- Changing any deployed-path behavior or the `check_docs_structure.py` ceiling policy beyond what this note requires.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261030-153000 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261030-153000 | documentation-only row N/A: documentation-only change; no tests added |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261030-153000 | doc checkers |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261030-153000 | this is the doc update |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261029-233829_deploy001_missing-binary-precheck.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-114844_deploy001_missing-binary-precheck.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125450
- **Related target files**: `docs/90_deployment/deployment_01_deployment.md`