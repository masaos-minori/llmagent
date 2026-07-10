# Implementation: `--print-metadata` flag for `scripts/agent/workflow/validate.py`

## Goal

Add an optional `--print-metadata` flag to the existing validation CLI that, on successful validation, additionally prints the workflow's name, version, and comma-joined stage IDs.

## Scope

**In:**
- `scripts/agent/workflow/validate.py`: add the flag and metadata-printing logic; restructure `main()` to retain the `WorkflowDef` returned by `.load()`

**Out:**
- No change to `WorkflowLoader`/`_validate()` — this reuses the already-parsed `WorkflowDef` object
- No change to the CLI's no-flag behavior or exit codes — must remain fully backward-compatible with `implementations/done/20260710-154648_agent_workflow_validate_cli.md`'s baseline

## Assumptions

1. Depends on `implementations/done/20260710-154648_agent_workflow_validate_cli.md` (`scripts/agent/workflow/validate.py` base CLI) already being implemented — this plan extends that same file.
2. `validate_path()` in the base CLI currently discards the `WorkflowDef` returned by `loader.load()`; this extension changes it to return that object so `main()` can print from it, without altering `validate_path()`'s role as the validation entry point.

## Implementation

### Target file

`scripts/agent/workflow/validate.py`

### Procedure

1. Change `validate_path()` to return the loaded `WorkflowDef`:
   ```python
   def validate_path(path: Path) -> WorkflowDef:
       """Return the loaded WorkflowDef, or raise WorkflowLoadError if invalid."""
       loader = WorkflowLoader(workflows_dir=path.parent)
       return loader.load(name=path.stem)
   ```
   (Import `WorkflowDef` from `agent.workflow.models`.)
2. Add the flag to the parser in `main()`:
   ```python
   parser.add_argument(
       "--print-metadata",
       action="store_true",
       help="On success, also print name/version/stage IDs",
   )
   ```
3. Update the `try`/`except` block in `main()` to capture the returned value and print metadata when requested:
   ```python
   try:
       wdef = validate_path(args.path)
   except WorkflowLoadError as exc:
       print(f"[FATAL] Invalid workflow definition {args.path}: {exc}", file=sys.stderr)
       return 1

   print(f"OK: {args.path} is a valid workflow definition")
   if args.print_metadata:
       print(f"Name     : {wdef.name}")
       print(f"Version  : {wdef.version}")
       print(f"Stages   : {', '.join(s.id for s in wdef.stages)}")
   return 0
   ```

### Method

Direct, minimal edit to the existing file — return-value change to `validate_path()`, one new `argparse` flag, one new conditional print block in `main()`. No other function signatures change.

### Details

- The no-flag path's printed output is unchanged (`OK: <path> is a valid workflow definition` only), preserving the base CLI's existing contract for any caller (e.g. `deploy.sh`'s pre-copy validation call from `implementations/done/20260710-154712_deploy_sh_workflow_validation_wiring.md`) that does not pass `--print-metadata`.
- `wdef.stages` is iterated for `.id` in definition order (the same order `_validate()` already requires to be duplicate-free), so the printed stage list matches the file's actual stage ordering.

## Validation plan

```bash
uv run ruff check scripts/agent/workflow/validate.py
uv run mypy scripts/agent/workflow/validate.py
PYTHONPATH=scripts uv run lint-imports

# Non-breaking (no flag)
PYTHONPATH=scripts uv run python -m agent.workflow.validate config/workflows/default.json
# expect: exactly "OK: config/workflows/default.json is a valid workflow definition", no metadata lines

# Metadata flag
PYTHONPATH=scripts uv run python -m agent.workflow.validate --print-metadata config/workflows/default.json
# expect: OK line + Name/Version/Stages lines matching config/workflows/default.json's actual contents

# Negative test (flag should not suppress existing failure behavior)
echo '{"name": "x"}' > /tmp/bad_workflow.json
PYTHONPATH=scripts uv run python -m agent.workflow.validate --print-metadata /tmp/bad_workflow.json; echo "exit: $?"
```

Expected outcome: no-flag invocation is byte-identical to the pre-extension baseline; `--print-metadata` adds exactly three new lines on success; invalid input still exits 1 with the `[FATAL]` message regardless of the flag.
