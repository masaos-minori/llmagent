# Implementation: docs/04_mcp_04_03_rag-pipeline-and-cicd.md — update requires_config mention to config_dependent

Source plan: `plans/20260717-173602_plan.md` ("Replace requires_config with config_dependent in MCP tool definitions")

Note: `implementations/done/20260716-141744_04_mcp_04_03_rag-pipeline-and-cicd_toolcount_removal.md.md`
matches this filename but its Goal is unrelated ("Remove the `（4個）`
parenthetical from both `**ツール（4個）:**` headings") — a stale filename
match, not covering the `requires_config` rename. Treated as
not-already-implemented.

## Goal

Update the 1 inline mention of `requires_config` in
`docs/04_mcp_04_03_rag-pipeline-and-cicd.md` (a table column header) to
`config_dependent`. Text-only change.

## Scope

**In scope**: the 1 occurrence at line 77 of this file (the cicd tools
table header).

**Out of scope**: any other content, including the `rag_pipeline` tools
section of this same doc (that server has no `requires_config`/
`config_dependent` field at all — out of scope per the plan's own Scope
section).

## Assumptions

- Pure text substitution of the table column header; table body values
  (`yes`) are unaffected since they don't repeat the field name literally.
- This doc covers both `rag_pipeline` and `cicd` tools; only the `cicd`
  table has this column (confirmed via grep — single match in the whole
  file).

## Implementation

### Target file

`/home/sugimoto/llmagent/docs/04_mcp_04_03_rag-pipeline-and-cicd.md`

### Procedure

1. Line 77 (table header row): `| ツール | ティア | 入力 |
   `requires_config` |` -> replace the `requires_config` column header with
   `config_dependent`; leave other columns unchanged.

### Method

Literal text find-and-replace of `requires_config` -> `config_dependent` at
the single identified line (verified via `grep -n "requires_config"
docs/04_mcp_04_03_rag-pipeline-and-cicd.md` — exactly 1 match).

### Details

- Table body row below (e.g. `| `trigger_workflow` | WRITE_DANGEROUS |
  `{repo, workflow, ref?, inputs?}` | yes |`) contains only `yes` values, not
  the literal field name, so no further edits needed.
- Post-edit: `grep -n "requires_config"
  docs/04_mcp_04_03_rag-pipeline-and-cicd.md` -> 0 matches;
  `grep -c "config_dependent" docs/04_mcp_04_03_rag-pipeline-and-cicd.md`
  -> 1.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Residual check (this file) | `grep -n "requires_config" docs/04_mcp_04_03_rag-pipeline-and-cicd.md` | 0 matches |
| New term present | `grep -c "config_dependent" docs/04_mcp_04_03_rag-pipeline-and-cicd.md` | 1 |

Full cross-file validation is covered by the cross-cutting doc
`full_validation_pass_config_dependent_rename.md`.
