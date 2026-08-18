"""scripts/rag/ingestion/document_manager.py

Document management for RagIngester."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable

from db.helper import SQLiteHelper
from db.models import RagConsistencyReport
from db.rag_consistency import check_rag_consistency, is_consistent
from rag.ingestion.etag_manager import ETagManager
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/ingest.log")


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_delete_document_chain__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_delete_document_chain__mutmut)
def delete_document_chain(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        "DELETE FROM chunks_vec WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
        (doc_id,),
    )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))


def x_delete_document_chain__mutmut_orig(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        "DELETE FROM chunks_vec WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
        (doc_id,),
    )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))


def x_delete_document_chain__mutmut_1(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        None,
        (doc_id,),
    )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))


def x_delete_document_chain__mutmut_2(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        "DELETE FROM chunks_vec WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
        None,
    )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))


def x_delete_document_chain__mutmut_3(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        (doc_id,),
    )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))


def x_delete_document_chain__mutmut_4(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        "DELETE FROM chunks_vec WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
        )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))


def x_delete_document_chain__mutmut_5(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        "XXDELETE FROM chunks_vec WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id = ?)XX",
        (doc_id,),
    )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))


def x_delete_document_chain__mutmut_6(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        "delete from chunks_vec where chunk_id in (select chunk_id from chunks where doc_id = ?)",
        (doc_id,),
    )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))


def x_delete_document_chain__mutmut_7(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        "DELETE FROM CHUNKS_VEC WHERE CHUNK_ID IN (SELECT CHUNK_ID FROM CHUNKS WHERE DOC_ID = ?)",
        (doc_id,),
    )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))


def x_delete_document_chain__mutmut_8(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        "DELETE FROM chunks_vec WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
        (doc_id,),
    )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute(None, (doc_id,))


def x_delete_document_chain__mutmut_9(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        "DELETE FROM chunks_vec WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
        (doc_id,),
    )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute("DELETE FROM documents WHERE doc_id = ?", None)


def x_delete_document_chain__mutmut_10(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        "DELETE FROM chunks_vec WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
        (doc_id,),
    )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute((doc_id,))


def x_delete_document_chain__mutmut_11(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        "DELETE FROM chunks_vec WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
        (doc_id,),
    )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute("DELETE FROM documents WHERE doc_id = ?", )


def x_delete_document_chain__mutmut_12(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        "DELETE FROM chunks_vec WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
        (doc_id,),
    )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute("XXDELETE FROM documents WHERE doc_id = ?XX", (doc_id,))


def x_delete_document_chain__mutmut_13(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        "DELETE FROM chunks_vec WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
        (doc_id,),
    )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute("delete from documents where doc_id = ?", (doc_id,))


def x_delete_document_chain__mutmut_14(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        "DELETE FROM chunks_vec WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
        (doc_id,),
    )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute("DELETE FROM DOCUMENTS WHERE DOC_ID = ?", (doc_id,))

mutants_x_delete_document_chain__mutmut['_mutmut_orig'] = x_delete_document_chain__mutmut_orig # type: ignore # mutmut generated
mutants_x_delete_document_chain__mutmut['x_delete_document_chain__mutmut_1'] = x_delete_document_chain__mutmut_1 # type: ignore # mutmut generated
mutants_x_delete_document_chain__mutmut['x_delete_document_chain__mutmut_2'] = x_delete_document_chain__mutmut_2 # type: ignore # mutmut generated
mutants_x_delete_document_chain__mutmut['x_delete_document_chain__mutmut_3'] = x_delete_document_chain__mutmut_3 # type: ignore # mutmut generated
mutants_x_delete_document_chain__mutmut['x_delete_document_chain__mutmut_4'] = x_delete_document_chain__mutmut_4 # type: ignore # mutmut generated
mutants_x_delete_document_chain__mutmut['x_delete_document_chain__mutmut_5'] = x_delete_document_chain__mutmut_5 # type: ignore # mutmut generated
mutants_x_delete_document_chain__mutmut['x_delete_document_chain__mutmut_6'] = x_delete_document_chain__mutmut_6 # type: ignore # mutmut generated
mutants_x_delete_document_chain__mutmut['x_delete_document_chain__mutmut_7'] = x_delete_document_chain__mutmut_7 # type: ignore # mutmut generated
mutants_x_delete_document_chain__mutmut['x_delete_document_chain__mutmut_8'] = x_delete_document_chain__mutmut_8 # type: ignore # mutmut generated
mutants_x_delete_document_chain__mutmut['x_delete_document_chain__mutmut_9'] = x_delete_document_chain__mutmut_9 # type: ignore # mutmut generated
mutants_x_delete_document_chain__mutmut['x_delete_document_chain__mutmut_10'] = x_delete_document_chain__mutmut_10 # type: ignore # mutmut generated
mutants_x_delete_document_chain__mutmut['x_delete_document_chain__mutmut_11'] = x_delete_document_chain__mutmut_11 # type: ignore # mutmut generated
mutants_x_delete_document_chain__mutmut['x_delete_document_chain__mutmut_12'] = x_delete_document_chain__mutmut_12 # type: ignore # mutmut generated
mutants_x_delete_document_chain__mutmut['x_delete_document_chain__mutmut_13'] = x_delete_document_chain__mutmut_13 # type: ignore # mutmut generated
mutants_x_delete_document_chain__mutmut['x_delete_document_chain__mutmut_14'] = x_delete_document_chain__mutmut_14 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut: MutantDict = {}  # type: ignore
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut: MutantDict = {}  # type: ignore
mutants_xǁDocumentManagerǁ_update_etag__mutmut: MutantDict = {}  # type: ignore
mutants_xǁDocumentManagerǁ_is_file_unchanged__mutmut: MutantDict = {}  # type: ignore
mutants_xǁDocumentManagerǁdelete_existing_document__mutmut: MutantDict = {}  # type: ignore
mutants_xǁDocumentManagerǁcheck_consistency__mutmut: MutantDict = {}  # type: ignore
mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut: MutantDict = {}  # type: ignore
mutants_xǁDocumentManagerǁ_invoke_callback__mutmut: MutantDict = {}  # type: ignore


class DocumentManager:
    """Manages document lifecycle for RagIngester.

    Handles existing document detection, ETag updates, and consistency reports.
    """

    @_mutmut_mutated(mutants_xǁDocumentManagerǁ__init____mutmut)
    def __init__(self, db: SQLiteHelper) -> None:
        """Initialize with a database helper instance."""
        self._db = db

    def xǁDocumentManagerǁ__init____mutmut_orig(self, db: SQLiteHelper) -> None:
        """Initialize with a database helper instance."""
        self._db = db

    def xǁDocumentManagerǁ__init____mutmut_1(self, db: SQLiteHelper) -> None:
        """Initialize with a database helper instance."""
        self._db = None

    @_mutmut_mutated(mutants_xǁDocumentManagerǁhandle_existing_document__mutmut)
    def handle_existing_document(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_orig(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_1(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, True, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_2(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, False
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_3(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(None):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_4(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = None
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_5(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                None,
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_6(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                None,
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_7(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_8(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_9(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "XXSELECT etag, last_modified FROM documents WHERE doc_id = ?XX",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_10(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "select etag, last_modified from documents where doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_11(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT ETAG, LAST_MODIFIED FROM DOCUMENTS WHERE DOC_ID = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_12(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is not None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_13(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, True, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_14(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, True
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_15(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                None, stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_16(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], None, etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_17(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], None, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_18(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, None
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_19(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_20(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_21(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_22(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_23(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["XXetagXX"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_24(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["ETAG"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_25(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["XXlast_modifiedXX"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_26(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["LAST_MODIFIED"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_27(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    None,
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_28(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    None,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_29(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra=None,
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_30(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_31(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_32(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_33(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "XXfile:// unchanged (sha256 match): %sXX",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_34(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "FILE:// UNCHANGED (SHA256 MATCH): %S",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_35(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"XXstage_nameXX": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_36(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"STAGE_NAME": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_37(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "XXingesterXX"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_38(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "INGESTER"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_39(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, False, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_40(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, True
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_41(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                None,
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_42(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                None,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_43(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra=None,
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_44(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_45(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_46(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_47(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "XXfile:// changed — auto re-ingesting: %sXX",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_48(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "FILE:// CHANGED — AUTO RE-INGESTING: %S",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_49(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"XXstage_nameXX": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_50(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"STAGE_NAME": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_51(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "XXingesterXX"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_52(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "INGESTER"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_53(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, True, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_54(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, False

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_55(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = None
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_56(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            None,
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_57(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            None,
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_58(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_59(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_60(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "XXSELECT etag, last_modified FROM documents WHERE doc_id = ?XX",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_61(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "select etag, last_modified from documents where doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_62(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT ETAG, LAST_MODIFIED FROM DOCUMENTS WHERE DOC_ID = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_63(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is not None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_64(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, True, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_65(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, True

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_66(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag or stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_67(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["XXetagXX"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_68(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["ETAG"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_69(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] != etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_70(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["XXlast_modifiedXX"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_71(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["LAST_MODIFIED"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_72(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] != last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_73(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, False, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_74(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, True

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_75(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(None, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_76(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, None, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_77(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, None, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_78(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, None)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_79(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_80(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, last_modified, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_81(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, fetched_at)
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_82(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, )
        return existing_doc_id, False, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_83(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, True, True

    def xǁDocumentManagerǁhandle_existing_document__mutmut_84(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, False

    @_mutmut_mutated(mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut)
    def _handle_existing_file(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_orig(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_1(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = None
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_2(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            None,
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_3(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            None,
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_4(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_5(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_6(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "XXSELECT etag, last_modified FROM documents WHERE doc_id = ?XX",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_7(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "select etag, last_modified from documents where doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_8(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT ETAG, LAST_MODIFIED FROM DOCUMENTS WHERE DOC_ID = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_9(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is not None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_10(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return True
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_11(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            None, stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_12(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], None, etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_13(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], None, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_14(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, None
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_15(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_16(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_17(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_18(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_19(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["XXetagXX"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_20(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["ETAG"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_21(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["XXlast_modifiedXX"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_22(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["LAST_MODIFIED"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_23(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                None,
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_24(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                None,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_25(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra=None,
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_26(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_27(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_28(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_29(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "XXfile:// unchanged (sha256 match): %sXX",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_30(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "FILE:// UNCHANGED (SHA256 MATCH): %S",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_31(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"XXstage_nameXX": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_32(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"STAGE_NAME": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_33(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "XXingesterXX"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_34(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "INGESTER"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_35(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return False
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_36(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            None,
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_37(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            None,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_38(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra=None,
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_39(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_40(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_41(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_42(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "XXfile:// changed — auto re-ingesting: %sXX",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_43(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "FILE:// CHANGED — AUTO RE-INGESTING: %S",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_44(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"XXstage_nameXX": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_45(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"STAGE_NAME": "ingester"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_46(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "XXingesterXX"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_47(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "INGESTER"},
        )
        return False

    def xǁDocumentManagerǁ_handle_existing_file__mutmut_48(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return True

    @_mutmut_mutated(mutants_xǁDocumentManagerǁ_update_etag__mutmut)
    def _update_etag(
        self,
        doc_id: int,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document (skip-case)."""
        ETagManager(self._db, doc_id).update(etag, last_modified, new_fetched_at)

    def xǁDocumentManagerǁ_update_etag__mutmut_orig(
        self,
        doc_id: int,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document (skip-case)."""
        ETagManager(self._db, doc_id).update(etag, last_modified, new_fetched_at)

    def xǁDocumentManagerǁ_update_etag__mutmut_1(
        self,
        doc_id: int,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document (skip-case)."""
        ETagManager(self._db, doc_id).update(None, last_modified, new_fetched_at)

    def xǁDocumentManagerǁ_update_etag__mutmut_2(
        self,
        doc_id: int,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document (skip-case)."""
        ETagManager(self._db, doc_id).update(etag, None, new_fetched_at)

    def xǁDocumentManagerǁ_update_etag__mutmut_3(
        self,
        doc_id: int,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document (skip-case)."""
        ETagManager(self._db, doc_id).update(etag, last_modified, None)

    def xǁDocumentManagerǁ_update_etag__mutmut_4(
        self,
        doc_id: int,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document (skip-case)."""
        ETagManager(self._db, doc_id).update(last_modified, new_fetched_at)

    def xǁDocumentManagerǁ_update_etag__mutmut_5(
        self,
        doc_id: int,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document (skip-case)."""
        ETagManager(self._db, doc_id).update(etag, new_fetched_at)

    def xǁDocumentManagerǁ_update_etag__mutmut_6(
        self,
        doc_id: int,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document (skip-case)."""
        ETagManager(self._db, doc_id).update(etag, last_modified, )

    def xǁDocumentManagerǁ_update_etag__mutmut_7(
        self,
        doc_id: int,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document (skip-case)."""
        ETagManager(None, doc_id).update(etag, last_modified, new_fetched_at)

    def xǁDocumentManagerǁ_update_etag__mutmut_8(
        self,
        doc_id: int,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document (skip-case)."""
        ETagManager(self._db, None).update(etag, last_modified, new_fetched_at)

    def xǁDocumentManagerǁ_update_etag__mutmut_9(
        self,
        doc_id: int,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document (skip-case)."""
        ETagManager(doc_id).update(etag, last_modified, new_fetched_at)

    def xǁDocumentManagerǁ_update_etag__mutmut_10(
        self,
        doc_id: int,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document (skip-case)."""
        ETagManager(self._db, ).update(etag, last_modified, new_fetched_at)

    @staticmethod
    @_mutmut_mutated(mutants_xǁDocumentManagerǁ_is_file_unchanged__mutmut)
    def _is_file_unchanged(
        existing_etag: str | None,
        existing_last_modified: str | None,
        new_etag: str | None,
        new_last_modified: str | None,
    ) -> bool:
        """Return True when the file SHA-256 hash is unchanged."""
        if existing_etag is None or new_etag is None:
            return False
        return existing_etag == new_etag

    @staticmethod
    def xǁDocumentManagerǁ_is_file_unchanged__mutmut_orig(
        existing_etag: str | None,
        existing_last_modified: str | None,
        new_etag: str | None,
        new_last_modified: str | None,
    ) -> bool:
        """Return True when the file SHA-256 hash is unchanged."""
        if existing_etag is None or new_etag is None:
            return False
        return existing_etag == new_etag

    @staticmethod
    def xǁDocumentManagerǁ_is_file_unchanged__mutmut_1(
        existing_etag: str | None,
        existing_last_modified: str | None,
        new_etag: str | None,
        new_last_modified: str | None,
    ) -> bool:
        """Return True when the file SHA-256 hash is unchanged."""
        if existing_etag is None and new_etag is None:
            return False
        return existing_etag == new_etag

    @staticmethod
    def xǁDocumentManagerǁ_is_file_unchanged__mutmut_2(
        existing_etag: str | None,
        existing_last_modified: str | None,
        new_etag: str | None,
        new_last_modified: str | None,
    ) -> bool:
        """Return True when the file SHA-256 hash is unchanged."""
        if existing_etag is not None or new_etag is None:
            return False
        return existing_etag == new_etag

    @staticmethod
    def xǁDocumentManagerǁ_is_file_unchanged__mutmut_3(
        existing_etag: str | None,
        existing_last_modified: str | None,
        new_etag: str | None,
        new_last_modified: str | None,
    ) -> bool:
        """Return True when the file SHA-256 hash is unchanged."""
        if existing_etag is None or new_etag is not None:
            return False
        return existing_etag == new_etag

    @staticmethod
    def xǁDocumentManagerǁ_is_file_unchanged__mutmut_4(
        existing_etag: str | None,
        existing_last_modified: str | None,
        new_etag: str | None,
        new_last_modified: str | None,
    ) -> bool:
        """Return True when the file SHA-256 hash is unchanged."""
        if existing_etag is None or new_etag is None:
            return True
        return existing_etag == new_etag

    @staticmethod
    def xǁDocumentManagerǁ_is_file_unchanged__mutmut_5(
        existing_etag: str | None,
        existing_last_modified: str | None,
        new_etag: str | None,
        new_last_modified: str | None,
    ) -> bool:
        """Return True when the file SHA-256 hash is unchanged."""
        if existing_etag is None or new_etag is None:
            return False
        return existing_etag != new_etag

    @_mutmut_mutated(mutants_xǁDocumentManagerǁdelete_existing_document__mutmut)
    def delete_existing_document(self, doc_id: int) -> None:
        """Delete a document and its chunks_vec rows; documents delete cascades to chunks."""
        delete_document_chain(self._db, doc_id)

    def xǁDocumentManagerǁdelete_existing_document__mutmut_orig(self, doc_id: int) -> None:
        """Delete a document and its chunks_vec rows; documents delete cascades to chunks."""
        delete_document_chain(self._db, doc_id)

    def xǁDocumentManagerǁdelete_existing_document__mutmut_1(self, doc_id: int) -> None:
        """Delete a document and its chunks_vec rows; documents delete cascades to chunks."""
        delete_document_chain(None, doc_id)

    def xǁDocumentManagerǁdelete_existing_document__mutmut_2(self, doc_id: int) -> None:
        """Delete a document and its chunks_vec rows; documents delete cascades to chunks."""
        delete_document_chain(self._db, None)

    def xǁDocumentManagerǁdelete_existing_document__mutmut_3(self, doc_id: int) -> None:
        """Delete a document and its chunks_vec rows; documents delete cascades to chunks."""
        delete_document_chain(doc_id)

    def xǁDocumentManagerǁdelete_existing_document__mutmut_4(self, doc_id: int) -> None:
        """Delete a document and its chunks_vec rows; documents delete cascades to chunks."""
        delete_document_chain(self._db, )

    @_mutmut_mutated(mutants_xǁDocumentManagerǁcheck_consistency__mutmut)
    def check_consistency(
        self, embed_failed: int, on_ingest_complete: Callable[[], None] | None = None
    ) -> RagConsistencyReport | None:
        """Run post-ingestion consistency check and callback."""
        try:
            report = check_rag_consistency(self._db, embed_failed=embed_failed)
        except (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError):
            logger.exception("Post-ingest consistency check failed")
            return None
        self._log_consistency_issues(report)
        self._invoke_callback(on_ingest_complete)
        return report

    def xǁDocumentManagerǁcheck_consistency__mutmut_orig(
        self, embed_failed: int, on_ingest_complete: Callable[[], None] | None = None
    ) -> RagConsistencyReport | None:
        """Run post-ingestion consistency check and callback."""
        try:
            report = check_rag_consistency(self._db, embed_failed=embed_failed)
        except (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError):
            logger.exception("Post-ingest consistency check failed")
            return None
        self._log_consistency_issues(report)
        self._invoke_callback(on_ingest_complete)
        return report

    def xǁDocumentManagerǁcheck_consistency__mutmut_1(
        self, embed_failed: int, on_ingest_complete: Callable[[], None] | None = None
    ) -> RagConsistencyReport | None:
        """Run post-ingestion consistency check and callback."""
        try:
            report = None
        except (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError):
            logger.exception("Post-ingest consistency check failed")
            return None
        self._log_consistency_issues(report)
        self._invoke_callback(on_ingest_complete)
        return report

    def xǁDocumentManagerǁcheck_consistency__mutmut_2(
        self, embed_failed: int, on_ingest_complete: Callable[[], None] | None = None
    ) -> RagConsistencyReport | None:
        """Run post-ingestion consistency check and callback."""
        try:
            report = check_rag_consistency(None, embed_failed=embed_failed)
        except (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError):
            logger.exception("Post-ingest consistency check failed")
            return None
        self._log_consistency_issues(report)
        self._invoke_callback(on_ingest_complete)
        return report

    def xǁDocumentManagerǁcheck_consistency__mutmut_3(
        self, embed_failed: int, on_ingest_complete: Callable[[], None] | None = None
    ) -> RagConsistencyReport | None:
        """Run post-ingestion consistency check and callback."""
        try:
            report = check_rag_consistency(self._db, embed_failed=None)
        except (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError):
            logger.exception("Post-ingest consistency check failed")
            return None
        self._log_consistency_issues(report)
        self._invoke_callback(on_ingest_complete)
        return report

    def xǁDocumentManagerǁcheck_consistency__mutmut_4(
        self, embed_failed: int, on_ingest_complete: Callable[[], None] | None = None
    ) -> RagConsistencyReport | None:
        """Run post-ingestion consistency check and callback."""
        try:
            report = check_rag_consistency(embed_failed=embed_failed)
        except (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError):
            logger.exception("Post-ingest consistency check failed")
            return None
        self._log_consistency_issues(report)
        self._invoke_callback(on_ingest_complete)
        return report

    def xǁDocumentManagerǁcheck_consistency__mutmut_5(
        self, embed_failed: int, on_ingest_complete: Callable[[], None] | None = None
    ) -> RagConsistencyReport | None:
        """Run post-ingestion consistency check and callback."""
        try:
            report = check_rag_consistency(self._db, )
        except (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError):
            logger.exception("Post-ingest consistency check failed")
            return None
        self._log_consistency_issues(report)
        self._invoke_callback(on_ingest_complete)
        return report

    def xǁDocumentManagerǁcheck_consistency__mutmut_6(
        self, embed_failed: int, on_ingest_complete: Callable[[], None] | None = None
    ) -> RagConsistencyReport | None:
        """Run post-ingestion consistency check and callback."""
        try:
            report = check_rag_consistency(self._db, embed_failed=embed_failed)
        except (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError):
            logger.exception(None)
            return None
        self._log_consistency_issues(report)
        self._invoke_callback(on_ingest_complete)
        return report

    def xǁDocumentManagerǁcheck_consistency__mutmut_7(
        self, embed_failed: int, on_ingest_complete: Callable[[], None] | None = None
    ) -> RagConsistencyReport | None:
        """Run post-ingestion consistency check and callback."""
        try:
            report = check_rag_consistency(self._db, embed_failed=embed_failed)
        except (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError):
            logger.exception("XXPost-ingest consistency check failedXX")
            return None
        self._log_consistency_issues(report)
        self._invoke_callback(on_ingest_complete)
        return report

    def xǁDocumentManagerǁcheck_consistency__mutmut_8(
        self, embed_failed: int, on_ingest_complete: Callable[[], None] | None = None
    ) -> RagConsistencyReport | None:
        """Run post-ingestion consistency check and callback."""
        try:
            report = check_rag_consistency(self._db, embed_failed=embed_failed)
        except (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError):
            logger.exception("post-ingest consistency check failed")
            return None
        self._log_consistency_issues(report)
        self._invoke_callback(on_ingest_complete)
        return report

    def xǁDocumentManagerǁcheck_consistency__mutmut_9(
        self, embed_failed: int, on_ingest_complete: Callable[[], None] | None = None
    ) -> RagConsistencyReport | None:
        """Run post-ingestion consistency check and callback."""
        try:
            report = check_rag_consistency(self._db, embed_failed=embed_failed)
        except (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError):
            logger.exception("POST-INGEST CONSISTENCY CHECK FAILED")
            return None
        self._log_consistency_issues(report)
        self._invoke_callback(on_ingest_complete)
        return report

    def xǁDocumentManagerǁcheck_consistency__mutmut_10(
        self, embed_failed: int, on_ingest_complete: Callable[[], None] | None = None
    ) -> RagConsistencyReport | None:
        """Run post-ingestion consistency check and callback."""
        try:
            report = check_rag_consistency(self._db, embed_failed=embed_failed)
        except (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError):
            logger.exception("Post-ingest consistency check failed")
            return None
        self._log_consistency_issues(None)
        self._invoke_callback(on_ingest_complete)
        return report

    def xǁDocumentManagerǁcheck_consistency__mutmut_11(
        self, embed_failed: int, on_ingest_complete: Callable[[], None] | None = None
    ) -> RagConsistencyReport | None:
        """Run post-ingestion consistency check and callback."""
        try:
            report = check_rag_consistency(self._db, embed_failed=embed_failed)
        except (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError):
            logger.exception("Post-ingest consistency check failed")
            return None
        self._log_consistency_issues(report)
        self._invoke_callback(None)
        return report

    @_mutmut_mutated(mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut)
    def _log_consistency_issues(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    "Post-ingest consistency: %s",
                    issue,
                    extra={"stage_name": "ingester"},
                )

    def xǁDocumentManagerǁ_log_consistency_issues__mutmut_orig(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    "Post-ingest consistency: %s",
                    issue,
                    extra={"stage_name": "ingester"},
                )

    def xǁDocumentManagerǁ_log_consistency_issues__mutmut_1(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    "Post-ingest consistency: %s",
                    issue,
                    extra={"stage_name": "ingester"},
                )

    def xǁDocumentManagerǁ_log_consistency_issues__mutmut_2(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(None):
            for issue in report.issues:
                logger.warning(
                    "Post-ingest consistency: %s",
                    issue,
                    extra={"stage_name": "ingester"},
                )

    def xǁDocumentManagerǁ_log_consistency_issues__mutmut_3(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    None,
                    issue,
                    extra={"stage_name": "ingester"},
                )

    def xǁDocumentManagerǁ_log_consistency_issues__mutmut_4(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    "Post-ingest consistency: %s",
                    None,
                    extra={"stage_name": "ingester"},
                )

    def xǁDocumentManagerǁ_log_consistency_issues__mutmut_5(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    "Post-ingest consistency: %s",
                    issue,
                    extra=None,
                )

    def xǁDocumentManagerǁ_log_consistency_issues__mutmut_6(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    issue,
                    extra={"stage_name": "ingester"},
                )

    def xǁDocumentManagerǁ_log_consistency_issues__mutmut_7(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    "Post-ingest consistency: %s",
                    extra={"stage_name": "ingester"},
                )

    def xǁDocumentManagerǁ_log_consistency_issues__mutmut_8(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    "Post-ingest consistency: %s",
                    issue,
                    )

    def xǁDocumentManagerǁ_log_consistency_issues__mutmut_9(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    "XXPost-ingest consistency: %sXX",
                    issue,
                    extra={"stage_name": "ingester"},
                )

    def xǁDocumentManagerǁ_log_consistency_issues__mutmut_10(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    "post-ingest consistency: %s",
                    issue,
                    extra={"stage_name": "ingester"},
                )

    def xǁDocumentManagerǁ_log_consistency_issues__mutmut_11(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    "POST-INGEST CONSISTENCY: %S",
                    issue,
                    extra={"stage_name": "ingester"},
                )

    def xǁDocumentManagerǁ_log_consistency_issues__mutmut_12(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    "Post-ingest consistency: %s",
                    issue,
                    extra={"XXstage_nameXX": "ingester"},
                )

    def xǁDocumentManagerǁ_log_consistency_issues__mutmut_13(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    "Post-ingest consistency: %s",
                    issue,
                    extra={"STAGE_NAME": "ingester"},
                )

    def xǁDocumentManagerǁ_log_consistency_issues__mutmut_14(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    "Post-ingest consistency: %s",
                    issue,
                    extra={"stage_name": "XXingesterXX"},
                )

    def xǁDocumentManagerǁ_log_consistency_issues__mutmut_15(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    "Post-ingest consistency: %s",
                    issue,
                    extra={"stage_name": "INGESTER"},
                )

    @staticmethod
    @_mutmut_mutated(mutants_xǁDocumentManagerǁ_invoke_callback__mutmut)
    def _invoke_callback(callback: Callable[[], None] | None) -> None:
        """Invoke the callback, logging any exception without re-raising."""
        if callback is not None:
            try:
                callback()
            except (TypeError, ValueError):
                logger.exception("on_ingest_complete callback failed")

    @staticmethod
    def xǁDocumentManagerǁ_invoke_callback__mutmut_orig(callback: Callable[[], None] | None) -> None:
        """Invoke the callback, logging any exception without re-raising."""
        if callback is not None:
            try:
                callback()
            except (TypeError, ValueError):
                logger.exception("on_ingest_complete callback failed")

    @staticmethod
    def xǁDocumentManagerǁ_invoke_callback__mutmut_1(callback: Callable[[], None] | None) -> None:
        """Invoke the callback, logging any exception without re-raising."""
        if callback is None:
            try:
                callback()
            except (TypeError, ValueError):
                logger.exception("on_ingest_complete callback failed")

    @staticmethod
    def xǁDocumentManagerǁ_invoke_callback__mutmut_2(callback: Callable[[], None] | None) -> None:
        """Invoke the callback, logging any exception without re-raising."""
        if callback is not None:
            try:
                callback()
            except (TypeError, ValueError):
                logger.exception(None)

    @staticmethod
    def xǁDocumentManagerǁ_invoke_callback__mutmut_3(callback: Callable[[], None] | None) -> None:
        """Invoke the callback, logging any exception without re-raising."""
        if callback is not None:
            try:
                callback()
            except (TypeError, ValueError):
                logger.exception("XXon_ingest_complete callback failedXX")

    @staticmethod
    def xǁDocumentManagerǁ_invoke_callback__mutmut_4(callback: Callable[[], None] | None) -> None:
        """Invoke the callback, logging any exception without re-raising."""
        if callback is not None:
            try:
                callback()
            except (TypeError, ValueError):
                logger.exception("ON_INGEST_COMPLETE CALLBACK FAILED")

mutants_xǁDocumentManagerǁ__init____mutmut['_mutmut_orig'] = DocumentManager.xǁDocumentManagerǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ__init____mutmut['xǁDocumentManagerǁ__init____mutmut_1'] = DocumentManager.xǁDocumentManagerǁ__init____mutmut_1 # type: ignore # mutmut generated

mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['_mutmut_orig'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_orig # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_1'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_1 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_2'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_2 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_3'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_3 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_4'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_4 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_5'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_5 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_6'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_6 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_7'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_7 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_8'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_8 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_9'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_9 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_10'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_10 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_11'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_11 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_12'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_12 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_13'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_13 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_14'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_14 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_15'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_15 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_16'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_16 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_17'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_17 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_18'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_18 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_19'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_19 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_20'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_20 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_21'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_21 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_22'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_22 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_23'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_23 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_24'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_24 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_25'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_25 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_26'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_26 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_27'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_27 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_28'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_28 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_29'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_29 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_30'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_30 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_31'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_31 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_32'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_32 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_33'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_33 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_34'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_34 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_35'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_35 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_36'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_36 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_37'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_37 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_38'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_38 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_39'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_39 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_40'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_40 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_41'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_41 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_42'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_42 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_43'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_43 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_44'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_44 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_45'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_45 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_46'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_46 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_47'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_47 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_48'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_48 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_49'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_49 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_50'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_50 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_51'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_51 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_52'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_52 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_53'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_53 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_54'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_54 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_55'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_55 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_56'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_56 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_57'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_57 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_58'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_58 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_59'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_59 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_60'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_60 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_61'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_61 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_62'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_62 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_63'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_63 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_64'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_64 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_65'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_65 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_66'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_66 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_67'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_67 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_68'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_68 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_69'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_69 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_70'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_70 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_71'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_71 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_72'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_72 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_73'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_73 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_74'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_74 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_75'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_75 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_76'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_76 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_77'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_77 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_78'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_78 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_79'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_79 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_80'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_80 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_81'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_81 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_82'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_82 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_83'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_83 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁhandle_existing_document__mutmut['xǁDocumentManagerǁhandle_existing_document__mutmut_84'] = DocumentManager.xǁDocumentManagerǁhandle_existing_document__mutmut_84 # type: ignore # mutmut generated

mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['_mutmut_orig'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_orig # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_1'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_1 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_2'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_2 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_3'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_3 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_4'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_4 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_5'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_5 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_6'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_6 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_7'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_7 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_8'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_8 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_9'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_9 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_10'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_10 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_11'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_11 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_12'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_12 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_13'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_13 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_14'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_14 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_15'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_15 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_16'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_16 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_17'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_17 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_18'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_18 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_19'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_19 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_20'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_20 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_21'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_21 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_22'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_22 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_23'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_23 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_24'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_24 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_25'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_25 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_26'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_26 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_27'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_27 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_28'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_28 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_29'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_29 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_30'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_30 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_31'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_31 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_32'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_32 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_33'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_33 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_34'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_34 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_35'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_35 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_36'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_36 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_37'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_37 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_38'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_38 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_39'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_39 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_40'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_40 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_41'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_41 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_42'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_42 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_43'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_43 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_44'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_44 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_45'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_45 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_46'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_46 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_47'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_47 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_handle_existing_file__mutmut['xǁDocumentManagerǁ_handle_existing_file__mutmut_48'] = DocumentManager.xǁDocumentManagerǁ_handle_existing_file__mutmut_48 # type: ignore # mutmut generated

mutants_xǁDocumentManagerǁ_update_etag__mutmut['_mutmut_orig'] = DocumentManager.xǁDocumentManagerǁ_update_etag__mutmut_orig # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_update_etag__mutmut['xǁDocumentManagerǁ_update_etag__mutmut_1'] = DocumentManager.xǁDocumentManagerǁ_update_etag__mutmut_1 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_update_etag__mutmut['xǁDocumentManagerǁ_update_etag__mutmut_2'] = DocumentManager.xǁDocumentManagerǁ_update_etag__mutmut_2 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_update_etag__mutmut['xǁDocumentManagerǁ_update_etag__mutmut_3'] = DocumentManager.xǁDocumentManagerǁ_update_etag__mutmut_3 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_update_etag__mutmut['xǁDocumentManagerǁ_update_etag__mutmut_4'] = DocumentManager.xǁDocumentManagerǁ_update_etag__mutmut_4 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_update_etag__mutmut['xǁDocumentManagerǁ_update_etag__mutmut_5'] = DocumentManager.xǁDocumentManagerǁ_update_etag__mutmut_5 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_update_etag__mutmut['xǁDocumentManagerǁ_update_etag__mutmut_6'] = DocumentManager.xǁDocumentManagerǁ_update_etag__mutmut_6 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_update_etag__mutmut['xǁDocumentManagerǁ_update_etag__mutmut_7'] = DocumentManager.xǁDocumentManagerǁ_update_etag__mutmut_7 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_update_etag__mutmut['xǁDocumentManagerǁ_update_etag__mutmut_8'] = DocumentManager.xǁDocumentManagerǁ_update_etag__mutmut_8 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_update_etag__mutmut['xǁDocumentManagerǁ_update_etag__mutmut_9'] = DocumentManager.xǁDocumentManagerǁ_update_etag__mutmut_9 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_update_etag__mutmut['xǁDocumentManagerǁ_update_etag__mutmut_10'] = DocumentManager.xǁDocumentManagerǁ_update_etag__mutmut_10 # type: ignore # mutmut generated

mutants_xǁDocumentManagerǁ_is_file_unchanged__mutmut['_mutmut_orig'] = DocumentManager.xǁDocumentManagerǁ_is_file_unchanged__mutmut_orig # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_is_file_unchanged__mutmut['xǁDocumentManagerǁ_is_file_unchanged__mutmut_1'] = DocumentManager.xǁDocumentManagerǁ_is_file_unchanged__mutmut_1 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_is_file_unchanged__mutmut['xǁDocumentManagerǁ_is_file_unchanged__mutmut_2'] = DocumentManager.xǁDocumentManagerǁ_is_file_unchanged__mutmut_2 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_is_file_unchanged__mutmut['xǁDocumentManagerǁ_is_file_unchanged__mutmut_3'] = DocumentManager.xǁDocumentManagerǁ_is_file_unchanged__mutmut_3 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_is_file_unchanged__mutmut['xǁDocumentManagerǁ_is_file_unchanged__mutmut_4'] = DocumentManager.xǁDocumentManagerǁ_is_file_unchanged__mutmut_4 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_is_file_unchanged__mutmut['xǁDocumentManagerǁ_is_file_unchanged__mutmut_5'] = DocumentManager.xǁDocumentManagerǁ_is_file_unchanged__mutmut_5 # type: ignore # mutmut generated

mutants_xǁDocumentManagerǁdelete_existing_document__mutmut['_mutmut_orig'] = DocumentManager.xǁDocumentManagerǁdelete_existing_document__mutmut_orig # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁdelete_existing_document__mutmut['xǁDocumentManagerǁdelete_existing_document__mutmut_1'] = DocumentManager.xǁDocumentManagerǁdelete_existing_document__mutmut_1 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁdelete_existing_document__mutmut['xǁDocumentManagerǁdelete_existing_document__mutmut_2'] = DocumentManager.xǁDocumentManagerǁdelete_existing_document__mutmut_2 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁdelete_existing_document__mutmut['xǁDocumentManagerǁdelete_existing_document__mutmut_3'] = DocumentManager.xǁDocumentManagerǁdelete_existing_document__mutmut_3 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁdelete_existing_document__mutmut['xǁDocumentManagerǁdelete_existing_document__mutmut_4'] = DocumentManager.xǁDocumentManagerǁdelete_existing_document__mutmut_4 # type: ignore # mutmut generated

mutants_xǁDocumentManagerǁcheck_consistency__mutmut['_mutmut_orig'] = DocumentManager.xǁDocumentManagerǁcheck_consistency__mutmut_orig # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁcheck_consistency__mutmut['xǁDocumentManagerǁcheck_consistency__mutmut_1'] = DocumentManager.xǁDocumentManagerǁcheck_consistency__mutmut_1 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁcheck_consistency__mutmut['xǁDocumentManagerǁcheck_consistency__mutmut_2'] = DocumentManager.xǁDocumentManagerǁcheck_consistency__mutmut_2 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁcheck_consistency__mutmut['xǁDocumentManagerǁcheck_consistency__mutmut_3'] = DocumentManager.xǁDocumentManagerǁcheck_consistency__mutmut_3 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁcheck_consistency__mutmut['xǁDocumentManagerǁcheck_consistency__mutmut_4'] = DocumentManager.xǁDocumentManagerǁcheck_consistency__mutmut_4 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁcheck_consistency__mutmut['xǁDocumentManagerǁcheck_consistency__mutmut_5'] = DocumentManager.xǁDocumentManagerǁcheck_consistency__mutmut_5 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁcheck_consistency__mutmut['xǁDocumentManagerǁcheck_consistency__mutmut_6'] = DocumentManager.xǁDocumentManagerǁcheck_consistency__mutmut_6 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁcheck_consistency__mutmut['xǁDocumentManagerǁcheck_consistency__mutmut_7'] = DocumentManager.xǁDocumentManagerǁcheck_consistency__mutmut_7 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁcheck_consistency__mutmut['xǁDocumentManagerǁcheck_consistency__mutmut_8'] = DocumentManager.xǁDocumentManagerǁcheck_consistency__mutmut_8 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁcheck_consistency__mutmut['xǁDocumentManagerǁcheck_consistency__mutmut_9'] = DocumentManager.xǁDocumentManagerǁcheck_consistency__mutmut_9 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁcheck_consistency__mutmut['xǁDocumentManagerǁcheck_consistency__mutmut_10'] = DocumentManager.xǁDocumentManagerǁcheck_consistency__mutmut_10 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁcheck_consistency__mutmut['xǁDocumentManagerǁcheck_consistency__mutmut_11'] = DocumentManager.xǁDocumentManagerǁcheck_consistency__mutmut_11 # type: ignore # mutmut generated

mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut['_mutmut_orig'] = DocumentManager.xǁDocumentManagerǁ_log_consistency_issues__mutmut_orig # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut['xǁDocumentManagerǁ_log_consistency_issues__mutmut_1'] = DocumentManager.xǁDocumentManagerǁ_log_consistency_issues__mutmut_1 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut['xǁDocumentManagerǁ_log_consistency_issues__mutmut_2'] = DocumentManager.xǁDocumentManagerǁ_log_consistency_issues__mutmut_2 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut['xǁDocumentManagerǁ_log_consistency_issues__mutmut_3'] = DocumentManager.xǁDocumentManagerǁ_log_consistency_issues__mutmut_3 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut['xǁDocumentManagerǁ_log_consistency_issues__mutmut_4'] = DocumentManager.xǁDocumentManagerǁ_log_consistency_issues__mutmut_4 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut['xǁDocumentManagerǁ_log_consistency_issues__mutmut_5'] = DocumentManager.xǁDocumentManagerǁ_log_consistency_issues__mutmut_5 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut['xǁDocumentManagerǁ_log_consistency_issues__mutmut_6'] = DocumentManager.xǁDocumentManagerǁ_log_consistency_issues__mutmut_6 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut['xǁDocumentManagerǁ_log_consistency_issues__mutmut_7'] = DocumentManager.xǁDocumentManagerǁ_log_consistency_issues__mutmut_7 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut['xǁDocumentManagerǁ_log_consistency_issues__mutmut_8'] = DocumentManager.xǁDocumentManagerǁ_log_consistency_issues__mutmut_8 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut['xǁDocumentManagerǁ_log_consistency_issues__mutmut_9'] = DocumentManager.xǁDocumentManagerǁ_log_consistency_issues__mutmut_9 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut['xǁDocumentManagerǁ_log_consistency_issues__mutmut_10'] = DocumentManager.xǁDocumentManagerǁ_log_consistency_issues__mutmut_10 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut['xǁDocumentManagerǁ_log_consistency_issues__mutmut_11'] = DocumentManager.xǁDocumentManagerǁ_log_consistency_issues__mutmut_11 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut['xǁDocumentManagerǁ_log_consistency_issues__mutmut_12'] = DocumentManager.xǁDocumentManagerǁ_log_consistency_issues__mutmut_12 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut['xǁDocumentManagerǁ_log_consistency_issues__mutmut_13'] = DocumentManager.xǁDocumentManagerǁ_log_consistency_issues__mutmut_13 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut['xǁDocumentManagerǁ_log_consistency_issues__mutmut_14'] = DocumentManager.xǁDocumentManagerǁ_log_consistency_issues__mutmut_14 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_log_consistency_issues__mutmut['xǁDocumentManagerǁ_log_consistency_issues__mutmut_15'] = DocumentManager.xǁDocumentManagerǁ_log_consistency_issues__mutmut_15 # type: ignore # mutmut generated

mutants_xǁDocumentManagerǁ_invoke_callback__mutmut['_mutmut_orig'] = DocumentManager.xǁDocumentManagerǁ_invoke_callback__mutmut_orig # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_invoke_callback__mutmut['xǁDocumentManagerǁ_invoke_callback__mutmut_1'] = DocumentManager.xǁDocumentManagerǁ_invoke_callback__mutmut_1 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_invoke_callback__mutmut['xǁDocumentManagerǁ_invoke_callback__mutmut_2'] = DocumentManager.xǁDocumentManagerǁ_invoke_callback__mutmut_2 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_invoke_callback__mutmut['xǁDocumentManagerǁ_invoke_callback__mutmut_3'] = DocumentManager.xǁDocumentManagerǁ_invoke_callback__mutmut_3 # type: ignore # mutmut generated
mutants_xǁDocumentManagerǁ_invoke_callback__mutmut['xǁDocumentManagerǁ_invoke_callback__mutmut_4'] = DocumentManager.xǁDocumentManagerǁ_invoke_callback__mutmut_4 # type: ignore # mutmut generated
