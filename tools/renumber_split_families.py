#!/usr/bin/env python3
"""Insert ordering numbers into split-file names so `ls`/alphabetical sort
matches the intended reading order (per each domain's document-guide File
Index), then rewrite every cross-reference across docs/ and routing.md.

Usage: uv run python tools/renumber_split_families.py [--apply]
Without --apply, only prints the planned renames (dry run).
"""

from __future__ import annotations

import argparse
import glob
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"

# Each entry: (old_filename, new_filename). Order within a list reflects the
# intended reading order and is used only for human review, not by the script.
RENAMES: list[tuple[str, str]] = []


def family(prefix: str, names: list[str], pad: int = 2, sep: str = "_") -> None:
    for i, name in enumerate(names, start=1):
        n = str(i).zfill(pad)
        RENAMES.append((f"{prefix}{name}.md", f"{prefix}{n}{sep}{name}.md"))


# 01_overview-arch-*
family("01_overview-arch-", ["process", "pipelines", "features"], sep="-")
# 01_overview-files-*
family(
    "01_overview-files-",
    ["build", "rag", "scripts", "shared", "config", "misc"],
    sep="-",
)

# 03_rag_02_ingestion_pipeline-*
family(
    "03_rag_02_",
    [
        "ingestion_pipeline-overview",
        "ingestion_pipeline-crawler",
        "ingestion_pipeline-chunksplitter",
        "ingestion_pipeline-ingester",
        "ingestion_pipeline-document-manager",
        "ingestion_pipeline-supporting-components",
        "ingestion_pipeline-utils",
        "ingestion_pipeline-shared",
        "ingestion_pipeline-shared-utilities",
    ],
)

# 03_rag_03_query_pipeline (base file gets a proper suffix + number 01)
RENAMES.append(
    ("03_rag_03_query_pipeline.md", "03_rag_03_01_query_pipeline-overview.md")
)
for i, name in enumerate(
    [
        "rag-pipeline-class",
        "context-and-diagnostics",
        "search-stages",
        "augment-stages",
        "helpers-and-cache",
        "tests",
    ],
    start=2,
):
    RENAMES.append(
        (
            f"03_rag_03_query_pipeline-{name}.md",
            f"03_rag_03_{str(i).zfill(2)}_query_pipeline-{name}.md",
        )
    )

# 03_rag_04_dto-*
RENAMES.append(("03_rag_04_dto-models_data.md", "03_rag_04_01_dto-models_data.md"))
RENAMES.append(("03_rag_04_dto-models_result.md", "03_rag_04_02_dto-models_result.md"))
RENAMES.append(("03_rag_04_dto-models_audit.md", "03_rag_04_03_dto-models_audit.md"))
RENAMES.append(("03_rag_04_dto-models_config.md", "03_rag_04_04_dto-models_config.md"))
RENAMES.append(("03_rag_04_dto-types.md", "03_rag_04_05_dto-types.md"))

# 03_rag_05_* — two unnumbered outliers continue the existing 1-6 convention
RENAMES.append(
    (
        "03_rag_05_rag-index-consistency-checks.md",
        "03_rag_05_7-rag-index-consistency-checks.md",
    )
)
RENAMES.append(
    (
        "03_rag_05_rag-mcp-internal-operations-direct-db-access.md",
        "03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md",
    )
)

# 04_mcp_06_*
family(
    "04_mcp_06_",
    [
        "purpose",
        "configuration-file-inventory",
        "mcpserverconfig-fields-agenttoml-mcp_servers",
        "major-default-values",
        "long-running-http-operation-startup_modesubprocess",
        "verification-methods",
        "reading-audit-logs",
        "end-to-end-tool-call-tracing",
        "mcp-failure-diagnosis",
        "settings-with-high-operational-impact",
        "startup-validation-behavior-tool_definitions_strict",
        "watchdog-configuration-monitoring",
        "watchdog-health-reasons-scheduling",
        "new-tool-registration-procedure",
        "new-mcp-server-addition-checklist",
        "pre-production-fail-open-checklist",
        "local-to-production-auth-migration",
    ],
)

# 05_agent_03_turn-processing-flow-*
family(
    "05_agent_03_",
    [
        "turn-processing-flow-overview",
        "turn-processing-flow-llm-tool-loop",
        "turn-processing-flow-workflow-engine",
    ],
)
# 05_agent_04_state-and-persistence-*
family(
    "05_agent_04_",
    [
        "state-and-persistence-state-model",
        "state-and-persistence-history-compression",
        "state-and-persistence-platform-databases",
    ],
)
# 05_agent_06_tool-execution-and-approval-*
family(
    "05_agent_06_",
    [
        "tool-execution-and-approval-execution",
        "tool-execution-and-approval-approval",
        "tool-execution-and-approval-concurrency-safety",
        "tool-execution-and-approval-canonical",
    ],
)
# 05_agent_07_cli-and-commands-* (includes slash-commands-* sub-family)
family(
    "05_agent_07_",
    [
        "cli-and-commands-cli-reference",
        "cli-and-commands-cliview",
        "cli-and-commands-command-registry",
        "cli-and-commands-purpose",
        "cli-and-commands-repl-io",
        "cli-and-commands-hot-reload",
        "cli-and-commands-migration-notes",
        "cli-and-commands-slash-commands-session-mcp",
        "cli-and-commands-slash-commands-context-db",
        "cli-and-commands-slash-commands-workflow-debug",
        "cli-and-commands-slash-commands-memory-other",
    ],
)
# 05_agent_08_configuration-*
family(
    "05_agent_08_",
    [
        "configuration-loading-agent-config",
        "configuration-llm-rag",
        "configuration-tools-memory",
        "configuration-mcp-approval-obs",
    ],
)
# 05_agent_09_data-layer-*
family(
    "05_agent_09_",
    [
        "data-layer-session-db",
        "data-layer-access-patterns",
        "data-layer-indexing-boundaries",
    ],
)
# 05_agent_10_operations-and-observability-*
family(
    "05_agent_10_",
    [
        "operations-and-observability-startup-and-health",
        "operations-and-observability-audit-and-otel",
        "operations-and-observability-workflow-observability",
        "operations-and-observability-validation-and-troubleshooting",
        "operations-and-observability-monitoring",
        "operations-and-observability-rag-diagnostics-and-memory",
    ],
)
# 05_agent_11_extension-points-*
family(
    "05_agent_11_",
    [
        "extension-points-plugin-command",
        "extension-points-tool-registration",
        "extension-points-registry-rules",
    ],
)
# 05_agent_12_memory-*
family(
    "05_agent_12_",
    [
        "memory-overview-and-modes",
        "memory-gate-data-model-search",
        "memory-module-ref-core-and-store",
        "memory-module-ref-retrieval-and-injection",
        "memory-module-ref-extraction-and-facade",
        "memory-module-ref-ops-and-scoring",
    ],
)

# 06_eventbus_02_*
family(
    "06_eventbus_02_",
    [
        "publish-replay",
        "subscribe-ack",
        "nack-health-dlq",
        "dlq-background-loop",
        "failure-behavior-summary",
    ],
)
# 06_eventbus_05_*
family(
    "06_eventbus_05_",
    [
        "config-env-and-fields",
        "bind-address-and-start",
        "health-endpoint-semantics",
        "consumer-id-stability",
        "delivery-operations",
        "dlq-operations",
        "validation-status",
    ],
)
# 06_eventbus_06_*
family(
    "06_eventbus_06_",
    [
        "reference-api-core-modules",
        "reference-api-route-handlers",
        "reference-api-broker-and-offsets",
    ],
)

# 90_shared_01_overview-*
family(
    "90_shared_01_",
    [
        "overview-purpose-and-scope",
        "overview-layer-responsibilities",
        "overview-constraints-and-reference",
    ],
)
# 90_shared_02_types_and_protocols-*
family(
    "90_shared_02_",
    [
        "types_and_protocols-core-types",
        "types_and_protocols-tool-and-execution-dto",
        "types_and_protocols-reference",
    ],
)
# 90_shared_03_runtime_and_execution-*
family(
    "90_shared_03_",
    [
        "runtime_and_execution-config-and-logging",
        "runtime_and_execution-plugin-and-tool-runtime",
        "runtime_and_execution-llm-and-mcp-clients",
        "runtime_and_execution-caching-and-reference",
    ],
)
# 90_shared_04_db_architecture_and_schema-*
family(
    "90_shared_04_",
    [
        "db_architecture_and_schema-overview-and-config",
        "db_architecture_and_schema-schema-reference",
        "db_architecture_and_schema-migration-and-scaling",
    ],
)
# 90_shared_05_db_api_and_operations-*
family(
    "90_shared_05_",
    [
        "db_api_and_operations-module-boundaries-and-helper",
        "db_api_and_operations-protocol-and-backend",
        "db_api_and_operations-maintenance-and-rotation",
        "db_api_and_operations-recovery-and-reference",
    ],
)


def verify_sources_exist() -> list[str]:
    missing = []
    for old, _new in RENAMES:
        if not (DOCS_DIR / old).is_file():
            missing.append(old)
    return missing


def apply_renames() -> None:
    for old, new in RENAMES:
        old_path = DOCS_DIR / old
        new_path = DOCS_DIR / new
        subprocess.run(
            ["git", "mv", str(old_path), str(new_path)], check=True, cwd=ROOT_DIR
        )
        print(f"renamed {old} -> {new}")


def update_references() -> None:
    mapping = dict(RENAMES)
    keys_sorted = sorted(mapping.keys(), key=len, reverse=True)
    files = glob.glob(str(DOCS_DIR / "*.md")) + [str(ROOT_DIR / "routing.md")]
    changed = 0
    for fp in files:
        path = Path(fp)
        content = path.read_text(encoding="utf-8")
        orig = content
        for old in keys_sorted:
            new = mapping[old]
            content = content.replace(old, new)
        if content != orig:
            path.write_text(content, encoding="utf-8")
            changed += 1
    print(f"updated references in {changed} files")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply", action="store_true", help="Perform the rename and reference update"
    )
    args = parser.parse_args()

    missing = verify_sources_exist()
    if missing:
        print(f"ERROR: {len(missing)} source file(s) not found:")
        for m in missing:
            print(f"  {m}")
        return

    print(f"{len(RENAMES)} planned renames:")
    for old, new in RENAMES:
        print(f"  {old} -> {new}")

    if args.apply:
        apply_renames()
        update_references()
    else:
        print("\nDry run only. Re-run with --apply to perform renames.")


if __name__ == "__main__":
    main()
