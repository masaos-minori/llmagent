"""tests/mcp_servers/file/test_file_schema_consistency.py

Schema-and-model consistency coverage for the file tool families (REQ-001, AC-1).

Group 1 pins the shared generator as the single schema source: every TOOL_LIST
inputSchema must equal build_input_schema(model) for its request model, so a local
schema helper reintroduced in the read, write, or delete tools fails here.

Group 2 pins the shared strict base: a request model built with an extra field is
rejected for every file tool. The arguments are the minimal valid set plus one
unknown key, so the rejection is attributable to the extra field alone.

Step 3a correction to the procedure: the wire path cannot carry this assertion.
No validator is registered for the file tools in tool_validators.py, and the
dispatch handlers construct the request model from cherry-picked arg keys rather
than from the whole args dict, so an extra field on POST /v1/call_tool is ignored
at runtime rather than rejected. The strict-base rejection is asserted at the model
boundary, which is where the shared base actually applies.
"""

from __future__ import annotations

from typing import Any

import pytest
from mcp_servers.file import delete_tools, read_tools, write_tools
from mcp_servers.file.delete_models import DeleteDirectoryRequest, DeleteFileRequest
from mcp_servers.file.read_models import (
    DirectoryTreeRequest,
    GetFileInfoRequest,
    GrepFilesRequest,
    ListDirectoryRequest,
    ReadMediaFileRequest,
    ReadMultipleFilesRequest,
    ReadTextFileRequest,
    SearchFilesRequest,
)
from mcp_servers.file.write_models import (
    CreateDirectoryRequest,
    EditFileRequest,
    MoveFileRequest,
    WriteFileRequest,
)
from mcp_servers.request_contract import build_input_schema
from pydantic import BaseModel, ValidationError

FAMILIES: list[tuple[str, Any, dict[str, type[BaseModel]]]] = [
    (
        "read",
        read_tools,
        {
            "list_directory": ListDirectoryRequest,
            "list_directory_with_sizes": ListDirectoryRequest,
            "directory_tree": DirectoryTreeRequest,
            "read_text_file": ReadTextFileRequest,
            "read_media_file": ReadMediaFileRequest,
            "read_multiple_files": ReadMultipleFilesRequest,
            "search_files": SearchFilesRequest,
            "grep_files": GrepFilesRequest,
            "get_file_info": GetFileInfoRequest,
        },
    ),
    (
        "write",
        write_tools,
        {
            "write_file": WriteFileRequest,
            "edit_file": EditFileRequest,
            "create_directory": CreateDirectoryRequest,
            "move_file": MoveFileRequest,
        },
    ),
    (
        "delete",
        delete_tools,
        {
            "delete_file": DeleteFileRequest,
            "delete_directory": DeleteDirectoryRequest,
        },
    ),
]

# Minimal valid arguments per tool, so the only rejection cause is the extra field.
VALID_ARGS: dict[str, dict[str, Any]] = {
    "list_directory": {"path": "/tmp/schema-consistency"},
    "list_directory_with_sizes": {"path": "/tmp/schema-consistency"},
    "directory_tree": {"path": "/tmp/schema-consistency"},
    "read_text_file": {"path": "/tmp/schema-consistency"},
    "read_media_file": {"path": "/tmp/schema-consistency"},
    "read_multiple_files": {"paths": ["/tmp/schema-consistency"]},
    "search_files": {"path": "/tmp/schema-consistency", "pattern": "*"},
    "grep_files": {"path": "/tmp/schema-consistency", "pattern": "x"},
    "get_file_info": {"path": "/tmp/schema-consistency"},
    "write_file": {"path": "/tmp/schema-consistency", "content": "x"},
    "edit_file": {
        "path": "/tmp/schema-consistency",
        "edits": [{"old_text": "a", "new_text": "b"}],
    },
    "create_directory": {"path": "/tmp/schema-consistency"},
    "move_file": {
        "source": "/tmp/schema-consistency-a",
        "destination": "/tmp/schema-consistency-b",
    },
    "delete_file": {"path": "/tmp/schema-consistency"},
    "delete_directory": {"path": "/tmp/schema-consistency"},
}


class TestSchemaEquality:
    """Every discovery schema is generated from its request model, not hand-built."""

    @pytest.mark.parametrize("family,tools_module,model_map", FAMILIES)
    def test_discovery_schema_equals_generated_schema(
        self, family: str, tools_module: Any, model_map: dict[str, type[BaseModel]]
    ) -> None:
        for tool in tools_module.TOOL_LIST:
            model = model_map[tool["name"]]
            assert tool["inputSchema"] == build_input_schema(model), (
                f"{family} tool {tool['name']} schema is not generated from the model"
            )


class TestExtraFieldRejection:
    """The shared strict base rejects unknown arguments at the model boundary."""

    @pytest.mark.parametrize("family,tools_module,model_map", FAMILIES)
    def test_extra_field_is_rejected(
        self, family: str, tools_module: Any, model_map: dict[str, type[BaseModel]]
    ) -> None:
        for tool_name, model in model_map.items():
            args = {**VALID_ARGS[tool_name], "unexpected_field": "x"}
            with pytest.raises(ValidationError):
                model.model_validate(args)
