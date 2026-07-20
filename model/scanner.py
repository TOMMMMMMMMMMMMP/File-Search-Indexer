import os
from datetime import datetime
from pathlib import Path
from model.file_entry import FileEntry


class FileScanner:
    """
    Recursively scans a directory and collects file metadata.
    Skips inaccessible files and broken symlinks gracefully.
    """

    def __init__(self):
        self.scanned: list[FileEntry] = []
        self.skipped: int = 0
        self.total: int = 0

    def scan(self, root_path: str) -> list[FileEntry]:
        """
        Recursively scan root_path and return a list of FileEntry objects.
        """
        if not os.path.exists(root_path):
            raise FileNotFoundError(f"Directory not found: {root_path}")
        if not os.path.isdir(root_path):
            raise NotADirectoryError(f"Not a directory: {root_path}")

        self.scanned = []
        self.skipped = 0
        self.total = 0

        for dirpath, _, filenames in os.walk(root_path):
            for filename in filenames:
                self.total += 1
                filepath = os.path.join(dirpath, filename)
                entry = self._get_entry(filepath)
                if entry:
                    self.scanned.append(entry)
                else:
                    self.skipped += 1

        return self.scanned

    def _get_entry(self, filepath: str) -> FileEntry | None:
        """Extract metadata from a file path. Returns None on error."""
        try:
            stat = os.stat(filepath)
            name = os.path.basename(filepath)
            ext = Path(filepath).suffix.lower()
            size = stat.st_size
            date_modified = datetime.fromtimestamp(stat.st_mtime)
            return FileEntry(
                name=name,
                path=filepath,
                extension=ext,
                size=size,
                date_modified=date_modified,
            )
        except (PermissionError, OSError, FileNotFoundError):
            return None
