# Implementation: PLC0415 comment-correction batch (multiple files) — Phase 2: codebase-wide `# noqa: PLC0415` correction

## Goal

Correct every `# noqa: PLC0415` comment in `scripts/` and `tests/` to reflect reality:
since `PLC0415` (`import-outside-top-level`) is confirmed inert (never selected in
`pyproject.toml`'s `[tool.ruff.lint] select`, and confirmed to stay excluded per the
sibling plan's decision), every such comment currently cites a rule ruff never raises. Two
mechanical transforms apply depending on whether the comment carries an existing
justification.

## Scope

**In-Scope:**
- All `# noqa: PLC0415` occurrences in `scripts/` and `tests/` (measured at plan-authoring
  time: 101 occurrences across 40 files via `rg -l "noqa: PLC0415" scripts/ tests/`;
  reconfirmed at this document-authoring time via `rg -n "noqa: PLC0415" scripts/ tests/`
  -> still 101 occurrences across 40 files).
  - Bare occurrences (no em-dash justification, e.g. `# noqa: PLC0415`): remove the
    entire trailing comment.
  - Occurrences with an existing em-dash justification (e.g.
    `# noqa: PLC0415 — lazy import`): strip the `noqa: PLC0415 — ` prefix, preserving
    the reason text as a plain trailing comment (e.g. `# lazy import`).
- Re-running `rg -n "noqa: PLC0415" scripts/ tests/` afterward to confirm zero remaining
  occurrences.
- Confirming no formatting/lint/test regressions from the comment-only edits.

**Out-of-Scope:**
- Adding `PLC0415`/`PLC` to `pyproject.toml`'s `select` — explicitly deferred (sibling
  plan's decision, reused here); no config activation performed.
- The sibling plan's `# noqa: BLE001` triage batch
  (`implementations/20260806-140022_ble001-triage-batch.md`) — separate concern, separate
  rule family, not duplicated here.
- Any change to code behavior, import statements, exception handling, or control flow —
  comment/annotation text only.
- The `RUF100` defer-decision recording in `pyproject.toml`/`rules/coding.md` — separate
  implementation procedures (`implementations/20260806-140401_pyproject.toml.md`,
  `implementations/20260806-140445_rules_coding.md.md`).

## Assumptions

- **Exact file/line list is not enumerated verbatim in this document** — per the source
  plan's own UNK-02 ("Full file list is regenerated fresh at implementation time...
  rather than enumerated here") and per `skills/DESIGN.md` §Avoid
  implementation-reference duplication. The implementer must re-run
  `rg -n "noqa: PLC0415" scripts/ tests/` at actual-implementation time to get the live,
  current file list, since the set may drift slightly between plan-authoring,
  procedure-authoring, and implementation time.
- Snapshot only, not authoritative: at this document's authoring time,
  `rg -n "noqa: PLC0415" scripts/ tests/` returns 101 matches across 40 files — consistent
  with the plan's own measurement. This confirms the plan's counts have not drifted as of
  now, but the implementer should still re-run the command fresh rather than trust this
  count, per the plan's own UNK-02 discipline.
- No line combines both `BLE001` and `PLC0415` in a single noqa directive — verified by
  the plan directly (`rg -n "noqa:.*BLE001.*PLC0415|noqa:.*PLC0415.*BLE001" scripts/
  tests/` -> zero matches), including in the 3 files where both codes appear on separate
  lines (`scripts/agent/repl_health.py`, `scripts/agent/services/mcp_status.py`,
  `scripts/agent/startup.py`). This means the transform below can safely target only the
  `PLC0415`-specific substring on a matched line without any risk of touching a
  co-located `BLE001` suppression.
- Comment removal/stripping cannot introduce a new `E501` (line-too-long) finding, since
  `E501` is in `pyproject.toml`'s `ignore` list (confirmed by direct read, line 91:
  `ignore = ["E501"]`) — shortening a line can never trigger a line-length rule that is
  disabled outright.
- Representative spot-checked occurrences (grounded by direct read at this
  document-authoring time):
  - With-reason (28-count category): `scripts/agent/factory.py:366-381` — 8 occurrences,
    all `# noqa: PLC0415 — lazy` (e.g. line 366:
    `from agent.memory.embedding_client import (  # noqa: PLC0415 — lazy`); and
    `scripts/agent/repl.py:751` —
    `StartupOrchestrator,  # noqa: PLC0415 — lazy: avoids circular import at module level`.
  - Bare (73-count category): `scripts/eventbus/route_helpers.py:68` —
    `from eventbus.db import get_db_lock  # noqa: PLC0415`; line 83:
    `import orjson  # noqa: PLC0415`; and `scripts/eventbus/app.py:194`:
    `import uvicorn  # noqa: PLC0415`.
- This is a single mechanical, well-defined transform (remove-or-de-prefix a fixed
  comment substring) applied uniformly across many files with zero behavioral change —
  per this workflow's guidance for large/non-cleanly-enumerable sets, this is handled as
  ONE batch document (matching the precedent set by the sibling plan's own Phase 2
  `# noqa: BLE001` triage, `implementations/20260806-140022_ble001-triage-batch.md`),
  rather than 40 separate per-file documents. Unlike the `BLE001` triage batch (which
  requires per-site human judgment about exception narrowing), this batch requires no
  judgment — the two transform rules apply uniformly and mechanically.

## Design decisions

- Handle this as one batch document, not 40 per-file documents — justified because (a)
  the transform is identical and mechanical across all occurrences (only two branches:
  bare vs. with-reason), (b) there is zero behavioral risk (comment-text only), and (c)
  this matches the established precedent in this same document set
  (`ble001-triage-batch`) for large, mechanically-uniform, cross-file changes.
- Defer the exact file/line enumeration to implementation time via a fresh
  `rg -n "noqa: PLC0415" scripts/ tests/` run, rather than freezing today's 101/40 count
  into this document — the plan itself follows this discipline (UNK-02) for the same
  drift-avoidance reason.
- Preserve the reason text verbatim (only strip the `noqa: PLC0415 — ` prefix) for the 28
  with-reason occurrences, per the plan's explicit instruction ("preserve the existing
  inline justification text... even if the rule code itself changes or the comment format
  changes") — the reason describes *why* the import is where it is (e.g. lazy-import to
  avoid a circular import), which remains true and useful even after the (now-inert)
  rule citation is removed.

## Alternatives considered

- Decompose into 40 separate per-file implementation procedure documents — rejected: no
  per-file judgment is required (unlike `BLE001` triage), so 40 near-identical documents
  would be pure duplication with no informational value; one batch document with a clear
  mechanical rule is sufficient and matches the sibling batch precedent.
- Delete the reason text along with the rule citation for the 28 with-reason occurrences
  (i.e., remove the whole trailing comment uniformly for all 101 occurrences) — rejected:
  the plan explicitly requires preserving the reason text as a plain comment, since it
  still documents useful context (e.g., "avoids circular import") independent of which
  rule code, if any, is cited.
- Leave the `# noqa: PLC0415` comments in place since they are functionally inert (no
  behavioral effect either way) — rejected: the plan's Goal explicitly requires
  correcting these comments "to reflect reality," and stale rule citations mislead future
  readers into thinking `PLC0415` is enforced or was once relevant to lint-passing.

## Implementation

### Target file
Multiple — exact set regenerated via `rg -n "noqa: PLC0415" scripts/ tests/` at actual
implementation time (101 occurrences across 40 files measured at this document's
authoring time; see Assumptions for grounded representative examples — this list is not
frozen here per UNK-02).

### Procedure
1. Run `rg -n "noqa: PLC0415" scripts/ tests/` to get the current, authoritative
   occurrence list (file + line number for each match).
2. For each matched line, classify it into one of two cases by checking for an em-dash
   (`—`) after `PLC0415`:
   - **Case A — bare** (no em-dash reason, e.g.
     `from eventbus.db import get_db_lock  # noqa: PLC0415`): remove the entire trailing
     `  # noqa: PLC0415` comment, leaving the code line otherwise untouched (e.g. ->
     `from eventbus.db import get_db_lock`).
   - **Case B — with reason** (em-dash present, e.g.
     `StartupOrchestrator,  # noqa: PLC0415 — lazy: avoids circular import at module
     level`): strip only the `noqa: PLC0415 — ` prefix from the comment, keeping
     everything after the em-dash as a plain comment (e.g. ->
     `StartupOrchestrator,  # lazy: avoids circular import at module level`).
3. Re-run `rg -n "noqa: PLC0415" scripts/ tests/` — expect zero remaining matches.
4. Run `uv run ruff format --check scripts/ tests/` and `uv run ruff check scripts/` —
   expect no diff and no new lint errors (comment-only edits, and `E501` stays ignored).
5. Run `uv run pytest` (full suite) — expect all pre-existing results unchanged (no code
   line altered, only comments).
6. Do not implement yet — this is a document-only phase. Given the number of files
   involved (40), the implementer may script the mechanical transform (e.g. a small
   sed/regex pass distinguishing the em-dash case) but must manually diff-review the
   result before staging, per `rules/toolchain.md` step 9 ("review every changed line
   before staging").

### Method
Mechanical text transform (comment substring removal or prefix-stripping) applied per
matched line — no code generation, no import/logic changes. Given the uniform,
judgment-free nature of the two cases, this may be scripted (e.g. a regex-based pass) but
every resulting diff must be reviewed line-by-line before commit, since a scripted
transform risks over-matching (e.g. accidentally matching a `PLC0415` substring inside an
unrelated string literal — verify this does not occur via the re-run in step 3).

### Details
- Per this plan's Implementation Steps Phase 2 (verbatim): "Re-run `rg -n "noqa:
  PLC0415" scripts/ tests/` to get the current, exact occurrence list (may drift slightly
  from the 101/40 measured here). For each of the 73 bare occurrences (no em-dash
  reason): remove the entire `# noqa: PLC0415` trailing comment (nothing else on the line
  is touched). For each of the 28 occurrences with an existing em-dash reason: strip the
  `noqa: PLC0415 — ` prefix, keeping the reason text as a plain trailing comment...
  Re-run `rg -n "noqa: PLC0415" scripts/ tests/` to confirm zero remaining occurrences.
  Run `uv run ruff format --check scripts/ tests/` and `uv run ruff check scripts/` to
  confirm no formatting or lint regressions from the comment edits. Run `uv run pytest`
  (full suite) to confirm zero behavioral change."
- Elevated-attention files (per plan Affected Areas — Risk Metrics): `scripts/agent/
  factory.py` and `scripts/agent/repl.py` carry existing `# noqa: PLC0415` lines inside
  lazy-import blocks used to avoid circular imports (high-centrality agent
  startup/factory wiring) — comment edits there carry low technical risk (text-only) but
  should be diffed carefully since the surrounding lazy-import blocks are
  circular-import-avoidance-critical. `scripts/eventbus/*.py` (route_helpers.py,
  subscribe_route.py, ack_route.py, app.py) hold several bare (Case A) occurrences —
  lower individual risk, straightforward full-comment removal.
- Files carrying both `BLE001` and `PLC0415` noqa on separate lines (`scripts/agent/
  repl_health.py`, `scripts/agent/services/mcp_status.py`, `scripts/agent/startup.py`):
  only the `PLC0415`-tagged lines are touched by this batch; the co-located `BLE001`
  lines (owned by `implementations/20260806-140022_ble001-triage-batch.md`) are
  untouched by construction, per Assumption above (no line combines both codes).
- This batch is independent of, and can be committed separately from, this plan's
  `pyproject.toml`/`rules/coding.md` RUF100-recording documents
  (`implementations/20260806-140401_pyproject.toml.md`,
  `implementations/20260806-140445_rules_coding.md.md`) — per the plan's own phased
  design (Phase 1 vs. Phase 2, independently committable).

## Compatibility considerations

- Zero behavioral change: comment-text only, no import statements, exception handling, or
  control flow touched. `ruff check` results are identical before and after (PLC0415 was
  never enforced either way).
- `tox.ini`'s `lint` environment (`ruff check scripts/`, no `tests/` argument per direct
  read) is unaffected either way; `.pre-commit-config.yaml`'s `ruff`/`ruff-format` hooks
  (which do cover `tests/`) should also show no diff after `ruff format --check`.

## Security considerations

N/A — comment/annotation text only, no runtime security surface.

## Rollback considerations

- Each file's edit is an independent, small comment-text diff; revertable per-file via
  `git checkout -- <file>` or as a single batch revert if committed together, since no
  file depends on another's edit (no shared state, no migration).
- If a future reviewer overrules the sibling plan's "keep PLC0415 out of select" decision
  (plan's own UNK-01, low-probability), this entire batch is a straightforward `git
  revert` since it is comment-only.

## Validation plan

- `rg -n "noqa: PLC0415" scripts/ tests/` — zero matches after the batch.
- `uv run ruff check scripts/` — 0 errors (unchanged from baseline; `PLC0415` was never
  enforced).
- `uv run ruff format --check scripts/ tests/` — no diff.
- `uv run ruff check scripts/ tests/` (default select) — exit 0; `RUF100`/`PLC0415`
  remain unselected as documented in the companion `pyproject.toml`/`rules/coding.md`
  documents.
- `uv run pytest` (full suite) — all pass, identical to pre-change baseline.
- `uv run mypy scripts/` — no new errors vs. pre-existing baseline.
- `PYTHONPATH=scripts uv run lint-imports` — 0 violations.
- `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` — comment-only
  changes carry no executable lines; confirm diff-cover does not flag them as uncovered.
- `uv run pre-commit run --all-files` — passes.

## Out of scope

- `pyproject.toml`/`rules/coding.md` RUF100-recording — separate implementation
  procedures (`implementations/20260806-140401_pyproject.toml.md`,
  `implementations/20260806-140445_rules_coding.md.md`).
- `# noqa: BLE001` triage — owned by
  `implementations/20260806-140022_ble001-triage-batch.md`.
- Enabling `PLC0415`/`PLC` or `RUF100` in `select` — both decisions are to defer; no
  config activation performed by this or any related item.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260806-134805_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-140518
- Related target files: plc0415-comment-correction-batch (multiple scripts/ and tests/
  files carrying `# noqa: PLC0415`; exact set regenerated at implementation time via
  `rg -n "noqa: PLC0415" scripts/ tests/`, measured as 101 occurrences across 40 files at
  both plan- and this document's authoring time)
