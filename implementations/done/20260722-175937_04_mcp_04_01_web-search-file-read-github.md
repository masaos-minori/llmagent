## Goal

Add availability metadata section to web-search documentation noting the gap between config_dependent and runtime enabled/disabled_reason.

## Scope

- Update `docs/04_mcp_04_01_web-search-file-read-github.md` — add availability metadata section for web-search

## Assumptions

1. The existing documentation structure and content are correct; only additions are needed
2. browser_fetch has `config_dependent=true` (confirmed in code: `web_search_tools.py:64`)
3. build_tools_response() does NOT add `enabled` or `disabled_reason` (confirmed in code: `server.py:224-233`)
4. Domain allowlist enforcement happens at call time (via `BrowserAuthorizationError`) rather than via availability metadata (confirmed in code: `search_provider.py:81-114`)

## Design decisions

- Add a dedicated "Availability metadata" subsection under the web-search section
- Clearly note the gap between config_dependent and runtime enabled/disabled_reason
- Document the actual enforcement mechanism (domain allowlist at call time)

## Alternatives considered

- Adding inline notes within existing sections instead of creating a new subsection
- Creating a separate appendix for availability metadata gaps

## Implementation

### Target file

- `docs/04_mcp_04_01_web-search-file-read-github.md`

### Procedure

#### Step 1: Locate insertion point

1. Open `docs/04_mcp_04_01_web-search-file-read-github.md`
2. Find the web-search section
3. Identify where the availability metadata subsection should be inserted

#### Step 2: Add availability metadata subsection

Insert the following markdown after the web-search section:

```markdown
## Availability metadata

The web-search server provides limited availability metadata through `/v1/tools`:

- `config_dependent`: `true` for `browser_fetch` — indicates the tool depends on configuration
- `enabled`: Not currently implemented for web-search tools
- `disabled_reason`: Not currently implemented for web-search tools

### Current limitations

The web-search server does NOT implement runtime `enabled/disabled_reason` fields despite having `config_dependent=true`. This means:

- Tools appear available to the LLM even when they may fail due to missing configuration
- Domain allowlist enforcement happens at call time (via `BrowserAuthorizationError`) rather than via availability metadata
- Operators cannot determine from `/v1/tools` alone whether `browser_fetch` will work

### Enforcement mechanism

When `browser_fetch` is called with a domain not in the allowlist, the server raises `BrowserAuthorizationError`. This error is returned via the `/v1/call_tool` response rather than being prevented by availability metadata.
```

#### Step 3: Cross-reference the metadata document

If there's a cross-reference to the tool-runtime-availability-metadata.md document, ensure it points to the updated content.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The new section complements existing web-search documentation without conflicting

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the added section if the current limitations description is incorrect

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `mcp_servers/web-search/search_provider.py` | Read-only verification | grep for BrowserAuthorizationError | Allowlist enforcement confirmed |
| `docs/04_mcp_04_01_web-search-file-read-github.md` | Documentation consistency check | Manual review | Section added correctly |

## Out of scope

- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-124007_require.md
- Source plan: plans/20260722-143806_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-175937
- Related target files: docs/04_mcp_04_01_web-search-file-read-github.md
