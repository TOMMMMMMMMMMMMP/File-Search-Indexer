from model.scanner import FileScanner
from model.index_db import IndexDB
from model.file_entry import FileEntry
from datetime import datetime

DB_FILE = "index.db"


class AppController:
    """Bridges the GUI and the Model (FileScanner + IndexDB)."""

    def __init__(self):
        self.scanner = FileScanner()
        self.db = IndexDB(DB_FILE)
        self.current_results: list[FileEntry] = []

    def scan(self, path: str) -> tuple[int, int, str | None]:
        """
        Scan a directory and index all files.
        Returns (total_scanned, total_indexed, error_message).
        """
        try:
            entries = self.scanner.scan(path)
            self.db.clear()
            inserted = self.db.insert_many(entries)
            return self.scanner.total, inserted, None
        except FileNotFoundError as e:
            return 0, 0, str(e)
        except NotADirectoryError as e:
            return 0, 0, str(e)
        except Exception as e:
            return 0, 0, f"Unexpected error: {e}"

    def search(self, keyword: str = "", extension: str = "",
               min_mb: float = 0, max_mb: float = 999999,
               sort_by: str = "name",
               limit: int = 200, offset: int = 0) -> list[FileEntry]:
        """Run a search with optional filters and sorting."""
        if keyword:
            results = self.db.search_by_name(keyword, limit=limit, offset=offset)
        elif extension:
            results = self.db.search_by_extension(extension, limit=limit, offset=offset)
        else:
            results = self.db.get_all(limit=limit, offset=offset)

        # Size filter
        min_bytes = int(min_mb * 1024 * 1024)
        max_bytes = int(max_mb * 1024 * 1024) if max_mb < 999999 else 999_999_999_999
        if min_mb > 0 or max_mb < 999999:
            results = [r for r in results if min_bytes <= r.size <= max_bytes]

        # Sort
        results = self.db.sort_results(results, by=sort_by)
        self.current_results = results
        return results

    def get_recently_added(self, limit: int = 50) -> list[FileEntry]:
        """Return recently indexed files."""
        return self.db.get_recently_added(limit=limit)

    def get_duplicates(self) -> list[list[FileEntry]]:
        """Return groups of duplicate files."""
        return self.db.find_duplicates()

    def get_count(self) -> int:
        """Return total indexed file count."""
        return self.db.count()

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Return human-readable file size."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024*1024):.2f} MB"
        return f"{size_bytes / (1024*1024*1024):.2f} GB"
