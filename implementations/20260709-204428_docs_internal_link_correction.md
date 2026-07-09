# Implementation Procedure: Internal Link and Section Number Batch Correction

## Goal

Correct all internal links and section numbers across the entire `docs/` directory after file splitting operations, including references in `routing.md`.

## Scope

### In scope

- Update all internal links (`[text](*.md)`, `[text](./file.md)`, etc.) within `docs/` files to reflect new filenames after splitting
- Update all anchor references to new section headings after splitting
- Update all cross-references between split files to point to correct new locations
- Update all references in `routing.md` Docs→task mapping to follow new file names
- Verify no ambiguous reference expressions remain (e.g., "see above", "see below")

### Out of scope

- Modifying source code or scripts outside `docs/`
- Creating new content beyond link corrections
- Fixing non-internal links (external URLs, etc.)

## Assumptions

1. All original internal links pointed to real files; no broken links existed before splitting.
2. After splitting, some original filenames no longer exist and must be updated to new filenames.
3. Anchor references (HTML anchors generated from section headings) may have changed due to filename changes.
4. `routing.md` contains fixed path references to `docs/*.md` files that must be updated.

## Implementation

### Target files

All markdown files under `docs/` directory plus `routing.md`:

- `docs/01_overview.md`
- `docs/02_deployment.md`
- `docs/01_overview-arch-process.md`, `docs/01_overview-arch-pipelines.md`, `docs/01_overview-arch-features.md`
- `docs/01_overview-files-build.md`, `docs/01_overview-files-rag.md`, `docs/01_overview-files-scripts.md`, `docs/01_overview-files-shared.md`, `docs/01_overview-files-config.md`, `docs/01_overview-files-misc.md`
- All RAG set files (`docs/03_rag_*.md`)
- All MCP set files (`docs/04_mcp_*.md`)
- All Agent set files (`docs/05_agent_*.md`)
- All Event Bus set files (`docs/06_eventbus_*.md`)
- All Shared/DB set files (`docs/90_shared_*.md`)
- `docs/index.md`
- `routing.md`

### Procedure

#### Step 1: Identify changed filenames

1. Compare original filenames against new filenames for each category set
2. Create a mapping table of old → new filenames per category

Example mapping for Agent set:
```
05_agent_03_turn-processing-flow.md → 05_agent_03_turn-processing-flow-part1.md, 05_agent_03_turn-processing-flow-part2.md
05_agent_12_memory.md → 05_agent_12_memory-layer.md, 05_agent_12_memory-store.md, 05_agent_12_memory-retriever.md, 05_agent_12_memory-extract.md
```

#### Step 2: Scan for internal links

For each file under `docs/`:

1. Search for all internal link patterns:
   - `[text](filename.md)` — relative links
   - `[text](#section-name)` — anchor links
   - `[text](../other/file.md)` — parent directory links
   - `[text](./subdir/file.md)` — subdirectory links
2. Record each link found with its line number and current target

#### Step 3: Update links by pattern

For each identified link:

1. If the link target filename has been renamed:
   - Update to the new filename(s) if one-to-one mapping exists
   - Update to the most appropriate new file if one-to-many mapping exists
   - Consider adding a note about the split if multiple targets exist
2. If the link target section heading has changed:
   - Update the anchor reference to match the new section heading
3. If the link target file no longer exists (was deleted during splitting):
   - Update to point to the most relevant new file(s)

#### Step 4: Handle ambiguous references

1. Search for ambiguous reference expressions:
   - "see above", "see below", "as mentioned earlier", "described previously"
   - Japanese equivalents: "前述", "後述", "上記", "以下"
2. Replace ambiguous references with explicit file/section references where possible

#### Step 5: Update routing.md

1. Read the full content of `routing.md`
2. Find all references to `docs/*.md` files in the Docs→task mapping section
3. Update each reference to point to the new file names after splitting
4. Ensure no broken references remain in `routing.md`

#### Step 6: Verify all links

1. For each file under `docs/`:
   - Extract all internal link targets
   - Verify each target file exists using `test -f` or similar
   - Report any broken links

### Method

- **Automated scanning**: Use regex-based search to find all internal link patterns across all files
- **Manual verification**: Manually verify each link update for correctness, especially for one-to-many mappings
- **Ambiguity elimination**: Replace all vague references with explicit file/section references

### Details

#### Internal link patterns to scan

```regex
\[([^\]]+)\]\(([^)]+\.md)\)
```

This matches Markdown links where the target ends with `.md`.

#### Verification command

After updating all links, run:

```bash
for file in docs/*.md; do
    grep -oP '\[([^\]]+)\]\(\K([^)]+\.md)' "$file" | while read -r link; do
        # Resolve relative paths
        dir=$(dirname "$file")
        target="$dir/$link"
        if [ ! -f "$target" ]; then
            echo "Broken link in $file: $link"
        fi
    done
done
```

#### Special considerations

1. **One-to-many splits**: When a single file is split into multiple files, choose the most relevant target file for each link. If ambiguity cannot be resolved, add a note like "(see also: see also: [File Part 2](file-part2.md))".
2. **Anchor consistency**: Ensure anchor references use the exact section heading text (case-sensitive, with spaces replaced by hyphens).
3. **routing.md priority**: This file is critical for context loading in other tasks. Ensure all updates here are accurate and complete.

## Validation Plan

| Check | Method | Target |
|---|---|---|
| Internal links in docs/ | Automated link existence check | Zero broken links |
| routing.md references | Manual review + automated check | Zero broken references |
| Ambiguous references | Search for vague expressions | Zero ambiguous references |
| Anchor consistency | Verify anchor text matches section headings | All anchors valid |
| Cross-reference accuracy | Spot-check random links across categories | Links resolve correctly |
