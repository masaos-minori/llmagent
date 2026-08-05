## Goal

Create `docs/02_deployment-operations.md` as a dedicated operations runbook containing the
service startup and health-check command examples that previously lived inline in
`docs/02_deployment-part1.md` §2.3, so operators have a single reference for runtime
verification commands.

## Scope

- In scope: creating `docs/02_deployment-operations.md` with a title, a "Service Startup and
  Health Check" section, and the verbatim command block moved from §2.3 of
  `docs/02_deployment-part1.md`.
- Out of scope: modifying `docs/02_deployment-part1.md` itself (covered by a separate,
  already-existing implementation procedure for that file); changing any command, port, or
  endpoint value; any source code change.

## Assumptions

- The file name `docs/02_deployment-operations.md` follows the existing `02_deployment-*.md`
  naming convention used for deployment documentation.
- Content language matches the surrounding deployment docs (Japanese section prose; command
  blocks are language-neutral shell).
- This is a documentation-only artifact; no import-linter, mypy, ruff, or pytest checks apply.

## Design decisions

- Single dedicated runbook file rather than a new subsection inside `part1`, per
  `skills/python-design` guidance to keep one responsibility per artifact: `part1` stays a
  deployment-flow reference, `02_deployment-operations.md` owns operational
  (post-deploy/runtime verification) command examples.
- Keep the command block verbatim (no re-derivation) to avoid introducing drift between the
  documented command and the actual `deploy/setup_services.sh` invocation.

## Alternatives considered

- Keep the command block inline in `part1` §2.3 — rejected: plan explicitly requires
  relocation to reduce `part1`'s scope to deployment-flow narrative only.
- Merge into an existing runbook-style doc (e.g. an existing operator workflow doc) — rejected:
  plan specifies a new, dedicated file name `docs/02_deployment-operations.md`.

## Implementation

### Target file

`docs/02_deployment-operations.md` (new)

### Procedure

1. Read `docs/02_deployment-part1.md` §2.3 to identify the exact command block to relocate
   (`bash deploy/setup_services.sh` plus the health-check `curl` calls for `embed-llm` /
   `agent-llm`, and `bash deploy/start_agent.sh`).
2. Create `docs/02_deployment-operations.md` with:
   - Title: "Operations Runbook"
   - Section: "Service Startup and Health Checks"
   - The relocated command block, unmodified.
3. Cross-check that `docs/02_deployment-part1.md` §2.3 already contains (or is updated by its
   own implementation procedure to contain) the prose pointer referencing this new file.

### Method

- Plain Markdown file creation; no code generation, no template engine.
- Content verified via `grep`/`Read` against the source section in `part1`, not retyped from
  memory.

### Details

- Evidence (as of this writing): `docs/02_deployment-operations.md` already exists on disk
  (16 lines) with title "Operations Runbook", section "Service Startup and Health Checks", and
  the command block:
  `bash deploy/setup_services.sh`, `curl -s http://127.0.0.1:8081/health` (embed-llm),
  `curl -s http://127.0.0.1:8080/health` (agent-llm), `bash deploy/start_agent.sh`.
- `docs/02_deployment-part1.md` line 102 already contains the Japanese prose pointer to
  `docs/02_deployment-operations.md`.
- This procedure document is generated per workflow rule even though the target content
  appears already present, because no implementation-procedure file matching
  `02_deployment-operations.md` existed under `implementations/` or `implementations/done/`
  at the time of this cycle (filename-only check, per workflow Step 3).

## Compatibility considerations

- N/A — new standalone file; no existing consumers to break. Internal Markdown links from
  `part1` must resolve (`docs/02_deployment-operations.md` relative path).

## Security considerations

- N/A — documentation only, no secrets, no executable code shipped; commands shown are the
  same ones already documented elsewhere (`deploy/setup_services.sh`, `deploy/start_agent.sh`).

## Rollback considerations

- Low risk: revert by deleting `docs/02_deployment-operations.md` and restoring the removed
  command block into `docs/02_deployment-part1.md` §2.3 via `git revert`/`git checkout`.

## Validation plan

| Target | Check | Command | Expected |
|---|---|---|---|
| `docs/02_deployment-operations.md` | Content present | `cat docs/02_deployment-operations.md` | Contains startup + health-check commands |
| `docs/02_deployment-part1.md` | Reference pointer present | `grep -n "02_deployment-operations.md" docs/02_deployment-part1.md` | Line found in §2.3 |
| Doc consistency | Internal link check | `uv run check-mcp-docs` (broken-link check portion) | No broken internal Markdown link reported |

## Out of scope

- Any change to `deploy/setup_services.sh`, `deploy/start_agent.sh`, or port/endpoint values.
- Reformatting or renaming unrelated sections of `docs/02_deployment-part1.md`.
- Updates to other `docs/*.md` files.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260803-214500_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-113658
- Related target files: 02_deployment-operations.md
