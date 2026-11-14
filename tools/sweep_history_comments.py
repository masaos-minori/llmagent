#!/usr/bin/env python3
"""Sweep provenance / plan-identifier comments in `scripts/` and `config/`.

Removes or rewrites the module docstrings and comments that describe where code
came from or which plan created it, so comments describe only current
responsibility and behavior:

- Pure provenance notes ("Extracted from ...", "Refactored: ...") are removed as
  whole docstring paragraphs.
- Plan / requirement identifiers embedded in a comment are stripped:
  `EBAUTHGEN001`, `RAGCORPUS001`, `crawl003`, and `REQ-<number>`.

The change is comment-only. It never touches:

- the module docstring first line (the `scripts/<relpath>` header verified by
  `tools/check_docstrings.py`);
- `# ADR-NNN` markers;
- suppression error codes or their em-dash justifications (`# noqa`,
  `# type: ignore`, `# nosec`) -- only the identifier token is removed.

Usage:
    python tools/sweep_history_comments.py [--dry-run] [paths...]

With no paths it walks `scripts/` and `config/`. `--dry-run` prints a unified
diff of every proposed change and changes nothing; omit it to apply.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from bisect import bisect_right
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# Provenance notes start a docstring paragraph with one of these prefixes.
PROVENANCE_PREFIXES = ("Extracted from", "Refactored:")

# Origin / plan identifier tokens stripped from inside a comment's text.
IDENTIFIER_TOKENS = ("EBAUTHGEN001", "RAGCORPUS001", "crawl003")

# Any identifier token: the three named origins plus a `REQ-<n>` label. Used to
# decide which open parens hold a citation (for citation-wrap detection).
IDENTIFIER_RE = re.compile(
    "|".join([re.escape(t) for t in IDENTIFIER_TOKENS] + [r"REQ-[0-9]+"])
)

REQ_RE = re.compile(r"REQ-[0-9]+")
PAREN_RE = re.compile(r"\(([^()]*)\)")
GROUP_LABEL_RE = re.compile(r"REQ-[0-9]+ group: ")
# "REQ-005, Plan" -> "Plan"; also drops "(REQ-002, AC-5)" -> "(AC-5)".
LABEL_COMMA_RE = re.compile(r"REQ-[0-9]+,\s*")
# Trailing citation after a separator: "; REQ-009" / ", REQ-009" / "/ REQ-009"
# -> "". Handles "md, REQ-001/REQ-007" -> "md" and "store REQ-002; x".
TRAILING_SEP_REQ_RE = re.compile(r"[;,/]\s*REQ-[0-9]+")
# A provenance citation run: one or more REQ labels (and bare continuations like
# /003) joined by any citation separator -- comma, semicolon, slash, plus, or a
# ".." range -- optionally followed by a surviving non-REQ label
# ("(REQ-007 / AC-7)" -> "(AC-7)"). An optional leading separator is eaten too so
# removing a trailing citation leaves no dangling comma
# ("(SQLite-first, REQ-006)" -> "(SQLite-first)"). The trailing separator+space is
# dropped so the surviving text keeps single spacing; collapse_open_paren_whitespace
# then fixes a space left after a dropped open paren. A separator that is part of
# the surviving text (e.g. a path slash in "plans/x.md") is safe because a separator
# is only eaten when a REQ label actually follows it.
# A trailing `\s*` here must NOT eat a newline: a `\n` after the last REQ label
# separates the citation from the next comment line, so consuming it would merge
# two comment lines into one (leaving the next line's `#` glued to the prior
# text). Internal separators keep `\s*` so a citation *run* may still wrap across
# lines ("(REQ-001,\n# REQ-002)"); only the final trailing run is newline-safe.
# An optional trailing `.` is eaten only when a space precedes it (a standalone
# trailing citation such as "(REQ-001).\nnext"), so a sentence period directly
# attached to the label ("shutdown); REQ-001." -> "shutdown).") is preserved; the
# leftover " ." is collapsed to "." by clean_trailing_artifacts. A period that
# continues the sentence (". REQ-002. Then") is never adjacent to the label, so
# it is likewise kept.
REQ_SEQ_RE = re.compile(
    r"(?:[;,/]\s*)?REQ-[0-9]+(?:/[0-9]+)*(?:\s*[;,+/\.]+\s*REQ-[0-9]+(?:/[0-9]+)*)*[^\S\n]*[;,/]*(?: \.(?=$|\n))?"
)
# An open paren that begins with one or more REQ labels followed by a colon is a
# label, not a citation: "(REQ-001: a non-empty key...)" -> ": a non-empty key..."
# (the surviving colon is kept, the open paren and its labels are dropped).
OPEN_LABEL_COLON_RE = re.compile(r"\((?:REQ-[0-9]+\s*)+\s*:")
# A citation introducer (per/for/via/see/cf) that attaches a REQ citation is
# dropped together with the citation: "marker for REQ-003" -> "marker", "per
# REQ-008." -> ".". An optional leading em/en dash is eaten too so a
# dash-introduced aside ("— see REQ-002.") leaves no dangling "— ." behind. Only
# matches when a real REQ label follows, so a real "for"/"see" is never touched.
# Case-insensitive so a capitalized introducer mid-sentence ("...attempts. See
# REQ-002." -> "...attempts.") is caught; the (?=REQ-) lookahead still guards
# against eating a real "for"/"see" that merely precedes a REQ token in prose.
CITE_INTRO_RE = re.compile(
    r"(?:\u2014\s+|\u2013\s+|\s-\s)?\b(per|for|via|see|cf)\s+(?=REQ-[0-9])",
    re.IGNORECASE,
)
# A bare `REQ-007:` label (colon immediately after the number, no open paren) is a
# citation, not prose: strip the label and its colon together so no dangling `:`
# survives in a docstring ("`"""REQ-007: x`" -> "`"""x`") or mid-sentence
# ("`. REQ-005: y`" -> "`. y`"). Eats the horizontal space after the colon so a
# start-of-body label leaves no leading space; `[^\S\n]` (not `\s`) never eats the
# newline separating the label from the next comment line. OPEN_LABEL_COLON_RE
# handles the parenthesised form first; this only sees the unparenthesised label.
REQ_LABEL_COLON_RE = re.compile(r"REQ-[0-9]+[^\S\n]*:[^\S\n]*")
# A colon left dangling right after a comment hash by a removed label:
# "# REQ-002: x" -> "# : x" -> "# x". Never matches `# type: ignore` or a
# code-suppression marker, because those have text between the hash and colon.
HASH_COLON_RE = re.compile(r"#\s*:\s*")
# Any line without one of these tokens is left byte-for-byte untouched, so the
# spacing cleanup in `clean_trailing_artifacts` never touches unrelated lines.
_MATCH_PATTERNS = [re.escape(t) for t in IDENTIFIER_TOKENS] + [r"REQ-[0-9]+"]
MATCH_RE = re.compile("|".join(_MATCH_PATTERNS))


def is_module_docstring_first_line(line: str) -> bool:
    """True when `line` is the protected module-docstring header."""

    return line.startswith('"""scripts/')


def _body_holds_only_identifiers(inner: str) -> bool:
    """True when a parenthetical's contents are only identifiers/REQ/separators."""

    rest = REQ_RE.sub("", inner)
    for tok in IDENTIFIER_TOKENS:
        rest = rest.replace(tok, "")
    return rest.strip(" ,;/-+.") == ""


def drop_req_only_parentheticals(text: str) -> str:
    """Drop a `( ... )` whose contents are only identifier/REQ tokens.

    `PAREN_RE` matches balanced pairs only, so prose that merely wraps across
    lines (an unmatched open paren, or a real parenthetical full of words) is
    left alone; only a pair whose contents reduce to nothing is removed.
    """

    def repl(match: re.Match[str]) -> str:
        inner = match.group(1)
        if not REQ_RE.search(inner):
            return match.group(0)
        if _body_holds_only_identifiers(inner):
            return ""
        return match.group(0)

    return PAREN_RE.sub(repl, text)


def collapse_open_paren_whitespace(text: str) -> str:
    """Collapse whitespace left right after an open paren by a removal.

    Removes the space/newline that a stripped token left between ``(`` and the
    surviving text: ``( REQ-006 /\\nADR-008)`` -> ``(ADR-008)`` and
    ``(REQ-005 no-masking)`` -> ``(no-masking)``.
    """

    return re.sub(r"\(\s+", "(", text)


# A parenthetical that opens at the start of a line (right after the newline) is
# a standalone citation: dropping it should merge onto the preceding line rather
# than leave a dangling punctuation on its own line, e.g.
#   "...window\n(REQ-004): sourced" -> "...window: sourced"
LINE_START_PAREN_RE = re.compile(r"\n\(([^()]*)\)")


def drop_line_start_identifiers(text: str) -> str:
    """Drop an identifier-only paren that starts a line, taking the newline."""

    def repl(match: re.Match[str]) -> str:
        inner = match.group(1)
        if REQ_RE.search(inner) and _body_holds_only_identifiers(inner):
            return ""
        return match.group(0)

    return LINE_START_PAREN_RE.sub(repl, text)


def clean_trailing_artifacts(text: str) -> str:
    """Repair spacing left behind after an identifier token was removed.

    Only collapses whitespace that a removal actually left dangling before a
    trailing punctuation mark; it never touches a separator that is part of the
    surviving text (e.g. the ``/undo`` command name in ``a /undo``).
    """

    # Collapse a period left adjacent to another by a removed trailing citation
    # ("attempts. See REQ-002." -> "attempts. ." -> "attempts."). Matches only
    # two periods separated by whitespace, so an Ellipsis / type-hint "..."
    # (no internal whitespace) is never touched. Runs first, before the
    # whitespace-collapses below, so the result never shows as "..".
    text = re.sub(r"\.\s+\.", ".", text)
    # " ." -> "."  " :" -> ":"  ")" -> ")"  -- collapse a space left before a
    # trailing punctuation mark after its identifier was removed. The closing
    # brace must sit inside the class; a trailing ``}`` outside it would require
    # a literal ``}`` after every match. The colon rule keeps a space when the
    # colon opens a cross-reference role (:func:, :data:) -- a following
    # identifier char means the colon is syntax, not a dangling removal -- so
    # Sphinx references survive untouched.
    text = re.sub(r" +(\.|,|;|\)|\})", r"\1", text)
    text = re.sub(r" +:(?![A-Za-z0-9_])", ":", text)
    text = re.sub(r" +,", ",", text)  # " ," -> ","
    text = re.sub(r",\s*,", ",", text)  # ", ," -> ","
    text = re.sub(r" {2,}", " ", text)  # collapse runs of spaces in the body
    # Drop a space left behind by a removal at a line boundary: an identifier-only
    # paren dropped mid-block (`word (REQ-004)\n# next`) leaves `word \n# next`;
    # a trailing `\n` is structural, so strip only the non-newline spaces at each
    # line end (never touching a separator that survives in the body).
    text = re.sub(r"[^\S\n]+$", "", text, flags=re.M)
    return text.rstrip()


def strip_identifier_tokens(text: str) -> str:
    """Apply the identifier sweep to a joined comment/docstring block.

    `text` may contain newlines: a run of consecutive comment or docstring lines
    is transformed together so a parenthetical that wraps across lines collapses
    as one unit. Indentation is NOT touched here -- `sweep_file_text` restores
    each line's original leading whitespace after this runs.
    """

    body = text
    for tok in IDENTIFIER_TOKENS:
        body = body.replace(tok, "")
    body = CITE_INTRO_RE.sub("", body)  # drop citation introducers bound to a REQ
    body = REQ_LABEL_COLON_RE.sub(
        "", body
    )  # drop a bare `REQ-007:` label (and its colon)
    body = drop_line_start_identifiers(
        body
    )  # merge a line-start "(REQ-004)" onto the prior line
    body = GROUP_LABEL_RE.sub("", body)  # "(REQ-006 group: x)" -> "(x)"
    body = OPEN_LABEL_COLON_RE.sub(
        ": ", body
    )  # "(REQ-001: x)" -> ": x" (before REQ_SEQ_RE eats the label)
    body = REQ_SEQ_RE.sub(
        "", body
    )  # "(REQ-007 / AC-7)" -> "(AC-7)", "(REQ-001/REQ-002)" -> ""
    body = LABEL_COMMA_RE.sub("", body)  # "REQ-005, Plan" -> "Plan"
    body = TRAILING_SEP_REQ_RE.sub("", body)  # ", REQ-009" / "/ REQ-009" -> ""
    body = drop_req_only_parentheticals(body)  # drop identifier-only "(...)"
    body = REQ_RE.sub("", body)  # remove any remaining bare REQ tokens
    body = collapse_open_paren_whitespace(
        body
    )  # "( REQ-006 /\nADR-008)" -> "(ADR-008)"
    # Drop a paren a removed label left empty -- but never a real call such as
    # ``run()``: the negative lookbehind keeps ``()`` that follows an identifier.
    # A mid-sentence paren ``word (REQ-004).`` keeps its sentence-ending period
    # (``word.``); only a standalone clause-closing paren ``(REQ-006).`` at the
    # start of a comment drops the trailing period so it leaves no ``# .`` behind.
    body = re.sub(r"(\w+)\s*\(\s*\)\.", r"\1.", body)
    # Drop an empty paren left by a removed label. Two shapes:
    #  - a standalone clause-closing paren at the *start* of a line
    #    ("(REQ-006)." -> "") -- drop it together with its trailing period so it
    #    leaves no "# ." behind;
    #  - a mid-sentence paren ("word (REQ-004)." -> "word.") -- keep the
    #    sentence-ending period.
    body = re.sub(r"(?:(?<=\n)|^)\(\s*\)\.?", "", body)
    body = re.sub(r"(?<![A-Za-z0-9_\n])\(\s*\)", "", body)
    body = clean_trailing_artifacts(body)  # fix dangling spacing before punctuation
    body = HASH_COLON_RE.sub("# ", body)  # "# :" -> "# " (keep hash separated)
    return body


def _classify_lines(lines: list[str]) -> list[str]:
    """Classify each line for sweeping.

    Returns one kind per line:

    - ``first`` -- the protected module-docstring header.
    - ``doc`` -- a real docstring (module/function/class). Swept as prose.
    - ``comment`` -- a ``#`` Python comment, or a ``--`` SQL comment inside a DDL
      string literal. Swept.
    - ``literal`` -- a triple-quoted *string literal* such as a
      ``NAME: str = \"\"\"...\"\"\"`` DDL template. Never swept: it is data, not
      documentation.
    - ``code`` -- everything else. Never swept.

    A triple-quoted string is a docstring only when it sits in doc position --
    the first statement of the module, a function, or a class -- and is not the
    right-hand side of an assignment. Anything else is a plain string literal,
    so a DDL template that merely *contains* a matching comment is left intact.
    """

    kinds: list[str] = []
    in_str = False  # inside a triple-quoted string
    is_doc = False  # the open string is a docstring (opened in doc position)
    expect_doc = False  # the next triple-quoted string should be a docstring
    module_doc_seen = False  # the module docstring has been opened
    sig_pending = False  # inside a multi-line def/class signature

    for index, line in enumerate(lines):
        # Protected module-docstring header (first line, byte-for-byte kept).
        if index == 0 and line.startswith('"""scripts/'):
            kinds.append("first")
            # An odd marker count means the module docstring opens here; a
            # one-line module docstring (two markers) nets to nothing.
            in_str = line.count('"""') % 2 == 1
            is_doc = in_str
            expect_doc = False
            continue

        # Inside a triple-quoted string opened on a prior line. Classify by the
        # current is_doc flag and flip state only on a line that actually carries
        # a closing marker. A blank or body line has zero markers and must keep
        # the string open WITHOUT resetting is_doc -- the old XOR
        # (`in_str ^ (markers % 2 == 1)`) set `closed` on every body line and the
        # following `if closed:` dropped is_doc, misclassifying every multi-line
        # docstring body as a literal.
        if in_str:
            markers = line.count('"""')
            stripped = line.lstrip()
            # A '--' SQL comment line inside a DDL literal is still a comment.
            if not is_doc and stripped.startswith("--"):
                kinds.append("comment")
            elif is_doc:
                kinds.append("doc")
            else:
                kinds.append("literal")
            if markers % 2 == 1:
                in_str = False
                is_doc = False
                expect_doc = False
            continue

        # Not inside a string on this line.
        if re.match(r"\s*#", line):
            kinds.append("comment")
            continue

        # A triple-quoted string opens/closes on this line.
        if '"""' in line:
            prefix = line[: line.index('"""')]
            odd = line.count('"""') % 2 == 1
            # A module docstring is the first doc-position string in the file. It
            # may follow a shebang or an encoding cookie, so it is not always at
            # index 0; recognise it by its ``scripts/`` path header before any code
            # has appeared. An assignment (``NAME = ...`` / ``NAME: T = ...``) makes
            # the string a literal, not a docstring. Only a doc-position string
            # (the next string after a def/class header) is a docstring.
            if (
                not module_doc_seen
                and "=" not in prefix
                and line.lstrip().startswith('"""scripts/')
            ):
                kind = "first"
                is_doc = odd
                module_doc_seen = True
            elif expect_doc and "=" not in prefix:
                kind = "doc"
                is_doc = True
            else:
                kind = "literal"
                is_doc = False
            expect_doc = False
            in_str = odd
            kinds.append(kind)
            continue

        # A plain code line. A def/class header puts the next string in doc
        # position; any other statement clears it. The header may open a
        # multi-line signature (ending on a later line with `:`), so track the
        # signature across lines instead of requiring the header itself to end
        # with `:` -- otherwise every multi-line-signature docstring is missed.
        if re.match(r"\s*(?:async def|def|class)\b", line):
            sig_pending = True
            if line.rstrip().endswith(":"):
                sig_pending = False  # single-line signature
                expect_doc = True
            # else stay pending until the closing `:` line
        elif sig_pending and line.rstrip().endswith(":"):
            sig_pending = False
            expect_doc = True
        elif sig_pending:
            pass  # a continuation line inside the open signature
        else:
            sig_pending = False
            expect_doc = False
        kinds.append("code")

    return kinds


def _transform_block(block: list[str], indents: list[str]) -> list[str]:
    """Transform a run of comment/doc lines and restore each line's indent.

    The lines are joined and transformed together so cross-line parentheticals
    collapse as one unit. Each input line's leading whitespace is stripped
    before joining and re-applied afterwards, so indentation is preserved even
    when a drop merges two lines into one (merged lines share their indent in
    practice, so the surviving line keeps the first line's indent).

    The only question is which indent each output line gets. The sweep never
    inserts a newline, so a source line yields at most one output line while an
    output line may absorb several source lines (a citation run bridging two
    lines). Each output line therefore takes the indent of the *first* source
    line it overlaps. Char-level alignment of the joined input against the
    merged result locates those overlaps precisely -- it distinguishes newlines
    that survived (still present in the merged text) from newlines a removal
    ate (a citation run that joined two source lines) -- so grouping is exact
    and a docstring's closing triple-quote terminator is never dropped. A blank
    output line stays blank (no indent re-applied) so a paragraph-separating
    blank never gains trailing whitespace.
    """

    bodies = [ln[len(indent) :] for ln, indent in zip(block, indents)]
    count = len(bodies)
    if count == 0:
        return []
    joined = "\n".join(bodies)
    merged = strip_identifier_tokens(joined)
    out_lines = merged.split("\n")
    # Start offset (in `joined`) of each source body; line_start[i] is the
    # position of body[i]'s first character.
    line_start = [0]
    for b in bodies:
        line_start.append(line_start[-1] + len(b) + 1)
    opcodes = difflib.SequenceMatcher(a=joined, b=merged, autojunk=False).get_opcodes()

    def _first_source_line(m_start: int, m_end: int) -> int:
        # Earliest source line whose joined content overlaps merged[m_start:m_end].
        # 'equal' regions map char-for-char; 'replace' regions map their joined
        # start. A zero-width range (a blank output line) still lands on the
        # adjacent region so its indent is well defined (it is emitted blank).
        best = count
        for tag, a1, a2, b1, b2 in opcodes:
            if tag == "insert":
                continue
            if b2 <= m_start or b1 >= m_end:
                continue
            joined_ref = a1 if tag == "replace" else a1 + max(0, m_start - b1)
            sl = bisect_right(line_start, joined_ref) - 1
            if sl < best:
                best = sl
        return best if best != count else count - 1

    out: list[str] = []
    for k, content in enumerate(out_lines):
        lo = sum(len(part) + 1 for part in out_lines[:k])
        hi = lo + len(content)
        sl = _first_source_line(lo, hi)
        if content.strip():
            out.append(indents[sl] + content)
        else:
            out.append("")
    return out


def _find_provenance_removals(
    block: list[str], block_kinds: list[str]
) -> tuple[list[list[int]], set[int]]:
    """Split a block into transform runs and the indices to drop.

    A provenance paragraph is a maximal run of consecutive non-blank *doc* lines
    whose first line starts with a ``PROVENANCE_PREFIX``. Each such span is dropped
    together with one preceding blank line -- the separator orphaned by the
    removal -- when that preceding line is blank. The span never crosses a
    triple-quote terminator (a docstring's closing marker), so the block's
    surrounding structure is preserved. Returns the remaining lines grouped into
    maximal runs (lists of block indices) and the set of block indices removed.
    Runs are transformed independently, so peeling a provenance paragraph never
    merges two unrelated paragraphs or a paragraph with the closing marker.
    """

    n = len(block)
    removed: set[int] = set()
    i = 0
    while i < n:
        if block_kinds[i] != "doc" or not block[i].strip():
            i += 1
            continue
        if not block[i].lstrip().startswith(PROVENANCE_PREFIXES):
            i += 1
            continue
        start = i
        j = i
        while (
            j < n
            and block[j].strip()
            and '"""' not in block[j]
            and block_kinds[j] == "doc"
        ):
            j += 1
        for k in range(start, j):
            removed.add(k)
        prev = start - 1
        if prev >= 0 and block[prev].strip() == "" and prev not in removed:
            removed.add(prev)
        i = j
    runs: list[list[int]] = []
    i = 0
    while i < n:
        if i in removed:
            i += 1
            continue
        j = i
        while j < n and j not in removed:
            j += 1
        runs.append(list(range(i, j)))
        i = j
    return runs, removed


def sweep_file_text(text: str) -> tuple[str, list[tuple[int, str, str]]]:
    """Return swept text and a list of (lineno, before, after) line changes."""

    lines = text.split("\n")
    if not lines:
        return text, []
    kinds = _classify_lines(lines)
    count = len(lines)
    out: list[str] = []
    changes: list[tuple[int, str, str]] = []

    index = 0
    while index < count:
        line = lines[index]

        # Never touch the module docstring first line.
        if index == 0 and kinds[index] == "first":
            out.append(line)
            index += 1
            continue

        # Otherwise sweep a maximal run of consecutive comment/doc lines as one
        # block, but only when at least one line carries a token. This keeps the
        # spacing on unrelated lines byte-for-byte intact and lets a paren that
        # wraps across lines collapse correctly.
        if kinds[index] in ("comment", "doc"):
            end = index
            while end < count and kinds[end] in ("comment", "doc"):
                end += 1
            block = lines[index:end]
            block_kinds = kinds[index:end]
            # Sweep the block only when it carries an identifier token or a
            # provenance paragraph. A provenance paragraph ("Extracted from ...",
            # "Refactored: ...") may contain neither a named origin nor a REQ
            # label, so it is detected independently of MATCH_RE; a pure provenance
            # note would otherwise slip past the sweep untouched.
            has_token = any(MATCH_RE.search(b) for b in block)
            # Peel off provenance paragraphs (whole docstring paragraphs that
            # state where the code came from) before transforming the rest, so
            # their identifier text is removed rather than left behind with a
            # stripped REQ label. Each surviving run is transformed on its own
            # so a provenance removal never joins two unrelated paragraphs.
            runs, removed = _find_provenance_removals(block, block_kinds)
            if not removed and not has_token:
                out.extend(block)
                index = end
                continue
            indents = [b[: len(b) - len(b.lstrip())] for b in block]
            for pos in sorted(removed):
                changes.append((index + pos + 1, block[pos], ""))
            for run in runs:
                run_lines = [block[i] for i in run]
                run_indents = [indents[i] for i in run]
                # Strip identifiers only when a token is present; a provenance-only
                # block keeps its surviving lines byte-for-byte.
                new_run = (
                    _transform_block(run_lines, run_indents) if has_token else run_lines
                )
                for delta, new in zip(run, new_run):
                    orig = block[delta]
                    if orig != new:
                        changes.append((index + delta + 1, orig, new))
                out.extend(new_run)
            index = end
            continue

        out.append(line)
        index += 1

    return "\n".join(out), changes


def iter_target_files(paths: list[str]) -> list[Path]:
    """Yield every .py/.toml file under the given paths."""

    files: list[Path] = []
    for raw in paths:
        path = (ROOT_DIR / raw) if not Path(raw).is_absolute() else Path(raw)
        if path.is_dir():
            files.extend(
                sorted(p for p in path.rglob("*") if p.suffix in {".py", ".toml"})
            )
        elif path.is_file():
            files.append(path)
    # De-duplicate while keeping order.
    seen: set[Path] = set()
    unique: list[Path] = []
    for f in files:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="print diffs, change nothing"
    )
    parser.add_argument(
        "paths", nargs="*", help="files or directories (default: scripts config)"
    )
    args = parser.parse_args(argv)

    paths = args.paths or ["scripts", "config"]
    files = iter_target_files(paths)

    total_changes = 0
    changed_files = 0
    for file_path in files:
        try:
            original = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"SKIP (non-UTF8): {file_path}", file=sys.stderr)
            continue

        swept, changes = sweep_file_text(original)
        if not changes:
            continue

        changed_files += 1
        total_changes += len(changes)
        print(f"=== {file_path.relative_to(ROOT_DIR)} ({len(changes)} line(s)) ===")
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            swept.splitlines(keepends=True),
            fromfile=str(file_path),
            tofile=str(file_path),
            n=1,
        )
        print("".join(diff))

        if not args.dry_run:
            file_path.write_text(swept, encoding="utf-8")

    print(
        f"\n{changed_files} file(s), {total_changes} line(s) changed.", file=sys.stderr
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
