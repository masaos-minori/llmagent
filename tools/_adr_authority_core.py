"""tools/_adr_authority_core.py

Shared, non-CLI validator core for the ADR authority model (ADR-016), same
role as tools/_front_matter_schema.py and tools/_docs_consistency_lib.py:
one implementation of the model schema, finding codes, and validators that
tools/check_adr_authority.py (standalone CI validator) and
tools/check_adr_reference.py (front matter cross-check) both import.

Finding codes (ADR-016 Decision 4/7, plan adrauth001 REQ-004/REQ-005):
  DUP_PRIMARY            one decision_target claims two primary ADRs
  DANGLING_ADR           a model ADR id resolves to no adr_02_*_NNN_*.md file
  AUTHORITY_CYCLE        a cycle of non-Reference edges, or a bidirectional
                         Reference pair violating the intentional-pair rule
  ASSUMPTION_DRIFT       a config-check assumption no longer matches live config
  EDGE_UNKNOWN_TYPE      an adr_edge edge_type outside the closed taxonomy
  FRONTMATTER_DIVERGENCE an ADR front matter related edge and a model edge
                         disagree (checked in both directions, ADR-016 Decision 7)
  EDGE_DUPLICATE         two [[adr_edge]] rows carry the same (from, to) pair
  ADR_STATUS_INVALID     a model-referenced ADR has a Status outside governance_01
                         "ADR Status Definitions", a Withdrawn ADR owns a decision
                         target or a non-Reference edge, or a Proposed ADR claims
                         primary authority

Not a check script itself — tools/check_adr_authority.py is the CLI.
"""

from __future__ import annotations

import re
import sys
import tomllib
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT_DIR / "config" / "adr_authority.toml"
ADR_DIR = ROOT_DIR / "docs" / "10_adr"
AGENT_CONFIG_PATH = ROOT_DIR / "config" / "agent.toml"
EVENTBUS_CONFIG_PATH = ROOT_DIR / "config" / "eventbus.toml"
GOVERNANCE_01_PATH = (
    ROOT_DIR / "docs" / "00_governance" / "governance_01_documentation-policy.md"
)

EDGE_TYPES: frozenset[str] = frozenset(
    ("Requires", "Governs", "Specializes", "Extends", "Exception-to", "Reference")
)
VALIDATION_METHODS: frozenset[str] = frozenset(("config-check", "manual-review"))

# ADR body files are `adr_02_<group>_<NNN>_<slug>.md`; the NNN is the ADR id.
# adr_01_index.md and adr_00_document-guide.md list ADR paths as navigation
# links, not edges, so only this pattern participates in the cross-check.
ADR_FILE_RE = re.compile(r"^adr_02_\d{2}_(\d{3})_.*\.md$")

# Config key patterns this core can assert (ADR-016 Decision 5 config-check).
# Any pattern outside this set fails closed in _check_config_key.
LOOPBACK_PATTERN = "mcp_servers.*.url"
EVENTBUS_HOST_PATTERN = "eventbus.host"
LOOPBACK_HOSTS: frozenset[str] = frozenset({"127.0.0.1", "::1", "localhost"})


class AuthorityModelError(Exception):
    """The model file is structurally invalid (unreadable TOML, missing fields).

    Reported as a tool error rather than a finding code: a broken model file
    cannot be partially validated (fail-closed)."""


# ---------------------------------------------------------------------------
# Model data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SupplementalADR:
    adr: str
    limit: str


@dataclass(frozen=True)
class AuthorityEntry:
    decision_target: str
    primary_adr: str
    supplemental_adrs: tuple[SupplementalADR, ...]


@dataclass(frozen=True)
class AdrEdge:
    from_adr: str
    to_adr: str
    edge_type: str
    intentional: bool
    note: str
    # Model-file row label recorded at load time (e.g. "[[adr_edge]] #3"); used
    # by EDGE_DUPLICATE findings to name every duplicate row.
    label: str = ""


@dataclass(frozen=True)
class Assumption:
    id: str
    name: str
    current_value: str
    applicable_adrs: tuple[str, ...]
    validation_method: str
    config_keys: tuple[str, ...]
    owner: str
    review_triggers: tuple[str, ...]


@dataclass(frozen=True)
class AuthorityModel:
    version: str
    authorities: tuple[AuthorityEntry, ...]
    edges: tuple[AdrEdge, ...]
    assumptions: tuple[Assumption, ...]


@dataclass(frozen=True)
class Finding:
    code: str
    location: str  # file or entry the finding points at
    message: str


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def _require_str(entry: dict, key: str, label: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise AuthorityModelError(f"{label}: field {key!r} missing or not a string")
    return value


def load_model(path: Path = MODEL_PATH) -> AuthorityModel:
    """Parse and structurally validate the authority model file."""
    if not path.is_file():
        raise AuthorityModelError(f"model file not found: {path}")
    data = tomllib.loads(path.read_text(encoding="utf-8"))

    version = data.get("version")
    if not isinstance(version, str) or not version:
        # String form per the config/documentation_canonical_sources.toml registry idiom.
        raise AuthorityModelError("model: field 'version' missing or not a string")

    authorities: list[AuthorityEntry] = []
    for i, entry in enumerate(data.get("authority", [])):
        label = f"[[authority]] #{i + 1}"
        if not isinstance(entry, dict):
            raise AuthorityModelError(f"{label}: not a table")
        supplemental: list[SupplementalADR] = []
        raw_supplemental = entry.get("supplemental_adrs", [])
        if not isinstance(raw_supplemental, list):
            raise AuthorityModelError(f"{label}: supplemental_adrs is not a list")
        for sup in raw_supplemental:
            if not isinstance(sup, dict):
                raise AuthorityModelError(f"{label}: supplemental entry is not a table")
            supplemental.append(
                SupplementalADR(
                    adr=_require_str(sup, "adr", f"{label} supplemental"),
                    limit=_require_str(sup, "limit", f"{label} supplemental"),
                )
            )
        authorities.append(
            AuthorityEntry(
                decision_target=_require_str(entry, "decision_target", label),
                primary_adr=_require_str(entry, "primary_adr", label),
                supplemental_adrs=tuple(supplemental),
            )
        )

    edges: list[AdrEdge] = []
    for i, entry in enumerate(data.get("adr_edge", [])):
        label = f"[[adr_edge]] #{i + 1}"
        if not isinstance(entry, dict):
            raise AuthorityModelError(f"{label}: not a table")
        intentional = entry.get("intentional", False)
        if not isinstance(intentional, bool):
            raise AuthorityModelError(f"{label}: intentional is not a boolean")
        note = entry.get("note", "")
        if not isinstance(note, str):
            raise AuthorityModelError(f"{label}: note is not a string")
        edges.append(
            AdrEdge(
                from_adr=_require_str(entry, "from", label),
                to_adr=_require_str(entry, "to", label),
                edge_type=_require_str(entry, "edge_type", label),
                intentional=intentional,
                note=note,
                label=label,
            )
        )

    assumptions: list[Assumption] = []
    for i, entry in enumerate(data.get("assumption", [])):
        label = f"[[assumption]] #{i + 1}"
        if not isinstance(entry, dict):
            raise AuthorityModelError(f"{label}: not a table")
        applicable = _require_str_list(entry, "applicable_adrs", label)
        triggers = entry.get("review_triggers", [])
        if not isinstance(triggers, list) or not all(
            isinstance(t, str) for t in triggers
        ):
            raise AuthorityModelError(
                f"{label}: review_triggers is not a list of strings"
            )
        config_keys = entry.get("config_keys", [])
        if not isinstance(config_keys, list) or not all(
            isinstance(k, str) for k in config_keys
        ):
            raise AuthorityModelError(f"{label}: config_keys is not a list of strings")
        assumptions.append(
            Assumption(
                id=_require_str(entry, "id", label),
                name=_require_str(entry, "name", label),
                current_value=_require_str(entry, "current_value", label),
                applicable_adrs=applicable,
                validation_method=_require_str(entry, "validation_method", label),
                config_keys=tuple(config_keys),
                owner=_require_str(entry, "owner", label),
                review_triggers=tuple(triggers),
            )
        )

    return AuthorityModel(
        version=version,
        authorities=tuple(authorities),
        edges=tuple(edges),
        assumptions=tuple(assumptions),
    )


def _require_str_list(entry: dict, key: str, label: str) -> tuple[str, ...]:
    value = entry.get(key)
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(v, str) and v for v in value)
    ):
        raise AuthorityModelError(
            f"{label}: field {key!r} missing or not a list of strings"
        )
    return tuple(value)


# ---------------------------------------------------------------------------
# ADR id resolution (DANGLING_ADR)
# ---------------------------------------------------------------------------


def adr_files_by_id(adr_dir: Path = ADR_DIR) -> dict[str, str]:
    """Map `ADR-NNN` -> filename for every ADR body file present on disk."""
    found: dict[str, str] = {}
    for path in sorted(adr_dir.glob("adr_02_*.md")):
        match = ADR_FILE_RE.match(path.name)
        if match:
            found[f"ADR-{int(match.group(1)):03d}"] = path.name
    return found


def _model_adr_ids(model: AuthorityModel) -> list[tuple[str, str]]:
    """Every (adr_id, source-entry label) pair the model references."""
    refs: list[tuple[str, str]] = []
    for entry in model.authorities:
        refs.append(
            (entry.primary_adr, f"[[authority]] {entry.decision_target} primary_adr")
        )
        for sup in entry.supplemental_adrs:
            refs.append(
                (sup.adr, f"[[authority]] {entry.decision_target} supplemental")
            )
    for edge in model.edges:
        refs.append(
            (edge.from_adr, f"[[adr_edge]] {edge.from_adr} -> {edge.to_adr} from")
        )
        refs.append((edge.to_adr, f"[[adr_edge]] {edge.from_adr} -> {edge.to_adr} to"))
    for assumption in model.assumptions:
        for adr in assumption.applicable_adrs:
            refs.append((adr, f"[[assumption]] {assumption.id} applicable_adrs"))
    return refs


# ---------------------------------------------------------------------------
# Validators (ADR-016 INV-01, INV-02, INV-05)
# ---------------------------------------------------------------------------


def check_duplicate_primaries(model: AuthorityModel) -> list[Finding]:
    """INV-01: a decision_target listed in two [[authority]] entries is DUP_PRIMARY."""
    findings: list[Finding] = []
    seen: dict[str, str] = {}
    for entry in model.authorities:
        if entry.decision_target in seen:
            findings.append(
                Finding(
                    code="DUP_PRIMARY",
                    location="config/adr_authority.toml",
                    message=(
                        f"decision_target {entry.decision_target!r} has two primaries: "
                        f"{seen[entry.decision_target]} and {entry.primary_adr}"
                    ),
                )
            )
        else:
            seen[entry.decision_target] = entry.primary_adr
        for sup in entry.supplemental_adrs:
            if sup.adr == entry.primary_adr:
                findings.append(
                    Finding(
                        code="DUP_PRIMARY",
                        location="config/adr_authority.toml",
                        message=(
                            f"decision_target {entry.decision_target!r} lists primary "
                            f"{entry.primary_adr} as a supplemental entry"
                        ),
                    )
                )
    return findings


def check_dangling_adrs(
    model: AuthorityModel, adr_dir: Path = ADR_DIR
) -> list[Finding]:
    """Every model ADR id must resolve to an adr_02_*_NNN_*.md file on disk."""
    known = adr_files_by_id(adr_dir)
    findings: list[Finding] = []
    for adr_id, label in _model_adr_ids(model):
        if adr_id not in known:
            findings.append(
                Finding(
                    code="DANGLING_ADR",
                    location="config/adr_authority.toml",
                    message=f"{label} references {adr_id}, which has no ADR file under docs/10_adr/",
                )
            )
    return findings


def check_edge_types(model: AuthorityModel) -> list[Finding]:
    """ADR-016 Decision 3: edge_type is restricted to the closed taxonomy."""
    return [
        Finding(
            code="EDGE_UNKNOWN_TYPE",
            location="config/adr_authority.toml",
            message=(
                f"edge {edge.from_adr} -> {edge.to_adr} has unknown edge_type "
                f"{edge.edge_type!r}; allowed: {', '.join(sorted(EDGE_TYPES))}"
            ),
        )
        for edge in model.edges
        if edge.edge_type not in EDGE_TYPES
    ]


def check_duplicate_edges(model: AuthorityModel) -> list[Finding]:
    """Pair-based consumers key on (from, to) and would silently overwrite a
    duplicate row; every duplicate pair must fail as EDGE_DUPLICATE, naming
    each duplicate row location."""
    groups: dict[tuple[str, str], list[str]] = {}
    for edge in model.edges:
        groups.setdefault((edge.from_adr, edge.to_adr), []).append(edge.label)
    findings: list[Finding] = []
    for (from_adr, to_adr), labels in sorted(groups.items()):
        if len(labels) > 1:
            findings.append(
                Finding(
                    code="EDGE_DUPLICATE",
                    location="config/adr_authority.toml",
                    message=(
                        f"edge {from_adr} -> {to_adr} appears {len(labels)} times "
                        f"({', '.join(labels)}); (from, to) pairs must be unique"
                    ),
                )
            )
    return findings


def check_authority_cycles(model: AuthorityModel) -> list[Finding]:
    """INV-02: the authority graph (non-Reference edges) is acyclic, and each
    bidirectional pair is either one typed edge plus one intentional Reference
    edge carrying a note, or two intentional Reference edges each carrying a note."""
    findings: list[Finding] = []

    typed = [
        edge
        for edge in model.edges
        if edge.edge_type in EDGE_TYPES and edge.edge_type != "Reference"
    ]
    adjacency: dict[str, list[tuple[str, str]]] = {}
    for edge in typed:
        adjacency.setdefault(edge.from_adr, []).append((edge.to_adr, edge.edge_type))

    # Iterative DFS with 0=unvisited, 1=on-stack, 2=done; a back edge closes a cycle.
    state: dict[str, int] = {}
    reported: set[frozenset[str]] = set()
    for start in sorted(adjacency):
        if state.get(start, 0) != 0:
            continue
        state[start] = 1
        stack: list[tuple[str, int, list[str]]] = [(start, 0, [start])]
        while stack:
            node, idx, path = stack[-1]
            neighbours = adjacency.get(node, [])
            if idx >= len(neighbours):
                state[node] = 2
                stack.pop()
                continue
            stack[-1] = (node, idx + 1, path)
            nxt, edge_type = neighbours[idx]
            if state.get(nxt, 0) == 1:
                cycle = path[path.index(nxt) :] + [nxt]
                key = frozenset(cycle)
                if key not in reported:
                    reported.add(key)
                    findings.append(
                        Finding(
                            code="AUTHORITY_CYCLE",
                            location="config/adr_authority.toml",
                            message=(
                                "authority graph cycle: "
                                + " -> ".join(
                                    f"{a} ({edge_type})"
                                    for a, edge_type in zip(
                                        cycle, _cycle_edge_types(cycle, adjacency)
                                    )
                                )
                            ),
                        )
                    )
            elif state.get(nxt, 0) == 0:
                state[nxt] = 1
                stack.append((nxt, 0, path + [nxt]))

    # Bidirectional pair rule: for each pair with edges in both directions,
    # either exactly one direction is typed and the other is an intentional
    # Reference with a note, or both directions are intentional Reference edges
    # each with a note (ADR-016 INV-02, reference-only pair form). Both-typed
    # pairs are caught by the DFS above.
    by_pair = {(edge.from_adr, edge.to_adr): edge for edge in model.edges}
    for (a, b), edge in sorted(by_pair.items()):
        reverse = by_pair.get((b, a))
        if reverse is None or a > b:
            continue
        sides = (edge, reverse)
        typed_sides = [s for s in sides if s.edge_type != "Reference"]
        reference_sides = [s for s in sides if s.edge_type == "Reference"]
        for ref in reference_sides:
            if not ref.intentional or not ref.note:
                findings.append(
                    Finding(
                        code="AUTHORITY_CYCLE",
                        location="config/adr_authority.toml",
                        message=(
                            f"unflagged bidirectional reference {a} <-> {b}: the Reference "
                            f"edge {ref.from_adr} -> {ref.to_adr} needs intentional = true "
                            "and a note recording the ownership split"
                        ),
                    )
                )
        if not typed_sides and any(
            not ref.intentional or not ref.note for ref in reference_sides
        ):
            findings.append(
                Finding(
                    code="AUTHORITY_CYCLE",
                    location="config/adr_authority.toml",
                    message=(
                        f"reference-only bidirectional pair {a} <-> {b}: per ADR-016 INV-02 "
                        "a pair with no typed direction requires every Reference direction "
                        "to carry intentional = true with a note"
                    ),
                )
            )
    return findings


def _cycle_edge_types(
    cycle: list[str], adjacency: dict[str, list[tuple[str, str]]]
) -> list[str]:
    """Edge types matching the zip() pairs of a rendered cycle path."""
    types: list[str] = []
    for a, b in zip(cycle, cycle[1:]):
        for nxt, edge_type in adjacency.get(a, []):
            if nxt == b:
                types.append(edge_type)
                break
    return types


def check_assumptions(
    model: AuthorityModel,
    config_path: Path = AGENT_CONFIG_PATH,
    eventbus_config_path: Path = EVENTBUS_CONFIG_PATH,
) -> list[Finding]:
    """INV-05: config-check assumptions are asserted against live configuration;
    manual-review assumptions are not policed by this tool (ADR-016 Decision 5)."""
    findings: list[Finding] = []
    config: dict | None = None
    for assumption in model.assumptions:
        if assumption.validation_method not in VALIDATION_METHODS:
            findings.append(
                Finding(
                    code="ASSUMPTION_DRIFT",
                    location="config/adr_authority.toml",
                    message=(
                        f"assumption {assumption.id} has unknown validation_method "
                        f"{assumption.validation_method!r}; allowed: {', '.join(sorted(VALIDATION_METHODS))}"
                    ),
                )
            )
            continue
        if assumption.validation_method != "config-check":
            continue
        if config is None:
            config = tomllib.loads(config_path.read_text(encoding="utf-8"))
        eventbus_config: dict | None = None
        if EVENTBUS_HOST_PATTERN in assumption.config_keys:
            eventbus_config = _load_toml(eventbus_config_path)
        for key_pattern in assumption.config_keys:
            findings.extend(
                _check_config_key(assumption, key_pattern, config, eventbus_config)
            )
        if not assumption.config_keys:
            findings.append(
                Finding(
                    code="ASSUMPTION_DRIFT",
                    location="config/adr_authority.toml",
                    message=(
                        f'assumption {assumption.id} is validation_method = "config-check" '
                        "but declares no config_keys to assert"
                    ),
                )
            )
        if any(
            key_pattern in (LOOPBACK_PATTERN, EVENTBUS_HOST_PATTERN)
            for key_pattern in assumption.config_keys
        ) and not any(token in assumption.current_value for token in LOOPBACK_HOSTS):
            findings.append(
                Finding(
                    code="ASSUMPTION_DRIFT",
                    location="config/adr_authority.toml",
                    message=(
                        f"assumption {assumption.id}: current_value no longer states the "
                        f"loopback binding asserted against {LOOPBACK_PATTERN} / "
                        f"{EVENTBUS_HOST_PATTERN}"
                    ),
                )
            )
    return findings


def _load_toml(path: Path) -> dict | None:
    """Read a TOML config file; None when missing or undecodable (the caller
    reports the fail-closed finding)."""
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None


def _check_config_key(
    assumption: Assumption,
    key_pattern: str,
    config: dict,
    eventbus_config: dict | None,
) -> list[Finding]:
    if key_pattern == LOOPBACK_PATTERN:
        return _check_mcp_loopback(assumption, config)
    if key_pattern == EVENTBUS_HOST_PATTERN:
        return _check_eventbus_host(assumption, eventbus_config)
    return [
        Finding(
            code="ASSUMPTION_DRIFT",
            location="config/adr_authority.toml",
            message=(
                f"assumption {assumption.id}: no validator assertion is implemented "
                f"for config key pattern {key_pattern!r} (fail-closed)"
            ),
        )
    ]


def _check_mcp_loopback(assumption: Assumption, config: dict) -> list[Finding]:
    findings: list[Finding] = []
    servers = config.get("mcp_servers")
    if not isinstance(servers, dict) or not servers:
        return [
            Finding(
                code="ASSUMPTION_DRIFT",
                location="config/agent.toml",
                message=(
                    f"assumption {assumption.id}: config has no [mcp_servers.*] entries "
                    f"to assert {LOOPBACK_PATTERN} against"
                ),
            )
        ]
    for name, server in sorted(servers.items()):
        url = server.get("url") if isinstance(server, dict) else None
        if not isinstance(url, str) or not url:
            findings.append(
                Finding(
                    code="ASSUMPTION_DRIFT",
                    location="config/agent.toml",
                    message=(
                        f"assumption {assumption.id}: mcp_servers.{name} has no url "
                        f"to assert {LOOPBACK_PATTERN} against"
                    ),
                )
            )
            continue
        host = urllib.parse.urlparse(url).hostname or ""
        if host not in LOOPBACK_HOSTS:
            findings.append(
                Finding(
                    code="ASSUMPTION_DRIFT",
                    location="config/agent.toml",
                    message=(
                        f"assumption {assumption.id} ({assumption.name}): "
                        f"mcp_servers.{name}.url host {host!r} is not loopback "
                        f"({', '.join(sorted(LOOPBACK_HOSTS))})"
                    ),
                )
            )
    return findings


def _check_eventbus_host(
    assumption: Assumption, eventbus_config: dict | None
) -> list[Finding]:
    """REQ-006 (ARCH-002): `eventbus.host` asserts config/eventbus.toml binds
    the EventBus to a loopback address; an absent key asserts the documented
    127.0.0.1 default of scripts/eventbus/config.py."""
    if eventbus_config is None:
        return [
            Finding(
                code="ASSUMPTION_DRIFT",
                location="config/eventbus.toml",
                message=(
                    f"assumption {assumption.id}: config/eventbus.toml is missing or "
                    f"unreadable; cannot assert {EVENTBUS_HOST_PATTERN} (fail-closed)"
                ),
            )
        ]
    host = eventbus_config.get("host")
    if host is None:
        return []  # absent key: the documented 127.0.0.1 default is asserted
    if not isinstance(host, str) or host not in LOOPBACK_HOSTS:
        return [
            Finding(
                code="ASSUMPTION_DRIFT",
                location="config/eventbus.toml",
                message=(
                    f"assumption {assumption.id} ({assumption.name}): eventbus.host "
                    f"{host!r} is not loopback ({', '.join(sorted(LOOPBACK_HOSTS))})"
                ),
            )
        ]
    return []


# ---------------------------------------------------------------------------
# ADR status validation (governance_01 "ADR Status Definitions"; REQ-004/REQ-005)
# ---------------------------------------------------------------------------

_STATUS_SECTION_RE = re.compile(r"^## ADR Status Definitions[ \t]*$", re.MULTILINE)
_STATUS_BULLET_RE = re.compile(r"^- `([A-Za-z-]+)`:", re.MULTILINE)


def _allowed_statuses(governance_path: Path) -> tuple[str, ...] | None:
    """Parse the allowed Status values from governance_01 "ADR Status
    Definitions" bullets; None when the section or bullets cannot be parsed
    (fail-closed caller contract). Must stay equal to
    check_adr_structure._ALLOWED_STATUSES."""
    try:
        content = governance_path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = _STATUS_SECTION_RE.search(content)
    if match is None:
        return None
    tail = content[match.end() :]
    next_section = re.search(r"^## ", tail, re.MULTILINE)
    section = tail if next_section is None else tail[: next_section.start()]
    return tuple(_STATUS_BULLET_RE.findall(section)) or None


def _adr_status(path: Path) -> str | None:
    """First non-empty line after the `## Status` heading (the convention
    check_adr_structure.py check (e) uses); None when no value follows."""
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "## Status":
            for following in lines[i + 1 :]:
                if following.strip():
                    return following.strip()
            return None
    return None


def check_adr_statuses(
    model: AuthorityModel,
    adr_dir: Path = ADR_DIR,
    governance_path: Path = GOVERNANCE_01_PATH,
) -> list[Finding]:
    """REQ-004/REQ-005: every model-referenced ADR must carry a Status value in
    the parsed allowed set. A Withdrawn ADR owns no decision target and holds no
    non-Reference edge; a Proposed ADR may not claim primary authority."""
    allowed = _allowed_statuses(governance_path)
    if allowed is None:
        return [
            Finding(
                code="ADR_STATUS_INVALID",
                location=f"docs/00_governance/{governance_path.name}",
                message=(
                    "could not parse the allowed Status set from 'ADR Status "
                    "Definitions'; status validation fails closed "
                    "(keep this section equal to check_adr_structure._ALLOWED_STATUSES)"
                ),
            )
        ]
    known = adr_files_by_id(adr_dir)
    statuses: dict[str, str | None] = {}
    for adr_id in sorted({adr_id for adr_id, _label in _model_adr_ids(model)}):
        filename = known.get(adr_id)
        if filename is None:
            continue  # unresolved ids are reported by DANGLING_ADR
        statuses[adr_id] = _adr_status(adr_dir / filename)

    findings: list[Finding] = []
    for adr_id, status in statuses.items():
        if status is None:
            findings.append(
                Finding(
                    code="ADR_STATUS_INVALID",
                    location=f"docs/10_adr/{known[adr_id]}",
                    message=(
                        f"{adr_id} is referenced by the model but its '## Status' "
                        "carries no value to validate"
                    ),
                )
            )
        elif status not in allowed:
            findings.append(
                Finding(
                    code="ADR_STATUS_INVALID",
                    location=f"docs/10_adr/{known[adr_id]}",
                    message=(
                        f"{adr_id} has Status {status!r}, outside the allowed set "
                        f"({', '.join(allowed)}) from governance_01 "
                        "'ADR Status Definitions'"
                    ),
                )
            )

    for entry in model.authorities:
        claims: list[tuple[str, str]] = [(entry.primary_adr, "primary_adr")]
        claims.extend((sup.adr, "supplemental") for sup in entry.supplemental_adrs)
        for adr_id, role in claims:
            status = statuses.get(adr_id)
            if status == "Withdrawn":
                findings.append(
                    Finding(
                        code="ADR_STATUS_INVALID",
                        location="config/adr_authority.toml",
                        message=(
                            f"withdrawn ADR {adr_id} is listed as {role} of "
                            f"decision_target {entry.decision_target!r}; a Withdrawn "
                            "ADR owns no decision target"
                        ),
                    )
                )
            elif status == "Proposed" and role == "primary_adr":
                findings.append(
                    Finding(
                        code="ADR_STATUS_INVALID",
                        location="config/adr_authority.toml",
                        message=(
                            f"proposed ADR {adr_id} claims primary_adr of "
                            f"decision_target {entry.decision_target!r}; primary "
                            "authority requires an Accepted ADR"
                        ),
                    )
                )

    for edge in model.edges:
        if edge.edge_type not in EDGE_TYPES or edge.edge_type == "Reference":
            continue  # taxonomy errors belong to EDGE_UNKNOWN_TYPE
        for adr_id in (edge.from_adr, edge.to_adr):
            if statuses.get(adr_id) == "Withdrawn":
                findings.append(
                    Finding(
                        code="ADR_STATUS_INVALID",
                        location="config/adr_authority.toml",
                        message=(
                            f"withdrawn ADR {adr_id} holds the {edge.edge_type} "
                            f"edge {edge.from_adr} -> {edge.to_adr}; a Withdrawn "
                            "ADR carries no normative edge"
                        ),
                    )
                )
    return findings


# ---------------------------------------------------------------------------
# Front matter / model cross-check (ADR-016 Decision 7, INV-04; row 05 calls this)
# ---------------------------------------------------------------------------


def _adr_related_files(adr_dir: Path) -> list[tuple[str, str, str, Path]]:
    """(adr_id, filename, related_filename, path) for every front matter related
    entry of an adr_02_* ADR body that names another adr_02_* ADR body."""
    pairs: list[tuple[str, str, str, Path]] = []
    for path in sorted(adr_dir.glob("adr_02_*.md")):
        match = ADR_FILE_RE.match(path.name)
        if match is None:
            continue
        content = path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            continue
        end = content.find("\n---", 3)
        if end == -1:
            continue
        try:
            data = yaml.safe_load(content[3:end]) or {}
        except yaml.YAMLError:
            continue
        related = data.get("related") if isinstance(data, dict) else None
        if not isinstance(related, list):
            continue
        for entry in related:
            if isinstance(entry, str) and ADR_FILE_RE.match(entry):
                pairs.append((f"ADR-{int(match.group(1)):03d}", path.name, entry, path))
    return pairs


def check_frontmatter_consistency(
    model: AuthorityModel, adr_dir: Path = ADR_DIR
) -> list[Finding]:
    """ADR-016 Decision 7, both directions:
    - every front matter related ADR edge exists in the model (same direction);
    - every non-Reference model edge appears in the owning ADR's front matter.
    Model-only Reference edges are clean (the model is the superset the
    generated graph renders)."""
    findings: list[Finding] = []
    filename_to_id: dict[str, str] = {}
    for adr_id, filename in adr_files_by_id(adr_dir).items():
        filename_to_id[filename] = adr_id

    model_pairs = {(edge.from_adr, edge.to_adr): edge for edge in model.edges}
    frontmatter_pairs: set[tuple[str, str]] = set()

    for adr_id, _filename, related_name, path in _adr_related_files(adr_dir):
        target_id = filename_to_id.get(related_name)
        if target_id is None:
            continue
        frontmatter_pairs.add((adr_id, target_id))
        if (adr_id, target_id) not in model_pairs:
            findings.append(
                Finding(
                    code="FRONTMATTER_DIVERGENCE",
                    location=f"docs/10_adr/{path.name}",
                    message=(
                        f"front matter related edge {adr_id} -> {target_id} "
                        f"({related_name}) is missing from config/adr_authority.toml"
                    ),
                )
            )

    for edge in model.edges:
        if edge.edge_type == "Reference":
            continue
        if (edge.from_adr, edge.to_adr) not in frontmatter_pairs:
            findings.append(
                Finding(
                    code="FRONTMATTER_DIVERGENCE",
                    location="config/adr_authority.toml",
                    message=(
                        f"non-Reference edge {edge.from_adr} -> {edge.to_adr} "
                        f"({edge.edge_type}) is missing from {edge.from_adr}'s front matter related list"
                    ),
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Aggregate entry point
# ---------------------------------------------------------------------------


def validate_model(
    model: AuthorityModel,
    *,
    adr_dir: Path = ADR_DIR,
    config_path: Path = AGENT_CONFIG_PATH,
    governance_path: Path = GOVERNANCE_01_PATH,
) -> list[Finding]:
    """Run every model validator (INV-01, INV-02, INV-05 plus taxonomy,
    duplicate-pair, status, and dangling-ID checks). The front matter
    cross-check is separate: only tools/check_adr_reference.py runs it
    (ADR-016 Verification)."""
    findings: list[Finding] = []
    findings.extend(check_edge_types(model))
    findings.extend(check_duplicate_edges(model))
    findings.extend(check_duplicate_primaries(model))
    findings.extend(check_dangling_adrs(model, adr_dir))
    findings.extend(check_adr_statuses(model, adr_dir, governance_path))
    findings.extend(check_authority_cycles(model))
    findings.extend(check_assumptions(model, config_path))
    return findings
