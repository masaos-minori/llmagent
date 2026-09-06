## Goal
Add an entry for `tools/check_canonical_source_registry.py` (seq 02) to
`tools/TOOL_DESCRIPTIONS.md`'s domain-checker table, per REQ-010/AC10.

## Scope
- In scope: one new table row in the "ドメイン別ドキュメント整合性チェッカー" table.
- Out of scope: any other row or section of this file; `check_canonical_source_conflicts.py`'s
  existing entry (row 19, already present — read-only reference for this row's wording,
  not modified here).

## Assumptions
- Seq 02 (`tools/check_canonical_source_registry.py`) lands with the schema described in
  its own procedure document (`implementations/20260906-150039_02_tools_check_canonical_source_registry.py.md`):
  validates the actual registry schema (`decision_target`/`claim_type`/`source_paths`/
  `area`/`notes`), checks path existence, enforces the single-source-vs-multi-file
  constraint, validates claim type against `M-01-01`'s 13 types, and checks ADR
  `## Status` for `architecture-decision` entries. This row's wording describes that
  tool's actual behavior, not this Plan's original (superseded) schema proposal.
- `check_canonical_source_conflicts.py` is already documented at row 19 of this same
  table, and its own description already notes it "wraps" a registry validator by
  that name — this row's addition makes that referenced tool exist and documented.

## Design decisions
- Match the existing table's exact column format (`| ファイル | 対象ドメイン | 主なチェック内容 |`)
  and Japanese-language description style already used by every other row in this
  table (e.g. `check_canonical_source_conflicts.py`'s own row) — this file is written
  in Japanese throughout; do not introduce an English-only row inconsistent with its
  neighbors.
- Place the new row immediately before or after `check_canonical_source_conflicts.py`'s
  existing row (row 19) — keeps the two related Canonical-Source-Registry tools
  adjacent for a reader scanning the table.

## Alternatives considered
- Add the row in a separate new table/section instead of the existing domain-checker
  table: rejected — this tool is a `docs/`-adjacent governance checker in the same
  vein as `check_needs_confirmation_inventory.py`/`check_canonical_source_conflicts.py`
  already in this table; a new section would fragment the inventory this file's own
  stated purpose (single system of record for `tools/*.py` descriptions, cross-checked
  by `check_tool_descriptions_sync.py`) exists to avoid.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Re-confirm seq 02 has landed with its actual final function/check set before
   writing this row's description (re-read that file directly rather than trusting
   this document's paraphrase, since a schema decision could still shift before
   implementation).
2. Add one new row to the "ドメイン別ドキュメント整合性チェッカー" table, adjacent to
   `check_canonical_source_conflicts.py`'s existing row (currently row 19), in the
   same `| ファイル | 対象ドメイン | 主なチェック内容 |` format:
   `| \`check_canonical_source_registry.py\` | \`config/documentation_canonical_sources.toml\` |
   Canonical Source Registryのスキーマ検証(バージョン付きdataclass定義)。登録された
   `source_paths`のリポジトリルート相対パス実在確認、単一正典ソース制約(`runtime-behavior`
   等の複数ファイル許容claim-type以外は1パスのみ)、`M-01-01`の13 claim-type網羅性検証、
   ADR由来エントリの`## Status`が`Accepted`であることの検証。`load_registry()`/
   `validate_registry_schema()`は`check_canonical_source_conflicts.py`から再利用される |`
3. Run `uv run python tools/check_tool_descriptions_sync.py` to confirm this addition
   satisfies the sync check (AC10, Tests section).

### Method
Confirmed this cycle (2026-09-06) via direct read: the table's exact column format
and Japanese-description convention (lines 13-28); `check_canonical_source_conflicts.py`'s
own existing row (line 19) already references a registry validator by the name this
row adds; `check_canonical_source_registry.py` itself does not yet appear anywhere in
this file (confirmed via `grep`) — genuinely new addition, not a duplicate.

### Details
No change to any other row.

## Compatibility considerations
Additive-only; `check_tool_descriptions_sync.py` is the automated check that
verifies this file stays in sync with actual `tools/*.py` files — re-run it after
this row lands.

## Security considerations
N/A.

## Rollback considerations
Revert via `git checkout` on this file alone if `check_tool_descriptions_sync.py`
flags an issue.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` — exits 0, no drift.

## Completion criteria
- A new row for `tools/check_canonical_source_registry.py` exists in the domain-checker
  table, matching its actual landed behavior.
- `check_tool_descriptions_sync.py` passes.

## Out of scope
- `routing.md`'s "When to run which tool" table — tracked in seq 07 (this same
  fork's other row).
- `tools/check_canonical_source_registry.py` itself — tracked in seq 02.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-010
- **Source issue**: issues/20260903-103027_m0104_introduce-machine-readable-canonical-source-registry.md
- **Source plan**: plans/20260905-165405_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-150039
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
