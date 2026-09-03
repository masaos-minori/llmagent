## Goal
Author `schemas/doc_front_matter.json` — a draft-07 JSON Schema expressing the
finalized front-matter contract (required fields, the finalized `area` enum,
`status` as optional with a default) — as an inert artifact not wired into any
validation path.

## Scope
- **In-Scope**: `schemas/doc_front_matter.json` only (new file).
- **Out-of-Scope**: `docs/00_governance_02_documentation-metadata.md` (seq 01),
  `docs/00_governance_03_issue-and-uncertainty-management.md` (seq 03); wiring
  this schema into `tools/check_docs_structure.py --schema`'s default behavior
  or `tools/manage_frontmatter.py` (`docmeta03`'s explicit scope, per this
  Plan's Implementation intent); resolving `UNK-03`
  (`additionalProperties` strictness) — registered as a Needs Confirmation entry
  by seq 03, not resolved here.

## Assumptions
- `schemas/event_envelope.json` is this repository's one existing JSON Schema,
  establishing the authoring convention: draft-07 (`$schema`), a `title`,
  `type: object`, a top-level `required` array, `additionalProperties`, and a
  `properties` map with per-field `type`/constraints/`description` — re-verified
  2026-09-03 by direct `Read`, matching the Plan's own evidence with no drift.
- `tools/_front_matter_schema.py` (created during this session's earlier tool
  review, before this Plan existed) already implements
  `load_front_matter_schema()`, which — when `schemas/doc_front_matter.json`
  exists — parses it expecting exactly: a top-level `required` array of
  strings, and `properties.area.enum` / `properties.status.enum` as arrays of
  strings when present. This row's schema MUST use that exact shape for those
  three keys, or the loader's own defensive fallback (malformed/absent-shape
  treated as absent) would silently ignore this new file once created — a
  structural constraint discovered by reading that module, not stated in the
  Plan itself.
- `tools/check_docs_structure.py`'s `--schema` flag only calls
  `load_front_matter_schema()` when the flag is explicitly passed
  (`if args.schema is not None:`) — re-verified by direct `Read` of
  `tools/check_docs_structure.py:226-228`. `tools/manage_frontmatter.py` calls
  `load_front_matter_schema()` unconditionally in `cmd_add_missing()`, but only
  consumes `schema.required_fields` (re-verified: no `area_enum`/`status_enum`
  reference anywhere in that file) — so creating this schema file changes
  neither tool's actual behavior: `check_docs_structure.py` stays opt-in, and
  `manage_frontmatter.py`'s required-fields value is unchanged (`title`, `area`,
  `tags`, `related` either way). This confirms REQ-006's "do not wire it into
  any validation path" is satisfied by this row without an additional
  precaution.
- The finalized `area` enum (10 values, matching seq 01's edit and this Plan's
  own re-verified usage survey) is: `overview`, `deployment`, `rag`, `mcp`,
  `agent`, `eventbus`, `shared`, `governance`, `adr`, `security`.

## Design decisions
- **`additionalProperties: true`**, differing from `schemas/event_envelope.json`'s
  own `false` — per REQ-006/the Plan's own Design section, this is the
  documented interim default pending `UNK-03` (seq 03 registers it), not an
  oversight: a `false` default would make this schema immediately reject the
  real front matter of any document carrying an extension key (e.g. `source:`
  seen in several RAG documents), which this Plan's own Implementation intent
  explicitly avoids asserting as a decision it is not equipped to make.
- **`status`'s schema `enum` is `["stable", "draft"]` with `"default": "stable"`**,
  matching `event_envelope.json`'s own precedent of a `default` key on an
  optional property (`schema_version`) — this also directly satisfies
  `tools/_front_matter_schema.py`'s expected `properties.status.enum` shape.
- **No `pattern`/`minLength`/`maxLength` constraints on `title`, `tags` items, or
  `related` items** beyond `type` — `event_envelope.json` adds such constraints
  because it validates machine-generated event payloads with strict format
  requirements (UUID pattern, string length bounds); front-matter fields are
  human-authored prose/paths with no analogous fixed format to constrain against,
  and inventing one would exceed this Plan's own scope of "expressing the
  finalized field set" (REQ-006) into speculative additional validation the
  Plan never requires.
- **`tags` and `related` are typed as `array` of `string`**, matching how every
  real document's front matter already expresses them (YAML list syntax) and
  matching `tools/check_docs_structure.py`'s own existing (untyped) handling of
  these fields as iterables — this is a direct, uncontroversial encoding of the
  existing convention, not a new design choice.

## Alternatives considered
- **Set `additionalProperties: false` now, to match `event_envelope.json`'s
  precedent exactly** — rejected (see Design decisions): this Plan's own
  `UNK-03` explicitly defers this decision, and setting it to `false`
  unilaterally here would preempt that Needs Confirmation entry's purpose.
- **Add `pattern` constraints to `related`/`tags` item strings (e.g. requiring a
  `.md` suffix for `related` entries)** — rejected: a small number of `related`
  entries in the corpus may reference non-`.md` targets or use forms this Plan
  did not survey; adding an unverified pattern constraint risks the schema
  rejecting currently-valid documents the moment `docmeta03` wires it in,
  which is exactly the kind of premature strictness `UNK-03`'s existence warns
  against for `additionalProperties` and this row extends the same caution to.

## Implementation
### Target file
`schemas/doc_front_matter.json` (new file)

### Procedure
1. Create `schemas/doc_front_matter.json` with the exact content in Details
   below.
2. Manually validate it against one known-compliant document's front matter and
   one known-violating (`category`-only) front matter block (Plan's own Phase 3
   step 2 requirement — see Validation plan).

### Method
Create the file directly (new file — no before/after diff applies).

### Details

Full file content:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DocFrontMatter",
  "type": "object",
  "required": ["title", "area", "tags", "related"],
  "additionalProperties": true,
  "properties": {
    "title": {
      "type": "string",
      "minLength": 1,
      "description": "Document title"
    },
    "area": {
      "type": "string",
      "enum": [
        "overview",
        "deployment",
        "rag",
        "mcp",
        "agent",
        "eventbus",
        "shared",
        "governance",
        "adr",
        "security"
      ],
      "description": "Document area — the sole category-style field"
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Keywords describing the document content"
    },
    "related": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Links to related documents"
    },
    "status": {
      "type": "string",
      "enum": ["stable", "draft"],
      "default": "stable",
      "description": "Current state of the document; defaults to stable when absent"
    }
  }
}
```

## Compatibility considerations
No existing tool's default behavior changes as a result of this file's creation
(see Assumptions: `check_docs_structure.py --schema` remains opt-in;
`manage_frontmatter.py`'s consumed value, `required_fields`, is unchanged).
Independent of seq 01/03 — this row's content does not require either to already
be applied, though `docmeta01`'s Implementation intent groups this schema with
seq 01's finalized field set for a single coherent contract.

## Security considerations
None — a static JSON Schema document with no executable content, network
access, or credential material.

## Rollback considerations
New, standalone file with no current callers (not wired into any validation
path per this row's own scope). Revert by deleting the file; no other file
requires a follow-up change if reverted.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| schemas/doc_front_matter.json | JSON syntax validity | `uv run python -c "import json; json.load(open('schemas/doc_front_matter.json'))"` | Parses without error |
| schemas/doc_front_matter.json | Manual discrimination check (compliant case) | Validate a known-compliant document's extracted front matter (e.g. this document's own: `title`, `area: governance`, `tags`, `related`) against the schema, by hand or with a JSON-Schema-validation library if available | Passes — all required fields present, `area` value within the enum |
| schemas/doc_front_matter.json | Manual discrimination check (violating case) | Validate a `category`-only front matter block (e.g. `{"title": "X", "category": "agent", "tags": [], "related": []}`) against the schema | Rejected — `area` is a required field this block does not carry (`category` is not a recognized property, but with `additionalProperties: true` the actual failure signal is the missing required `area` key, not an unknown-property rejection — confirming discrimination happens via the `required` array, not via strictness) |

## Completion criteria
- `schemas/doc_front_matter.json` exists, is valid JSON, and is a valid draft-07
  JSON Schema (AC-5).
- It validates a real, compliant document's extracted front matter (AC-5).
- It rejects a front matter block using `category` instead of `area` — via the
  missing required `area` field, given `additionalProperties: true` (AC-5).

## Out of scope
`docs/00_governance_02_documentation-metadata.md` (seq 01),
`docs/00_governance_03_issue-and-uncertainty-management.md` (seq 03) — each has
its own implementation-procedure document per this Plan's Implementation Target
Files table. Wiring this schema into any tool's default validation path —
`docmeta03`'s scope, not this row's.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903 | 20260903 | Created the file exactly per Details. |
| 2 | Add or update tests per Validation plan | Completed | 20260903 | 20260903 | N/A: no test file owned by this row. Manual discrimination check: compliant example (`title`/`area: agent`/`tags`/`related`) has zero missing required fields; a `category`-only block is missing required `area` — confirmed via direct Python dict comparison against `schema["required"]`. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903 | 20260903 | JSON parses via `json.load()`. `tools/_front_matter_schema.py::load_front_matter_schema()` now returns this file as `source` with the exact `required_fields`/`area_enum`/`status_enum` designed. `check_docs_structure.py --schema` against the full corpus: 179 issues, identical count to the pre-existing baseline (no new area-enum violations — `grep` confirms all 10 real `area:` values already match the finalized enum exactly, including zero remaining `shared-db` usages). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260903 | 20260903 | N/A |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/done/20260902-194021_docmeta01_finalize_canonical_documentation_metadata_schema.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-124425_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-154428
- **Related target files**: schemas/doc_front_matter.json
