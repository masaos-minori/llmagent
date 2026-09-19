## Goal
Add an optional `class` enum property to `schemas/doc_front_matter.json` and set
`additionalProperties` explicitly, resolving `NC-032` (`REQ-001`, `REQ-002`).

## Scope
In scope: this one JSON Schema file's `properties.class` addition and its
`additionalProperties` value. Out of scope: classifying any existing document
(bulk-classification is separate follow-up work, per the source Plan).

## Assumptions
- File content unchanged since the Plan was written — re-confirmed:
  `required: ["title", "area", "tags", "related"]`, `additionalProperties: true`,
  no `class` property.
- **`additionalProperties` decision** (carried forward from the Plan's own
  Assumptions, itself subject to accountable-party override via a comment on
  `plans/done/20260919-105328_plan.md` before this row is executed — re-check
  for such a comment before implementing): keep `additionalProperties: true`.
  Rationale (from the Plan): `NC-032`'s own Evidence confirms area-specific
  extension keys (e.g. `source:` in RAG documents) are already in legitimate
  active use, and no completed survey of non-required-key usage exists yet — 
  setting `false` now would immediately break validation for every file using
  an undocumented extension key.

## Design decisions
Add `class` as `{"type": "string", "enum": [...7 values...], "description":
"Document class — one of the 7 classes defined in
00_governance_01_documentation-policy.md's Document Classification"}` under
`properties`, without adding it to `required` (per the source issue's explicit
"optional, not required" constraint). Leave `additionalProperties` at its
current `true` value, but change its inline comment/description context (JSON
Schema has no native comment syntax; if this project's convention keeps a
sibling explanatory field or the schema is otherwise self-documenting via
`docs/00_governance_02_documentation-metadata.md`, follow that existing
pattern — no schema-level comment field currently exists in this file, so no
change is needed there beyond the value staying `true`).

## Alternatives considered
Setting `additionalProperties: false` now, paired with an immediate
documents-using-extension-keys survey, was considered (this is `NC-032`'s
originally envisioned "Required Action" path) but rejected for this row — no
survey has been completed, and per `rules/workflow-lifecycle.md`'s evidence
standards, changing a schema constraint without completing the action its own
open question calls for would be an unverified, ungrounded change.

## Implementation
### Target file
schemas/doc_front_matter.json

### Procedure
1. Add the `class` property object under `properties` (after the existing
   `status` property), with the 7-value enum
   (`["Governance", "Guide", "Specification", "Reference", "Operations",
   "Note", "Known Issues"]`, matching
   `docs/00_governance_01_documentation-policy.md`'s Document Classification
   list verbatim).
2. Leave `required` and `additionalProperties` unchanged from their current
   values (`required` stays `["title", "area", "tags", "related"]`;
   `additionalProperties` stays `true`, now as an explicit, documented decision
   — see Design decisions).

### Method
Direct JSON edit (`Edit` tool) — add one property object; no other schema
change.

### Details
- Enum values must exactly match `docs/00_governance_01_documentation-policy.md`'s
  Document Classification wording (Governance / Guide / Specification /
  Reference / Operations / Note / Known Issues) — re-read that section
  immediately before finalizing the enum list, in case it has changed since
  this Plan's drafting.
- Confirm the resulting JSON is still valid (`python -c "import json;
  json.load(open('schemas/doc_front_matter.json'))"`) after the edit.

## Compatibility considerations
Adding an optional property is backward-compatible: no existing document's
front matter becomes invalid (the property is not in `required`), and
`additionalProperties` is unchanged, so no existing document using an unrelated
extension key becomes invalid either.

## Security considerations
N/A: schema file only, no credentials or runtime code.

## Rollback considerations
`git checkout -- schemas/doc_front_matter.json` reverts this row independently
— `tools/_front_matter_schema.py` (seq 02) gracefully falls back to
`class_enum=None` when the schema lacks the property (same pattern as its
existing `area_enum`/`status_enum` fallback), so a partial rollback of only this
row does not break seq 02's code.

## Validation plan
- `python -c "import json; json.load(open('schemas/doc_front_matter.json'))"` —
  confirm valid JSON.
- `uv run pytest tests/tools/test_front_matter_schema.py -v` (seq 06's updated
  tests) — confirm `class_enum` parses correctly.
- `uv run python tools/check_docs_structure.py` — confirm `check_schema_compliance`
  still passes against documents that now optionally carry `class`.

## Completion criteria
- `schemas/doc_front_matter.json` accepts a valid `class` value from the 7-value
  enum and (when validated with a JSON Schema validator) rejects an invalid one.
- `required` and `additionalProperties` are unchanged from their current values,
  now with the decision explicitly recorded (this document + the source Plan).

## Out of scope
Classifying any existing document; changing `required` or `additionalProperties`'s
value (only documenting the decision to keep it as-is).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Check for an accountable-party override comment on `plans/done/20260919-105328_plan.md` before executing (see Assumptions) |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests live in seq 06's document (`tests/tools/test_front_matter_schema.py`) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | JSON validity + `tools/check_docs_structure.py` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Doc update lives in seq 04's document (`docs/00_governance_02_documentation-metadata.md`) |

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
- **Requirement ID**: REQ-001, REQ-002 (add optional class property; decide additionalProperties, resolving NC-032)
- **Source issue**: issues/done/20260918-130249_docsmeta01_add-class-front-matter-field.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-105328_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-115041
- **Related target files**: schemas/doc_front_matter.json
