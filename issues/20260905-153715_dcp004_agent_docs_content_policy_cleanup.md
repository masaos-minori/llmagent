# Review and clean up Agent domain docs against the content policy

## Priority
Medium

## Summary
Review `docs/05_agent_02_runtime-architecture.md`,
`05_agent_03_01_turn-processing-flow-overview.md`, and
`05_agent_07_11_cli-and-commands-slash-commands-memory-other.md` against
`skills/DESIGN.md` Docs content policy — remove/retain, and remove genuine
violations. This issue explicitly requires a manual read before editing,
because `tools/check_docs_content_policy.py`'s ASCII-tree-drawing-character
pattern appears to over-match at least one of these files (see Problem).

## Background
`docscope1`/`docscope2` (in `issues/done/`) established the policy and the
detection tool (`GV-021`, report-only by design specifically because it can
over- or under-match).

## Problem
`uv run python tools/check_docs_content_policy.py` reports 48 findings:
`05_agent_03_01_turn-processing-flow-overview.md` (38),
`05_agent_02_runtime-architecture.md` (9), and
`05_agent_07_11_cli-and-commands-slash-commands-memory-other.md` (1). Reading
`05_agent_03_01_turn-processing-flow-overview.md` shows most of its 38
"full file tree" findings come from a "### Single Turn Processing Flow"
section: a sequence/flow diagram (`User input (line)` → branches through
`├─`/`│`/`└─` connectors → numbered steps ①–⑥) describing control flow
through `Orchestrator.handle_turn()`, not a directory listing. The detection
tool matches on ASCII tree-drawing characters alone and cannot distinguish a
directory tree from a flow diagram — this is a known false-positive risk,
which is exactly why `docscope2` shipped the check as report-only rather
than a blocking gate. The same file's prose (e.g. "`Orchestrator.__init__`
calls `WorkflowLoader().load()`...") is legitimate class/method-name
reference under `skills/DESIGN.md` "No source-code line numbers"'s own
carve-out, not a violation. `05_agent_02_runtime-architecture.md`'s 9
findings have not been read yet and may be genuine file-tree content (needs
confirmation during implementation).

## Reason for Change
The flow diagram in `05_agent_03_01_turn-processing-flow-overview.md`
appears to be exactly the kind of design-intent content the policy wants
retained (it documents the turn-processing responsibility boundary,
including the mandatory-workflow-engine design decision and why there is no
fallback path) — deleting it to satisfy a mechanical warning count would
remove genuinely valuable content the policy was never meant to target.
Any content in `05_agent_02_runtime-architecture.md` that is a genuine
directory/file-tree listing, by contrast, should be removed per the same
policy applied elsewhere in this cleanup effort.

## Implementation Intent
Read each flagged section before acting. For
`05_agent_03_01_turn-processing-flow-overview.md`'s "Single Turn Processing
Flow" diagram: keep it as-is if it is confirmed to be a control-flow
diagram rather than a file/directory listing (the current reading strongly
suggests this) — this is a case where the detection tool's warning does not
correspond to an actual policy violation, and `check_docs_content_policy.py`
being report-only exists precisely to allow this kind of human override. For
`05_agent_02_runtime-architecture.md`: read its 9 flagged lines and
determine whether they are genuine file-tree/per-file-description content
(remove/rewrite per the same pattern as `dcp002`) or another diagram-type
false positive (keep, as above). Apply the same read-before-removing
judgment to `05_agent_07_11_...`'s single finding.

## Target Files or Areas
- `docs/05_agent_02_runtime-architecture.md`
- `docs/05_agent_03_01_turn-processing-flow-overview.md`
- `docs/05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Required Changes
1. Read all 9 flagged lines in `05_agent_02_runtime-architecture.md` and
   classify each as genuine file-tree content (remove/rewrite into
   design-intent prose per the `dcp002` pattern) or a non-tree false
   positive (leave in place, and note the classification in this issue's
   completion evidence).
2. Confirm `05_agent_03_01_turn-processing-flow-overview.md`'s "Single Turn
   Processing Flow" section is a control-flow diagram, not a file tree —
   if confirmed, leave it in place; if any sub-portion instead lists files
   or directories, remove only that sub-portion.
3. Read and resolve `05_agent_07_11_...`'s single flagged line.
4. Where content is genuinely removed, replace it per the retain-category
   list (component responsibility, owned state, allowed dependency
   direction, process/config separation rationale, joint-review design
   boundaries) rather than leaving a gap.

## Constraints
- Do not remove the "Single Turn Processing Flow" diagram (or any other
  confirmed non-tree diagram) solely to make
  `check_docs_content_policy.py`'s warning count reach zero — a report-only
  check is advisory, not a removal mandate, per its own `GV-021`
  registration.
- Do not alter `05_agent_03_02_turn-processing-flow-llm-tool-loop.md` or
  `05_agent_03_03_turn-processing-flow-workflow-engine.md` (linked from this
  file but out of scope here).

## Acceptance Criteria
- Each of the 48 flagged lines has an explicit disposition recorded (removed
  as a genuine violation, or kept with a stated reason it is a false
  positive) — not a blanket accept-all-warnings or reject-all-warnings
  pass.
- Any content actually removed is replaced with retain-category design
  intent, not left as a gap.
- `uv run python tools/check_docs_consistency.py --domain agent` passes.

## Testing Expectations
Documentation-only change. Run
`uv run python tools/check_docs_content_policy.py`,
`uv run python tools/check_docs_structure.py docs/05_agent_02_runtime-architecture.md
docs/05_agent_03_01_turn-processing-flow-overview.md
docs/05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`, and
`uv run python tools/check_docs_consistency.py --domain agent`
(`check-agent-docs` shorthand). No `pytest`/`mypy`/`ruff` run required.

## Documentation Impact
Yes — the outcome (what was removed vs. kept as a false positive, and why)
must itself be documented as this issue's completion evidence, since a
residual `check_docs_content_policy.py` warning count above zero is expected
and intentional here if the flow diagram is confirmed legitimate.

## Out of Scope
- `05_agent_03_02_...` and `05_agent_03_03_...` (linked, not flagged, not in
  scope).
- Extending `check_docs_content_policy.py`'s pattern-matching to
  distinguish flow diagrams from file trees automatically — if this
  recurs elsewhere, file a separate tooling issue rather than fixing the
  detector here.

## Dependencies
N/A: none. Independent of `dcp001`–`dcp003`, `dcp005`, `dcp006`.

## Unresolved Questions
- If `05_agent_02_runtime-architecture.md`'s 9 findings turn out to be a mix
  of genuine tree content and other diagram types, whether
  `check_docs_content_policy.py` should gain a narrower pattern (e.g.
  requiring a `path/` or file-extension token near the tree characters) to
  reduce this false-positive class repository-wide — flagged for a
  separate tooling issue if the implementer judges it recurs enough to
  warrant a Global Rule 7 script change, not decided here.

## AI Implementation Instruction
Read the actual flagged content in each file before deciding whether to
remove it — do not treat the warning count as a target to zero out
mechanically, since this domain is the one place in this cleanup effort
where the detector is known to produce likely false positives. State the
disposition (removed / kept-as-false-positive) for every flagged line in
the completion report. Stop and ask if a flagged section is ambiguous
between "control-flow diagram" and "file/directory listing" rather than
guessing.
