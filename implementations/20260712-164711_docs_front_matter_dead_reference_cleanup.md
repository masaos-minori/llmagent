# Implementation Procedure: docs/*.md front matter dead-reference cleanup (13 groups, 58 files)

Source plan: `plans/20260712-162714_plan.md`, Implementation step 1-2

## Goal

Remove references to non-existent (pre-split) filenames from the `related:`/`source:` YAML
front-matter lists across 58 documentation files, grouped into 13 clusters by the dead filename
they reference.

## Scope

**In scope:**
- Deleting the exact YAML list line(s) referencing a dead filename, in each of the 58 files below.
- Removing the two duplicate `03_rag_91_design_notes.md` entries in
  `03_rag_91_design_notes-part1.md` / `-part2.md` (each file lists it twice; both occurrences of
  the dead entry are removed, leaving zero occurrences, not one).

**Out of scope:**
- Adding any replacement reference in place of a deleted one (per
  `03_rag_02_02_ingestion_pipeline-crawler-part1.md` / `-part2.md` precedent: delete only, do not
  invent a substitute).
- Any other front-matter field (`title`, `category`, `tags`).
- Body content of any file.
- `docs/04_mcp_03_03_transport-and-health.md`'s eventual split (separate plan,
  `plans/20260712-163522_plan.md` / its implementation docs) — this task only cleans its front
  matter; it must run **before** that file is split.
- `tools/validate_docs_structure.py` changes (separate implementation doc,
  `implementations/20260712-164730_tools_validate_docs_structure_py.md`).

## Assumptions

1. Every file listed below currently exists at `docs/<filename>` — reconfirmed by direct
   `python3`-based front-matter parse at planning time (see Validation plan for the exact
   reproduction script).
2. Deleting a YAML list item only requires removing its `  - <filename>` line under `related:`
   or `source:`; no other reflow of the YAML is needed (each remaining item stays on its own line).

## Implementation

### Target file

68 dead reference-line deletions across 58 distinct `docs/*.md` files. Grouped by the dead
filename referenced (delete the group's dead filename line from every listed file's front matter):

| Dead reference to delete | Files to edit (delete the one line referencing it, in each) |
|---|---|
| `01_overview-arch.md` | `01_overview-arch-01-process.md`, `01_overview-arch-02-pipelines.md`, `01_overview-arch-03-features.md` |
| `01_overview-files.md` | `01_overview-files-01-build.md`, `01_overview-files-02-rag.md`, `01_overview-files-05-config.md`, `01_overview-files-06-misc.md` |
| `01_overview-files-03-scripts.md` | `01_overview-files-01-build.md`, `01_overview-files-02-rag.md`, `01_overview-files-03-scripts-part1.md`, `01_overview-files-03-scripts-part2.md`, `01_overview-files-03-scripts-part3.md`, `01_overview-files-03-scripts-part4.md`, `01_overview-files-03-scripts-part5.md`, `01_overview-files-05-config.md`, `01_overview-files-06-misc.md` |
| `01_overview-files-04-shared.md` | `01_overview-files-01-build.md`, `01_overview-files-02-rag.md`, `01_overview-files-04-shared-part1.md`, `01_overview-files-04-shared-part2.md`, `01_overview-files-05-config.md`, `01_overview-files-06-misc.md` |
| `03_rag_03_query_pipeline-stages.md` | `03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md`, `03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md`, `03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`, `03_rag_03_06_query_pipeline-helpers-and-cache-part2.md`, `03_rag_03_07_query_pipeline-tests.md` |
| `03_rag_91_design_notes.md` (duplicated, delete both occurrences) | `03_rag_91_design_notes-part1.md`, `03_rag_91_design_notes-part2.md` |
| `04_mcp_02_protocol_and_transport.md` | `04_mcp_02_01_endpoints-and-transport.md`, `04_mcp_02_02_startup-modes-and-health.md`, `04_mcp_02_03_audit-logging-and-errors.md` |
| `04_mcp_03_routing_lifecycle_and_execution.md` | `04_mcp_03_01_dispatch-and-routing.md`, `04_mcp_03_02_tool-registry.md`, `04_mcp_03_03_transport-and-health.md`, `04_mcp_03_04_tool-call-tracing-and-watchdog.md`, `04_mcp_03_05_lifecycle-and-new-server.md` |
| `04_mcp_04_server_catalog.md` | `04_mcp_04_01_web-search-file-read-github.md`, `04_mcp_04_02_file-write-file-delete-shell.md`, `04_mcp_04_03_rag-pipeline-and-cicd.md`, `04_mcp_04_04_mdq.md`, `04_mcp_04_05_git.md` |
| `04_mcp_05_security_and_safety_model.md` | `04_mcp_05_01_access-control-and-allowlists.md`, `04_mcp_05_02_auth-profiles-and-sandboxing.md`, `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`, `04_mcp_05_04_mdq-rag-boundary.md`, `04_mcp_05_05_mdq-enforcement-and-lockdown.md` |
| `05_agent_06_tool-execution-and-approval.md` | `05_agent_06_01_tool-execution-and-approval-execution.md`, `05_agent_06_02_tool-execution-and-approval-approval.md`, `05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`, `05_agent_06_04_tool-execution-and-approval-canonical.md` |
| `05_agent_07_cli-and-commands.md` | `05_agent_07_01_cli-and-commands-cli-reference.md`, `05_agent_07_02_cli-and-commands-cliview.md`, `05_agent_07_03_cli-and-commands-command-registry.md`, `05_agent_07_04_cli-and-commands-purpose.md`, `05_agent_07_05_cli-and-commands-repl-io.md`, `05_agent_07_06_cli-and-commands-hot-reload.md`, `05_agent_07_07_cli-and-commands-migration-notes.md`, `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`, `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`, `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`, `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md` |
| `05_agent_12_memory.md` | `05_agent_12_03_memory-module-ref-core-and-store.md`, `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`, `05_agent_12_05_memory-module-ref-extraction-and-facade.md`, `05_agent_12_06_memory-module-ref-ops-and-scoring.md` |

### Procedure

1. For each row above, open every listed file and delete the single YAML line
   `  - <dead-reference-filename>` from wherever it appears (`related:` list, or `source:` list —
   check both; most occurrences are under `related:`, a few files also list the dead name under
   `source:`).
2. For `03_rag_91_design_notes-part1.md` and `-part2.md` specifically: the dead reference
   `03_rag_91_design_notes.md` appears **twice** in each file's front matter (a pre-existing
   duplication bug independent of this task) — delete both occurrences, leaving zero.
3. Do not add any replacement line. Do not touch any other `related:`/`source:` entry that
   points to a real, existing file.
4. Process groups independently — each group/row is an independently committable unit of work
   (per the plan's own framing), but doing all 13 in one pass before validation is also fine
   given the mechanical, low-risk nature of the edit.
5. Skip `04_mcp_03_03_transport-and-health.md`'s eventual deletion/split — this task only edits
   its front matter (removing the `04_mcp_03_routing_lifecycle_and_execution.md` line); the file
   itself still exists as a single file after this task completes.

### Method

For each file, use the `Edit` tool with an `old_string` containing the exact
`  - <dead-filename>` line (plus enough surrounding context to make the match unique if the
file has multiple similar-looking lines) and `new_string` omitting that line entirely.

### Details

- Do not use `sed`/bulk regex replace across files blindly — verify each file's YAML front matter
  by reading it first, since a couple of files may have the dead reference under `source:` rather
  than `related:` (re-check per file rather than assuming the field).
- After editing all 58 files, the re-verification script in Validation plan must print zero output.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Zero remaining dead references | `python3 -c "$(cat <<'PY'\nimport re, os, glob\nexisting = set(os.path.basename(f) for f in glob.glob('docs/*.md'))\nfor path in sorted(glob.glob('docs/*.md')):\n    text = open(path, encoding='utf-8').read()\n    m = re.match(r'^---\\n(.*?)\\n---\\n', text, re.S)\n    if not m:\n        continue\n    for ref in re.findall(r'-\\s*([A-Za-z0-9_\\-]+\\.md)', m.group(1)):\n        if ref not in existing:\n            print(path, '->', ref)\nPY\n)"` | No output |
| RAG doc consistency | `uv run python tools/check_docs_consistency.py` | `All checks passed` |
| No unrelated diffs | `git diff --stat docs/` | Only the 58 listed files appear, each with small (1-2 line) deletions |
