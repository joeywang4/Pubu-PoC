"""Test database manager"""
import sqlite3
from pathlib import Path
import pytest
from test_book import sample_book, book_eq
from test_page import sample_page, page_eq
from PubuPoC import DB, Book, to_blob


def check_fronts(database: DB):
    """Check `front_id` and `id_front` contain expected data"""
    expected = [
        ("duyldfll42se2", 0),
        ("d3lcxj447n2nux", 1),
        ("d24p424bn3x9og", 2),
        ("d3rhh0yz0hi1gj", 3),
    ]

    for front in expected:
        assert database.front_id[front[0]] == front[1]
        assert database.id_front[front[1]] == front[0]


def check_ext(database: DB):
    """Check `ext_id` and `id_ext` contain expected data"""
    assert database.ext_id[".jpg"] == 1
    assert database.id_ext[1] == ".jpg"


def test_constructor(tmp_path: Path):
    """Test DB constructor"""
    path = tmp_path.as_posix()
    database = DB(path + "/test.database")

    # test tables exist
    tables = database.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    tables = [table[0] for table in tables]
    assert "books" in tables
    assert "pages" in tables
    assert "extensions" in tables
    assert "fronts" in tables
    assert "states" in tables

    # test default data
    extensions = database.conn.execute("SELECT * FROM extensions").fetchall()
    assert extensions[0][0] == 1
    assert extensions[0][1] == ".jpg"

    fronts = database.conn.execute("SELECT * FROM fronts").fetchall()
    fronts_dict = {}
    for front in fronts:
        fronts_dict[front[0]] = front[1]
    assert fronts_dict["duyldfll42se2"] == 0
    assert fronts_dict["d3lcxj447n2nux"] == 1
    assert fronts_dict["d24p424bn3x9og"] == 2
    assert fronts_dict["d3rhh0yz0hi1gj"] == 3

    states = database.conn.execute("SELECT * FROM states").fetchall()
    assert states[0][0] == 0
    assert states[0][1] == 0

    check_fronts(database)
    check_ext(database)

    # test can't create readonly DB
    with pytest.raises(FileNotFoundError):
        DB(path + "/test2.database", True)

    # test load existing DB
    with database.conn:
        database.conn.execute("INSERT INTO states VALUES(1, 123)")
    database.conn.close()

    # new state should exist
    db2 = DB(path + "/test.database")
    got = db2.conn.execute("SELECT * FROM states WHERE id = 1").fetchone()
    assert got[1] == 123
    check_fronts(db2)
    check_ext(db2)

    # readonly DB cannot be updated
    db3 = DB(path + "/test.database", True)
    check_fronts(db3)
    check_ext(db3)
    with pytest.raises(sqlite3.OperationalError):
        with db3.conn:
            db3.conn.execute("INSERT INTO states VALUES(1, 123)")


# books


def test_search_books(tmp_path: Path):
    """Test search books from DB"""
    path = tmp_path.as_posix()
    database = DB(path + "/test.database")

    book = sample_book()
    books = []
    for i in range(5):
        book.book_id = i
        book.doc_id = 100 - i
        books.append(book.to_tuple())

    with database.conn:
        database.conn.executemany(
            "INSERT INTO books VALUES(" + ", ".join(["?"] * 10) + ")", books
        )

    # search_book should find the same book
    new_book = database.search_book(2)
    book = Book.from_tuple(books[2])
    book_eq(book, new_book)

    # should return None for non-exist book
    assert database.search_book(1234) is None


def test_get_max_book_id(tmp_path: Path):
    """Test get max book id from DB"""
    path = tmp_path.as_posix()
    database = DB(path + "/test.database")

    # should return 0 with empty data
    assert database.get_max_book_id() == 0

    # should return max book_id
    book = sample_book()
    book.book_id = 400
    database.update_books([book])
    book.book_id = 700
    database.update_books([book])
    book.book_id = 600
    database.update_books([book])
    assert database.get_max_book_id() == 700

    # should ignore error books
    book.book_id = 9999
    book.error = 404
    database.update_books([book])
    assert database.get_max_book_id() == 700


def test_update_books(tmp_path: Path):
    """Test update books to DB"""
    path = tmp_path.as_posix()
    database = DB(path + "/test.database")

    book1 = sample_book()
    book2 = sample_book()
    book2.book_id = book1.book_id + 1
    book2.title = ""
    book3 = sample_book()
    book3.book_id = book2.book_id + 1

    # books should be added
    database.update_books([book1, book2], extend=False)
    new_book1 = database.search_book(book1.book_id)
    book_eq(book1, new_book1)
    new_book2 = database.search_book(book2.book_id)
    book_eq(book2, new_book2)

    # books should be extended
    book2.title = "hello"
    book2.cover = ""
    database.update_books([book2, book3])
    book_eq(book2, database.search_book(book2.book_id))
    book_eq(book3, database.search_book(book3.book_id))


# states


def test_last_page_id(tmp_path: Path):
    """Test get and set last page id from DB"""
    path = tmp_path.as_posix()
    database = DB(path + "/test.database")

    assert database.get_last_page_id() == 0

    database.set_last_page_id(321)

    assert database.get_last_page_id() == 321


# pages


def test_get_pages(tmp_path: Path):
    """Test get pages from DB"""
    path = tmp_path.as_posix()
    database = DB(path + "/test.database")

    pages = []
    for i in range(10):
        page = sample_page()
        # page_id is neglected
        page.page_id = 0
        page.filename = f"{i}abc{i}2"
        pages.append(page)

    with database.conn:
        database.conn.execute(
            "INSERT INTO pages VALUES(?, ?)", (pages[0].doc_id, to_blob(pages))
        )

    # get_pages should get the same pages
    got = database.get_pages(pages[0].doc_id)
    assert len(got) == len(pages)
    for i in range(len(got)):
        page_eq(got[i], pages[i])

    # get_pages should return an empty list for non-exist doc
    got = database.get_pages(9876)
    assert isinstance(got, list)
    assert len(got) == 0


def test_save_pages(tmp_path: Path):
    """Test save pages from DB"""
    path = tmp_path.as_posix()
    database = DB(path + "/test.database")

    doc1 = []
    for i in range(10):
        page = sample_page()
        page.page_id = i + 1
        page.filename = f"{i}abc{i}2"
        doc1.append(page)

    doc2 = []
    for i in range(10):
        page = sample_page()
        page.page_id = 10 + i
        page.doc_id = 222
        page.filename = f"aaaaa{i}"
        doc2.append(page)

    doc2[5].error = 404

    # check pages are saved correctly
    database.save_pages(doc1 + doc2)
    new_doc1 = database.get_pages(doc1[0].doc_id)
    assert len(new_doc1) == len(doc1)
    for i in range(len(doc1)):
        doc1[i].page_id = 0
        page_eq(doc1[i], new_doc1[i])

    # check last_page_id is updated
    assert database.get_last_page_id() == doc2[-1].page_id

    # make sure error page is not added
    got = database.get_pages(222)
    assert len(got) == 9
    for i in range(9):
        doc2_page = doc2[i if i < 5 else i + 1]
        doc2_page.page_id = 0
        page_eq(doc2_page, got[i])

    add_doc1 = []
    for i in range(10):
        page = sample_page()
        page.page_id = 20 + i
        page.filename = f"bbbbb{i}"
        add_doc1.append(page)

    database.save_pages(add_doc1)
    new_doc1 = doc1 + add_doc1
    got = database.get_pages(new_doc1[0].doc_id)
    # check pages are extended
    assert len(new_doc1) == len(got)
    for i in range(len(got)):
        doc1_page = new_doc1[i]
        doc1_page.page_id = 0
        page_eq(doc1_page, got[i])

    page1 = sample_page()
    page2 = sample_page()
    page1.page_id = 2000
    page2.page_id = 1000
    # check pages should be sorted
    with pytest.raises(AssertionError):
        database.save_pages([page1, page2])

    database.save_pages([page2, page1])
    page1.page_id = 1998
    page2.page_id = 1999
    # check page_id should larger than last_page_id
    with pytest.raises(AssertionError):
        database.save_pages([page1, page2])
