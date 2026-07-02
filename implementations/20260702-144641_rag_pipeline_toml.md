# Implementation Procedure: config/rag_pipeline.toml

## Goal

Add `strict_artifact_validation = false` to `config/rag_pipeline.toml` under the appropriate
section, enabling operators to opt in to strict chunk file header validation without any code
changes (Plan 142134 Phase 2).

## Scope

**In scope:**
- Add one key-value pair to `config/rag_pipeline.toml`

**Out of scope:**
- Changes to any Python source file
- Deploy steps (deploy.sh copies this file; covered in Phase 6)

## Assumptions

1. `config/rag_pipeline.toml` has a `[ingester]` section or similar; the new key should be
   placed under it. If no section exists, place at top level matching existing key style.
2. `ConfigLoader().load("rag_pipeline.toml")["strict_artifact_validation"]` is the runtime
   access path — verify by reading `scripts/shared/config_loader.py`.
3. Default `false` ensures no behavioral change for existing deployments.

## Implementation

### Target file

`config/rag_pipeline.toml`

### Procedure

1. Read `config/rag_pipeline.toml` to understand existing structure and section headers.
2. Identify the `[ingester]` section (or top-level, if no section exists).
3. Add the line `strict_artifact_validation = false` with a comment:
   ```toml
   # When true, reject chunk files missing schema_version, artifact_type, or created_by fields.
   strict_artifact_validation = false
   ```
4. Verify with `python -c "import tomllib; d=tomllib.load(open('config/rag_pipeline.toml','rb')); print(d.get('ingester',d).get('strict_artifact_validation'))"` — expect `False`.

### Method

Single-line TOML addition. No structural changes.

## Validation plan

| Step | Command | Expected result |
|------|---------|----------------|
| Key present | `grep strict_artifact_validation config/rag_pipeline.toml` | match found |
| Value is false | `python -c "import tomllib; ..."` (see above) | `False` |
| Pre-commit | `pre-commit run --all-files` | pass |
