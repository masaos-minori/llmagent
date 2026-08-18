#!/usr/bin/env python3
"""scripts/rag/ingestion/crawler_utils.py

Pure-function utilities for WebCrawler: URL helpers, content extraction,
language detection, and target URL parsing.

Extracted from web_crawler.py to keep WebCrawler under 400 lines.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from urllib.parse import urldefrag, urlparse

import trafilatura
from bs4 import BeautifulSoup
from rag.utils import MIN_TEXT_LENGTH_FOR_DETECTION, validate_url

# Supported language codes for resolved (output) lang values
_SUPPORTED_LANGS: frozenset[str] = frozenset({"en", "ja"})
# Valid hint lang values including "auto" for per-page CJK-ratio detection
_VALID_HINT_LANGS: frozenset[str] = frozenset({"en", "ja", "auto"})
# CJK character ratio threshold above which text is classified as Japanese
_CJK_RATIO_THRESHOLD: float = 0.1

# Expected element count for target_urls entries: [url, lang]
_TARGET_URL_ENTRY_LENGTH = 2


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x__validate_target_url__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__validate_target_url__mutmut)
def _validate_target_url(url: str) -> bool:
    """Return True when url has an accepted scheme (http, https, or file).

    Unlike validate_url() in rag.utils, this function also accepts file://
    URIs used by the --targets-file crawl path.
    """
    from urllib.parse import urlparse

    scheme = urlparse(url).scheme
    return scheme in {"http", "https", "file"}


def x__validate_target_url__mutmut_orig(url: str) -> bool:
    """Return True when url has an accepted scheme (http, https, or file).

    Unlike validate_url() in rag.utils, this function also accepts file://
    URIs used by the --targets-file crawl path.
    """
    from urllib.parse import urlparse

    scheme = urlparse(url).scheme
    return scheme in {"http", "https", "file"}


def x__validate_target_url__mutmut_1(url: str) -> bool:
    """Return True when url has an accepted scheme (http, https, or file).

    Unlike validate_url() in rag.utils, this function also accepts file://
    URIs used by the --targets-file crawl path.
    """
    from urllib.parse import urlparse

    scheme = None
    return scheme in {"http", "https", "file"}


def x__validate_target_url__mutmut_2(url: str) -> bool:
    """Return True when url has an accepted scheme (http, https, or file).

    Unlike validate_url() in rag.utils, this function also accepts file://
    URIs used by the --targets-file crawl path.
    """
    from urllib.parse import urlparse

    scheme = urlparse(None).scheme
    return scheme in {"http", "https", "file"}


def x__validate_target_url__mutmut_3(url: str) -> bool:
    """Return True when url has an accepted scheme (http, https, or file).

    Unlike validate_url() in rag.utils, this function also accepts file://
    URIs used by the --targets-file crawl path.
    """
    from urllib.parse import urlparse

    scheme = urlparse(url).scheme
    return scheme not in {"http", "https", "file"}


def x__validate_target_url__mutmut_4(url: str) -> bool:
    """Return True when url has an accepted scheme (http, https, or file).

    Unlike validate_url() in rag.utils, this function also accepts file://
    URIs used by the --targets-file crawl path.
    """
    from urllib.parse import urlparse

    scheme = urlparse(url).scheme
    return scheme in {"XXhttpXX", "https", "file"}


def x__validate_target_url__mutmut_5(url: str) -> bool:
    """Return True when url has an accepted scheme (http, https, or file).

    Unlike validate_url() in rag.utils, this function also accepts file://
    URIs used by the --targets-file crawl path.
    """
    from urllib.parse import urlparse

    scheme = urlparse(url).scheme
    return scheme in {"HTTP", "https", "file"}


def x__validate_target_url__mutmut_6(url: str) -> bool:
    """Return True when url has an accepted scheme (http, https, or file).

    Unlike validate_url() in rag.utils, this function also accepts file://
    URIs used by the --targets-file crawl path.
    """
    from urllib.parse import urlparse

    scheme = urlparse(url).scheme
    return scheme in {"http", "XXhttpsXX", "file"}


def x__validate_target_url__mutmut_7(url: str) -> bool:
    """Return True when url has an accepted scheme (http, https, or file).

    Unlike validate_url() in rag.utils, this function also accepts file://
    URIs used by the --targets-file crawl path.
    """
    from urllib.parse import urlparse

    scheme = urlparse(url).scheme
    return scheme in {"http", "HTTPS", "file"}


def x__validate_target_url__mutmut_8(url: str) -> bool:
    """Return True when url has an accepted scheme (http, https, or file).

    Unlike validate_url() in rag.utils, this function also accepts file://
    URIs used by the --targets-file crawl path.
    """
    from urllib.parse import urlparse

    scheme = urlparse(url).scheme
    return scheme in {"http", "https", "XXfileXX"}


def x__validate_target_url__mutmut_9(url: str) -> bool:
    """Return True when url has an accepted scheme (http, https, or file).

    Unlike validate_url() in rag.utils, this function also accepts file://
    URIs used by the --targets-file crawl path.
    """
    from urllib.parse import urlparse

    scheme = urlparse(url).scheme
    return scheme in {"http", "https", "FILE"}

mutants_x__validate_target_url__mutmut['_mutmut_orig'] = x__validate_target_url__mutmut_orig # type: ignore # mutmut generated
mutants_x__validate_target_url__mutmut['x__validate_target_url__mutmut_1'] = x__validate_target_url__mutmut_1 # type: ignore # mutmut generated
mutants_x__validate_target_url__mutmut['x__validate_target_url__mutmut_2'] = x__validate_target_url__mutmut_2 # type: ignore # mutmut generated
mutants_x__validate_target_url__mutmut['x__validate_target_url__mutmut_3'] = x__validate_target_url__mutmut_3 # type: ignore # mutmut generated
mutants_x__validate_target_url__mutmut['x__validate_target_url__mutmut_4'] = x__validate_target_url__mutmut_4 # type: ignore # mutmut generated
mutants_x__validate_target_url__mutmut['x__validate_target_url__mutmut_5'] = x__validate_target_url__mutmut_5 # type: ignore # mutmut generated
mutants_x__validate_target_url__mutmut['x__validate_target_url__mutmut_6'] = x__validate_target_url__mutmut_6 # type: ignore # mutmut generated
mutants_x__validate_target_url__mutmut['x__validate_target_url__mutmut_7'] = x__validate_target_url__mutmut_7 # type: ignore # mutmut generated
mutants_x__validate_target_url__mutmut['x__validate_target_url__mutmut_8'] = x__validate_target_url__mutmut_8 # type: ignore # mutmut generated
mutants_x__validate_target_url__mutmut['x__validate_target_url__mutmut_9'] = x__validate_target_url__mutmut_9 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_parse_targets_file__mutmut)
def parse_targets_file(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_orig(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_1(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = None
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_2(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding=None)
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_3(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="XXutf-8XX")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_4(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="UTF-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_5(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = None
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_6(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(None)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_7(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = None
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_8(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get(None, [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_9(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", None)
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_10(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get([])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_11(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", )
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_12(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("XXtarget_urlsXX", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_13(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("TARGET_URLS", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_14(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = None
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_15(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(None):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_16(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple) and len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_17(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_18(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) == _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_19(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                None
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_20(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = None
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_21(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(None), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_22(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[1]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_23(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(None)
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_24(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[2])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_25(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_26(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(None):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_27(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                None
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_28(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_29(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                None
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_30(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(None)})"
            )
        result.append((url, lang))
    return result


def x_parse_targets_file__mutmut_31(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append(None)
    return result

mutants_x_parse_targets_file__mutmut['_mutmut_orig'] = x_parse_targets_file__mutmut_orig # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_1'] = x_parse_targets_file__mutmut_1 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_2'] = x_parse_targets_file__mutmut_2 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_3'] = x_parse_targets_file__mutmut_3 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_4'] = x_parse_targets_file__mutmut_4 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_5'] = x_parse_targets_file__mutmut_5 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_6'] = x_parse_targets_file__mutmut_6 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_7'] = x_parse_targets_file__mutmut_7 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_8'] = x_parse_targets_file__mutmut_8 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_9'] = x_parse_targets_file__mutmut_9 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_10'] = x_parse_targets_file__mutmut_10 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_11'] = x_parse_targets_file__mutmut_11 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_12'] = x_parse_targets_file__mutmut_12 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_13'] = x_parse_targets_file__mutmut_13 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_14'] = x_parse_targets_file__mutmut_14 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_15'] = x_parse_targets_file__mutmut_15 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_16'] = x_parse_targets_file__mutmut_16 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_17'] = x_parse_targets_file__mutmut_17 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_18'] = x_parse_targets_file__mutmut_18 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_19'] = x_parse_targets_file__mutmut_19 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_20'] = x_parse_targets_file__mutmut_20 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_21'] = x_parse_targets_file__mutmut_21 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_22'] = x_parse_targets_file__mutmut_22 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_23'] = x_parse_targets_file__mutmut_23 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_24'] = x_parse_targets_file__mutmut_24 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_25'] = x_parse_targets_file__mutmut_25 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_26'] = x_parse_targets_file__mutmut_26 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_27'] = x_parse_targets_file__mutmut_27 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_28'] = x_parse_targets_file__mutmut_28 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_29'] = x_parse_targets_file__mutmut_29 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_30'] = x_parse_targets_file__mutmut_30 # type: ignore # mutmut generated
mutants_x_parse_targets_file__mutmut['x_parse_targets_file__mutmut_31'] = x_parse_targets_file__mutmut_31 # type: ignore # mutmut generated


# Unicode code point ranges for CJK character detection in detect_lang()
_HIRAGANA_KATAKANA_START = "぀"
_HIRAGANA_KATAKANA_END = "ヿ"
_CJK_UNIFIED_START = "一"
_CJK_UNIFIED_END = "鿿"
_CJK_EXT_A_START = "㐀"
_CJK_EXT_A_END = "䶿"
mutants_x_url_to_slug__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_url_to_slug__mutmut)
def url_to_slug(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_orig(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_1(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = None
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_2(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(None, "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_3(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", None, url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_4(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", None)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_5(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub("", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_6(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_7(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", )
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_8(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"XX^https?://XX", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_9(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^HTTPS?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_10(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "XXXX", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_11(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = None
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_12(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(None, "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_13(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", None, slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_14(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", None)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_15(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub("-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_16(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_17(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", )
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_18(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"XX[^a-zA-Z0-9._-]XX", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_19(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-za-z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_20(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^A-ZA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_21(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "XX-XX", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_22(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = None
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_23(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(None, "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_24(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", None, slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_25(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", None)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_26(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub("-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_27(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_28(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", )
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_29(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"XX-+XX", "-", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_30(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "XX-XX", slug)
    return slug.strip("-")[:80]


def x_url_to_slug__mutmut_31(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip(None)[:80]


def x_url_to_slug__mutmut_32(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("XX-XX")[:80]


def x_url_to_slug__mutmut_33(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:81]

mutants_x_url_to_slug__mutmut['_mutmut_orig'] = x_url_to_slug__mutmut_orig # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_1'] = x_url_to_slug__mutmut_1 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_2'] = x_url_to_slug__mutmut_2 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_3'] = x_url_to_slug__mutmut_3 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_4'] = x_url_to_slug__mutmut_4 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_5'] = x_url_to_slug__mutmut_5 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_6'] = x_url_to_slug__mutmut_6 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_7'] = x_url_to_slug__mutmut_7 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_8'] = x_url_to_slug__mutmut_8 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_9'] = x_url_to_slug__mutmut_9 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_10'] = x_url_to_slug__mutmut_10 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_11'] = x_url_to_slug__mutmut_11 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_12'] = x_url_to_slug__mutmut_12 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_13'] = x_url_to_slug__mutmut_13 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_14'] = x_url_to_slug__mutmut_14 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_15'] = x_url_to_slug__mutmut_15 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_16'] = x_url_to_slug__mutmut_16 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_17'] = x_url_to_slug__mutmut_17 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_18'] = x_url_to_slug__mutmut_18 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_19'] = x_url_to_slug__mutmut_19 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_20'] = x_url_to_slug__mutmut_20 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_21'] = x_url_to_slug__mutmut_21 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_22'] = x_url_to_slug__mutmut_22 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_23'] = x_url_to_slug__mutmut_23 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_24'] = x_url_to_slug__mutmut_24 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_25'] = x_url_to_slug__mutmut_25 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_26'] = x_url_to_slug__mutmut_26 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_27'] = x_url_to_slug__mutmut_27 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_28'] = x_url_to_slug__mutmut_28 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_29'] = x_url_to_slug__mutmut_29 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_30'] = x_url_to_slug__mutmut_30 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_31'] = x_url_to_slug__mutmut_31 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_32'] = x_url_to_slug__mutmut_32 # type: ignore # mutmut generated
mutants_x_url_to_slug__mutmut['x_url_to_slug__mutmut_33'] = x_url_to_slug__mutmut_33 # type: ignore # mutmut generated
mutants_x_normalize_url__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_normalize_url__mutmut)
def normalize_url(url: str) -> str:
    """Normalize a URL by stripping the fragment and trailing slash."""
    url, _ = urldefrag(url)
    return url.rstrip("/")


def x_normalize_url__mutmut_orig(url: str) -> str:
    """Normalize a URL by stripping the fragment and trailing slash."""
    url, _ = urldefrag(url)
    return url.rstrip("/")


def x_normalize_url__mutmut_1(url: str) -> str:
    """Normalize a URL by stripping the fragment and trailing slash."""
    url, _ = None
    return url.rstrip("/")


def x_normalize_url__mutmut_2(url: str) -> str:
    """Normalize a URL by stripping the fragment and trailing slash."""
    url, _ = urldefrag(None)
    return url.rstrip("/")


def x_normalize_url__mutmut_3(url: str) -> str:
    """Normalize a URL by stripping the fragment and trailing slash."""
    url, _ = urldefrag(url)
    return url.rstrip(None)


def x_normalize_url__mutmut_4(url: str) -> str:
    """Normalize a URL by stripping the fragment and trailing slash."""
    url, _ = urldefrag(url)
    return url.lstrip("/")


def x_normalize_url__mutmut_5(url: str) -> str:
    """Normalize a URL by stripping the fragment and trailing slash."""
    url, _ = urldefrag(url)
    return url.rstrip("XX/XX")

mutants_x_normalize_url__mutmut['_mutmut_orig'] = x_normalize_url__mutmut_orig # type: ignore # mutmut generated
mutants_x_normalize_url__mutmut['x_normalize_url__mutmut_1'] = x_normalize_url__mutmut_1 # type: ignore # mutmut generated
mutants_x_normalize_url__mutmut['x_normalize_url__mutmut_2'] = x_normalize_url__mutmut_2 # type: ignore # mutmut generated
mutants_x_normalize_url__mutmut['x_normalize_url__mutmut_3'] = x_normalize_url__mutmut_3 # type: ignore # mutmut generated
mutants_x_normalize_url__mutmut['x_normalize_url__mutmut_4'] = x_normalize_url__mutmut_4 # type: ignore # mutmut generated
mutants_x_normalize_url__mutmut['x_normalize_url__mutmut_5'] = x_normalize_url__mutmut_5 # type: ignore # mutmut generated
mutants_x_same_origin__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_same_origin__mutmut)
def same_origin(url: str, base: str) -> bool:
    """Return True if url and base share the same origin (scheme + hostname)."""
    p1, p2 = urlparse(url), urlparse(base)
    return p1.scheme == p2.scheme and p1.netloc == p2.netloc


def x_same_origin__mutmut_orig(url: str, base: str) -> bool:
    """Return True if url and base share the same origin (scheme + hostname)."""
    p1, p2 = urlparse(url), urlparse(base)
    return p1.scheme == p2.scheme and p1.netloc == p2.netloc


def x_same_origin__mutmut_1(url: str, base: str) -> bool:
    """Return True if url and base share the same origin (scheme + hostname)."""
    p1, p2 = None
    return p1.scheme == p2.scheme and p1.netloc == p2.netloc


def x_same_origin__mutmut_2(url: str, base: str) -> bool:
    """Return True if url and base share the same origin (scheme + hostname)."""
    p1, p2 = urlparse(None), urlparse(base)
    return p1.scheme == p2.scheme and p1.netloc == p2.netloc


def x_same_origin__mutmut_3(url: str, base: str) -> bool:
    """Return True if url and base share the same origin (scheme + hostname)."""
    p1, p2 = urlparse(url), urlparse(None)
    return p1.scheme == p2.scheme and p1.netloc == p2.netloc


def x_same_origin__mutmut_4(url: str, base: str) -> bool:
    """Return True if url and base share the same origin (scheme + hostname)."""
    p1, p2 = urlparse(url), urlparse(base)
    return p1.scheme == p2.scheme or p1.netloc == p2.netloc


def x_same_origin__mutmut_5(url: str, base: str) -> bool:
    """Return True if url and base share the same origin (scheme + hostname)."""
    p1, p2 = urlparse(url), urlparse(base)
    return p1.scheme != p2.scheme and p1.netloc == p2.netloc


def x_same_origin__mutmut_6(url: str, base: str) -> bool:
    """Return True if url and base share the same origin (scheme + hostname)."""
    p1, p2 = urlparse(url), urlparse(base)
    return p1.scheme == p2.scheme and p1.netloc != p2.netloc

mutants_x_same_origin__mutmut['_mutmut_orig'] = x_same_origin__mutmut_orig # type: ignore # mutmut generated
mutants_x_same_origin__mutmut['x_same_origin__mutmut_1'] = x_same_origin__mutmut_1 # type: ignore # mutmut generated
mutants_x_same_origin__mutmut['x_same_origin__mutmut_2'] = x_same_origin__mutmut_2 # type: ignore # mutmut generated
mutants_x_same_origin__mutmut['x_same_origin__mutmut_3'] = x_same_origin__mutmut_3 # type: ignore # mutmut generated
mutants_x_same_origin__mutmut['x_same_origin__mutmut_4'] = x_same_origin__mutmut_4 # type: ignore # mutmut generated
mutants_x_same_origin__mutmut['x_same_origin__mutmut_5'] = x_same_origin__mutmut_5 # type: ignore # mutmut generated
mutants_x_same_origin__mutmut['x_same_origin__mutmut_6'] = x_same_origin__mutmut_6 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_extract_text__mutmut)
def extract_text(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_orig(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_1(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = None
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_2(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["XXnavXX", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_3(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["NAV", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_4(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "XXfooterXX", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_5(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "FOOTER", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_6(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "XXasideXX", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_7(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "ASIDE", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_8(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "XXscriptXX", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_9(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "SCRIPT", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_10(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "XXstyleXX", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_11(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "STYLE", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_12(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "XXnoscriptXX"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_13(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "NOSCRIPT"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_14(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(None):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_15(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = None
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_16(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        None,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_17(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=None,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_18(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=None,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_19(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=None,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_20(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_21(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_22(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_23(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_24(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_25(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(None),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_26(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=True,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_27(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=False,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_28(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=True,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_29(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = None
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_30(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator=None, strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_31(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=None)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_32(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_33(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", )
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_34(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="XX\nXX", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_35(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=False)
    extracted: str = text or fallback
    return extracted.strip()


def x_extract_text__mutmut_36(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = None
    return extracted.strip()


def x_extract_text__mutmut_37(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text and fallback
    return extracted.strip()

mutants_x_extract_text__mutmut['_mutmut_orig'] = x_extract_text__mutmut_orig # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_1'] = x_extract_text__mutmut_1 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_2'] = x_extract_text__mutmut_2 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_3'] = x_extract_text__mutmut_3 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_4'] = x_extract_text__mutmut_4 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_5'] = x_extract_text__mutmut_5 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_6'] = x_extract_text__mutmut_6 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_7'] = x_extract_text__mutmut_7 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_8'] = x_extract_text__mutmut_8 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_9'] = x_extract_text__mutmut_9 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_10'] = x_extract_text__mutmut_10 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_11'] = x_extract_text__mutmut_11 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_12'] = x_extract_text__mutmut_12 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_13'] = x_extract_text__mutmut_13 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_14'] = x_extract_text__mutmut_14 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_15'] = x_extract_text__mutmut_15 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_16'] = x_extract_text__mutmut_16 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_17'] = x_extract_text__mutmut_17 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_18'] = x_extract_text__mutmut_18 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_19'] = x_extract_text__mutmut_19 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_20'] = x_extract_text__mutmut_20 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_21'] = x_extract_text__mutmut_21 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_22'] = x_extract_text__mutmut_22 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_23'] = x_extract_text__mutmut_23 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_24'] = x_extract_text__mutmut_24 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_25'] = x_extract_text__mutmut_25 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_26'] = x_extract_text__mutmut_26 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_27'] = x_extract_text__mutmut_27 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_28'] = x_extract_text__mutmut_28 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_29'] = x_extract_text__mutmut_29 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_30'] = x_extract_text__mutmut_30 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_31'] = x_extract_text__mutmut_31 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_32'] = x_extract_text__mutmut_32 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_33'] = x_extract_text__mutmut_33 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_34'] = x_extract_text__mutmut_34 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_35'] = x_extract_text__mutmut_35 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_36'] = x_extract_text__mutmut_36 # type: ignore # mutmut generated
mutants_x_extract_text__mutmut['x_extract_text__mutmut_37'] = x_extract_text__mutmut_37 # type: ignore # mutmut generated
mutants_x_detect_lang__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_detect_lang__mutmut)
def detect_lang(text: str) -> str | None:
    """Detect language by CJK character ratio.

    Returns 'ja' when CJK ratio >= _CJK_RATIO_THRESHOLD, 'en' otherwise.
    Returns None for texts shorter than 100 characters (too short for reliable
    detection).
    """
    if len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
        return None
    # Count Hiragana, Katakana, and CJK Unified Ideographs (incl. Extension A)
    cjk_count = sum(1 for c in text if _is_cjk_char(c))
    return "ja" if cjk_count / len(text) >= _CJK_RATIO_THRESHOLD else "en"


def x_detect_lang__mutmut_orig(text: str) -> str | None:
    """Detect language by CJK character ratio.

    Returns 'ja' when CJK ratio >= _CJK_RATIO_THRESHOLD, 'en' otherwise.
    Returns None for texts shorter than 100 characters (too short for reliable
    detection).
    """
    if len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
        return None
    # Count Hiragana, Katakana, and CJK Unified Ideographs (incl. Extension A)
    cjk_count = sum(1 for c in text if _is_cjk_char(c))
    return "ja" if cjk_count / len(text) >= _CJK_RATIO_THRESHOLD else "en"


def x_detect_lang__mutmut_1(text: str) -> str | None:
    """Detect language by CJK character ratio.

    Returns 'ja' when CJK ratio >= _CJK_RATIO_THRESHOLD, 'en' otherwise.
    Returns None for texts shorter than 100 characters (too short for reliable
    detection).
    """
    if len(text) <= MIN_TEXT_LENGTH_FOR_DETECTION:
        return None
    # Count Hiragana, Katakana, and CJK Unified Ideographs (incl. Extension A)
    cjk_count = sum(1 for c in text if _is_cjk_char(c))
    return "ja" if cjk_count / len(text) >= _CJK_RATIO_THRESHOLD else "en"


def x_detect_lang__mutmut_2(text: str) -> str | None:
    """Detect language by CJK character ratio.

    Returns 'ja' when CJK ratio >= _CJK_RATIO_THRESHOLD, 'en' otherwise.
    Returns None for texts shorter than 100 characters (too short for reliable
    detection).
    """
    if len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
        return None
    # Count Hiragana, Katakana, and CJK Unified Ideographs (incl. Extension A)
    cjk_count = None
    return "ja" if cjk_count / len(text) >= _CJK_RATIO_THRESHOLD else "en"


def x_detect_lang__mutmut_3(text: str) -> str | None:
    """Detect language by CJK character ratio.

    Returns 'ja' when CJK ratio >= _CJK_RATIO_THRESHOLD, 'en' otherwise.
    Returns None for texts shorter than 100 characters (too short for reliable
    detection).
    """
    if len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
        return None
    # Count Hiragana, Katakana, and CJK Unified Ideographs (incl. Extension A)
    cjk_count = sum(None)
    return "ja" if cjk_count / len(text) >= _CJK_RATIO_THRESHOLD else "en"


def x_detect_lang__mutmut_4(text: str) -> str | None:
    """Detect language by CJK character ratio.

    Returns 'ja' when CJK ratio >= _CJK_RATIO_THRESHOLD, 'en' otherwise.
    Returns None for texts shorter than 100 characters (too short for reliable
    detection).
    """
    if len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
        return None
    # Count Hiragana, Katakana, and CJK Unified Ideographs (incl. Extension A)
    cjk_count = sum(2 for c in text if _is_cjk_char(c))
    return "ja" if cjk_count / len(text) >= _CJK_RATIO_THRESHOLD else "en"


def x_detect_lang__mutmut_5(text: str) -> str | None:
    """Detect language by CJK character ratio.

    Returns 'ja' when CJK ratio >= _CJK_RATIO_THRESHOLD, 'en' otherwise.
    Returns None for texts shorter than 100 characters (too short for reliable
    detection).
    """
    if len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
        return None
    # Count Hiragana, Katakana, and CJK Unified Ideographs (incl. Extension A)
    cjk_count = sum(1 for c in text if _is_cjk_char(None))
    return "ja" if cjk_count / len(text) >= _CJK_RATIO_THRESHOLD else "en"


def x_detect_lang__mutmut_6(text: str) -> str | None:
    """Detect language by CJK character ratio.

    Returns 'ja' when CJK ratio >= _CJK_RATIO_THRESHOLD, 'en' otherwise.
    Returns None for texts shorter than 100 characters (too short for reliable
    detection).
    """
    if len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
        return None
    # Count Hiragana, Katakana, and CJK Unified Ideographs (incl. Extension A)
    cjk_count = sum(1 for c in text if _is_cjk_char(c))
    return "XXjaXX" if cjk_count / len(text) >= _CJK_RATIO_THRESHOLD else "en"


def x_detect_lang__mutmut_7(text: str) -> str | None:
    """Detect language by CJK character ratio.

    Returns 'ja' when CJK ratio >= _CJK_RATIO_THRESHOLD, 'en' otherwise.
    Returns None for texts shorter than 100 characters (too short for reliable
    detection).
    """
    if len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
        return None
    # Count Hiragana, Katakana, and CJK Unified Ideographs (incl. Extension A)
    cjk_count = sum(1 for c in text if _is_cjk_char(c))
    return "JA" if cjk_count / len(text) >= _CJK_RATIO_THRESHOLD else "en"


def x_detect_lang__mutmut_8(text: str) -> str | None:
    """Detect language by CJK character ratio.

    Returns 'ja' when CJK ratio >= _CJK_RATIO_THRESHOLD, 'en' otherwise.
    Returns None for texts shorter than 100 characters (too short for reliable
    detection).
    """
    if len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
        return None
    # Count Hiragana, Katakana, and CJK Unified Ideographs (incl. Extension A)
    cjk_count = sum(1 for c in text if _is_cjk_char(c))
    return "ja" if cjk_count * len(text) >= _CJK_RATIO_THRESHOLD else "en"


def x_detect_lang__mutmut_9(text: str) -> str | None:
    """Detect language by CJK character ratio.

    Returns 'ja' when CJK ratio >= _CJK_RATIO_THRESHOLD, 'en' otherwise.
    Returns None for texts shorter than 100 characters (too short for reliable
    detection).
    """
    if len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
        return None
    # Count Hiragana, Katakana, and CJK Unified Ideographs (incl. Extension A)
    cjk_count = sum(1 for c in text if _is_cjk_char(c))
    return "ja" if cjk_count / len(text) > _CJK_RATIO_THRESHOLD else "en"


def x_detect_lang__mutmut_10(text: str) -> str | None:
    """Detect language by CJK character ratio.

    Returns 'ja' when CJK ratio >= _CJK_RATIO_THRESHOLD, 'en' otherwise.
    Returns None for texts shorter than 100 characters (too short for reliable
    detection).
    """
    if len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
        return None
    # Count Hiragana, Katakana, and CJK Unified Ideographs (incl. Extension A)
    cjk_count = sum(1 for c in text if _is_cjk_char(c))
    return "ja" if cjk_count / len(text) >= _CJK_RATIO_THRESHOLD else "XXenXX"


def x_detect_lang__mutmut_11(text: str) -> str | None:
    """Detect language by CJK character ratio.

    Returns 'ja' when CJK ratio >= _CJK_RATIO_THRESHOLD, 'en' otherwise.
    Returns None for texts shorter than 100 characters (too short for reliable
    detection).
    """
    if len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
        return None
    # Count Hiragana, Katakana, and CJK Unified Ideographs (incl. Extension A)
    cjk_count = sum(1 for c in text if _is_cjk_char(c))
    return "ja" if cjk_count / len(text) >= _CJK_RATIO_THRESHOLD else "EN"

mutants_x_detect_lang__mutmut['_mutmut_orig'] = x_detect_lang__mutmut_orig # type: ignore # mutmut generated
mutants_x_detect_lang__mutmut['x_detect_lang__mutmut_1'] = x_detect_lang__mutmut_1 # type: ignore # mutmut generated
mutants_x_detect_lang__mutmut['x_detect_lang__mutmut_2'] = x_detect_lang__mutmut_2 # type: ignore # mutmut generated
mutants_x_detect_lang__mutmut['x_detect_lang__mutmut_3'] = x_detect_lang__mutmut_3 # type: ignore # mutmut generated
mutants_x_detect_lang__mutmut['x_detect_lang__mutmut_4'] = x_detect_lang__mutmut_4 # type: ignore # mutmut generated
mutants_x_detect_lang__mutmut['x_detect_lang__mutmut_5'] = x_detect_lang__mutmut_5 # type: ignore # mutmut generated
mutants_x_detect_lang__mutmut['x_detect_lang__mutmut_6'] = x_detect_lang__mutmut_6 # type: ignore # mutmut generated
mutants_x_detect_lang__mutmut['x_detect_lang__mutmut_7'] = x_detect_lang__mutmut_7 # type: ignore # mutmut generated
mutants_x_detect_lang__mutmut['x_detect_lang__mutmut_8'] = x_detect_lang__mutmut_8 # type: ignore # mutmut generated
mutants_x_detect_lang__mutmut['x_detect_lang__mutmut_9'] = x_detect_lang__mutmut_9 # type: ignore # mutmut generated
mutants_x_detect_lang__mutmut['x_detect_lang__mutmut_10'] = x_detect_lang__mutmut_10 # type: ignore # mutmut generated
mutants_x_detect_lang__mutmut['x_detect_lang__mutmut_11'] = x_detect_lang__mutmut_11 # type: ignore # mutmut generated
mutants_x__is_cjk_char__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__is_cjk_char__mutmut)
def _is_cjk_char(c: str) -> bool:
    """Check if a character is CJK (Hiragana, Katakana, or CJK Unified Ideograph)."""
    return (
        (_HIRAGANA_KATAKANA_START <= c <= _HIRAGANA_KATAKANA_END)
        or (_CJK_UNIFIED_START <= c <= _CJK_UNIFIED_END)
        or (_CJK_EXT_A_START <= c <= _CJK_EXT_A_END)
    )


def x__is_cjk_char__mutmut_orig(c: str) -> bool:
    """Check if a character is CJK (Hiragana, Katakana, or CJK Unified Ideograph)."""
    return (
        (_HIRAGANA_KATAKANA_START <= c <= _HIRAGANA_KATAKANA_END)
        or (_CJK_UNIFIED_START <= c <= _CJK_UNIFIED_END)
        or (_CJK_EXT_A_START <= c <= _CJK_EXT_A_END)
    )


def x__is_cjk_char__mutmut_1(c: str) -> bool:
    """Check if a character is CJK (Hiragana, Katakana, or CJK Unified Ideograph)."""
    return (
        (_HIRAGANA_KATAKANA_START <= c <= _HIRAGANA_KATAKANA_END)
        or (_CJK_UNIFIED_START <= c <= _CJK_UNIFIED_END) and (_CJK_EXT_A_START <= c <= _CJK_EXT_A_END)
    )


def x__is_cjk_char__mutmut_2(c: str) -> bool:
    """Check if a character is CJK (Hiragana, Katakana, or CJK Unified Ideograph)."""
    return (
        (_HIRAGANA_KATAKANA_START <= c <= _HIRAGANA_KATAKANA_END) and (_CJK_UNIFIED_START <= c <= _CJK_UNIFIED_END)
        or (_CJK_EXT_A_START <= c <= _CJK_EXT_A_END)
    )


def x__is_cjk_char__mutmut_3(c: str) -> bool:
    """Check if a character is CJK (Hiragana, Katakana, or CJK Unified Ideograph)."""
    return (
        (_HIRAGANA_KATAKANA_START < c <= _HIRAGANA_KATAKANA_END)
        or (_CJK_UNIFIED_START <= c <= _CJK_UNIFIED_END)
        or (_CJK_EXT_A_START <= c <= _CJK_EXT_A_END)
    )


def x__is_cjk_char__mutmut_4(c: str) -> bool:
    """Check if a character is CJK (Hiragana, Katakana, or CJK Unified Ideograph)."""
    return (
        (_HIRAGANA_KATAKANA_START <= c < _HIRAGANA_KATAKANA_END)
        or (_CJK_UNIFIED_START <= c <= _CJK_UNIFIED_END)
        or (_CJK_EXT_A_START <= c <= _CJK_EXT_A_END)
    )


def x__is_cjk_char__mutmut_5(c: str) -> bool:
    """Check if a character is CJK (Hiragana, Katakana, or CJK Unified Ideograph)."""
    return (
        (_HIRAGANA_KATAKANA_START <= c <= _HIRAGANA_KATAKANA_END)
        or (_CJK_UNIFIED_START < c <= _CJK_UNIFIED_END)
        or (_CJK_EXT_A_START <= c <= _CJK_EXT_A_END)
    )


def x__is_cjk_char__mutmut_6(c: str) -> bool:
    """Check if a character is CJK (Hiragana, Katakana, or CJK Unified Ideograph)."""
    return (
        (_HIRAGANA_KATAKANA_START <= c <= _HIRAGANA_KATAKANA_END)
        or (_CJK_UNIFIED_START <= c < _CJK_UNIFIED_END)
        or (_CJK_EXT_A_START <= c <= _CJK_EXT_A_END)
    )


def x__is_cjk_char__mutmut_7(c: str) -> bool:
    """Check if a character is CJK (Hiragana, Katakana, or CJK Unified Ideograph)."""
    return (
        (_HIRAGANA_KATAKANA_START <= c <= _HIRAGANA_KATAKANA_END)
        or (_CJK_UNIFIED_START <= c <= _CJK_UNIFIED_END)
        or (_CJK_EXT_A_START < c <= _CJK_EXT_A_END)
    )


def x__is_cjk_char__mutmut_8(c: str) -> bool:
    """Check if a character is CJK (Hiragana, Katakana, or CJK Unified Ideograph)."""
    return (
        (_HIRAGANA_KATAKANA_START <= c <= _HIRAGANA_KATAKANA_END)
        or (_CJK_UNIFIED_START <= c <= _CJK_UNIFIED_END)
        or (_CJK_EXT_A_START <= c < _CJK_EXT_A_END)
    )

mutants_x__is_cjk_char__mutmut['_mutmut_orig'] = x__is_cjk_char__mutmut_orig # type: ignore # mutmut generated
mutants_x__is_cjk_char__mutmut['x__is_cjk_char__mutmut_1'] = x__is_cjk_char__mutmut_1 # type: ignore # mutmut generated
mutants_x__is_cjk_char__mutmut['x__is_cjk_char__mutmut_2'] = x__is_cjk_char__mutmut_2 # type: ignore # mutmut generated
mutants_x__is_cjk_char__mutmut['x__is_cjk_char__mutmut_3'] = x__is_cjk_char__mutmut_3 # type: ignore # mutmut generated
mutants_x__is_cjk_char__mutmut['x__is_cjk_char__mutmut_4'] = x__is_cjk_char__mutmut_4 # type: ignore # mutmut generated
mutants_x__is_cjk_char__mutmut['x__is_cjk_char__mutmut_5'] = x__is_cjk_char__mutmut_5 # type: ignore # mutmut generated
mutants_x__is_cjk_char__mutmut['x__is_cjk_char__mutmut_6'] = x__is_cjk_char__mutmut_6 # type: ignore # mutmut generated
mutants_x__is_cjk_char__mutmut['x__is_cjk_char__mutmut_7'] = x__is_cjk_char__mutmut_7 # type: ignore # mutmut generated
mutants_x__is_cjk_char__mutmut['x__is_cjk_char__mutmut_8'] = x__is_cjk_char__mutmut_8 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_parse_target_urls__mutmut)
def parse_target_urls(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_orig(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_1(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = None
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_2(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_3(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                None,
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_4(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "XXEach entry in target_urls must be a 2-element list of [url, lang]XX",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_5(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_6(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "EACH ENTRY IN TARGET_URLS MUST BE A 2-ELEMENT LIST OF [URL, LANG]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_7(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) == _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_8(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                None,
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_9(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "XXEach entry in target_urls must be a 2-element list of [url, lang]XX",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_10(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_11(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "EACH ENTRY IN TARGET_URLS MUST BE A 2-ELEMENT LIST OF [URL, LANG]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_12(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = None
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_13(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(None), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_14(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[1]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_15(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(None)
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_16(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[2])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_17(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_18(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                None
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_19(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(None).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_20(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(None).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_21(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_22(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                None
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_23(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(None).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_24(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(None).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_25(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = None
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_26(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_27(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(None):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_28(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(None)
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_29(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_30(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                None,
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_31(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(None)})",
            )
        result.append((url, lang))
    return result


def x_parse_target_urls__mutmut_32(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append(None)
    return result

mutants_x_parse_target_urls__mutmut['_mutmut_orig'] = x_parse_target_urls__mutmut_orig # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_1'] = x_parse_target_urls__mutmut_1 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_2'] = x_parse_target_urls__mutmut_2 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_3'] = x_parse_target_urls__mutmut_3 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_4'] = x_parse_target_urls__mutmut_4 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_5'] = x_parse_target_urls__mutmut_5 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_6'] = x_parse_target_urls__mutmut_6 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_7'] = x_parse_target_urls__mutmut_7 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_8'] = x_parse_target_urls__mutmut_8 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_9'] = x_parse_target_urls__mutmut_9 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_10'] = x_parse_target_urls__mutmut_10 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_11'] = x_parse_target_urls__mutmut_11 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_12'] = x_parse_target_urls__mutmut_12 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_13'] = x_parse_target_urls__mutmut_13 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_14'] = x_parse_target_urls__mutmut_14 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_15'] = x_parse_target_urls__mutmut_15 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_16'] = x_parse_target_urls__mutmut_16 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_17'] = x_parse_target_urls__mutmut_17 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_18'] = x_parse_target_urls__mutmut_18 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_19'] = x_parse_target_urls__mutmut_19 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_20'] = x_parse_target_urls__mutmut_20 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_21'] = x_parse_target_urls__mutmut_21 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_22'] = x_parse_target_urls__mutmut_22 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_23'] = x_parse_target_urls__mutmut_23 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_24'] = x_parse_target_urls__mutmut_24 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_25'] = x_parse_target_urls__mutmut_25 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_26'] = x_parse_target_urls__mutmut_26 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_27'] = x_parse_target_urls__mutmut_27 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_28'] = x_parse_target_urls__mutmut_28 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_29'] = x_parse_target_urls__mutmut_29 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_30'] = x_parse_target_urls__mutmut_30 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_31'] = x_parse_target_urls__mutmut_31 # type: ignore # mutmut generated
mutants_x_parse_target_urls__mutmut['x_parse_target_urls__mutmut_32'] = x_parse_target_urls__mutmut_32 # type: ignore # mutmut generated
