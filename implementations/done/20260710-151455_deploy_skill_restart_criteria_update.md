# Implementation: Update deploy skill's restart decision criteria for `cmd`-path changes (Phase 3)

## Goal

Make `skills/deploy/workflow.md`'s Agent restart decision criteria explicit about the case introduced by Phase 1's rename: changing an *existing* `[mcp_servers.*]` entry's `cmd` (or `url`/`transport`/`startup_mode`/`env`) value requires a full agent restart, since `/reload` does not apply those fields — and add a post-restart verification step for this case.

## Scope

**In:**
- `skills/deploy/workflow.md`: append one bullet to the "Agent restart decision criteria" section (after the existing "`config/agent.toml` with a new `mcp_servers` entry" bullet)
- `skills/deploy/workflow.md`: append a verification note directly after the existing "Check status after restart" `curl` command block

**Out:**
- No change to the actual restart mechanism or subprocess management commands — this is a documentation-only clarification of an existing (undocumented) restart requirement
- No change to `/reload`'s implementation — this document only clarifies which fields it does not cover

## Assumptions

1. `skills/deploy/workflow.md`'s "Agent restart decision criteria" section is currently at lines 49-57, with the two existing bullets at lines 51-53 (confirmed by direct read at planning time) — line numbers may shift slightly by the time this is implemented if other concurrent edits land first; locate by section heading text, not by hardcoded line number.
2. This addition is motivated specifically by Phase 1 of this plan (the `scripts/mcp` → `scripts/mcp_servers` rename changes every server's `cmd` path in `config/agent.toml`), but the wording should be general (any `cmd`/`url`/`transport`/`startup_mode`/`env` value change on an existing entry), since the same restart requirement applies to any future config change of this shape, not just this one rename.
3. `docs/04_mcp_06_configuration_and_operations.md` (or its current post-split successor file covering "Reload vs. restart") already documents that `/reload` does not apply `cmd`/`url`/etc. field changes — this document's new bullet should cross-reference that existing section rather than duplicate its content in full.

## Implementation

### Target file

`skills/deploy/workflow.md`

### Procedure

1. Locate the "Agent restart decision criteria" section and its two existing bullets under "Restart `llama-agent` ONLY if changes are in:".
2. Append a third bullet:
   ```diff
    Restart `llama-agent` ONLY if changes are in:
    - `agent/repl.py`, `agent/context.py`, `agent/config.py`, or any file under `agent/commands/`
    - `config/agent.toml` with a new `mcp_servers` entry (requires full restart)
   +- `config/agent.toml` with an existing `[mcp_servers.*]` entry's `cmd`/`url`/`transport`/
   +  `startup_mode`/`env` value changed (e.g. package rename affecting launch paths) —
   +  `/reload` does not apply these fields; see the MCP configuration doc's Reload vs. restart section
   ```
3. Locate the "Check status after restart" code block (`curl -s http://127.0.0.1:<PORT>/health`).
4. Append a verification note directly after it:
   ```diff
    Check status after restart:

    ```bash
    curl -s http://127.0.0.1:<PORT>/health
   +
   +# For deploys that changed cmd paths (e.g. package rename):
   +# /mcp status must show every MCP server's PID updated to the post-restart value
    ```
   ```
5. Run `python -m tools.check_docs_consistency` if it covers skill files, or otherwise visually confirm the diff renders correctly as Markdown.

### Method

Direct prose/diff insertion into an existing, well-defined section — no new section structure introduced, matching the existing bullet-list and code-block conventions already used in this file.

### Details

- The new restart-criteria bullet is written generally (not "when scripts/mcp is renamed to scripts/mcp_servers") so it remains correct and applicable after this specific rename is history — it documents a standing rule about `/reload`'s field coverage, not a one-time migration note.
- Cross-reference the MCP configuration doc by section name ("Reload vs. restart") rather than by a specific filename, since `docs/04_mcp_*.md` files have been undergoing concurrent splits this session — a section-name reference degrades more gracefully than a hardcoded filename if the doc is split again.

## Validation plan

```bash
grep -n "cmd.*url.*transport.*startup_mode.*env" skills/deploy/workflow.md   # expect 1 match (new bullet)
grep -n "/mcp status" skills/deploy/workflow.md                              # expect the new verification line present
```

Expected outcome: the deploy skill explicitly documents that `cmd`/`url`/`transport`/`startup_mode`/`env` changes on existing MCP server entries require a full restart (not `/reload`), with a concrete post-restart verification step.
