from dataclasses import dataclass
from datetime import datetime


@dataclass
class FileEntry:
    """Represents a single indexed file with its metadata."""
    name: str
    path: str
    extension: str
    size: int           # in bytes
    date_modified: datetime

    def size_mb(self) -> float:
        """Return file size in megabytes."""
        return round(self.size / (1024 * 1024), 3)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "extension": self.extension,
            "size": self.size,
            "date_modified": self.date_modified.isoformat(),
        }
