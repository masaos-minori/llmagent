"""One-shot corrective patcher for the 20261101-163219 wflease001 procedure docs.

Applies the findings of the 2026-11-01 pre-execution adversarial verification:
- de-duplicate the doubled `## Goal` heading in all 18 procedure docs,
- replace the stale "Ledger landing order" assumption bullet in all 18 docs
  (wftaskapi001 procedure 12 landed as code 3 / "1.3.0", so this Plan takes
  code 4 / "1.4.0"),
- refresh drifted `path:line` citations, byte sizes, and version-slot wording
  per file against the current `master` source.

Every replacement must match exactly once in its target file; the script
aborts without writing on any mismatch. Run once; re-running after the fix
exits non-zero by design (the old patterns are gone).
"""

from __future__ import annotations

from pathlib import Path

GOAL_OLD = "## Goal\n\n## Goal\n"
GOAL_NEW = "## Goal\n"

LAND_OLD = (
    '- Ledger landing order (Plan UNK-06): `master` records code 2 / "1.2.0" '
    "(`migrations_workflow.py:42`); wftaskapi001 procedure 12 "
    "(`implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md`, Pending) "
    'reserves the next slot. This Plan takes code 3 / "1.3.0" only if its step registers '
    'before wftaskapi001\'s, otherwise 4 / "1.4.0" (same rule as '
    "`implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`)."
)
LAND_NEW = (
    "- Ledger landing order (Plan UNK-06; fixed by the 2026-11-01 pre-execution "
    "verification): wftaskapi001 procedure 12 has landed "
    "(`implementations/done/20261101-140834_12_scripts_db_migrations_workflow.py.md`) and "
    'registered code 3 / "1.3.0" (`migrations_workflow.py:42`, `WORKFLOW_TARGET_VERSION` '
    '= 3 at `:49`). This Plan takes code 4 / "1.4.0": procedure 17 registers '
    "`workflow_attempt_lease` with `from_version=3, to_version=4`, and procedure 06 sets "
    '`WORKFLOW_SCHEMA_VERSION` to "1.4.0". The still-Pending wfrecovery001 procedure 26 '
    "(`implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`) takes "
    '5 / "1.5.0" when it lands after this Plan.'
)

EDITS: dict[str, list[tuple[str, str]]] = {
    "20261101-163219_02_scripts_agent_workflow_state_store.py.md": [
        (
            "`find_stale_running_attempts` (`state_store.py:250-277`) parses",
            "`find_stale_running_attempts` (`state_store.py:193-218`) parses",
        ),
        (
            "`time.mktime(time.strptime(...))` at `:265` and the silent `continue`",
            "`time.mktime(time.strptime(...))` at `:208` and the silent `continue`",
        ),
        (
            "`_STALE_GRACE_SEC` (`:25`) is removed and replaced",
            "`_STALE_GRACE_SEC` (`:30`) is removed and replaced",
        ),
        (
            "`recover_stale_attempts` (`:279-316`) takeover becomes",
            "`recover_stale_attempts` (`:222-259`) takeover becomes",
        ),
        (
            "Replace the parse block at `:263-271` with",
            "Replace the parse block at `:206-212` with",
        ),
        (
            "remove `_STALE_GRACE_SEC` (`:25`) and add",
            "remove `_STALE_GRACE_SEC` (`:30`) and add",
        ),
        (
            "Rewrite `recover_stale_attempts` (`:279-316`): classify rows",
            "Rewrite `recover_stale_attempts` (`:222-259`): classify rows",
        ),
        (
            "`state_store.py` is 11164 B at baseline",
            "`state_store.py` is 10171 B at baseline",
        ),
    ],
    "20261101-163219_03_scripts_agent_workflow_attempt_ops.py.md": [
        (
            "(`attempt_ops.py:44-45` region)",
            "(`attempt_ops.py:15-22` region)",
        ),
    ],
    "20261101-163219_06_scripts_db_schema_sql.py.md": [
        (
            '- Bump `WORKFLOW_SCHEMA_VERSION` (`:27`) from the current `"1.2.0"` to the '
            'landing-order value: `"1.3.0"` if this Plan\'s migration step registers '
            'before wftaskapi001\'s pending step, else `"1.4.0"` (Plan Assumptions, '
            "ledger landing order).",
            '- Bump `WORKFLOW_SCHEMA_VERSION` (`:27`) from the landed `"1.3.0"` to '
            '`"1.4.0"` — the value fixed by the 2026-11-01 verification (procedure 17 '
            "registers registry code 4).",
        ),
        (
            "2. Update `WORKFLOW_SCHEMA_VERSION` (`:27`) to the agreed landing-order value "
            "at implementation time (coordinate with "
            "`implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md` and "
            "`implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`).",
            '2. Set `WORKFLOW_SCHEMA_VERSION` (`:27`) to `"1.4.0"` (landing order fixed '
            "by the 2026-11-01 verification; see Assumptions).",
        ),
        (
            '- AC-8: the version constant differs from `"1.2.0"` and the new columns '
            "appear in the canonical DDL.",
            '- AC-8: the version constant differs from `"1.3.0"` (it becomes '
            '`"1.4.0"`) and the new columns appear in the canonical DDL.',
        ),
    ],
    "20261101-163219_07_scripts_agent_services_workflow_schema.py.md": [
        (
            "Confirm the error message path at `:93-100` already names the missing column",
            "Confirm the error message path at `:93-107` already names the missing column",
        ),
    ],
    "20261101-163219_08_tests_shared_test_json_utils.py.md": [
        (
            "New `TestParseIsoUtc` class after `TestNowIsoRaw` (`:453-510`)",
            "New `TestParseIsoUtc` class after `TestNowIsoRaw` (`:453-514`)",
        ),
        (
            "Existing `TestNowIso` (`:382-451`) and `TestNowIsoRaw` (`:453-510`) tests",
            "Existing `TestNowIso` (`:382-450`) and `TestNowIsoRaw` (`:453-514`) tests",
        ),
        (
            "Import `parse_iso_utc` in the module import block at `:18-19`.",
            "Import `parse_iso_utc` in the module import block at `:15-23` (insert after "
            "`now_iso_raw` at `:19`).",
        ),
    ],
    "20261101-163219_09_tests_agent_workflow_test_workflow_state_store.py.md": [
        (
            'Replace the naive seeds `"2026-01-01T00:00:00"` at `:286`, `:336`, `:360` '
            "(and remaining seeds inside the recovery block `:274-452`) with the "
            "production format",
            'Replace the naive seeds `"2026-01-01T00:00:00"` at `:277`, `:327`, '
            "`:351`, `:378` and the `time.localtime`-formatted seeds at `:301`, `:353`, "
            "`:401`, `:454`, `:494` (whole recovery region `:250-562`, classes "
            "`TestRecoverStaleAttempts` and `TestStaleRecoveryConcurrency`) with the "
            "production format",
        ),
        (
            "(`test_stale_attempt_marked_failed` `:274`, "
            "`test_find_stale_returns_only_old_attempts` `:348`, "
            "`test_recovered_attempt_has_ended_at_set` `:375`, "
            "`test_recover_multiple_stale_attempts` `:399`, "
            "`test_recover_no_stale_attempts` `:452`)",
            "(`test_stale_attempt_marked_failed` `:265`, "
            "`test_find_stale_returns_only_old_attempts` `:339`, "
            "`test_recovered_attempt_has_ended_at_set` `:366`, "
            "`test_recover_multiple_stale_attempts` `:390`, "
            "`test_recover_no_stale_attempts` `:443`)",
        ),
    ],
    "20261101-163219_10_tests_agent_workflow_test_state_store.py.md": [
        (
            "the mock-based tests (`find_stale_running_attempts` lambdas at `:26-167`)",
            "the mock-based tests (`find_stale_running_attempts` lambdas at `:39-229`)",
        ),
    ],
    "20261101-163219_13_tests_db_test_create_schema.py.md": [
        (
            "Extend the embedded no-vec0 `attempts` DDL copy (`:392-421`)",
            "Extend the embedded no-vec0 `attempts` DDL copy (`:391-399`)",
        ),
        (
            "Update the workflow version assertion (currently pinned to the landed "
            '`"1.2.0"` behavior via the `workflow_schema_version` assertions at '
            "`:662-728`) to the new landing-order version together with procedure 17's "
            "registry codes.",
            "The `workflow_schema_version` assertions at `:662-728` read the "
            "`WORKFLOW_SCHEMA_VERSION` constant dynamically (no literal pin to edit); the "
            "pin to bump is the `PRAGMA user_version` head-code assertion at `:734` "
            "(currently `== 3`, becomes `== 4` with procedure 17's registry code 4).",
        ),
        (
            "Extend the attempts-column assertions (`INSERT` shape test around `:575-581`)",
            "Extend the attempts-column assertions in `test_attempts_foreign_key_cascade` "
            "(`:552-582`) to write and read back the two columns. Fixture note (fixed by "
            "the 2026-11-01 verification): `_WORKFLOW_SCHEMA_NO_VEC0` (`:375`) is a "
            "historical 7-column `attempts` copy already divergent from the live 9-column "
            "canonical DDL (`schema_sql.py:197-206`); canonical coverage is a new "
            "assertion on the unpatched real-DDL create path (pattern "
            "`test_workflow_schema_timestamps` `:964-990`): `PRAGMA table_info(attempts)` "
            "on a fresh real-DDL database lists the two new columns (11 columns total).",
        ),
        (
            "1. Edit the DDL copy at `:392-421`.",
            "1. Edit the DDL copy at `:391-399` (fixture block `:375-421`).",
        ),
    ],
    "20261101-163219_14_tests_agent_test_repl_health.py.md": [
        (
            "hand-written `CREATE TABLE attempts` fixture (`:538`, fixture block "
            "`:538-590`)",
            "hand-written `CREATE TABLE attempts` fixture (`:538`, fixture helper "
            "`:519-561`)",
        ),
        (
            "Add the missing-column negative test next to the existing health-check cases "
            "(`:523-554`, `:599` region).",
            "Add the missing-column negative case using the fixture's existing "
            "`missing_column` mechanism (`:546-549`; example test `:598-602`) in the "
            "health-check class (`:567-640` region).",
        ),
    ],
    "20261101-163219_15_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md": [  # noqa: E501
        (
            "- Baseline wording expectation at landing: wfrecovery001 procedure 24 "
            "(`implementations/20261101-145309_24_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md`, "
            "Pending) rewrites the same section to atomic attempt+task failure semantics "
            "first; this procedure amends that rewrite (the later plan reconciles the "
            "shared wording per Plan Assumptions).",
            "- Baseline wording (fixed by the 2026-11-01 verification): wfrecovery001 "
            "procedure 24 "
            "(`implementations/20261101-145309_24_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md`) "
            'is still Pending, so this rewrite applies to the current "Startup Recovery" '
            "section text (`:143`); the wfrecovery001 document carries the reconciliation "
            "note when it lands (Plan Assumptions).",
        ),
    ],
    "20261101-163219_16_docs_10_adr_adr_02_02_001_agent-workflow-engine-mandatory.md.md": [
        (
            "- wfrecovery001 procedure 23 amends the same INV-07 first (Pending); the "
            "landing order decides which amendment is applied to which baseline text — the "
            "later document reconciles (Plan Assumptions overlap record).",
            "- wfrecovery001 procedure 23 amends the same INV-07 and is still Pending at "
            "the 2026-11-01 verification, so this amendment applies to the current `:171` "
            "text; the wfrecovery001 document reconciles when it lands (Plan Assumptions "
            "overlap record).",
        ),
        (
            "1. Apply the amendment on top of the wfrecovery001 amendment baseline.",
            "1. Apply the amendment to the current INV-07 text (`:171`); the "
            "wfrecovery001 amendment reconciles when its Pending procedure lands.",
        ),
    ],
    "20261101-163219_17_scripts_db_migrations_workflow.py.md": [
        (
            "- Append a `MigrationSpec` `workflow_attempt_lease` to `REGISTRY` "
            "(`:246-262`): `from_version=2`, `to_version=3` (or `4` if wftaskapi001's "
            "pending step registers first), `mutation_sql` =",
            "- Append a `MigrationSpec` `workflow_attempt_lease` to `REGISTRY` "
            "(`:328-353`) after `workflow_task_nonce`: `from_version=3`, `to_version=4` "
            "(fixed by the 2026-11-01 verification: wftaskapi001 landed as code 3), "
            "`mutation_sql` =",
        ),
        (
            '- Extend `WORKFLOW_VERSION_CODES` (`:42`, currently `{"1.1.0": 0, '
            '"1.2.0": 2}`) with the landing-order mapping (`"1.3.0": 3` or '
            '`"1.4.0": 4`) and raise `WORKFLOW_TARGET_VERSION` (`:48`) to match '
            "procedure 06's version string.",
            '- Extend `WORKFLOW_VERSION_CODES` (`:42`, currently `{"1.1.0": 0, '
            '"1.2.0": 2, "1.3.0": 3}`) with `"1.4.0": 4` and raise '
            "`WORKFLOW_TARGET_VERSION` (`:49`, currently 3) to 4, matching procedure 06's "
            '"1.4.0".',
        ),
        (
            "- Landing-order rule (Plan UNK-06, shared with "
            "`implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md` and "
            "`implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md`): "
            'the plan whose step registers first takes code 3 / "1.3.0"; the others '
            "shift up. The codes are fixed at implementation time, not in this document.",
            "- Landing-order rule (Plan UNK-06, shared with "
            "`implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md` and "
            "`implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md`): "
            "fixed at the 2026-11-01 verification — wftaskapi001 landed first with code 3 "
            '/ "1.3.0"; this Plan registers 4 / "1.4.0"; the still-Pending '
            'wfrecovery001 procedure 26 takes 5 / "1.5.0".',
        ),
        (
            "3. Extend the fingerprint/validation path (`:159-163` version-code check)",
            "3. Extend the fingerprint/validation path (`:174-178` version-code check)",
        ),
        (
            "- Mutation SQL follows the existing `_TOOL_STATE_MUTATION_SQL` pattern "
            "(module-level SQL constants near `:246`).",
            "- Mutation SQL follows the existing pattern (module-level SQL constants "
            "`_TOOL_STATE_MUTATION_SQL` `:116`, `_TASK_NONCE_MUTATION_SQL` `:127`).",
        ),
        (
            "- Postcondition raises on missing columns exactly like `_postcondition_tool_state` "
            "(`:240-242` pattern).",
            "- Postcondition raises on missing columns exactly like "
            "`_postcondition_task_nonce` (`:309-325` pattern).",
        ),
        (
            "| 1 | Ledger code/version values are Blocked until the landing order against "
            'pending wftaskapi001 step (code 3 / "1.3.0" reservation) is fixed | No | — |',
            "| 1 | Ledger code/version values were Blocked until the landing order against "
            "wftaskapi001 was fixed | Yes | 2026-11-01: wftaskapi001 landed as code 3 / "
            '"1.3.0"; this Plan registers 4 / "1.4.0" |',
        ),
        (
            "- Shared file with wfrecovery001 (landed codes 0-2) and pending wftaskapi001 "
            "code 3 reservation — coordinate at landing (Blocker Log).",
            "- Shared file: codes 0-3 are landed (bootstrap 0->1, tool_call_state 1->2, "
            "task_nonce 2->3, the last via wftaskapi001 procedure 12); this Plan appends "
            "code 4; the still-Pending wfrecovery001 procedure 26 takes 5.",
        ),
    ],
    "20261101-163219_18_tests_db_test_migrations_workflow.py.md": [
        (
            "Extend `TestWorkflowRegistry` (`:106-121`)",
            "Extend `TestWorkflowRegistry` (`:109-133`)",
        ),
        (
            "Extend the migration-execution pattern (`TestWorkflowToolCallStateStep`, "
            "`:192-260`): seed an old-shape attempts table",
            "Extend the migration-execution pattern (`TestWorkflowTaskNonceStep`, "
            "`:361-438`; closest landed template): seed an old-shape attempts table",
        ),
        (
            "a forged stamp without the ledger row is refused (pattern at `:260`)",
            "a forged stamp without the ledger row is refused (pattern at `:276`)",
        ),
        (
            "2. Add a `TestWorkflowAttemptLeaseStep` class following the `:192-260` "
            "template.",
            "2. Add a `TestWorkflowAttemptLeaseStep` class following the `:361-438` "
            "template.",
        ),
    ],
}


def apply_edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    n = text.count(old)
    if n == 0:
        if new in text:
            print(f"already fixed: {path.name}: {old[:50]!r}...")
            return
        raise SystemExit(
            f"{path.name}: pattern {old[:60]!r}... not found and not already applied"
        )
    if n != 1:
        raise SystemExit(
            f"{path.name}: expected exactly 1 occurrence of {old[:60]!r}..., found {n}"
        )
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    impl_dir = Path("implementations")
    targets = sorted(impl_dir.glob("20261101-163219_*.md"))
    if len(targets) != 18:
        raise SystemExit(f"expected 18 procedure docs, found {len(targets)}")
    for path in targets:
        apply_edit(path, GOAL_OLD, GOAL_NEW)
        apply_edit(path, LAND_OLD, LAND_NEW)
        for old, new in EDITS.get(path.name, []):
            apply_edit(path, old, new)
        print(f"fixed {path.name}")


if __name__ == "__main__":
    main()
