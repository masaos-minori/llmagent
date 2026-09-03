"""tools/_front_matter_schema.py

Shared, non-CLI helper (same role as tools/_docs_consistency_lib.py) that
gives every Front Matter tool a single source of truth for the required
field set and the `area`/`status` enums, instead of each tool hardcoding its
own copy.

If `schemas/doc_front_matter.json` exists (the artifact
`plans/20260903-124425_plan.md` REQ-006 assigns to a future documentation
Plan, not to this module), it is parsed as a draft-07 JSON Schema (matching
the existing `schemas/event_envelope.json` convention: a top-level
`required` array and per-field `enum` arrays under `properties`). When that
file does not yet exist, `load_front_matter_schema()` returns the same
required-field set every Front Matter tool already enforces today
(`title`, `area`, `tags`, `related`), with no enum restriction — i.e. calling
this module never changes behavior until the schema file is authored.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT_DIR / "schemas" / "doc_front_matter.json"

# The one bundled fallback — every current Front Matter tool's own hardcoded
# default before this module existed. Kept here, once, so no tool needs its
# own copy even in the schema-absent case.
DEFAULT_REQUIRED_FIELDS: tuple[str, ...] = ("title", "area", "tags", "related")


@dataclass(frozen=True)
class FrontMatterSchema:
    """The subset of a Front Matter JSON Schema every tool needs.

    `area_enum`/`status_enum` are `None` (not enforced) unless the schema
    file defines an `enum` for that property — matching today's behavior
    exactly when no schema file exists yet.
    """

    required_fields: tuple[str, ...]
    area_enum: tuple[str, ...] | None
    status_enum: tuple[str, ...] | None
    source: str  # SCHEMA_PATH's str, or "built-in default" when absent/unreadable


def _default_schema() -> FrontMatterSchema:
    return FrontMatterSchema(
        required_fields=DEFAULT_REQUIRED_FIELDS,
        area_enum=None,
        status_enum=None,
        source="built-in default",
    )


def load_front_matter_schema(schema_path: Path | None = None) -> FrontMatterSchema:
    """Load the canonical Front Matter schema, falling back to the built-in
    default when the schema file does not exist or cannot be parsed.

    A malformed schema file is treated the same as an absent one (falls back
    silently) rather than raising — this module's job is to be a safe,
    always-available lookup, not a schema-authoring validator.
    """
    path = schema_path if schema_path is not None else SCHEMA_PATH
    if not path.is_file():
        return _default_schema()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _default_schema()

    required = data.get("required")
    if not isinstance(required, list) or not all(isinstance(f, str) for f in required):
        required_fields = DEFAULT_REQUIRED_FIELDS
    else:
        required_fields = tuple(required)

    properties = data.get("properties")
    area_enum: tuple[str, ...] | None = None
    status_enum: tuple[str, ...] | None = None
    if isinstance(properties, dict):
        area_prop = properties.get("area")
        if isinstance(area_prop, dict):
            enum = area_prop.get("enum")
            if isinstance(enum, list) and all(isinstance(v, str) for v in enum):
                area_enum = tuple(enum)
        status_prop = properties.get("status")
        if isinstance(status_prop, dict):
            enum = status_prop.get("enum")
            if isinstance(enum, list) and all(isinstance(v, str) for v in enum):
                status_enum = tuple(enum)

    return FrontMatterSchema(
        required_fields=required_fields,
        area_enum=area_enum,
        status_enum=status_enum,
        source=str(path),
    )
