#!/usr/bin/env python3
"""Fill the 20261027-154425 rag003 implementation-procedure skeletons with plan-derived content.

One-shot generator used by the plan-to-implementation-procedure workflow for
plans/20261027-110727_rag003_rag-url-key-ambiguity.md. Each section is populated
from the Plan row plus live line-number evidence verified on 2026-10-27.
"""

from pathlib import Path

PREFIX = "implementations/20261027-154425"
PLAN = "plans/20261027-110727_rag003_rag-url-key-ambiguity.md"
ISSUE = "issues/20261027-071953_rag003_rag-url-key-ambiguity.md"
GEN_AT = "20261027-154425"
NEW = "rag_query_service_url"
OLD = "rag_service_url"

COMMON_ASSUMPTION_RENAME = (
    "- Mechanical rename only: every edit is a whole-word substitution of "
    f"`{OLD}` to `{NEW}`; no semantics, defaults, or reader logic change (Plan Design).\n"
    "- `rag_pipeline_service_url` occurrences are a superset substring of the old key; every "
    "validation grep excludes it (`grep -v rag_pipeline_service_url`) so ingestion-path text "
    "is never touched (REQ-003).\n"
    "- Rebase immediately before implementing: the sibling rag001 Plan procedures "
    "(implementations/20261027-131124_*) touch `tests/rag/test_rag_pipeline.py` and "
    "`tests/rag/test_augment_refiner.py`, and the rag002 Plan procedures "
    "(implementations/20261027-144351_*) touch `docs/21_rag/rag_05_01-configuration-reference.md` "
    "and `tests/rag/test_rag_pipeline.py`; edits are disjoint, whichever implements second "
    "rebases (Plan Dependencies)."
)

COMMON_AC1 = (
    f'- `uv run python -c "import subprocess,sys; sys.exit(0 if not subprocess.run('
    f"[ 'grep','-rn','{OLD}','scripts/','tests/','docs/','--include=*.py','--include=*.md'], "
    "capture_output=True).stdout.replace(b'rag_pipeline_service_url', b'') else 1)\"`-style "
    f'exhaustiveness check: `grep -rn "{OLD}" scripts/ tests/ docs/ | grep -v '
    f'"rag_pipeline_service_url"` returns zero matches outside the single ADR rename note '
    "(AC-1, AC-5)."
)


def traceability(target: str) -> str:
    return (
        "## Traceability\n"
        "- **Workflow phase**: plan-to-implementation-procedure\n"
        "- **Requirement ID**: {REQ}\n"
        f"- **Source issue**: {ISSUE}\n"
        "- **Source requirement**: N/A: no standalone requirement document is generated\n"
        f"- **Source plan**: {PLAN}\n"
        "- **Source implementation procedure**: N/A: this document is the generated "
        "implementation procedure\n"
        f"- **Generated at**: {GEN_AT}\n"
        f"- **Related target files**: {target}"
    )


def status_table() -> str:
    return (
        "## Execution Status\n\n"
        "### Execution Status\n"
        "| Step | Description | Status | Started | Completed | Notes |\n"
        "|------|-------------|--------|---------|-----------|-------|\n"
        "| 1 | Implement the change described in Implementation > Procedure/Method/Details | "
        "Pending | — | — | |\n"
        "| 2 | Add or update tests per Validation plan | Pending | — | — | |\n"
        "| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |\n"
        "| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | "
        "— | — | |\n\n"
        "### Blocker Log\n"
        "| Step | Blocker Description | Resolved | Resolution Date |\n"
        "|------|---------------------|----------|-----------------|\n"
        "| — | — | — | — |\n\n"
        "### Work Items Created\n"
        "| Item ID | Related Step | Type | Status | Owner | Due Date |\n"
        "|---------|--------------|------|--------|-------|----------|\n"
        "| — | — | — | — | — | — |\n"
    )


def doc(
    title: str,
    target: str,
    reqs: str,
    goal: str,
    scope: str,
    assumptions: str,
    decisions: str,
    alternatives: str,
    procedure: str,
    method: str,
    details: str,
    compat: str,
    security: str,
    rollback: str,
    validation: str,
    completion: str,
    oos: str,
) -> str:
    parts = [
        f"# Implementation Procedure: {title}",
        "",
        "## Goal",
        goal,
        "",
        "## Scope",
        scope,
        "",
        "## Assumptions",
        assumptions,
        "",
        "## Design decisions",
        decisions,
        "",
        "## Alternatives considered",
        alternatives,
        "",
        "## Implementation",
        "### Target file",
        f"`{target}`",
        "### Procedure",
        procedure,
        "### Method",
        method,
        "### Details",
        details,
        "",
        "## Compatibility considerations",
        compat,
        "",
        "## Security considerations",
        security,
        "",
        "## Rollback considerations",
        rollback,
        "",
        "## Validation plan",
        validation,
        "",
        "## Completion criteria",
        completion,
        "",
        "## Out of Scope",
        oos,
        "",
        status_table(),
        traceability(target).replace("{REQ}", reqs),
    ]
    return "\n".join(parts) + "\n"


RENAME_ONLY_VALIDATION = (
    COMMON_AC1 + "\n"
    "- `uv run mypy --no-namespace-packages scripts/` — protocol/dataclass rename type-checks "
    "across packages; MagicMock-based fixtures accept any attribute name, so mypy plus the "
    "grep are the safety net (Plan Risks).\n"
    "- `uv run ruff check scripts/` and `PYTHONPATH=scripts uv run lint-imports` unchanged.\n"
    "- `uv run pytest tests/` — full suite green with name-only test edits (AC-6)."
)

RENAME_COMPAT = (
    "- The rename is repo-internal: no repo or deployed config file references the old spelling "
    "(verified 2026-10-27 across `config/` and `/opt/llm/config/`), so no external consumer is "
    "affected (REQ-006, Plan Design).\n"
    f"- `{NEW}` collides with no existing identifier; the only `rag_query*` names in the repo are "
    "the unrelated `rag_query_id` log context key and `rag_query_count` session stat "
    "(Plan Assumptions, verified)."
)

OOS_STANDARD = (
    "- Renaming `rag_pipeline_service_url` or editing `config/ingester.toml` / "
    "`/opt/llm/config/ingester.toml` (REQ-003).\n"
    "- Backward-compat alias or mapping for the old spelling (Plan Design: no consumer exists).\n"
    "- Renaming `rag_auth_token` or any other RAG config field.\n"
    "- Changes to which path reads which key, defaults, or delegation semantics."
)

ROLLBACK_STANDARD = (
    "- Single atomic rename commit; rollback is `git revert` of that commit. No data migration, "
    "no config-file change, and no deployed-state change means revert is complete on its own."
)

SECURITY_STANDARD = (
    "- No security surface change. With an unrecognized key the loader keeps the `None` default, "
    'which means "no HTTP delegation" — the fail-safe direction (Plan Design). '
    "`rag_auth_token` pairing semantics are unchanged."
)

MECHANICAL_METHOD = (
    "Whole-word substitution of `rag_service_url` restricted to occurrences NOT part of "
    "`rag_pipeline_service_url` (the ingestion key is a superset substring — verify each match "
    "or use `grep -v rag_pipeline_service_url`), followed by the exhaustiveness grep."
)

ALT_NO_ALIAS = (
    f"- Keep an alias mapping `{OLD}` -> `{NEW}` — rejected: zero consumers exist (verified "
    "inventory), and an alias re-introduces the ambiguity the rename removes (Plan Design).\n"
    "- Rename the ingestion key instead — rejected: it is live in `config/ingester.toml` and "
    "`/opt/llm/config/ingester.toml` (Plan Design)."
)

DESIGN_QUERY_KEY = (
    "- Rename the query-path key only: config-key renames are safe only where no config file "
    "lives, and the inventory shows the old query key appears in no repo or deployed config "
    "file, while the ingestion key is deployed (Plan Design)."
)

FILES: list[str] = []


def emit(name: str, text: str) -> None:
    path = Path(f"{PREFIX}_{name}")
    path.write_text(text, encoding="utf-8")
    FILES.append(path.name)


# --- scripts/ declarations (rows 1-3) ---
emit(
    "01_scripts_rag_config_resolution.py.md",
    doc(
        f"Rename the `{OLD}` declaration entries in `config_resolution.py`",
        "scripts/rag/config_resolution.py",
        "REQ-001, REQ-006",
        f"Rename the query-path key in the primary declaration of the config surface — "
        f"`_ALL_FIELDS` and `_DEFAULTS_FOR_ALL` — preserving the `None` default, so the config "
        f"surface exposes the query-path URL only as `{NEW}` (REQ-001, REQ-006).",
        "- Two entry renames (`_ALL_FIELDS` element, `_DEFAULTS_FOR_ALL` key). No change to the "
        "`resolve_rag_config` extras-ignoring filter or `RagConfigImpl` construction.",
        COMMON_ASSUMPTION_RENAME,
        DESIGN_QUERY_KEY
        + "\n- The `None` default is preserved unchanged: the renamed key absent/empty still "
        'means "no HTTP delegation, run in-process" (REQ-006).',
        ALT_NO_ALIAS,
        '1. Rename the `_ALL_FIELDS` entry `"rag_service_url"` (verified at L34) to '
        '`"rag_query_service_url"`.\n'
        '2. Rename the `_DEFAULTS_FOR_ALL` entry `"rag_service_url": None` (verified at L66) '
        'to `"rag_query_service_url": None`.\n'
        '3. Confirm the surrounding comment ("Only pass known fields ... ignore extras from '
        'config loader") stays accurate: after the rename, a config dict carrying the old '
        "spelling is filtered out exactly like any other extra key.",
        MECHANICAL_METHOD,
        "- `RagConfigValidator` usage in this file performs no validation keyed on either URL "
        "key name (Plan Reference Files), so no validator edit is required.\n"
        "- The filter-to-`_ALL_FIELDS` behavior is what the new regression test in "
        "`tests/rag/test_config_resolution.py` pins (see procedure _08).",
        RENAME_COMPAT,
        SECURITY_STANDARD,
        ROLLBACK_STANDARD,
        RENAME_ONLY_VALIDATION
        + "\n- `uv run pytest tests/rag/test_config_resolution.py` passes with renamed fixtures.",
        "- L34 and L66 carry `rag_query_service_url`; the old spelling does not appear in the "
        "file; full suite green.",
        OOS_STANDARD,
    ),
)
emit(
    "02_scripts_rag_models_config.py.md",
    doc(
        "Rename the `RagConfigImpl.rag_service_url` dataclass field",
        "scripts/rag/models_config.py",
        "REQ-001",
        f"Rename the `RagConfigImpl` dataclass field so the dataclass declaration matches the "
        f"renamed config surface attribute `{NEW}` (REQ-001).",
        "- One field rename in `RagConfigImpl`. No other field, default, or method changes.",
        COMMON_ASSUMPTION_RENAME,
        "- Field name mirrors the protocol attribute renamed in `scripts/shared/types.py` "
        "(procedure _03) and the `_ALL_FIELDS` entry renamed in `scripts/rag/config_resolution.py` "
        "(procedure _01); mypy checks the three-line rename as one contract (Plan Validation plan).",
        ALT_NO_ALIAS,
        "1. Rename the dataclass field `rag_service_url: str` (verified at L26) to "
        "`rag_query_service_url: str`.\n"
        "2. `RagConfigImpl` is constructed from keyword arguments in `resolve_rag_config` "
        "(config_resolution.py); the rename lands together with procedure _01 so the two files "
        "must be committed in the same change.",
        MECHANICAL_METHOD,
        "- The dataclass is built by keyword from the filtered config dict; no positional "
        "construction depends on the name.",
        RENAME_COMPAT,
        SECURITY_STANDARD,
        ROLLBACK_STANDARD,
        RENAME_ONLY_VALIDATION,
        "- L26 declares `rag_query_service_url: str`; mypy reports no attribute mismatch; "
        "full suite green.",
        OOS_STANDARD,
    ),
)
emit(
    "03_scripts_shared_types.py.md",
    doc(
        "Rename the `RagConfig` protocol attribute",
        "scripts/shared/types.py",
        "REQ-001",
        f"Rename the `RagConfig` protocol attribute to `{NEW}` so the cross-package contract "
        f"consumed by the query path, MCP adapter, and agent code carries the new name (REQ-001).",
        "- One protocol attribute rename. No other protocol member changes.",
        COMMON_ASSUMPTION_RENAME,
        "- The protocol is the boundary mypy uses to validate the rename across packages "
        "(scripts/rag, scripts/mcp_servers, scripts/agent); renaming it in the same commit as "
        "the dataclass and declaration entries makes any missed reader a type error.",
        ALT_NO_ALIAS,
        "1. Rename the protocol attribute `rag_service_url: str` (verified at L97) to "
        "`rag_query_service_url: str`.",
        MECHANICAL_METHOD,
        "- `tests/agent/test_rag_get_cfg.py` exercises this protocol surface and is renamed by "
        "procedure _21.",
        RENAME_COMPAT,
        SECURITY_STANDARD,
        ROLLBACK_STANDARD,
        RENAME_ONLY_VALIDATION,
        "- L97 declares `rag_query_service_url: str`; mypy passes across all consumers; "
        "full suite green.",
        OOS_STANDARD,
    ),
)

# --- readers (rows 4-7) ---
emit(
    "04_scripts_rag_pipeline.py.md",
    doc(
        "Rename the delegation check in `RagPipeline`",
        "scripts/rag/pipeline.py",
        "REQ-002, REQ-006",
        "Rename the reader that selects HTTP-delegation vs in-process mode so it reads "
        "`self._cfg.rag_query_service_url`, preserving the empty/absent -> in-process semantics "
        "(REQ-002, REQ-006).",
        "- One attribute access rename and one adjacent comment rename. No control-flow change.",
        COMMON_ASSUMPTION_RENAME,
        "- The walrus delegation check is the single switch between HTTP and in-process modes "
        "(ADR-010 INV-01); renaming only the attribute keeps the invariant identical.",
        ALT_NO_ALIAS,
        "1. Rename the delegation check `if rag_url := self._cfg.rag_service_url:` (verified at "
        "L243) to `if rag_url := self._cfg.rag_query_service_url:`.\n"
        '2. Rename the key named in the preceding comment at L241 ("HTTP mode: delegate to '
        'external RAG service when rag_service_url is configured").',
        MECHANICAL_METHOD,
        "- `call_rag_service()` in `scripts/rag/pipeline_service.py` receives `rag_url` as a "
        "local variable; the local name `rag_url` is unchanged.",
        RENAME_COMPAT,
        SECURITY_STANDARD,
        ROLLBACK_STANDARD,
        RENAME_ONLY_VALIDATION
        + "\n- HTTP-mode regression: `uv run pytest tests/rag/test_rag_http_mode.py "
        "tests/rag/test_pipeline_http_result_kind.py` green (AC-3).",
        "- L241/L243 reference only the new name; HTTP-mode and in-process mode tests green "
        "with renamed fixtures.",
        OOS_STANDARD,
    ),
)
emit(
    "05_scripts_rag_http_augment.py.md",
    doc(
        "Rename the key references in `http_augment.py` docstrings",
        "scripts/rag/http_augment.py",
        "REQ-002",
        f"Rename the key named in the module/class docstrings so the documented trigger for "
        f"HTTP augmentation is `{NEW}` (REQ-002). Docstrings only; no code change.",
        "- Docstring rename(s). The class reads the value through the pipeline delegation check "
        "(procedure _04), not by attribute name of its own.",
        COMMON_ASSUMPTION_RENAME,
        "- Docstrings that name a config key must name the live key; a stale name here is "
        "exactly the ambiguity the Issue removes.",
        ALT_NO_ALIAS,
        f'1. Rename the occurrence in the docstring line "When rag_service_url is configured, '
        f'delegates augment to an external" (verified at L73) to `{NEW}`.\n'
        "2. Grep the file for any further standalone occurrence and rename it the same way.",
        MECHANICAL_METHOD,
        "- Verified occurrence: exactly one standalone occurrence (L73) in current source.",
        RENAME_COMPAT,
        SECURITY_STANDARD,
        ROLLBACK_STANDARD,
        RENAME_ONLY_VALIDATION
        + "\n- `uv run pytest tests/rag/test_augment_integration.py` green (AC-1 for docstrings "
        "is the exhaustiveness grep).",
        "- The file names only `rag_query_service_url`; augment integration tests green.",
        OOS_STANDARD,
    ),
)
emit(
    "06_scripts_mcp_servers_rag_pipeline_rag_pipeline_models.py.md",
    doc(
        "Rename the anti-loop pin keyword in `build_rag_cfg_adapter()`",
        "scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py",
        "REQ-002, REQ-006",
        'Rename the `rag_service_url=""` keyword pin so the HTTP-loop guard binds to the '
        'renamed field and still pins the value to `""` (REQ-002, REQ-006).',
        "- One keyword rename plus its inline comment. The pinned empty-string value and the "
        "adapter's other fields are unchanged.",
        COMMON_ASSUMPTION_RENAME,
        "- The pin is what guarantees the rag_pipeline MCP server never re-delegates (ADR-010 "
        "consequence); the keyword name must match the renamed dataclass field or construction "
        "fails at import/runtime — mypy and the adapter test catch either miss.",
        ALT_NO_ALIAS,
        '1. Rename `rag_service_url="",  # prevent HTTP loop when augment() is called '
        'in-process` (verified at L171) to `rag_query_service_url="",  # ...` keeping the '
        "anti-loop comment.\n"
        "2. Commit together with procedure _02 (dataclass field rename): the keyword binds to "
        "the dataclass parameter name.",
        MECHANICAL_METHOD,
        "- Adapter anti-loop assertions in `tests/mcp_servers/rag_pipeline/"
        "test_rag_pipeline_mcp_service.py` (L37, L76-80, L119, L148 verified) are renamed by "
        "procedure _19.",
        RENAME_COMPAT,
        SECURITY_STANDARD,
        ROLLBACK_STANDARD,
        RENAME_ONLY_VALIDATION
        + "\n- Adapter anti-loop test: `uv run pytest tests/mcp_servers/rag_pipeline/` green; "
        'the pin assertion `adapter.rag_query_service_url == ""` holds (AC-3).',
        '- L171 pins `rag_query_service_url=""`; anti-loop assertions pass; full suite green.',
        OOS_STANDARD,
    ),
)
emit(
    "07_scripts_mcp_servers_rag_pipeline_rag_pipeline_server.py.md",
    doc(
        "Rename the key references in the `rag_pipeline_server.py` module docstring",
        "scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py",
        "REQ-002",
        f"Rename the two key mentions in the module docstring so the server's description of "
        f"when it replaces in-process augment names `{NEW}` (REQ-002). Docstring only.",
        "- Module docstring rename (2 occurrences). No code change.",
        COMMON_ASSUMPTION_RENAME,
        "- The docstring is the entry point operators read when deciding whether to configure "
        "delegation; it must name the live key.",
        ALT_NO_ALIAS,
        '1. Rename the occurrences in the module docstring (verified at L7-8: "Replaces the '
        "in-process augment() call when rag_service_url is configured in rag.toml "
        '(rag_service_url)").\n'
        '2. The parenthetical "(rag_service_url)" becomes "(rag_query_service_url)"; note '
        "this is a docstring mention, not a config-file fact claim, so no rename note is needed "
        "(unlike the ADR handling, procedure _29).",
        MECHANICAL_METHOD,
        "- Verified occurrences: L7 and L8.",
        RENAME_COMPAT,
        SECURITY_STANDARD,
        ROLLBACK_STANDARD,
        RENAME_ONLY_VALIDATION,
        "- The module docstring names only `rag_query_service_url`.",
        OOS_STANDARD,
    ),
)

# --- test files (rows 8-21) ---
emit(
    "08_tests_rag_test_config_resolution.py.md",
    doc(
        "Rename key fixtures and add the new-key-resolves / old-key-ignored regression test",
        "tests/rag/test_config_resolution.py",
        "REQ-004",
        "Rename existing key fixtures and add the Plan's new test pinning the contract: "
        '`{"rag_query_service_url": ...}` resolves, and the old spelling '
        '`{"rag_service_url": ...}` is ignored (stays `None`) (REQ-004, AC-2).',
        "- Fixture renames in existing tests plus one new test function. Assertion logic "
        "otherwise unchanged.",
        COMMON_ASSUMPTION_RENAME
        + "\n- The old spelling being ignored is the documented extras-filter behavior "
        "(`_ALL_FIELDS` filter in `resolve_rag_config`); the new test converts it from implicit "
        "to pinned contract (Plan Design).",
        "- New test rather than modifying an existing one: the old spelling must stay asserted "
        "as ignored so a stray legacy key in any future config fails visibly (fail-safe "
        "`None` = no delegation) (Plan Assumptions).",
        "- Treat the old spelling as a config-dict input only in the one new test — everywhere "
        "else in tests/ the rename is complete (AC-1).\n"
        "- Add a compat alias test asserting the old key still resolves — rejected: no alias "
        "exists by design.",
        '1. Rename fixture occurrences: the expected-dict entry `"rag_service_url": None` '
        "(verified at L29) and the construction kwarg `rag_service_url=None` (verified at L77).\n"
        "2. Add a new test (new): `test_renamed_key_resolves_and_old_spelling_ignored` — "
        'resolve a config dict containing `{"rag_query_service_url": "http://x"}` and '
        'assert `rag_query_service_url == "http://x"` (AC-2).\n'
        "3. In the same or a companion test case, resolve a config dict containing "
        '`{"rag_service_url": "http://x"}` and assert the resolved value stays `None` '
        "(old spelling ignored, AC-2).",
        "Add one test function with two cases (new key resolves; old key ignored); rename the "
        "two fixture occurrences. Keep the file's existing helper/config-builder style.",
        "- The new test depends on procedures _01/_02 landing first (declaration rename); it "
        "belongs to Plan Phase 3 after Phase 2.",
        RENAME_COMPAT,
        SECURITY_STANDARD,
        ROLLBACK_STANDARD,
        "- `uv run pytest tests/rag/test_config_resolution.py` green including the new test.\n"
        + COMMON_AC1
        + "\n- Full suite green.",
        "- New test present and passing; no standalone old-spelling fixture references remain "
        "outside the new test's ignore-assertion input.",
        OOS_STANDARD,
    ),
)

SIMPLE_TEST_RENAME_ROWS = [
    (
        "09",
        "tests/rag/test_rag_pipeline.py",
        'fixture kwarg occurrences at L186 and L262 (`rag_service_url="",`)',
    ),
    (
        "10",
        "tests/rag/test_rag_http_mode.py",
        "helper parameter and attribute: "
        '`_make_pipeline(rag_service_url: str = "http://rag.local")` (L20) and '
        "`cfg.rag_service_url = rag_service_url` (L23); rename both the kwarg name and the local "
        "helper parameter for consistency",
    ),
    (
        "11",
        "tests/rag/test_pipeline_http_result_kind.py",
        "helper parameter and attribute "
        '(L18, L21), the docstring mention at L160, and the call kwarg `rag_service_url=""` at '
        "L161",
    ),
    (
        "12",
        "tests/rag/test_rag_quality_regression.py",
        'kwarg occurrence at L40 (`rag_service_url="",`)',
    ),
    (
        "13",
        "tests/rag/test_stage_observability.py",
        'kwarg occurrence at L22 (`rag_service_url="",`)',
    ),
    (
        "14",
        "tests/rag/test_stage_lifecycle.py",
        "kwarg occurrence at L34 (`rag_service_url=None,`)",
    ),
    (
        "15",
        "tests/rag/test_rag_pipeline_no_cache_freshness.py",
        'kwarg occurrence at L56 (`rag_service_url="",`)',
    ),
    (
        "16",
        "tests/rag/test_augment_integration.py",
        "fixture default `rag_service_url=None` "
        "(L42) and every `_make_cfg(rag_service_url=...)` call kwarg (verified at L181, L212, "
        "L237, L268, L297, L326, L352, L377, L401, L425, L454, L483, L502, L538)",
    ),
    (
        "17",
        "tests/rag/test_augment_refiner.py",
        "fixture default `rag_service_url=None` "
        "(L42) and every `_make_cfg(rag_service_url=...)` call kwarg (same occurrence pattern as "
        "test_augment_integration.py: L181, L212, L237, L268, L297, L326, L352, L377, L401, L425, "
        "L454, L483, L502, L538)",
    ),
    (
        "18",
        "tests/rag/test_rag_pipeline_stage.py",
        "local dataclass/attribute field "
        '`rag_service_url: str = ""` (L33) and the kwarg occurrence at L65',
    ),
    (
        "19",
        "tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py",
        "assertion "
        'attributes `ns.rag_service_url == ""` (L37, L80), the test method name '
        "`test_rag_service_url_always_empty` (L76), its comment (L77), the expected-keys list "
        'entry `"rag_service_url"` (L119), and the adapter assertion '
        '`adapter.rag_service_url == ""` (L148)',
    ),
    (
        "20",
        "tests/agent/commands/test_agent_rag.py",
        'config-dict entry `"rag_service_url": "http://127.0.0.1:8010"` (L21)',
    ),
    (
        "21",
        "tests/agent/test_rag_get_cfg.py",
        'protocol-exercise kwarg `rag_service_url=""` (L26)',
    ),
]

for num, target, occ in SIMPLE_TEST_RENAME_ROWS:
    is_overlap = target in (
        "tests/rag/test_rag_pipeline.py",
        "tests/rag/test_augment_refiner.py",
    )
    extra = ""
    if target == "tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py":
        extra = (
            "\n- Rename the test method name itself (`test_rag_query_service_url_"
            "always_empty`) so the suite vocabulary matches the renamed key (name-only "
            "edit, no assertion-logic change, AC-6)."
        )
    overlap_note = (
        "\n- Overlap: this file is also targeted by the rag001 Plan procedures "
        "(appended refiner tests) and — for test_rag_pipeline.py — the rag002 Plan "
        "procedures; edit regions are disjoint, rebase before implementing."
        if is_overlap
        else ""
    )
    emit(
        f"{num}_{target.replace('/', '_')}.md",
        doc(
            f"M mechanical key rename in `{target.split('/')[-1]}`",
            target,
            "REQ-004",
            f"Rename every standalone `{OLD}` spelling in this test file to `{NEW}` with no "
            f"assertion or logic edits (REQ-004, AC-6).",
            f"- Name-only rename of: {occ}. Fixture/assertion logic unchanged.\n"
            f"- Occurrences verified 2026-10-27 by grep (standalone matches only).",
            COMMON_ASSUMPTION_RENAME + overlap_note,
            "- Test renames ride the production rename in the same commit so no intermediate "
            "state has fixtures naming a key the loader no longer recognizes (a stale fixture "
            "key would silently resolve to the `None` default and flip HTTP-mode tests to "
            "in-process mode — the MagicMock risk called out in Plan Risks).",
            "- Leave fixtures on the old spelling — rejected: they would silently build "
            "in-process configs instead of failing (Plan Risks).",
            f"1. Whole-word rename of every standalone occurrence: {occ}.\n"
            f"2. Do NOT touch `rag_pipeline_service_url` occurrences in the same "
            f"config fixtures (they are the ingestion key; REQ-003).{extra}",
            MECHANICAL_METHOD,
            "The Plan lists 14 renamed test files; this is one of them. `tests/rag/"
            "test_config_resolution.py` gets the new regression test (procedure _08), not "
            "this file.",
            RENAME_COMPAT + overlap_note,
            SECURITY_STANDARD,
            ROLLBACK_STANDARD,
            RENAME_ONLY_VALIDATION,
            f"- Zero standalone `{OLD}` occurrences remain in the file; the file's tests pass with "
            "renamed names and unchanged logic.",
            OOS_STANDARD,
        ),
    )

# --- docs (rows 22-29) ---
emit(
    "22_docs_21_rag_rag_05_01-configuration-reference.md.md",
    doc(
        "Rename key occurrences and add the two-key purpose-contrast paragraph",
        "docs/21_rag/rag_05_01-configuration-reference.md",
        "REQ-005",
        f"Rename both `{OLD}` occurrences to `{NEW}` and add an explicit paragraph contrasting "
        f"the two service-URL keys (query delegation vs ingestion callback) (REQ-005, AC-5).",
        "- Two occurrence renames (verified at L90 and L93, both negative statements about "
        "`config/agent.toml`) plus one new contrast paragraph.",
        COMMON_ASSUMPTION_RENAME
        + "\n- Overlap: the rag002 Plan procedures (implementations/20261027-144351_03_*) add "
        "the `http_timeout` paragraph to this same page; the paragraphs are disjoint and "
        "whichever implements second rebases (Plan Dependencies).",
        "- The contrast paragraph is required by the Issue's Documentation Impact: neither this "
        "page nor ADR-010 currently presents the two key names as a pair (Plan Problem).",
        "- Document the distinction only in ADR-010 — rejected: the config reference is the "
        "page operators read when configuring RAG (Plan Documentation Impact).",
        '1. Rename the occurrence in the L90 sentence ("... or `rag_service_url`. Those are '
        'owned by `config/rag_pipeline_mcp_server.toml` ...").\n'
        '2. Rename the L93 bullet ("`rag_service_url` is not a key of `config/agent.toml`, and '
        'no production process sets it to a non-empty value ...").\n'
        "3. Add a contrast paragraph (new) near those lines stating: "
        "`rag_query_service_url` selects query-path HTTP delegation (paired with "
        "`rag_auth_token` as the outbound Bearer token; default `None` = run in-process), while "
        "`rag_pipeline_service_url` is the ingestion-path callback URL read by the ingester "
        "from `config/ingester.toml` (live in the deployed config); the keys are independent "
        "and name-distinct by design (REQ-005, Assumptions pairing note).\n"
        "4. Do not restate deployment facts beyond what the renamed L93 bullet already claims.",
        "Two token renames plus a short (3-5 sentence) paragraph in the existing section voice; "
        "keep the page's negative-claim structure intact.",
        "`rag_pipeline_service_url` mentions elsewhere on this page (the "
        "`config/ingester.toml` section) stay byte-identical.",
        RENAME_COMPAT,
        SECURITY_STANDARD,
        ROLLBACK_STANDARD,
        "- `rules/toolchain.md` documentation consistency check for the 21_rag domain passes; "
        "the contrast paragraph is present (AC-5).\n" + COMMON_AC1,
        "- Page names only `rag_query_service_url` for the query key; contrast paragraph "
        "present; `rag_pipeline_service_url` sections untouched.",
        OOS_STANDARD,
    ),
)
emit(
    "23_docs_21_rag_rag_03_02_query_pipeline-rag-pipeline-class.md.md",
    doc(
        "Rename the HTTP Mode heading, body, and prevention-table occurrences",
        "docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md",
        "REQ-005",
        f"Rename all three `{OLD}` occurrences — the section heading, body sentence, and "
        f"prevention-table row — to `{NEW}` (REQ-005).",
        '- Heading rename "### HTTP Mode (`rag_service_url`)" (L36), body sentence rename '
        "(L38), prevention-table cell rename (L46). No other content changes.",
        COMMON_ASSUMPTION_RENAME,
        "- Heading renames keep any in-repo links to this page working only if the anchor is "
        "not referenced by name; grep docs/ for links to the old heading anchor before "
        "committing and update them in the same edit if found.",
        ALT_NO_ALIAS.replace(
            "Rename the ingestion key instead", "Keep the heading on the old key"
        ),
        '1. Rename L36 heading to "### HTTP Mode (`rag_query_service_url`)".\n'
        "2. Rename L38 body occurrence (keeping the `rag_auth_token` pairing sentence intact).\n"
        '3. Rename L46 prevention-table cell ("The MCP adapter hardcodes '
        '`rag_query_service_url=""` ...").',
        MECHANICAL_METHOD,
        "- Verified occurrences: L36, L38, L46.",
        RENAME_COMPAT,
        SECURITY_STANDARD,
        ROLLBACK_STANDARD,
        "- 21_rag documentation consistency check passes; grep shows zero standalone old-name "
        "occurrences on the page.",
        "- Heading, body, and table name only `rag_query_service_url`.",
        OOS_STANDARD,
    ),
)
for num, target, occ, sec in [
    (
        "24",
        "docs/21_rag/rag_03_01_query_pipeline-overview.md",
        'flow-diagram line "-> rag_service_url is configured? -> call_rag_service() ..." (L36)',
        "21_rag",
    ),
    (
        "25",
        "docs/21_rag/rag_01_system_overview.md",
        'delegation mention "HTTP delegation (`rag_service_url`) is not used in production '
        '(ADR-010)" (L180)',
        "21_rag",
    ),
    (
        "26",
        "docs/21_rag/rag_05_04-error-handling-reference.md",
        'fallback-table row "Failure when setting `rag_service_url` | Fallback to in-process '
        'pipeline" (L97)',
        "21_rag",
    ),
    (
        "27",
        "docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md",
        'adapter-pin bullet "`rag_service_url = ""` is fixed in `build_rag_cfg_adapter()`" '
        "(L41)",
        "22_mcp",
    ),
    (
        "28",
        "docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md",
        'HttpAugment presence condition "(present when `rag_service_url` is configured)" (L48)',
        "23_agent",
    ),
]:
    overlap = ""
    if target == "docs/21_rag/rag_05_04-error-handling-reference.md":
        overlap = (
            "\n- Overlap: the rag004 Plan adds a row to the RagIngester table on this "
            "same page; sections are disjoint (this edits the RagPipeline fallback "
            "table), second implementer rebases (Plan Dependencies)."
        )
    emit(
        f"{num}_{target.replace('/', '_')}.md",
        doc(
            f"M single-occurrence key rename on `{target.split('/')[-1]}`",
            target,
            "REQ-005",
            f"Rename the standalone `{OLD}` occurrence to `{NEW}` (REQ-005, AC-5).",
            f"- One occurrence rename: {occ}. No surrounding content changes.",
            COMMON_ASSUMPTION_RENAME + overlap,
            "- Single-token substitution; docs pages are high-churn (Plan Risks), so rebase "
            "immediately before editing and re-verify the occurrence line numbers.",
            ALT_NO_ALIAS,
            "1. Rename the verified occurrence.\n"
            "2. Re-grep the page to confirm no further standalone occurrence.",
            MECHANICAL_METHOD,
            f"- Domain: {sec}. Part of the 8-page docs rename set.",
            RENAME_COMPAT,
            SECURITY_STANDARD,
            ROLLBACK_STANDARD,
            f"- `{sec}` documentation consistency check passes.\n" + COMMON_AC1,
            "- Page names only `rag_query_service_url` for the query key.",
            OOS_STANDARD,
        ),
    )

emit(
    "29_docs_10_adr_adr_02_06_010_rag-fallback.md.md",
    doc(
        "Rename present-tense key references in ADR-010 with a one-time rename note",
        "docs/10_adr/adr_02_06_010_rag-fallback.md",
        "REQ-005",
        f'Rename every `{OLD}` reference to `{NEW}` and add a one-time "(renamed from '
        f'`rag_service_url`)" note at first mention, keeping the decision record and rationale '
        f"text otherwise intact (REQ-005, AC-5).",
        "- Rename of every standalone key occurrence in the ADR plus one rename note. No "
        "changes to decisions, rationale, invariant semantics, or verification-matrix logic.",
        "- 14 verified occurrences (L43, L48, L51, L56, L67, L68, L83 [3 mentions on that line "
        "region], L161, L216, L222, L226, L241, L244, L299) renamed; one rename note added; "
        "decision/rationale wording otherwise unchanged.",
        COMMON_ASSUMPTION_RENAME
        + "\n- The ADR records a decision, but its Scope and consequence paragraphs state "
        "present-tense config facts keyed on the old name; renaming them keeps the ADR truthful "
        "about today without rewriting the decision (Plan Design).",
        "- Leave the ADR untouched as a historical record — rejected: its Scope claims are "
        "present-tense production-state facts that become false after the rename (Plan Design); "
        "the one-time note preserves the history.",
        "1. At the first Scope-section mention (L43 region), append the rename note: "
        '"`rag_query_service_url` (renamed from `rag_service_url`)".\n'
        "2. Rename all remaining standalone occurrences listed above; keep INV-01's invariant "
        "statement (L161), the verification matrix row (L216, including the referenced test "
        "`tests/rag/test_pipeline_http_result_kind.py::test_no_http_mode`), and the "
        "consequences/implementation-map rows semantically identical — name substitution only.\n"
        "3. Do not rename the note's own quoted old name (it is the single allowed legacy "
        "mention, AC-5).",
        MECHANICAL_METHOD
        + " In the ADR, treat the rename note's quoted old name as the only "
        "intentional surviving occurrence.",
        "- The grep exhaustiveness check (AC-1/AC-5) whitelists exactly this one note mention.",
        RENAME_COMPAT,
        SECURITY_STANDARD,
        ROLLBACK_STANDARD,
        "- 10_adr documentation consistency check passes; ADR-010 names the new key throughout "
        "with exactly one rename note (AC-5).\n" + COMMON_AC1,
        "- Every ADR reference names `rag_query_service_url`; the one-time rename note is "
        "present; decision record wording unchanged.",
        OOS_STANDARD + "\n- Rewriting or re-deciding ADR-010's decision record.",
    ),
)

print(f"filled {len(FILES)} procedure documents")
