"""scripts/rag/maintenance.py — RAG-specific database maintenance operations."""

from __future__ import annotations

from db.helper import SQLiteHelper


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁRagDbMaintenanceServiceǁrotate__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRagDbMaintenanceServiceǁvacuum__mutmut: MutantDict = {}  # type: ignore


class RagDbMaintenanceService:
    """Maintenance operations scoped to the RAG database."""

    @_mutmut_mutated(mutants_xǁRagDbMaintenanceServiceǁrotate__mutmut)
    def rotate(self) -> None:
        """Rotate the RAG database (copy + truncate + WAL checkpoint)."""
        with SQLiteHelper("rag").open() as db:
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def xǁRagDbMaintenanceServiceǁrotate__mutmut_orig(self) -> None:
        """Rotate the RAG database (copy + truncate + WAL checkpoint)."""
        with SQLiteHelper("rag").open() as db:
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def xǁRagDbMaintenanceServiceǁrotate__mutmut_1(self) -> None:
        """Rotate the RAG database (copy + truncate + WAL checkpoint)."""
        with SQLiteHelper(None).open() as db:
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def xǁRagDbMaintenanceServiceǁrotate__mutmut_2(self) -> None:
        """Rotate the RAG database (copy + truncate + WAL checkpoint)."""
        with SQLiteHelper("XXragXX").open() as db:
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def xǁRagDbMaintenanceServiceǁrotate__mutmut_3(self) -> None:
        """Rotate the RAG database (copy + truncate + WAL checkpoint)."""
        with SQLiteHelper("RAG").open() as db:
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def xǁRagDbMaintenanceServiceǁrotate__mutmut_4(self) -> None:
        """Rotate the RAG database (copy + truncate + WAL checkpoint)."""
        with SQLiteHelper("rag").open() as db:
            db.execute(None)

    def xǁRagDbMaintenanceServiceǁrotate__mutmut_5(self) -> None:
        """Rotate the RAG database (copy + truncate + WAL checkpoint)."""
        with SQLiteHelper("rag").open() as db:
            db.execute("XXPRAGMA wal_checkpoint(TRUNCATE)XX")

    def xǁRagDbMaintenanceServiceǁrotate__mutmut_6(self) -> None:
        """Rotate the RAG database (copy + truncate + WAL checkpoint)."""
        with SQLiteHelper("rag").open() as db:
            db.execute("pragma wal_checkpoint(truncate)")

    def xǁRagDbMaintenanceServiceǁrotate__mutmut_7(self) -> None:
        """Rotate the RAG database (copy + truncate + WAL checkpoint)."""
        with SQLiteHelper("rag").open() as db:
            db.execute("PRAGMA WAL_CHECKPOINT(TRUNCATE)")

    @_mutmut_mutated(mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut)
    def rebuild_fts(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_orig(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_1(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper(None).open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_2(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("XXragXX").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_3(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("RAG").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_4(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute(None)
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_5(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("XXDROP TRIGGER IF EXISTS chunks_aiXX")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_6(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("drop trigger if exists chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_7(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS CHUNKS_AI")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_8(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute(None)
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_9(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("XXDROP TRIGGER IF EXISTS chunks_adXX")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_10(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("drop trigger if exists chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_11(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS CHUNKS_AD")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_12(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute(None)
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_13(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("XXDROP TRIGGER IF EXISTS chunks_auXX")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_14(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("drop trigger if exists chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_15(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS CHUNKS_AU")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_16(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute(None)
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_17(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("XXDROP TABLE IF EXISTS chunks_ftsXX")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_18(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("drop table if exists chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_19(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS CHUNKS_FTS")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_20(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                None
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_21(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "XXCREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')XX"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_22(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "create virtual table chunks_fts using fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_23(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE CHUNKS_FTS USING FTS5(  CONTENT,  TOKENIZE = 'UNICODE61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_24(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                None
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_25(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "XXINSERT INTO chunks_fts(rowid, content)XX"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_26(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "insert into chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_27(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO CHUNKS_FTS(ROWID, CONTENT)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_28(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                "XX SELECT chunk_id, COALESCE(normalized_content, content) FROM chunksXX"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_29(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " select chunk_id, coalesce(normalized_content, content) from chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_30(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT CHUNK_ID, COALESCE(NORMALIZED_CONTENT, CONTENT) FROM CHUNKS"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_31(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                None
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_32(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "XXCREATE TRIGGER IF NOT EXISTS chunks_ai XX"
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_33(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "create trigger if not exists chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_34(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS CHUNKS_AI "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_35(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "XXAFTER INSERT ON chunks BEGIN XX"
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_36(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "after insert on chunks begin "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_37(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON CHUNKS BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_38(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "XX  INSERT INTO chunks_fts (rowid, content) XX"
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_39(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  insert into chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_40(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO CHUNKS_FTS (ROWID, CONTENT) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_41(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "XX  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); XX"
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_42(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  values (new.chunk_id, coalesce(new.normalized_content, new.content)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_43(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (NEW.CHUNK_ID, COALESCE(NEW.NORMALIZED_CONTENT, NEW.CONTENT)); "
                "END"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_44(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "XXENDXX"
            )

    def xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_45(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5(  content,  tokenize = 'unicode61')"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "end"
            )

    @_mutmut_mutated(mutants_xǁRagDbMaintenanceServiceǁvacuum__mutmut)
    def vacuum(self) -> None:
        """VACUUM the RAG database to reclaim space."""
        with SQLiteHelper("rag").open() as db:
            db.execute("VACUUM")

    def xǁRagDbMaintenanceServiceǁvacuum__mutmut_orig(self) -> None:
        """VACUUM the RAG database to reclaim space."""
        with SQLiteHelper("rag").open() as db:
            db.execute("VACUUM")

    def xǁRagDbMaintenanceServiceǁvacuum__mutmut_1(self) -> None:
        """VACUUM the RAG database to reclaim space."""
        with SQLiteHelper(None).open() as db:
            db.execute("VACUUM")

    def xǁRagDbMaintenanceServiceǁvacuum__mutmut_2(self) -> None:
        """VACUUM the RAG database to reclaim space."""
        with SQLiteHelper("XXragXX").open() as db:
            db.execute("VACUUM")

    def xǁRagDbMaintenanceServiceǁvacuum__mutmut_3(self) -> None:
        """VACUUM the RAG database to reclaim space."""
        with SQLiteHelper("RAG").open() as db:
            db.execute("VACUUM")

    def xǁRagDbMaintenanceServiceǁvacuum__mutmut_4(self) -> None:
        """VACUUM the RAG database to reclaim space."""
        with SQLiteHelper("rag").open() as db:
            db.execute(None)

    def xǁRagDbMaintenanceServiceǁvacuum__mutmut_5(self) -> None:
        """VACUUM the RAG database to reclaim space."""
        with SQLiteHelper("rag").open() as db:
            db.execute("XXVACUUMXX")

    def xǁRagDbMaintenanceServiceǁvacuum__mutmut_6(self) -> None:
        """VACUUM the RAG database to reclaim space."""
        with SQLiteHelper("rag").open() as db:
            db.execute("vacuum")

mutants_xǁRagDbMaintenanceServiceǁrotate__mutmut['_mutmut_orig'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrotate__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrotate__mutmut['xǁRagDbMaintenanceServiceǁrotate__mutmut_1'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrotate__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrotate__mutmut['xǁRagDbMaintenanceServiceǁrotate__mutmut_2'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrotate__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrotate__mutmut['xǁRagDbMaintenanceServiceǁrotate__mutmut_3'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrotate__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrotate__mutmut['xǁRagDbMaintenanceServiceǁrotate__mutmut_4'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrotate__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrotate__mutmut['xǁRagDbMaintenanceServiceǁrotate__mutmut_5'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrotate__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrotate__mutmut['xǁRagDbMaintenanceServiceǁrotate__mutmut_6'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrotate__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrotate__mutmut['xǁRagDbMaintenanceServiceǁrotate__mutmut_7'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrotate__mutmut_7 # type: ignore # mutmut generated

mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['_mutmut_orig'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_1'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_2'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_3'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_4'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_5'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_6'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_7'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_8'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_9'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_10'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_11'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_12'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_13'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_14'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_15'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_15 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_16'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_16 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_17'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_17 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_18'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_18 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_19'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_19 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_20'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_20 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_21'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_21 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_22'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_22 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_23'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_23 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_24'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_24 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_25'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_25 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_26'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_26 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_27'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_27 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_28'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_28 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_29'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_29 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_30'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_30 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_31'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_31 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_32'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_32 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_33'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_33 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_34'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_34 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_35'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_35 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_36'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_36 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_37'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_37 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_38'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_38 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_39'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_39 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_40'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_40 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_41'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_41 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_42'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_42 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_43'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_43 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_44'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_44 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut['xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_45'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁrebuild_fts__mutmut_45 # type: ignore # mutmut generated

mutants_xǁRagDbMaintenanceServiceǁvacuum__mutmut['_mutmut_orig'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁvacuum__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁvacuum__mutmut['xǁRagDbMaintenanceServiceǁvacuum__mutmut_1'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁvacuum__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁvacuum__mutmut['xǁRagDbMaintenanceServiceǁvacuum__mutmut_2'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁvacuum__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁvacuum__mutmut['xǁRagDbMaintenanceServiceǁvacuum__mutmut_3'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁvacuum__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁvacuum__mutmut['xǁRagDbMaintenanceServiceǁvacuum__mutmut_4'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁvacuum__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁvacuum__mutmut['xǁRagDbMaintenanceServiceǁvacuum__mutmut_5'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁvacuum__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagDbMaintenanceServiceǁvacuum__mutmut['xǁRagDbMaintenanceServiceǁvacuum__mutmut_6'] = RagDbMaintenanceService.xǁRagDbMaintenanceServiceǁvacuum__mutmut_6 # type: ignore # mutmut generated
