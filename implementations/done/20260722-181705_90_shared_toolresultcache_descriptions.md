## Goal

Reduce excessive descriptions of unused components like ToolResultCache that are not used in production.

## Scope

- Update `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md` — reduce ToolResultCache description (lines 112-138)
- Update `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md` — reduce ToolResultCache description (lines 47-71)
- Update `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md` — reduce ToolResultCache references (lines 114, 132)

## Assumptions

1. The existing documentation structure and content are correct; only the excessive descriptions need reduction
2. ToolResultCache is not used by ToolExecutor (confirmed via grep)
3. It's a standalone LRU+TTL cache utility kept for future use without stampede protection

## Design decisions

- Reduce each ToolResultCache description to 1-2 sentences noting it exists as a standalone utility but is not used by ToolExecutor
- Keep the essential information about what ToolResultCache is while removing unnecessary details

## Alternatives considered

- Removing ToolResultCache descriptions entirely
- Adding inline notes within existing sections instead of reducing them

## Implementation

### Target files

- `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md`
- `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md`
- `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md`

### Procedure

#### Step 1: Reduce ToolResultCache description in types/DTOs doc

1. Open `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md`
2. Find lines 112-138 (the ToolResultCache description)
3. Replace with:

```markdown
**ToolResultCache**: Standalone LRU+TTL cache utility for tool results. Not currently used by ToolExecutor; kept for potential future use without stampede protection.
```

#### Step 2: Reduce ToolResultCache description in caching doc part 1

1. Open `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md`
2. Find lines 47-71 (the ToolResultCache description)
3. Replace with:

```markdown
**ToolResultCache**: Standalone LRU+TTL cache utility for tool results. Not currently used by ToolExecutor; kept for potential future use without stampede protection.
```

#### Step 3: Reduce ToolResultCache references in caching doc part 2

1. Open `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md`
2. Find lines 114 and 132 (ToolResultCache references)
3. Replace each reference with a brief note indicating it's a standalone utility not used by ToolExecutor

Change from:

```markdown
... detailed ToolResultCache description ...
```

To:

```markdown
... ToolResultCache (standalone utility, not used by ToolExecutor) ...
```

#### Step 4: Verify cross-references

If there are any cross-references to these sections elsewhere in the document, ensure they still work correctly.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The reduced descriptions help prevent misunderstanding about ToolResultCache usage

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the reductions if the original meaning was intentional

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md` | Excessive description reduction | grep for ToolResultCache | Description reduced to 1-2 sentences |
| `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md` | Excessive description reduction | grep for ToolResultCache | Description reduced to 1-2 sentences |
| `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md` | Reference reduction | grep for ToolResultCache | References reduced appropriately |

## Out of scope

- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-125213_require.md
- Source plan: plans/20260722-170920_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-181705
- Related target files: docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md, docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md, docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md
