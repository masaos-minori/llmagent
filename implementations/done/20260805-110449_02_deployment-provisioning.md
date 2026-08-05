# Implementation Procedure: 02_deployment-provisioning.md

## Goal

Establish `docs/02_deployment-provisioning.md` as the single authoritative runbook for
OS-level provisioning (Gentoo package installation) and the llama.cpp build, extracted
verbatim from `docs/02_deployment-part1.md`, per `plans/20260802-121203_plan.md`.

## Scope

- In scope: content of `docs/02_deployment-provisioning.md` (package list + `emerge`
  command; llama.cpp `git clone` + `cmake` build commands).
- Out of scope: editing `docs/02_deployment-part1.md` itself — that side of the plan is
  already covered by `implementations/20260805-110139_02_deployment-part1.md`.

## Assumptions

- `docs/02_deployment-part1.md` §1.1 and §1.3 already contain pointers to
  `docs/02_deployment-provisioning.md` (verified by inspection during this procedure's
  creation) — the sqlite3 USE-flag design note remains in part1 §1.1 as required.
- `docs/02_deployment-provisioning.md` already exists on disk with the expected content
  (verified by inspection). No matching filename existed under `implementations/` or
  `implementations/done/`, so per the workflow's filename-matching rule this procedure
  document is created regardless of the doc's current on-disk state — this document
  records the intended procedure and its post-hoc verification.

## Design decisions

- One dedicated file for mechanical OS/build steps only, kept separate from part1's
  design narrative (separation of concerns between "why" and "how to install").
- Content extracted verbatim (no rewriting) from part1's original §1.1/§1.3 to avoid
  introducing command drift during relocation.

## Alternatives considered

- Keep provisioning steps inline in part1 — rejected; contradicts the plan's objective
  of separating design narrative from mechanical install steps.
- Split into two separate runbooks (packages vs. build) — rejected as unnecessary
  granularity; the plan specifies a single provisioning runbook.

## Implementation

### Target file

`docs/02_deployment-provisioning.md`

### Procedure

1. Verify the file exists; create it if missing.
2. Verify/populate a "Package Installation (Gentoo Linux)" section with the package list
   and `emerge --ask ...` command extracted verbatim from part1 §1.1.
3. Verify/populate an "llama.cpp Build" section with the `git clone` and `cmake` build
   commands extracted verbatim from part1 §1.3.
4. Cross-check that part1 §1.1/§1.3 point to this file and that the sqlite3 USE-flag
   note remains in part1 §1.1 (tracked by the separate part1 implementation procedure,
   not modified here).

### Method

Manual Markdown edit; no code or tooling involved. Verification via `grep` for pointer
text and section headers across both files.

### Details

- part1 §1.1 currently reads: "OSのパッケージ導入手順については、
  [docs/02_deployment-provisioning.md](docs/02_deployment-provisioning.md) を参照してください。"
  followed by the preserved sqlite3 note (`docs/02_deployment-part1.md` lines 20-26).
- part1 §1.3 currently reads: "ビルド手順については、
  [docs/02_deployment-provisioning.md](docs/02_deployment-provisioning.md) を参照してください。"
  (`docs/02_deployment-part1.md` line 40).
- `docs/02_deployment-provisioning.md` currently contains "## 1. Package Installation
  (Gentoo Linux)" with the `emerge --ask sys-devel/gcc sys-devel/make dev-util/cmake
  dev-util/ninja dev-db/sqlite dev-lang/python:3.13 dev-libs/libxml2 dev-libs/libxslt
  dev-vcs/git` command, and "## 2. llama.cpp Build" with the `git clone
  https://github.com/ggerganov/llama.cpp.git /opt/llm/llama.cpp` plus `cmake -B build
  ...` / `cmake --build build ...` commands.

## Compatibility considerations

- Purely additive/organizational Markdown change; no impact on runtime code, config
  files, or deployment scripts.
- Part1's section headers (§1.1, §1.3) are unchanged, so any existing external
  cross-references to those anchors remain valid; only body content moved.

## Security considerations

N/A — documentation reorganization only; no secrets, credentials, or executable code
are introduced or changed.

## Rollback considerations

- Revert via `git revert` of the commit(s) that introduced the split, or manually
  restore part1's original inline package-list/build commands and delete
  `docs/02_deployment-provisioning.md`.
- Low risk: single new file plus a pointer replacement confined to one existing file.

## Validation plan

- `grep -n "provisioning" docs/02_deployment-part1.md` — confirm both pointers present.
- Manual read-through of `docs/02_deployment-provisioning.md` — confirm package list and
  llama.cpp build commands match part1's original content verbatim (no command drift).
- `grep -n "sqlite3" docs/02_deployment-part1.md` — confirm the USE-flag note is still
  present in §1.1.
- Not applicable: the Python validation sequence in `rules/toolchain.md` (ruff/mypy/
  pytest/bandit/etc.) does not apply to a docs-only change. Optionally run
  `uv run check-mcp-docs` / `tools/check_agent_docs_consistency.py` for broken-link
  checks; no MCP tool/port references are involved here so no findings are expected.

## Out of scope

- Modifying `docs/02_deployment-part1.md` content — covered by
  `implementations/20260805-110139_02_deployment-part1.md`.
- Moving `requires/20260802-121203_require.md` to `requires/done/` (plan Step 5) — this
  is an administrative cleanup step belonging to a different pipeline stage; this
  workflow's Step 4 moves only the source plan file.
- `docs/02_deployment-operations.md`, `docs/02_deployment-part2.md` — unrelated, not
  touched.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260802-121203_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-110449
- Related target files: 02_deployment-provisioning.md
