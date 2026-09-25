#!/usr/bin/env python3
"""Generate implementation procedure documents for docs reorganization plans."""

import os
import sys
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
IMPL_DIR = REPO_ROOT / "implementations"
PLAN_DIR = REPO_ROOT / "plans"

def slugify(path_str: str) -> str:
    """Convert a file path to a slug."""
    result = path_str.replace("/", "_")
    result = re.sub(r"[^a-zA-Z0-9_\-.]", "_", result)
    return result

def extract_rows(plan_content: str) -> list[tuple[str, str, str]]:
    """Extract Implementation Target Files rows."""
    rows = []
    in_table = False
    header_seen = False
    
    for line in plan_content.split("\n"):
        if "**Freeze status**:" in line:
            in_table = True
            continue
        
        if not in_table:
            continue
        
        # Stop at blank line after prose
        if line.strip() == "" and not header_seen:
            continue
        
        # Skip prose lines between Freeze status and table
        if in_table and not header_seen and "|" not in line:
            continue
        
        # Detect table header (contains pipe-separated column names)
        if in_table and not header_seen and line.startswith("|") and "---" not in line:
            parts = [p.strip() for p in line.strip("|").split("|")]
            if any("File Path" in p for p in parts):
                header_seen = True
            continue
        
        # Skip separator line
        if in_table and header_seen and "---" in line:
            continue
        
        # Parse data rows
        if in_table and header_seen and line.startswith("|") and line.endswith("|"):
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) >= 3:
                file_path = parts[0]
                change_resp = parts[1]
                related_req = parts[3] if len(parts) > 3 else ""
                rows.append((file_path, change_resp, related_req))
        
        # Stop at next section
        if in_table and header_seen and line.startswith("## "):
            break
    
    return rows

def get_source_issue(plan_content: str) -> str:
    """Extract Source issue from Traceability section."""
    match = re.search(r"- \*\*Source issue\*\*: (.+)", plan_content)
    return match.group(1).strip() if match else "N/A"

def create_document(plan_id: str, seq: int, target_file: str, change_resp: str, 
                    related_req: str, source_issue: str, timestamp: str) -> tuple[str, str]:
    """Create the content of an implementation procedure document."""
    target_slug = slugify(target_file)
    filename = f"{timestamp}_{seq:02d}_{target_slug}.md"
    
    dest = ""
    op_type = "other"
    if "Move to" in change_resp:
        dest_match = re.search(r"Move to (.+)", change_resp)
        dest = dest_match.group(1).strip() if dest_match else ""
        op_type = "move"
    elif "Update" in change_resp:
        op_type = "update"
    elif "Validate" in change_resp:
        op_type = "validate"
    elif "Confirm" in change_resp:
        op_type = "confirm"
    
    # Goal
    if op_type == "move":
        goal = f"Move `{target_file}` to `{dest}` using `git mv`, preserving file history."
    elif op_type == "update":
        goal = f"Update `{target_file}`: {change_resp}"
    elif op_type == "validate":
        goal = f"Validate `{target_file}` after the docs reorganization."
    elif op_type == "confirm":
        goal = f"Confirm `{target_file}` path references are correct per docsreorg04."
    else:
        goal = f"Process `{target_file}`: {change_resp}"
    
    # Procedure
    if op_type == "move":
        procedure = f"`git mv {target_file} {dest}`"
    elif op_type == "update":
        if "EXPECTED_WITHIN_FILE_PAIRS" in change_resp:
            procedure = ("Update `EXPECTED_WITHIN_FILE_PAIRS` keys in the test file.\n\n"
                        "For each entry keyed to the moved ADR/eventbus/RAG/MCP/Agent files:\n"
                        "- Change old path prefix (e.g. `adr/ADR-NNN-*.md`) to new path prefix (e.g. `10_adr/ADR-NNN-*.md`)\n"
                        "- Update flat-file prefixes (e.g. `06_eventbus_*` → `24_eventbus/*`)\n"
                        "- Verify the count matches the plan's assertion")
        elif "command arg" in change_resp.lower():
            procedure = ("Update the command argument in the CI workflow YAML file.\n\n"
                        "- Old: `docs/03_rag_*.md`\n- New: `docs/21_rag/03_rag_*.md`\n"
                        "Note: The paths filter was already updated by docsreorg03; only the command argument needs updating.")
        else:
            procedure = f"Edit `{target_file}`: {change_resp}"
    elif op_type == "validate":
        if "entire tree" in target_file.lower() or target_file == "docs/":
            procedure = ("Run validation commands against the fully-reorganized `docs/` tree.\n\n"
                        "1. `uv run python tools/check_docs_structure.py \"docs/**/*.md\" --schema schemas/doc_front_matter.json`\n"
                        "2. `uv run python -m tools.check_docs_quality`\n"
                        "3. `uv run pre-commit run --all-files`\n"
                        "4. `uv run pytest -q`\n"
                        "5. Verify 5 workflows triggered correctly via `gh workflow view <name> --yaml`\n"
                        "6. Check no file remains under old flat locations or old subdirectories")
        elif "tools/" in target_file.lower():
            procedure = ("Verify all 9 tools touched by docsreorg02 are operational.\n\n"
                        "Run: `uv run python -m tools.check_docs_quality`\n"
                        "Expected: Passes or reports only pre-existing unrelated findings.")
        elif ".github/workflows/" in target_file.lower():
            procedure = ("Verify CI triggers on new paths.\n\n"
                        "For each of the 5 workflows updated by docsreorg03:\n"
                        "- `agent-docs-consistency.yml`, `overview-docs-consistency.yml`, `deployment-docs-consistency.yml`, `rag-docs-consistency.yml`, `rag-docs-quality.yml`\n"
                        "- Inspect trigger paths via `gh workflow view <name> --yaml`\n"
                        "- Note: `rag-docs-quality.yml` line 35 command argument still references `docs/03_rag_*.md` while its paths filter was updated to `docs/21_rag/03_rag_*.md` — report as gap against docsreorg13.")
        elif "tests/" in target_file.lower():
            procedure = ("Verify full test suite passes.\n\n"
                        "Run: `uv run pytest -q`\n"
                        "Expected: All tests pass.")
        else:
            procedure = f"Validate `{target_file}`."
    elif op_type == "confirm":
        procedure = ("Verify `{target_file}` line 23 paths already point at `docs/22_mcp/` (or `docs/23_agent/`) per docsreorg04.\n\n"
                    "No modification needed — just confirm the paths are correct.")
    else:
        procedure = f"Process `{target_file}`: {change_resp}"
    
    # Method
    method_map = {"move": "File move via `git mv`", "update": "Text replacement in existing file",
                  "validate": "Execute validation commands", "confirm": "Path verification"}
    method = method_map.get(op_type, "Other processing")
    
    # Details
    details = ""
    if op_type == "move":
        details = (f"- Old location: `{target_file}`\n- New location: `{dest}`\n"
                   "- Use `git mv` to preserve file history\n"
                   f"- After move, verify with `git log --follow {dest.lstrip('docs/')}`")
    elif op_type == "update":
        if "EXPECTED_WITHIN_FILE_PAIRS" in change_resp:
            if "adr" in target_file.lower() or "ADR" in target_file:
                details = ("- Update all 54 keys from `adr/ADR-NNN-*.md` to `10_adr/ADR-NNN-*.md`\n"
                          "- Keys cover: ADR-001 through ADR-010, ADR-012 through ADR-014\n"
                          "- Run `uv run python -m tools.check_docs_quality` after update to verify")
            elif "eventbus" in target_file.lower():
                details = ("- Update 34 keys from bare `06_eventbus_*.md` filenames to `24_eventbus/06_eventbus_*.md`\n"
                          "- Update 9 keys from `eventbus/*.md` to `24_eventbus/*.md`\n"
                          "- Total: 43 entries\n"
                          "- Run `uv run python -m tools.check_docs_quality` after update to verify")
            elif "rag" in target_file.lower():
                details = ("- Update all 26 keys from bare `03_rag_*.md` filenames to `21_rag/03_rag_*.md`\n"
                          "- Key breakdown: `03_rag_02_04_ingestion_pipeline-ingester.md`(9), `03_rag_05_2-execution-guide.md`(8), `03_rag_02_01_ingestion_pipeline-overview.md`(5), `03_rag_02_03_ingestion_pipeline-chunksplitter.md`(2), `03_rag_03_06_query_pipeline-helpers-and-cache.md`(1), `03_rag_03_02_query_pipeline-rag-pipeline-class.md`(1)\n"
                          "- Run `uv run python -m tools.check_docs_quality` after update to verify")
            elif "mcp" in target_file.lower():
                details = ("- Update all 23 keys from bare `04_mcp_*.md` filenames to `22_mcp/04_mcp_*.md`\n"
                          "- Key breakdown: `04_mcp_05_01_access-control-and-allowlists.md`(21), `04_mcp_06_13_watchdog-health-reasons-scheduling.md`(1), `04_mcp_06_07_reading-audit-logs.md`(1)\n"
                          "- Run `uv run python -m tools.check_docs_quality` after update to verify")
            elif "agent" in target_file.lower():
                details = ("- Update all 29 keys from bare `05_agent_*.md` filenames to `23_agent/05_agent_*.md`\n"
                          "- Key breakdown: `05_agent_13_reference-api.md`(6), `05_agent_08_01_configuration-loading-agent-config.md`(3), `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`(3), `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`(3), `05_agent_02_runtime-architecture.md`(3), remaining 10 files: 1 entry each\n"
                          "- Run `uv run python -m tools.check_docs_quality` after update to verify")
            else:
                details = f"- Update EXPECTED_WITHIN_FILE_PAIRS keys for `{target_file}`\n- Run `uv run python -m tools.check_docs_quality` after update to verify"
        elif "command arg" in change_resp.lower():
            details = ("- Line 35: change `docs/03_rag_*.md` to `docs/21_rag/03_rag_*.md`\n"
                      "- The paths filter was already updated by docsreorg03\n"
                      "- Only the command argument needs updating")
        else:
            details = f"- Edit `{target_file}`: {change_resp}"
    elif op_type == "validate":
        if "entire tree" in target_file.lower() or target_file == "docs/":
            details = ("- `uv run python tools/check_docs_structure.py \"docs/**/*.md\" --schema schemas/doc_front_matter.json` — zero findings beyond pre-existing\n"
                      "- `uv run python -m tools.check_docs_quality` — passes or reports only pre-existing\n"
                      "- `uv run pre-commit run --all-files` — passes\n"
                      "- `uv run pytest -q` — all tests pass\n"
                      "- 5 workflows verified via `gh workflow view <name> --yaml`\n"
                      "- No files remain under old flat locations or old subdirectories")
        elif "tools/" in target_file.lower():
            details = ("- `uv run python -m tools.check_docs_quality` — passes or reports only pre-existing\n"
                      "- All 9 tools confirmed operational during docsreorg02 execution")
        elif ".github/workflows/" in target_file.lower():
            details = ("- `gh workflow view agent-docs-consistency --yaml`\n"
                      "- `gh workflow view overview-docs-consistency --yaml`\n"
                      "- `gh workflow view deployment-docs-consistency --yaml`\n"
                      "- `gh workflow view rag-docs-consistency --yaml`\n"
                      "- `gh workflow view rag-docs-quality --yaml` — note: line 35 command arg mismatch must be reported")
        elif "tests/" in target_file.lower():
            details = ("- `uv run pytest -q` — all tests pass\n"
                      "- Full test suite confirmed passing during docsreorg02 execution")
        else:
            details = f"- Validate `{target_file}`"
    elif op_type == "confirm":
        details = ("- No modification required\n- Just verify the path references are correct")
    else:
        details = f"- Process `{target_file}`: {change_resp}"
    
    # Validation plan
    validation = "| Target | Strategy | Command | Expected |\n|---|---|---|---|"
    if op_type == "move":
        validation += f"\n| `{dest.lstrip('docs/')}` | Integration: verify git history preserved | `git log --follow {dest.lstrip('docs/')}` | Continuous history shown |"
    elif op_type == "update":
        if "EXPECTED_WITHIN_FILE_PAIRS" in change_resp:
            validation += ("\n| `test_check_docs_quality.py` | Unit: verify baseline updated | `uv run python -m tools.check_docs_quality` | Passes or reports only pre-existing findings |\n"
                          "| `test_check_docs_quality.py` | Unit: verify test passes | `uv run pytest tests/tools/test_check_docs_quality.py -q` | Tests pass |")
        elif "command arg" in change_resp.lower():
            validation += ("\n| `.github/workflows/rag-docs-quality.yml` | Integration: verify CI trigger | `gh workflow view rag-docs-quality --yaml` | Trigger paths include `docs/21_rag/03_rag_*.md` |")
        else:
            validation += f"\n| `{target_file}` | Integration: verify update applied | Manual review | Changes match plan requirements |"
    elif op_type == "validate":
        if "entire tree" in target_file.lower() or target_file == "docs/":
            validation += ("\n| `docs/` tree | Integration: verify structure | `uv run python tools/check_docs_structure.py \"docs/**/*.md\" --schema schemas/doc_front_matter.json` | Zero findings beyond pre-existing |\n"
                          "| tools/ | Integration: verify functionality | `uv run python -m tools.check_docs_quality` | Passes or reports only pre-existing |\n"
                          "| .github/workflows/ | Integration: verify CI triggers | `gh workflow view <name> --yaml` | Trigger paths include new folder paths |\n"
                          "| tests/ | Integration: verify full suite | `uv run pytest -q` | All tests pass |")
        elif "tools/" in target_file.lower():
            validation += ("\n| tools/ | Integration: verify functionality | `uv run python -m tools.check_docs_quality` | Passes or reports only pre-existing |")
        elif ".github/workflows/" in target_file.lower():
            validation += ("\n| .github/workflows/ | Integration: verify CI triggers | `gh workflow view <name> --yaml` | Trigger paths include new folder paths |")
        elif "tests/" in target_file.lower():
            validation += ("\n| tests/ | Integration: verify full suite | `uv run pytest -q` | All tests pass |")
        else:
            validation += f"\n| `{target_file}` | Integration: verify operation | N/A | Operation succeeds |"
    elif op_type == "confirm":
        validation += f"\n| `{target_file}` | Verification: confirm paths | Manual review / `rg` | Paths point to new location |"
    else:
        validation += f"\n| `{target_file}` | Integration: verify operation | N/A | Operation succeeds |"
    
    # Completion criteria
    completion = ""
    if op_type == "move":
        completion = (f"- File exists at `{dest}`\n"
                     f"- `git log --follow {dest.lstrip('docs/')}` shows continuous history\n"
                     f"- No orphaned file remains at `{target_file}`")
    elif op_type == "update":
        if "EXPECTED_WITHIN_FILE_PAIRS" in change_resp:
            completion = ("- All keys in `EXPECTED_WITHIN_FILE_PAIRS` updated from old to new path prefix\n"
                         "- `uv run python -m tools.check_docs_quality` passes\n"
                         "- `uv run pytest tests/tools/test_check_docs_quality.py -q` passes")
        elif "command arg" in change_resp.lower():
            completion = ("- Command argument on line 35 changed from `docs/03_rag_*.md` to `docs/21_rag/03_rag_*.md`\n"
                         "- CI workflow trigger verified")
        else:
            completion = f"- `{target_file}` updated as specified in `{related_req}`"
    elif op_type == "validate":
        completion = "- All validation commands pass with expected results\n- No new findings introduced by reorganization"
    elif op_type == "confirm":
        completion = "- Path references confirmed correct per docsreorg04\n- No further action needed"
    else:
        completion = f"- `{target_file}` processed successfully"
    
    req_short = related_req if related_req else "N/A"
    
    doc = f"""## Goal

{goal}

## Scope

Move/update `{target_file}` as part of the docs/ reorganization. This is a pure documentation reorganization — no code changes beyond what the plan specifies.

## Assumptions

- `docsreorg01` and `docsreorg02` have landed before merging this move (confirmed via repository evidence).
- The plan's `Implementation Target Files` table is accurate and frozen.
- No filename collision exists between moved files.

## Design decisions

- Use `git mv` for all moves to preserve file history.
- Do not rename any files during the move.
- Test baselines must be updated alongside file moves.

## Alternatives considered

- Using `mv` instead of `git mv`: rejected because `git mv` preserves file history.
- Renaming files during the move: rejected because the plan explicitly forbids renaming.

## Implementation

### Target file

`{target_file}`

### Procedure

{procedure}

### Method

{method}

### Details

{details}

## Compatibility considerations

- Moving files without updating test baselines could cause test failures.
- CI workflows that reference moved files need their path filters updated (handled separately by docsreorg03).
- Tool constants pointing at moved directories need updating (handled by docsreorg02).

## Security considerations

N/A: Documentation reorganization does not introduce security risks.

## Rollback considerations

- To rollback, use `git revert` on the commit that performed the move.
- After rollback, restore the original file locations and revert test baseline updates.
- Revert CI workflow path filter changes if they were part of the same commit.

## Validation plan

{validation}

## Completion criteria

{completion}

## Out of scope

- Any filename change including not renaming files.
- Filling numbering gaps (e.g., ADR-011).
- Content edits beyond what other issues cover.
- Pre-existing broken body links tracked separately.

## Execution Status

### Execution Status

### Blocker Log

### Work Items Created

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: {req_short}: {change_resp.split(':')[0] if ':' in change_resp else change_resp[:50]}
- **Source issue**: {source_issue}
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/{plan_id}_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: {timestamp}
- **Related target files**: {target_file}
"""
    return filename, doc

def main():
    timestamp = "20260925-111411"
    
    if len(sys.argv) > 1:
        plan_ids = [sys.argv[1]]
    else:
        plan_ids = sorted([f.replace("_plan.md", "") for f in os.listdir(PLAN_DIR) 
                          if f.endswith("_plan.md")])
    
    created_count = 0
    
    for plan_id in plan_ids:
        plan_path = PLAN_DIR / f"{plan_id}_plan.md"
        if not plan_path.exists():
            print(f"Plan not found: {plan_path}")
            continue
        
        plan_content = plan_path.read_text()
        source_issue = get_source_issue(plan_content)
        
        rows = extract_rows(plan_content)
        print(f"\n=== Processing plan: {plan_id} ({len(rows)} target files) ===")
        
        for seq, (file_path, change_resp, related_req) in enumerate(rows, start=1):
            filename, content = create_document(
                plan_id, seq, file_path, change_resp, related_req,
                source_issue, timestamp
            )
            
            impl_path = IMPL_DIR / filename
            if impl_path.exists():
                print(f"  SKIP (exists): {filename}")
                continue
            
            impl_path.write_text(content)
            print(f"  CREATED: {filename}")
            created_count += 1
    
    print(f"\nTotal created: {created_count}")

if __name__ == "__main__":
    main()
