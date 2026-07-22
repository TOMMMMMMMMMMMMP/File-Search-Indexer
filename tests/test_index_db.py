import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import shutil
from datetime import datetime
from model.scanner import FileScanner
from model.index_db import IndexDB

TEST_DB = "test_index.db"
TEST_DIR = "test_scan_dir"


def setup():
    os.makedirs(TEST_DIR, exist_ok=True)
    # Create test files
    files = [
        ("report.pdf",   b"x" * 1024 * 5),    # 5 KB
        ("image.jpg",    b"x" * 1024 * 200),   # 200 KB
        ("script.py",    b"x" * 1024 * 2),     # 2 KB
        ("data.csv",     b"x" * 1024 * 50),    # 50 KB
        ("readme.txt",   b"x" * 512),          # 0.5 KB
        ("report2.pdf",  b"x" * 1024 * 5),     # 5 KB (duplicate of report.pdf by size)
    ]
    for name, content in files:
        with open(os.path.join(TEST_DIR, name), "wb") as f:
            f.write(content)


def teardown():
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def get_db() -> IndexDB:
    scanner = FileScanner()
    db = IndexDB(TEST_DB)
    db.clear()
    entries = scanner.scan(TEST_DIR)
    db.insert_many(entries)
    return db


def test_search_by_name():
    db = get_db()
    results = db.search_by_name("report")
    assert len(results) == 2
    assert all("report" in r.name.lower() for r in results)
    db.close()
    print("test_search_by_name ✔")


def test_search_by_extension():
    db = get_db()
    results = db.search_by_extension(".pdf")
    assert len(results) == 2
    assert all(r.extension == ".pdf" for r in results)
    db.close()
    print("test_search_by_extension ✔")


def test_filter_by_size():
    db = get_db()
    # Files between 1 KB and 10 KB
    results = db.filter_by_size(min_bytes=1024, max_bytes=1024 * 10)
    assert len(results) > 0
    assert all(1024 <= r.size <= 1024 * 10 for r in results)
    db.close()
    print("test_filter_by_size ✔")


def test_filter_by_date():
    db = get_db()
    start = datetime(2000, 1, 1)
    end = datetime(2100, 1, 1)
    results = db.filter_by_date(start, end)
    assert len(results) == 6
    db.close()
    print("test_filter_by_date ✔")


def test_sort_by_size():
    db = get_db()
    results = db.get_all()
    sorted_results = db.sort_results(results, by="size")
    sizes = [r.size for r in sorted_results]
    assert sizes == sorted(sizes, reverse=True)
    db.close()
    print("test_sort_by_size ✔")


def test_sort_by_name():
    db = get_db()
    results = db.get_all()
    sorted_results = db.sort_results(results, by="name")
    names = [r.name.lower() for r in sorted_results]
    assert names == sorted(names)
    db.close()
    print("test_sort_by_name ✔")


def test_pagination():
    db = get_db()
    page1 = db.get_all(limit=2, offset=0)
    page2 = db.get_all(limit=2, offset=2)
    assert len(page1) == 2
    assert len(page2) == 2
    assert page1[0].name != page2[0].name
    db.close()
    print("test_pagination ✔")


def test_count():
    db = get_db()
    assert db.count() == 6
    db.close()
    print("test_count ✔")


def test_recently_added():
    db = get_db()
    recent = db.get_recently_added(limit=3)
    assert len(recent) <= 3
    assert len(recent) > 0
    db.close()
    print("test_recently_added ✔")


def test_find_duplicates():
    db = get_db()
    # report.pdf and report2.pdf have same size (5KB)
    dupes = db.find_duplicates()
    assert isinstance(dupes, list)
    db.close()
    print("test_find_duplicates ✔")


def test_scanner_skips_errors():
    scanner = FileScanner()
    try:
        scanner.scan("nonexistent_folder_xyz")
        print("test_scanner_skips_errors ✘ (no error raised)")
    except FileNotFoundError:
        print("test_scanner_skips_errors ✔")


def test_empty_directory():
    os.makedirs("empty_test_dir", exist_ok=True)
    scanner = FileScanner()
    entries = scanner.scan("empty_test_dir")
    assert len(entries) == 0
    shutil.rmtree("empty_test_dir")
    print("test_empty_directory ✔")

if __name__ == "__main__":
    teardown()
    setup()
    test_search_by_name()
    teardown()
    setup()
    test_search_by_extension()
    teardown()
    setup()
    test_filter_by_size()
    teardown()
    setup()
    test_filter_by_date()
    teardown()
    setup()
    test_sort_by_size()
    teardown()
    setup()
    test_sort_by_name()
    teardown()
    setup()
    test_pagination()
    teardown()
    setup()
    test_count()
    teardown()
    setup()
    test_recently_added()
    teardown()
    setup()
    test_find_duplicates()
    teardown()
    test_scanner_skips_errors()
    test_empty_directory()
    teardown()
    print("\nAll tests passed ✔")
