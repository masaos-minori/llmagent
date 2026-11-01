"""One-shot corrective patcher for the 20261101-165312 wfretry001 procedure docs.

Applies the findings of the 2026-11-02 pre-execution adversarial verification:
- refresh the shared 'Landing order' assumption bullet in all 12 docs (wftaskapi001
  and wflease001 have landed on master, wflease001 registered code 4 / "1.4.0";
  the wfrecovery001 20261101-145309 procedures remain Pending and this batch
  lands ahead of them),
- refresh the shared migration-ledger note (HEAD code 2 / "1.2.0" is stale; the
  landed ledger is code 4 / "1.4.0").

Every replacement must match exactly once in its target file; the script
aborts without writing on any mismatch. Run once; re-running after the fix
prints 'already fixed' lines by design (the old patterns are gone).
"""

from __future__ import annotations

from pathlib import Path

LAND_OLD = (
    "- Landing order (Plan Assumptions 'Re-verification record'): this batch lands "
    "after the pending procedure batches in plan order — wftaskapi001 "
    "`20261101-140834`, wfrecovery001 `20261101-145309`, wflease001 "
    "`20261101-163219` — so shared-file edits (`workflow_engine.py`, `models.py`, "
    "`workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`, "
    "`tests/agent/test_orchestrator.py`, `docs/23_agent/agent_03_03_...md`) rebase "
    "predictably."
)
LAND_NEW = (
    "- Landing order (Plan Assumptions 'Re-verification record'; updated by the "
    "2026-11-02 execution verification): wftaskapi001 `20261101-140834` and wflease001 "
    "`20261101-163219` have landed on `master` (wflease001 registered migration code 4 "
    '/ "1.4.0"); the wfrecovery001 `20261101-145309` procedures remain Pending and '
    "this batch lands ahead of them by owner decision, so those Pending procedure docs "
    "must be re-verified against the landed source before their own execution. Shared-"
    "file edits (`workflow_engine.py`, `models.py`, `workflow_engine_adapter.py`, "
    "`tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, "
    "`docs/23_agent/agent_03_03_...md`) rebase predictably."
)

LEDGER_OLD = (
    '(`scripts/db/migrations_workflow.py`, HEAD code 2 / "1.2.0") is not a target '
    "row and needs no change here."
)
LEDGER_NEW = (
    '(`scripts/db/migrations_workflow.py`, landed HEAD code 4 / "1.4.0") is not a '
    "target row and needs no change here."
)

EDITS: dict[str, list[tuple[str, str]]] = {
    "20261101-165312_02_scripts_agent_workflow_models.py.md": [
        (
            "- The pending wftaskapi001 (`20261101-140834_03`) and wfrecovery001 "
            "(`20261101-145309_01`) procedures edit the same file earlier in plan "
            "order; Plan Assumptions record the overlap as non-contradicting (distinct "
            "dataclasses/fields).",
            "- wftaskapi001 procedure 03 (`20261101-140834_03`, landed) and "
            "wfrecovery001 procedure 01 (`20261101-145309_01`, Pending) touch the same "
            "file; Plan Assumptions record the overlap as non-contradicting (distinct "
            "dataclasses/fields). The landed `RetryPolicy` still has only "
            "`max_attempts`/`backoff_sec`, so the field addition applies cleanly.",
        ),
    ],
    "20261101-165312_08_tests_agent_workflow_test_workflow_engine.py.md": [
        (
            "- File is shared with pending wftaskapi001/wfrecovery001/wflease001 test "
            "procedures (`20261101-140834_06`, `20261101-145309_14/15`, "
            "`20261101-163219_11`); Plan Assumptions classify the overlap as compatible "
            "(additive tests in different classes) — this batch lands last and rebases.",
            "- File is shared with wftaskapi001/wfrecovery001/wflease001 test procedures "
            "(`20261101-140834_06` and `20261101-163219_11` landed, "
            "`20261101-145309_14/15` Pending); Plan Assumptions classify the overlap as "
            "compatible (additive tests in different classes) — this batch lands before "
            "the remaining wfrecovery001 procedures and rebases ahead of them.",
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
    targets = sorted(impl_dir.glob("20261101-165312_*.md"))
    if len(targets) != 12:
        raise SystemExit(f"expected 12 procedure docs, found {len(targets)}")
    for path in targets:
        apply_edit(path, LAND_OLD, LAND_NEW)
        apply_edit(path, LEDGER_OLD, LEDGER_NEW)
        for old, new in EDITS.get(path.name, []):
            apply_edit(path, old, new)
        print(f"fixed {path.name}")


if __name__ == "__main__":
    main()
