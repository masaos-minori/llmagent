"""scripts/rag/ingestion/etag_manager.py

ETag manager for document freshness tracking."""

from __future__ import annotations

from datetime import UTC, datetime

from db.helper import SQLiteHelper
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/ingest.log")


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁETagManagerǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁETagManagerǁupdate__mutmut: MutantDict = {}  # type: ignore
mutants_xǁETagManagerǁ_is_stale_update__mutmut: MutantDict = {}  # type: ignore
mutants_xǁETagManagerǁ_update_with_freshness__mutmut: MutantDict = {}  # type: ignore
mutants_xǁETagManagerǁ_update_null_fill__mutmut: MutantDict = {}  # type: ignore
mutants_xǁETagManagerǁ_log_updated__mutmut: MutantDict = {}  # type: ignore


class ETagManager:
    """Manages ETag/Last-Modified updates for existing documents."""

    @_mutmut_mutated(mutants_xǁETagManagerǁ__init____mutmut)
    def __init__(self, db: SQLiteHelper, doc_id: int) -> None:
        """Initialize with database helper and document ID."""
        self._db = db
        self._doc_id = doc_id

    def xǁETagManagerǁ__init____mutmut_orig(self, db: SQLiteHelper, doc_id: int) -> None:
        """Initialize with database helper and document ID."""
        self._db = db
        self._doc_id = doc_id

    def xǁETagManagerǁ__init____mutmut_1(self, db: SQLiteHelper, doc_id: int) -> None:
        """Initialize with database helper and document ID."""
        self._db = None
        self._doc_id = doc_id

    def xǁETagManagerǁ__init____mutmut_2(self, db: SQLiteHelper, doc_id: int) -> None:
        """Initialize with database helper and document ID."""
        self._db = db
        self._doc_id = None

    @_mutmut_mutated(mutants_xǁETagManagerǁupdate__mutmut)
    def update(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_orig(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_1(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None or last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_2(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is not None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_3(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is not None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_4(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(None):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_5(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                None,
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_6(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                None,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_7(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                None,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_8(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra=None,
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_9(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_10(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_11(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_12(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_13(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "XXskip-path etag update skipped: incoming stale (%s < %s) for doc_id=%dXX",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_14(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "SKIP-PATH ETAG UPDATE SKIPPED: INCOMING STALE (%S < %S) FOR DOC_ID=%D",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_15(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"XXstage_nameXX": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_16(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"STAGE_NAME": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_17(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "XXingesterXX"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_18(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "INGESTER"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_19(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_20(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(None, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_21(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, None, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_22(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, None)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_23(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_24(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_25(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, )
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_26(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(None, last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_27(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, None)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_28(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(last_modified)
        self._log_updated()

    def xǁETagManagerǁupdate__mutmut_29(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, )
        self._log_updated()

    @_mutmut_mutated(mutants_xǁETagManagerǁ_is_stale_update__mutmut)
    def _is_stale_update(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_orig(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_1(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is not None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_2(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return True

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_3(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = None
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_4(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(None)
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_5(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace(None, "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_6(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", None))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_7(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_8(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", ))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_9(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("XXZXX", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_10(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_11(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "XX+00:00XX"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_12(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is not None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_13(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = None
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_14(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=None)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_15(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(None)
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_16(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return True  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_17(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = None
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_18(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            None, (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_19(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", None
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_20(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_21(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_22(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "XXSELECT fetched_at FROM documents WHERE doc_id = ?XX", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_23(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "select fetched_at from documents where doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_24(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT FETCHED_AT FROM DOCUMENTS WHERE DOC_ID = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_25(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_26(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[1][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_27(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][1] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_28(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_29(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return True

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_30(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = None
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_31(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(None)
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_32(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace(None, "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_33(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", None))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_34(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_35(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", ))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_36(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("XXZXX", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_37(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_38(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "XX+00:00XX"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_39(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is not None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_40(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = None
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_41(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=None)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_42(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(None)
            return False  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_43(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return True  # Treat invalid timestamps as non-stale

        return new_dt < stored_dt

    def xǁETagManagerǁ_is_stale_update__mutmut_44(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {new_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            logger.error(f"Invalid timestamp format: {stored_fetched_at}")
            return False  # Treat invalid timestamps as non-stale

        return new_dt <= stored_dt

    @_mutmut_mutated(mutants_xǁETagManagerǁ_update_with_freshness__mutmut)
    def _update_with_freshness(
        self,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str,
    ) -> None:
        """Overwrite ETag/Last-Modified when freshness is proven."""
        self._db.execute(
            "UPDATE documents SET etag = ?, last_modified = ?, fetched_at = COALESCE(?, fetched_at) WHERE doc_id = ?",
            (etag, last_modified, fetched_at, self._doc_id),
        )

    def xǁETagManagerǁ_update_with_freshness__mutmut_orig(
        self,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str,
    ) -> None:
        """Overwrite ETag/Last-Modified when freshness is proven."""
        self._db.execute(
            "UPDATE documents SET etag = ?, last_modified = ?, fetched_at = COALESCE(?, fetched_at) WHERE doc_id = ?",
            (etag, last_modified, fetched_at, self._doc_id),
        )

    def xǁETagManagerǁ_update_with_freshness__mutmut_1(
        self,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str,
    ) -> None:
        """Overwrite ETag/Last-Modified when freshness is proven."""
        self._db.execute(
            None,
            (etag, last_modified, fetched_at, self._doc_id),
        )

    def xǁETagManagerǁ_update_with_freshness__mutmut_2(
        self,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str,
    ) -> None:
        """Overwrite ETag/Last-Modified when freshness is proven."""
        self._db.execute(
            "UPDATE documents SET etag = ?, last_modified = ?, fetched_at = COALESCE(?, fetched_at) WHERE doc_id = ?",
            None,
        )

    def xǁETagManagerǁ_update_with_freshness__mutmut_3(
        self,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str,
    ) -> None:
        """Overwrite ETag/Last-Modified when freshness is proven."""
        self._db.execute(
            (etag, last_modified, fetched_at, self._doc_id),
        )

    def xǁETagManagerǁ_update_with_freshness__mutmut_4(
        self,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str,
    ) -> None:
        """Overwrite ETag/Last-Modified when freshness is proven."""
        self._db.execute(
            "UPDATE documents SET etag = ?, last_modified = ?, fetched_at = COALESCE(?, fetched_at) WHERE doc_id = ?",
            )

    def xǁETagManagerǁ_update_with_freshness__mutmut_5(
        self,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str,
    ) -> None:
        """Overwrite ETag/Last-Modified when freshness is proven."""
        self._db.execute(
            "XXUPDATE documents SET etag = ?, last_modified = ?, fetched_at = COALESCE(?, fetched_at) WHERE doc_id = ?XX",
            (etag, last_modified, fetched_at, self._doc_id),
        )

    def xǁETagManagerǁ_update_with_freshness__mutmut_6(
        self,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str,
    ) -> None:
        """Overwrite ETag/Last-Modified when freshness is proven."""
        self._db.execute(
            "update documents set etag = ?, last_modified = ?, fetched_at = coalesce(?, fetched_at) where doc_id = ?",
            (etag, last_modified, fetched_at, self._doc_id),
        )

    def xǁETagManagerǁ_update_with_freshness__mutmut_7(
        self,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str,
    ) -> None:
        """Overwrite ETag/Last-Modified when freshness is proven."""
        self._db.execute(
            "UPDATE DOCUMENTS SET ETAG = ?, LAST_MODIFIED = ?, FETCHED_AT = COALESCE(?, FETCHED_AT) WHERE DOC_ID = ?",
            (etag, last_modified, fetched_at, self._doc_id),
        )

    @_mutmut_mutated(mutants_xǁETagManagerǁ_update_null_fill__mutmut)
    def _update_null_fill(self, etag: str | None, last_modified: str | None) -> None:
        """Fill NULL only; never overwrite existing values."""
        self._db.execute(
            "UPDATE documents SET etag = COALESCE(etag, ?), last_modified = COALESCE(last_modified, ?)"
            " WHERE doc_id = ?",
            (etag, last_modified, self._doc_id),
        )

    def xǁETagManagerǁ_update_null_fill__mutmut_orig(self, etag: str | None, last_modified: str | None) -> None:
        """Fill NULL only; never overwrite existing values."""
        self._db.execute(
            "UPDATE documents SET etag = COALESCE(etag, ?), last_modified = COALESCE(last_modified, ?)"
            " WHERE doc_id = ?",
            (etag, last_modified, self._doc_id),
        )

    def xǁETagManagerǁ_update_null_fill__mutmut_1(self, etag: str | None, last_modified: str | None) -> None:
        """Fill NULL only; never overwrite existing values."""
        self._db.execute(
            None,
            (etag, last_modified, self._doc_id),
        )

    def xǁETagManagerǁ_update_null_fill__mutmut_2(self, etag: str | None, last_modified: str | None) -> None:
        """Fill NULL only; never overwrite existing values."""
        self._db.execute(
            "UPDATE documents SET etag = COALESCE(etag, ?), last_modified = COALESCE(last_modified, ?)"
            " WHERE doc_id = ?",
            None,
        )

    def xǁETagManagerǁ_update_null_fill__mutmut_3(self, etag: str | None, last_modified: str | None) -> None:
        """Fill NULL only; never overwrite existing values."""
        self._db.execute(
            (etag, last_modified, self._doc_id),
        )

    def xǁETagManagerǁ_update_null_fill__mutmut_4(self, etag: str | None, last_modified: str | None) -> None:
        """Fill NULL only; never overwrite existing values."""
        self._db.execute(
            "UPDATE documents SET etag = COALESCE(etag, ?), last_modified = COALESCE(last_modified, ?)"
            " WHERE doc_id = ?",
            )

    def xǁETagManagerǁ_update_null_fill__mutmut_5(self, etag: str | None, last_modified: str | None) -> None:
        """Fill NULL only; never overwrite existing values."""
        self._db.execute(
            "XXUPDATE documents SET etag = COALESCE(etag, ?), last_modified = COALESCE(last_modified, ?)XX"
            " WHERE doc_id = ?",
            (etag, last_modified, self._doc_id),
        )

    def xǁETagManagerǁ_update_null_fill__mutmut_6(self, etag: str | None, last_modified: str | None) -> None:
        """Fill NULL only; never overwrite existing values."""
        self._db.execute(
            "update documents set etag = coalesce(etag, ?), last_modified = coalesce(last_modified, ?)"
            " WHERE doc_id = ?",
            (etag, last_modified, self._doc_id),
        )

    def xǁETagManagerǁ_update_null_fill__mutmut_7(self, etag: str | None, last_modified: str | None) -> None:
        """Fill NULL only; never overwrite existing values."""
        self._db.execute(
            "UPDATE DOCUMENTS SET ETAG = COALESCE(ETAG, ?), LAST_MODIFIED = COALESCE(LAST_MODIFIED, ?)"
            " WHERE doc_id = ?",
            (etag, last_modified, self._doc_id),
        )

    def xǁETagManagerǁ_update_null_fill__mutmut_8(self, etag: str | None, last_modified: str | None) -> None:
        """Fill NULL only; never overwrite existing values."""
        self._db.execute(
            "UPDATE documents SET etag = COALESCE(etag, ?), last_modified = COALESCE(last_modified, ?)"
            "XX WHERE doc_id = ?XX",
            (etag, last_modified, self._doc_id),
        )

    def xǁETagManagerǁ_update_null_fill__mutmut_9(self, etag: str | None, last_modified: str | None) -> None:
        """Fill NULL only; never overwrite existing values."""
        self._db.execute(
            "UPDATE documents SET etag = COALESCE(etag, ?), last_modified = COALESCE(last_modified, ?)"
            " where doc_id = ?",
            (etag, last_modified, self._doc_id),
        )

    def xǁETagManagerǁ_update_null_fill__mutmut_10(self, etag: str | None, last_modified: str | None) -> None:
        """Fill NULL only; never overwrite existing values."""
        self._db.execute(
            "UPDATE documents SET etag = COALESCE(etag, ?), last_modified = COALESCE(last_modified, ?)"
            " WHERE DOC_ID = ?",
            (etag, last_modified, self._doc_id),
        )

    @_mutmut_mutated(mutants_xǁETagManagerǁ_log_updated__mutmut)
    def _log_updated(self) -> None:
        """Log the etag update."""
        logger.info(
            "skip-path etag updated for doc_id=%d",
            self._doc_id,
            extra={"stage_name": "ingester"},
        )

    def xǁETagManagerǁ_log_updated__mutmut_orig(self) -> None:
        """Log the etag update."""
        logger.info(
            "skip-path etag updated for doc_id=%d",
            self._doc_id,
            extra={"stage_name": "ingester"},
        )

    def xǁETagManagerǁ_log_updated__mutmut_1(self) -> None:
        """Log the etag update."""
        logger.info(
            None,
            self._doc_id,
            extra={"stage_name": "ingester"},
        )

    def xǁETagManagerǁ_log_updated__mutmut_2(self) -> None:
        """Log the etag update."""
        logger.info(
            "skip-path etag updated for doc_id=%d",
            None,
            extra={"stage_name": "ingester"},
        )

    def xǁETagManagerǁ_log_updated__mutmut_3(self) -> None:
        """Log the etag update."""
        logger.info(
            "skip-path etag updated for doc_id=%d",
            self._doc_id,
            extra=None,
        )

    def xǁETagManagerǁ_log_updated__mutmut_4(self) -> None:
        """Log the etag update."""
        logger.info(
            self._doc_id,
            extra={"stage_name": "ingester"},
        )

    def xǁETagManagerǁ_log_updated__mutmut_5(self) -> None:
        """Log the etag update."""
        logger.info(
            "skip-path etag updated for doc_id=%d",
            extra={"stage_name": "ingester"},
        )

    def xǁETagManagerǁ_log_updated__mutmut_6(self) -> None:
        """Log the etag update."""
        logger.info(
            "skip-path etag updated for doc_id=%d",
            self._doc_id,
            )

    def xǁETagManagerǁ_log_updated__mutmut_7(self) -> None:
        """Log the etag update."""
        logger.info(
            "XXskip-path etag updated for doc_id=%dXX",
            self._doc_id,
            extra={"stage_name": "ingester"},
        )

    def xǁETagManagerǁ_log_updated__mutmut_8(self) -> None:
        """Log the etag update."""
        logger.info(
            "SKIP-PATH ETAG UPDATED FOR DOC_ID=%D",
            self._doc_id,
            extra={"stage_name": "ingester"},
        )

    def xǁETagManagerǁ_log_updated__mutmut_9(self) -> None:
        """Log the etag update."""
        logger.info(
            "skip-path etag updated for doc_id=%d",
            self._doc_id,
            extra={"XXstage_nameXX": "ingester"},
        )

    def xǁETagManagerǁ_log_updated__mutmut_10(self) -> None:
        """Log the etag update."""
        logger.info(
            "skip-path etag updated for doc_id=%d",
            self._doc_id,
            extra={"STAGE_NAME": "ingester"},
        )

    def xǁETagManagerǁ_log_updated__mutmut_11(self) -> None:
        """Log the etag update."""
        logger.info(
            "skip-path etag updated for doc_id=%d",
            self._doc_id,
            extra={"stage_name": "XXingesterXX"},
        )

    def xǁETagManagerǁ_log_updated__mutmut_12(self) -> None:
        """Log the etag update."""
        logger.info(
            "skip-path etag updated for doc_id=%d",
            self._doc_id,
            extra={"stage_name": "INGESTER"},
        )

mutants_xǁETagManagerǁ__init____mutmut['_mutmut_orig'] = ETagManager.xǁETagManagerǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁETagManagerǁ__init____mutmut['xǁETagManagerǁ__init____mutmut_1'] = ETagManager.xǁETagManagerǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ__init____mutmut['xǁETagManagerǁ__init____mutmut_2'] = ETagManager.xǁETagManagerǁ__init____mutmut_2 # type: ignore # mutmut generated

mutants_xǁETagManagerǁupdate__mutmut['_mutmut_orig'] = ETagManager.xǁETagManagerǁupdate__mutmut_orig # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_1'] = ETagManager.xǁETagManagerǁupdate__mutmut_1 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_2'] = ETagManager.xǁETagManagerǁupdate__mutmut_2 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_3'] = ETagManager.xǁETagManagerǁupdate__mutmut_3 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_4'] = ETagManager.xǁETagManagerǁupdate__mutmut_4 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_5'] = ETagManager.xǁETagManagerǁupdate__mutmut_5 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_6'] = ETagManager.xǁETagManagerǁupdate__mutmut_6 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_7'] = ETagManager.xǁETagManagerǁupdate__mutmut_7 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_8'] = ETagManager.xǁETagManagerǁupdate__mutmut_8 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_9'] = ETagManager.xǁETagManagerǁupdate__mutmut_9 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_10'] = ETagManager.xǁETagManagerǁupdate__mutmut_10 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_11'] = ETagManager.xǁETagManagerǁupdate__mutmut_11 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_12'] = ETagManager.xǁETagManagerǁupdate__mutmut_12 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_13'] = ETagManager.xǁETagManagerǁupdate__mutmut_13 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_14'] = ETagManager.xǁETagManagerǁupdate__mutmut_14 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_15'] = ETagManager.xǁETagManagerǁupdate__mutmut_15 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_16'] = ETagManager.xǁETagManagerǁupdate__mutmut_16 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_17'] = ETagManager.xǁETagManagerǁupdate__mutmut_17 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_18'] = ETagManager.xǁETagManagerǁupdate__mutmut_18 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_19'] = ETagManager.xǁETagManagerǁupdate__mutmut_19 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_20'] = ETagManager.xǁETagManagerǁupdate__mutmut_20 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_21'] = ETagManager.xǁETagManagerǁupdate__mutmut_21 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_22'] = ETagManager.xǁETagManagerǁupdate__mutmut_22 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_23'] = ETagManager.xǁETagManagerǁupdate__mutmut_23 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_24'] = ETagManager.xǁETagManagerǁupdate__mutmut_24 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_25'] = ETagManager.xǁETagManagerǁupdate__mutmut_25 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_26'] = ETagManager.xǁETagManagerǁupdate__mutmut_26 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_27'] = ETagManager.xǁETagManagerǁupdate__mutmut_27 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_28'] = ETagManager.xǁETagManagerǁupdate__mutmut_28 # type: ignore # mutmut generated
mutants_xǁETagManagerǁupdate__mutmut['xǁETagManagerǁupdate__mutmut_29'] = ETagManager.xǁETagManagerǁupdate__mutmut_29 # type: ignore # mutmut generated

mutants_xǁETagManagerǁ_is_stale_update__mutmut['_mutmut_orig'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_orig # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_1'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_1 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_2'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_2 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_3'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_3 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_4'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_4 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_5'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_5 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_6'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_6 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_7'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_7 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_8'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_8 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_9'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_9 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_10'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_10 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_11'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_11 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_12'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_12 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_13'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_13 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_14'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_14 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_15'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_15 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_16'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_16 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_17'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_17 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_18'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_18 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_19'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_19 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_20'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_20 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_21'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_21 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_22'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_22 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_23'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_23 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_24'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_24 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_25'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_25 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_26'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_26 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_27'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_27 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_28'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_28 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_29'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_29 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_30'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_30 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_31'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_31 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_32'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_32 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_33'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_33 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_34'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_34 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_35'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_35 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_36'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_36 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_37'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_37 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_38'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_38 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_39'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_39 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_40'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_40 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_41'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_41 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_42'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_42 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_43'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_43 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_is_stale_update__mutmut['xǁETagManagerǁ_is_stale_update__mutmut_44'] = ETagManager.xǁETagManagerǁ_is_stale_update__mutmut_44 # type: ignore # mutmut generated

mutants_xǁETagManagerǁ_update_with_freshness__mutmut['_mutmut_orig'] = ETagManager.xǁETagManagerǁ_update_with_freshness__mutmut_orig # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_with_freshness__mutmut['xǁETagManagerǁ_update_with_freshness__mutmut_1'] = ETagManager.xǁETagManagerǁ_update_with_freshness__mutmut_1 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_with_freshness__mutmut['xǁETagManagerǁ_update_with_freshness__mutmut_2'] = ETagManager.xǁETagManagerǁ_update_with_freshness__mutmut_2 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_with_freshness__mutmut['xǁETagManagerǁ_update_with_freshness__mutmut_3'] = ETagManager.xǁETagManagerǁ_update_with_freshness__mutmut_3 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_with_freshness__mutmut['xǁETagManagerǁ_update_with_freshness__mutmut_4'] = ETagManager.xǁETagManagerǁ_update_with_freshness__mutmut_4 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_with_freshness__mutmut['xǁETagManagerǁ_update_with_freshness__mutmut_5'] = ETagManager.xǁETagManagerǁ_update_with_freshness__mutmut_5 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_with_freshness__mutmut['xǁETagManagerǁ_update_with_freshness__mutmut_6'] = ETagManager.xǁETagManagerǁ_update_with_freshness__mutmut_6 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_with_freshness__mutmut['xǁETagManagerǁ_update_with_freshness__mutmut_7'] = ETagManager.xǁETagManagerǁ_update_with_freshness__mutmut_7 # type: ignore # mutmut generated

mutants_xǁETagManagerǁ_update_null_fill__mutmut['_mutmut_orig'] = ETagManager.xǁETagManagerǁ_update_null_fill__mutmut_orig # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_null_fill__mutmut['xǁETagManagerǁ_update_null_fill__mutmut_1'] = ETagManager.xǁETagManagerǁ_update_null_fill__mutmut_1 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_null_fill__mutmut['xǁETagManagerǁ_update_null_fill__mutmut_2'] = ETagManager.xǁETagManagerǁ_update_null_fill__mutmut_2 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_null_fill__mutmut['xǁETagManagerǁ_update_null_fill__mutmut_3'] = ETagManager.xǁETagManagerǁ_update_null_fill__mutmut_3 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_null_fill__mutmut['xǁETagManagerǁ_update_null_fill__mutmut_4'] = ETagManager.xǁETagManagerǁ_update_null_fill__mutmut_4 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_null_fill__mutmut['xǁETagManagerǁ_update_null_fill__mutmut_5'] = ETagManager.xǁETagManagerǁ_update_null_fill__mutmut_5 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_null_fill__mutmut['xǁETagManagerǁ_update_null_fill__mutmut_6'] = ETagManager.xǁETagManagerǁ_update_null_fill__mutmut_6 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_null_fill__mutmut['xǁETagManagerǁ_update_null_fill__mutmut_7'] = ETagManager.xǁETagManagerǁ_update_null_fill__mutmut_7 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_null_fill__mutmut['xǁETagManagerǁ_update_null_fill__mutmut_8'] = ETagManager.xǁETagManagerǁ_update_null_fill__mutmut_8 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_null_fill__mutmut['xǁETagManagerǁ_update_null_fill__mutmut_9'] = ETagManager.xǁETagManagerǁ_update_null_fill__mutmut_9 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_update_null_fill__mutmut['xǁETagManagerǁ_update_null_fill__mutmut_10'] = ETagManager.xǁETagManagerǁ_update_null_fill__mutmut_10 # type: ignore # mutmut generated

mutants_xǁETagManagerǁ_log_updated__mutmut['_mutmut_orig'] = ETagManager.xǁETagManagerǁ_log_updated__mutmut_orig # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_log_updated__mutmut['xǁETagManagerǁ_log_updated__mutmut_1'] = ETagManager.xǁETagManagerǁ_log_updated__mutmut_1 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_log_updated__mutmut['xǁETagManagerǁ_log_updated__mutmut_2'] = ETagManager.xǁETagManagerǁ_log_updated__mutmut_2 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_log_updated__mutmut['xǁETagManagerǁ_log_updated__mutmut_3'] = ETagManager.xǁETagManagerǁ_log_updated__mutmut_3 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_log_updated__mutmut['xǁETagManagerǁ_log_updated__mutmut_4'] = ETagManager.xǁETagManagerǁ_log_updated__mutmut_4 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_log_updated__mutmut['xǁETagManagerǁ_log_updated__mutmut_5'] = ETagManager.xǁETagManagerǁ_log_updated__mutmut_5 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_log_updated__mutmut['xǁETagManagerǁ_log_updated__mutmut_6'] = ETagManager.xǁETagManagerǁ_log_updated__mutmut_6 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_log_updated__mutmut['xǁETagManagerǁ_log_updated__mutmut_7'] = ETagManager.xǁETagManagerǁ_log_updated__mutmut_7 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_log_updated__mutmut['xǁETagManagerǁ_log_updated__mutmut_8'] = ETagManager.xǁETagManagerǁ_log_updated__mutmut_8 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_log_updated__mutmut['xǁETagManagerǁ_log_updated__mutmut_9'] = ETagManager.xǁETagManagerǁ_log_updated__mutmut_9 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_log_updated__mutmut['xǁETagManagerǁ_log_updated__mutmut_10'] = ETagManager.xǁETagManagerǁ_log_updated__mutmut_10 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_log_updated__mutmut['xǁETagManagerǁ_log_updated__mutmut_11'] = ETagManager.xǁETagManagerǁ_log_updated__mutmut_11 # type: ignore # mutmut generated
mutants_xǁETagManagerǁ_log_updated__mutmut['xǁETagManagerǁ_log_updated__mutmut_12'] = ETagManager.xǁETagManagerǁ_log_updated__mutmut_12 # type: ignore # mutmut generated
