## Goal

Add missing required Front Matter fields (`area`, `related`) to `docs/eventbus/ack-nack-endpoints.md` per REQ-001 and REQ-002.

## Scope

Modify only `docs/eventbus/ack-nack-endpoints.md` to add `area` and `related` Front Matter fields.

## Assumptions

- The `area` field can be inferred from directory path: `docs/eventbus/*` → `eventbus`
- No specific related documents exist for this endpoint reference doc; use empty array `[]`
- Existing Front Matter values (title, description, tags, created) must not be changed

## Design decisions

- Infer `area` from directory path as documented in the Plan's Assumptions section
- Use `[]` for `related` since this is an API reference doc with no specific cross-references
- Preserve existing Front Matter fields and their order

## Alternatives considered

- Inferring `related` from document content: rejected because the doc describes standalone endpoints without referencing other docs
- Using a different area value: rejected because `eventbus` matches the directory convention used elsewhere

## Implementation

### Target file

`docs/eventbus/ack-nack-endpoints.md`

### Procedure

1. Read the current Front Matter block at the top of the file
2. Add `area: eventbus` after the `tags` field
3. Add `related: []` after the `area` field
4. Verify YAML validity

### Method

Edit the YAML Front Matter block directly using text insertion between existing fields.

### Details

Current Front Matter (lines 1-6):
```yaml
---
title: ACK/NACK Endpoints
description: Consumer acknowledgment and negative acknowledgment endpoint contracts
tags: [api-reference, ack, nack, consumer]
created: 20260916
---
```

After modification:
```yaml
---
title: ACK/NACK Endpoints
description: Consumer acknowledgment and negative acknowledgment endpoint contracts
tags: [api-reference, ack, nack, consumer]
area: eventbus
related: []
created: 20260916
---
```

Insert `area: eventbus` after line 4 (`tags:`) and `related: []` after line 5 (`area:`).

## Compatibility considerations

- Adding `area` and `related` fields does not change the semantic meaning of existing fields
- The `area` value `eventbus` aligns with the directory naming convention
- Empty `related: []` is valid YAML and consistent with the Plan's approach for docs without specific references

## Security considerations

No security impact — adding metadata fields does not affect access control or authentication.

## Rollback considerations

Revert the two added lines to restore original Front Matter if the change causes validation failures downstream.

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file.

## Completion criteria

- `area: eventbus` present in Front Matter
- `related: []` present in Front Matter
- All existing Front Matter fields preserved unchanged
- YAML parses without errors

## Out of scope

- Fixing H1 heading counts in this file
- Adding `## Keywords` or `## Related Documents` sections (separate requirement)
- Modifying any other file

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260922-155735 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260922-155735 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260922-155735 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260922-155735 |  |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260922-094335_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260922-095006
- **Related target files**: docs/eventbus/ack-nack-endpoints.md