#!/usr/bin/env python3
"""gen_nuitka_helpers_header.py — Write a canonical Nuitka ``__helpers.h``.

Nuitka generates ``__helpers.h`` per build with only the call helpers that build
uses (``CALL_FUNCTION_WITH_ARGS<n>`` and its variants). Every generated module C file
includes it, so two binaries that share a third-party module still produce different
preprocessed text for it and ccache never hits across binaries.

This tool writes one header that declares every helper for arities
``max_quick_call + 1`` .. ``--max-arity``, using Nuitka's own generators. It is a
superset of any real ``__helpers.h`` (an unused ``extern`` is harmless), so
``deploy/nuitka_ccache_wrapper.sh`` can substitute it for each build's header. A module
that calls a helper above ``--max-arity`` then fails to compile (undeclared function)
instead of misbehaving.

Nuitka must be importable: run it with ``uv run --group build python``.

Usage:
    python3 tools/gen_nuitka_helpers_header.py --out PATH [--max-arity N]

Exit codes:
    0  Header written
    1  Nuitka could not be imported or its generators are unavailable
    2  Usage error
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from types import ModuleType

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._atomic_write import atomic_write_text

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

DEFAULT_MAX_ARITY = 40
CALL_CODES_MODULE = "nuitka.code_generation.CallCodes"


def build_header(call_codes: ModuleType, max_arity: int) -> str:
    """Return the header text declaring every helper up to ``max_arity``."""
    declare = call_codes.getTemplateCodeDeclaredFunction
    lines: set[str] = set()
    for count in range(call_codes.max_quick_call + 1, max_arity + 1):
        for has_tuple in (False, True):
            lines.add(
                declare(call_codes.getQuickCallCode(count, has_tuple_arg=has_tuple))
            )
            for has_dict in (False, True):
                lines.add(
                    declare(
                        call_codes.getQuickMixedCallCode(
                            count, has_tuple_arg=has_tuple, has_dict_values=has_dict
                        )
                    )
                )
        lines.add(declare(call_codes.getQuickMethodCallCode(count)))
    header: str = call_codes.template_header_guard % {
        "header_guard_name": "__NUITKA_CALLS_H__",
        "header_body": "\n".join(sorted(lines)),
    }
    return header


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-arity", type=int, default=DEFAULT_MAX_ARITY)
    args = parser.parse_args(argv)
    try:
        call_codes = importlib.import_module(CALL_CODES_MODULE)
        header = build_header(call_codes, args.max_arity)
    except (ImportError, AttributeError, TypeError) as exc:
        print(
            f"gen_nuitka_helpers_header: {type(exc).__name__}: {exc}", file=sys.stderr
        )
        return EXIT_FAIL
    args.out.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(args.out, header)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
