# Implementation: Runtime Arch vs Reference API Chapter Boundary

## Goal

Establish a clear boundary between runtime architecture docs (`05_agent_02`) and reference API docs (`05_agent_13`). Update `05_agent_00` routing table and add cross-references in both docs.

## Scope

**In:**
- `docs/05_agent_00_document-guide.md` — add boundary note in routing table
- `docs/05_agent_02_architecture_overview.md` — add cross-reference to `05_agent_13`
- `docs/05_agent_13_api_reference.md` — add cross-reference to `05_agent_02`

**Out:** No content moved between files.

## Assumptions

1. `05_agent_02` covers: module graph, data flows, component lifecycles (HOW it works).
2. `05_agent_13` covers: function signatures, parameter types, return types (WHAT it does).
3. Some duplication may exist — cross-references are the fix, not content merging.

## Implementation

### Target file

`docs/05_agent_00_document-guide.md`, `docs/05_agent_02_architecture_overview.md`, `docs/05_agent_13_api_reference.md`

### Procedure

1. Read `docs/05_agent_02_architecture_overview.md` introduction to confirm scope.
2. Read `docs/05_agent_13_api_reference.md` introduction to confirm scope.
3. Update routing table in `05_agent_00` with boundary note.
4. Add cross-reference at end of intro in `05_agent_02`.
5. Add cross-reference at end of intro in `05_agent_13`.

### Method

Read docs → Edit patches.

### Details

**Routing table update for `05_agent_00`:**

```markdown
| Chapter | Scope | Notes |
|---|---|---|
| `05_agent_02` Architecture Overview | Runtime behavior: module graph, data flow, component lifecycles | For function signatures → see `05_agent_13` |
| `05_agent_13` API Reference | Function signatures, parameter types, return values, error conditions | For component context → see `05_agent_02` |
```

**Cross-reference in `05_agent_02` intro:**
```markdown
> For function signatures and parameter-level documentation, see `05_agent_13` §API Reference.
> This chapter covers runtime behavior and component relationships.
```

**Cross-reference in `05_agent_13` intro:**
```markdown
> For component context, data flow, and runtime behavior, see `05_agent_02` §Architecture Overview.
> This chapter covers function signatures and type contracts.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Boundary note in 05_agent_00 | `grep -n "05_agent_13\|05_agent_02.*function" docs/05_agent_00_document-guide.md` | found |
| Cross-reference in 05_agent_02 | `grep -n "05_agent_13" docs/05_agent_02_architecture_overview.md` | found |
| Cross-reference in 05_agent_13 | `grep -n "05_agent_02" docs/05_agent_13_api_reference.md` | found |
| No code changes | `git diff agent/` | empty |
