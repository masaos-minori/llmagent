## Goal

Replace the single-line `masked_fields` bullet in `docs/23_agent/agent_08_03_configuration-tools-memory.md`
with the explicit masking boundary rule, so the documented behavior matches the implemented one
(`REQ-001`, `AC-4`).

## Scope

- `docs/23_agent/agent_08_03_configuration-tools-memory.md`: the `masked_fields` bullet in the
  `#### Safety` list under `### Tool Configuration` (`:32`), and the immediately following sentences if
  the boundary needs a short paragraph.
- No other section of the file changes, and no other document is edited; `docs/00_index.md` and
  `docs/23_agent/agent_13_reference-api-generated.md` are not touched by this row.

## Assumptions

- This file is the documentation home for `masked_fields`: `docs/00_index.md`'s task mapping for
  "AgentConfig / config constants" reaches
  `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`, whose `related:` indexes this file
  (confirmed by this file's own `related:` entry at `:10`).
- The current bullet at `:32` reads: "`masked_fields` lists argument keys masked in console output.",
  which understates the sinks and omits the recursion and the preview exception.
- The file is 5232 B, well under the 24576 B `MAX_SIZE` in `tools/check_docs_structure.py`.

### Procedure-local findings

- The Plan cites this bullet at `:32`; confirmed by read on 2026-10-24.
- The Plan's Validation plan row used the glob `'23_agent/agent_08_03_*.md'`, which silently matches no
  file. The corrected `docs/`-prefixed form is recorded in the Plan's corrections subsection and filed
  as its own issue.

## Design decisions

- Document the boundary as a rule with its reader-facing consequence (what appears redacted, what does
  not, and why), not as a list of code call sites. The `masked_fields` bullet sits in a Safety list
  read by whoever edits `config/agent.toml`.
- State the inert default as a usability fact: `file_content` matches no current tool-argument key, so
  masking only takes effect when the list names keys the tools actually accept (`content`, `old_text`,
  `new_text`). The default value itself is not changed here — that change is filed as
  `issues/20261024-124138_tool005_default-masked-fields-names-match-no-real-tool-argument.md`.
- Keep the entry as list bullets in the existing `#### Safety` list rather than adding a new section,
  so the document's heading structure and checker-visible shape stay unchanged.

## Alternatives considered

- Replacing the bullet with a table of sink names and file paths: rejected. It reads as implementation
  detail and is maintained nowhere; `tools/check_docs_content_policy.py` targets exactly this kind of
  drift.
- Documenting only the mask side and leaving the preview exception implicit: rejected. The preview
  exception is the decision `REQ-001` exists to record, and `T-3`
  (`implementations/20261024-124138_04_tests_agent_test_tool_approval_risk.py.md`) pins it in tests.
- Adding a new `## Data Redaction` section to this document: rejected. The document's scope is
  ToolConfig and MemoryConfig fields; a new section would need its own index and `related:` wiring for
  no benefit.

## Implementation

### Target file

`docs/23_agent/agent_08_03_configuration-tools-memory.md`, `#### Safety` list, `:32`.

### Procedure

1. Replace the `masked_fields` bullet with a bullet plus two short sub-bullets that state: masked
   anywhere in the argument tree at any depth; applied to audit events, logger writes, the REPL
   tool-call line, and the plan-mode blocked notice; not applied to the interactive approval preview.
2. Add the rationale sentence for the preview exception: the preview exists so the approving user can
   judge the operation they are approving, and its reader is the person who supplied the arguments.
3. Add the usability sentence naming the real argument keys and stating that the shipped default
   matches none of them.
4. Leave the front matter `related:` list, `## Purpose`, `## Responsibility Boundary`,
   `## Key Constraints`, and `## Keywords` unchanged.

### Method

- Write from the behavior the tests pin (`T-3` for the preview boundary, `T-1`/`T-2` for recursive
  masking), not from line numbers.
- Keep the wording consistent with `docs/23_agent/agent_13_reference-api-generated.md`'s `mask_args`
  Summary row so the two documents do not disagree; the generated row states masking replaces
  `masked_fields` keys with `***` at any depth.

### Details

- Terms to use consistently: "masked", `"***"`, "audit event", "approval preview", "plan-mode blocked
  notice".
- Do not state that the default list is effective; state that it matches no current argument key.
- Do not introduce cross-document links in the body; this file already links through front matter.

## Compatibility considerations

- Documentation-only change: no code or config behavior changes in this row.
- The sentence about the default must match the code as it exists today
  (`scripts/agent/config_dataclasses.py:182`, `scripts/agent/config_section_builders.py:204-205`,
  `config/agent.toml:98`); if the filed issue later changes the default, this bullet is the text that
  must be updated with it.
- No `## Related Documents`-type body section may be added: `tools/check_docs_structure.py` reports a
  body Related-type section when one remains.

## Security considerations

- The documented boundary is a privacy claim: it tells operators which outputs redact configured keys
  and which do not. An inaccurate claim here causes users to assume secrets are absent from outputs
  where they are present (the approval preview).
- Stating that previews are unmasked is the disclosure half of the decision; the docs must not soften
  it.

## Rollback considerations

- Restore the original single bullet text at `:32`; nothing else in the document depends on it.

## Validation plan

- `uv run python tools/check_docs_structure.py 'docs/23_agent/agent_08_03_*.md'` — exits 0. The glob
  must be `docs/`-prefixed; the checker resolves patterns against the repo root and a `docs/`-less
  pattern checks nothing (`issues/20261024-124138_docs010_check_docs_structure-glob-matching-no-files-passes-silently.md`).
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_content_policy.py`,
  `uv run python tools/check_docs_consistency.py --domain agent` — all pass.
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json
  --check-duplicates` — the CI form of the check, exits 0.
- Cross-check the wording against the regenerated `mask_args` row in
  `docs/23_agent/agent_13_reference-api-generated.md` after
  `implementations/20261024-124138_06_docs_23_agent_agent_13_reference-api-generated.md.md` runs.

## Completion criteria

- `AC-4`: the document states the boundary (logs and audit mask recursively, including the plan-mode
  blocked notice; interactive approval previews do not), gives the rationale, and passes all four docs
  checkers.
- The text names at least one real tool-argument key so a reader can configure masking that actually
  applies.

## Out of Scope

- Changing `masked_fields` defaults in code or config: filed as
  `issues/20261024-124138_tool005_default-masked-fields-names-match-no-real-tool-argument.md`.
- `docs/00_index.md`: no index change is required because this document is already reachable through
  `agent_08_01`'s `related:` list.
- `docs/23_agent/agent_13_reference-api-generated.md`, owned by
  `implementations/20261024-124138_06_docs_23_agent_agent_13_reference-api-generated.md.md`.


## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the `masked_fields` bullet at `:32` with the boundary rule | Pending | — | — | Bullet plus two sub-bullets |
| 2 | Run the four docs checkers with `docs/`-prefixed globs | Pending | — | — | `AC-4` |
| 3 | Re-read the wording against the regenerated `mask_args` Summary row | Pending | — | — | After `_06` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `issues/20261024-124138_docs010_check_docs_structure-glob-matching-no-files-passes-silently.md` | Step 2 | Issue | Open | repo owner | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261021-093421_tool005-masked-args-not-applied-to-previews-or-nesting.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-072425_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-124138
- **Related target files**: `docs/23_agent/agent_08_03_configuration-tools-memory.md`
