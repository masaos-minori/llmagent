## Goal

Correct `docs/04_mcp_02_02_startup-modes-and-health.md`'s `restart_recommended`/
`operator_action_required` field descriptions (REQ-001) so they no longer describe an
active "Watchdog" consumer, per `plans/20260826-114325_plan.md`.

## Scope

- In scope: the `restart_recommended` description (~line 26) and its "Note (Current
  Implementation)" (line 28), and the `operator_action_required` description (~line
  30), in this one document.
- Out of scope: the "Interpretation in `/mcp status`" section (line 44, already
  accurate), the response-example JSON blocks (lines 57-71, field values unaffected),
  and any other section; `scripts/mcp_servers/server.py`'s docstring (Plan's UNK-01,
  non-blocking, explicitly out of this Plan's scope).

## Assumptions

- The MCP watchdog was removed 2026-07-16 and no code path today acts on
  `restart_recommended`/`operator_action_required` to trigger a restart — re-verified
  2026-08-27: `McpStatusService.probe_all()`/`cmd_mcp.py` only display these fields
  (line 44 of this same document already states this correctly).
- The field *definitions* themselves (what `restart_recommended=true` vs. `false`
  means, what `operator_action_required=true` means) remain accurate and must not
  change — only the consumer/action language changes.

## Design decisions

- Replace "informs the Watchdog that restarting the process may resolve the issue"
  and "The Watchdog logs a WARNING ... will not perform a restart" with language
  stating no live consumer performs an automatic restart today (removed 2026-07-16);
  the field is surfaced read-only via `/mcp status`
  (`agent/services/mcp_status.py::probe_all()`).
- Keep the "Note (Current Implementation)" bullet's substantive claim (all 10 MCP
  servers currently return `False` for `restart_recommended`) — only its "automatic
  restarts by the Watchdog" closing clause needs rewording to match the corrected
  framing.

## Alternatives considered

- Deleting the Watchdog-consumer sentences outright (rather than replacing them with
  corrected framing) was considered and rejected — the field descriptions would then
  say nothing about who reads the field, leaving a gap; REQ-001's Acceptance
  Criterion requires consistency with the existing display-only note, which implies
  replacement, not deletion.

## Implementation
### Target file
`docs/04_mcp_02_02_startup-modes-and-health.md`

### Procedure
1. Rewrite the `restart_recommended` description (line 26) and its trailing "Note
   (Current Implementation)" bullet (line 28) per Method/Details.
2. Rewrite the `operator_action_required` description (line 30) per Method/Details.
3. Re-read the full document top-to-bottom to confirm lines ~26/~30, the existing
   display-only note (line 44), and the existing removal note (line 49) no longer
   contradict each other.
4. Run `uv run python tools/check_docs_quality.py`,
   `uv run python tools/check_docs_consistency.py --domain mcp`, and
   `rg -n "Watchdog" docs/04_mcp_02_02_startup-modes-and-health.md` (confirm all
   remaining hits are historical/removal-note framing).

### Method
Direct text edits (Edit tool) on two field-description paragraphs and one note
bullet; no restructuring of the surrounding document.

### Details
Current text (verified 2026-08-27):
- Line 26: `**\`restart_recommended\`**: Setting this to \`true\` informs the
  Watchdog that restarting the process may resolve the issue. \`false\` means a
  restart will not help (e.g., missing credentials require operator intervention).`
- Line 28: `**Note (Current Implementation):** ... Therefore, currently, automatic
  restarts by the Watchdog are only triggered in "unreachable" cases
  (\`reachable=False\`), while "reachable but \`restart_recommended=true\`" is
  supported by design but does not occur in implemented servers (Explicit in code).`
- Line 30: `**\`operator_action_required\`**: \`true\` if human intervention is
  required (e.g., missing credentials, missing binaries). The Watchdog logs a
  WARNING, but if both \`operator_action_required\` is \`true\` and
  \`restart_recommended\` is \`false\`, it will not perform a restart.`

Rewrite line 26 to state the field's meaning without naming an active consumer
(e.g., "Setting this to `true` indicates that restarting the process may resolve the
issue; `false` means a restart will not help. No live consumer acts on this field
today — the MCP watchdog that once did was removed 2026-07-16; the field is surfaced
read-only via `/mcp status`, see Interpretation below.").

Rewrite line 28's closing clause: replace "automatic restarts by the Watchdog are
only triggered in ..." with a statement that no automatic restart occurs regardless
of this field's value today, while keeping the factual claim that all current
implementations return `False`.

Rewrite line 30 to remove "The Watchdog logs a WARNING ... will not perform a
restart" — replace with a statement that human intervention is required and this is
surfaced via `/mcp status`, with no automated action taken.

## Compatibility considerations

- Documentation-only; no runtime behavior, health-response schema, or public
  interface is affected — the fields themselves are unchanged, only their described
  consumer.

## Security considerations

- N/A: no security-relevant behavior is described or changed by this correction.

## Rollback considerations

- Three-paragraph text revert via `git diff`/`git checkout -- <path>`; no other
  document or code depends on this exact wording (the "Interpretation in `/mcp
  status`" section elsewhere in the same document is not touched and remains the
  authoritative description of actual behavior).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_02_02_startup-modes-and-health.md` | Doc quality check | `uv run python tools/check_docs_quality.py` | Passes; no structural/formatting regressions |
| `docs/04_mcp_02_02_startup-modes-and-health.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py --domain mcp` | Passes; no new drift |
| `docs/04_mcp_02_02_startup-modes-and-health.md` | Manual | `rg -n "Watchdog" docs/04_mcp_02_02_startup-modes-and-health.md` | Only historical/removal-note hits remain |

## Completion criteria

- Reading the document top-to-bottom shows no remaining internal contradiction
  between the `restart_recommended`/`operator_action_required` field descriptions and
  the document's own display-only (line 44) and removal (line 49) notes.

## Out of scope

- The "Interpretation in `/mcp status`" section and response-example JSON blocks.
- `scripts/mcp_servers/server.py`'s docstring (Plan's UNK-01).
- Any code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite `restart_recommended` description and its Note bullet | Completed | — | — | Removed Watchdog-consumer language |
| 2 | Rewrite `operator_action_required` description | Completed | — | — | Removed Watchdog-consumer language |
| 3 | Re-read full document to confirm no internal contradiction remains | Completed | — | — | Confirmed lines ~26/~30 consistent with display-only note (line 44) and removal note (line 49) |
| 4 | Run `check_docs_quality.py`, `check_docs_consistency.py --domain mcp`, and the `rg` Watchdog check | Completed | — | — | Pre-existing errors only; no new findings; no "Watchdog" hits remain |

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
- **Requirement ID**: REQ-001
- **Source issue**: `issues/20260821_04_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-114325_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-110529
- **Related target files**: `docs/04_mcp_02_02_startup-modes-and-health.md`
