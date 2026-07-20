import sqlite3
import os
from datetime import datetime
from model.file_entry import FileEntry

DB_FILE = "index.db"


class IndexDB:
    """
    Handles all SQLite operations for the file index.
    Stores file metadata and provides search, filter, and sort methods.
    """

    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self._init_table()

    def _init_table(self) -> None:
        """Create the files table if it doesn't exist."""
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                path          TEXT NOT NULL UNIQUE,
                extension     TEXT,
                size          INTEGER,
                date_modified TEXT,
                indexed_at    TEXT DEFAULT (datetime('now'))
            )
        """)
        self.connection.commit()

    def insert_many(self, entries: list[FileEntry]) -> int:
        """
        Insert a list of FileEntry objects into the index.
        Skips duplicates (same path). Returns number of inserted rows.
        """
        inserted = 0
        for entry in entries:
            try:
                self.connection.execute("""
                    INSERT OR IGNORE INTO files (name, path, extension, size, date_modified)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    entry.name,
                    entry.path,
                    entry.extension,
                    entry.size,
                    entry.date_modified.isoformat(),
                ))
                inserted += 1
            except sqlite3.Error:
                pass
        self.connection.commit()
        return inserted

    def clear(self) -> None:
        """Delete all records from the index."""
        self.connection.execute("DELETE FROM files")
        self.connection.commit()

    def count(self) -> int:
        """Return total number of indexed files."""
        return self.connection.execute("SELECT COUNT(*) FROM files").fetchone()[0]

    def get_all(self, limit: int = 100, offset: int = 0) -> list[FileEntry]:
        """Return all files with pagination."""
        rows = self.connection.execute(
            "SELECT * FROM files ORDER BY name LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def search_by_name(self, keyword: str, limit: int = 100, offset: int = 0) -> list[FileEntry]:
        """Search files by name keyword (case-insensitive)."""
        rows = self.connection.execute(
            "SELECT * FROM files WHERE LOWER(name) LIKE ? ORDER BY name LIMIT ? OFFSET ?",
            (f"%{keyword.lower()}%", limit, offset)
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def search_by_extension(self, ext: str, limit: int = 100, offset: int = 0) -> list[FileEntry]:
        """Search files by extension (e.g. '.pdf')."""
        if not ext.startswith("."):
            ext = "." + ext
        rows = self.connection.execute(
            "SELECT * FROM files WHERE LOWER(extension) = ? ORDER BY name LIMIT ? OFFSET ?",
            (ext.lower(), limit, offset)
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def filter_by_size(self, min_bytes: int = 0, max_bytes: int = 999_999_999_999) -> list[FileEntry]:
        """Filter files by size range in bytes."""
        rows = self.connection.execute(
            "SELECT * FROM files WHERE size BETWEEN ? AND ? ORDER BY size DESC",
            (min_bytes, max_bytes)
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def filter_by_date(self, start: datetime, end: datetime) -> list[FileEntry]:
        """Filter files modified between start and end dates."""
        rows = self.connection.execute(
            "SELECT * FROM files WHERE date_modified BETWEEN ? AND ? ORDER BY date_modified DESC",
            (start.isoformat(), end.isoformat())
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def sort_results(self, results: list[FileEntry], by: str = "name") -> list[FileEntry]:
        """Sort a list of FileEntry by 'name', 'size', or 'date'."""
        if by == "size":
            return sorted(results, key=lambda f: f.size, reverse=True)
        elif by == "date":
            return sorted(results, key=lambda f: f.date_modified, reverse=True)
        return sorted(results, key=lambda f: f.name.lower())

    def get_recently_added(self, limit: int = 20) -> list[FileEntry]:
        """Return the most recently indexed files."""
        rows = self.connection.execute(
            "SELECT * FROM files ORDER BY indexed_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def find_duplicates(self) -> list[list[FileEntry]]:
        """
        Find files with the same name and size.
        Returns a list of groups, each group being a list of duplicate FileEntry.
        """
        rows = self.connection.execute("""
            SELECT name, size, COUNT(*) as cnt
            FROM files
            WHERE size > 0
            GROUP BY name, size
            HAVING cnt > 1
        """).fetchall()

        duplicates = []
        for row in rows:
            matches = self.connection.execute(
                "SELECT * FROM files WHERE name = ? AND size = ?",
                (row["name"], row["size"])
            ).fetchall()
            duplicates.append([self._row_to_entry(r) for r in matches])
        return duplicates

    def _row_to_entry(self, row) -> FileEntry:
        """Convert a SQLite row to a FileEntry object."""
        return FileEntry(
            name=row["name"],
            path=row["path"],
            extension=row["extension"] or "",
            size=row["size"] or 0,
            date_modified=datetime.fromisoformat(row["date_modified"]),
        )

    def close(self) -> None:
        """Close the database connection."""
        self.connection.close()
