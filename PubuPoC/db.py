"""Manage local books and pages database"""
import os
import sqlite3
from collections import defaultdict
from .page import Page, from_blob, to_blob
from .book import Book


class DB:
    """Database manager"""

    def __init__(self, path: str = "data/pubu.db", readonly: bool = False) -> None:
        """
        Open or create a database
        """
        self.front_id, self.id_front = None, None
        self.ext_id, self.id_ext = None, None

        if os.path.isfile(path):
            if readonly:
                self.conn = sqlite3.connect(
                    f"file:{path}?mode=ro", uri=True, check_same_thread=False
                )
            else:
                self.conn = sqlite3.connect(path, check_same_thread=False)

            self.load_fronts_ext()
            return

        if readonly:
            raise FileNotFoundError(f"The database: {path} does not exist!")

        # create a new database
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.create_tables()
        self.load_fronts_ext()

    def create_tables(self) -> None:
        """
        Create table for a new database
        """

        # create books
        self.conn.execute(
            """CREATE TABLE books(
            id INT PRIMARY KEY, 
            documentId INT,
            title TEXT,
            pages INT,
            author TEXT,
            cover TEXT,
            price INT,
            publisher TEXT,
            type TEXT,
            error INT
        )"""
        )

        # create pages
        self.conn.execute(
            """CREATE TABLE pages(
            documentId INT PRIMARY KEY,
            pagesBlob BLOB NOT NULL
        )"""
        )

        # create file extensions
        self.conn.execute(
            """CREATE TABLE extensions(
            id INT PRIMARY KEY,
            ext TEXT NOT NULL
        )"""
        )
        with self.conn:
            self.conn.execute("INSERT INTO extensions VALUES (1, '.jpg')")

        # create front (text at the beginning of a page url)
        self.conn.execute(
            """CREATE TABLE fronts(
            front TEXT PRIMARY KEY,
            enum INT UNIQUE NOT NULL
        )"""
        )
        fronts = [
            ("duyldfll42se2", 0),
            ("d3lcxj447n2nux", 1),
            ("d24p424bn3x9og", 2),
            ("d3rhh0yz0hi1gj", 3),
        ]
        with self.conn:
            self.conn.executemany("INSERT INTO fronts VALUES(?, ?)", fronts)

        # create states
        self.conn.execute(
            """CREATE TABLE states(
            id INT PRIMARY KEY,
            data INT
        )"""
        )
        with self.conn:
            self.conn.execute("INSERT INTO states VALUES(0, 0)")

    # Books

    def search_book(self, book_id: int) -> Book or None:
        """
        Query a book by its id
        """

        res = self.conn.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        got = res.fetchone()
        return got if got is None else Book.from_tuple(got)

    def get_max_book_id(self) -> int:
        """Query the max book id"""
        res = self.conn.execute("SELECT MAX(id) FROM books WHERE error = 0")
        got = res.fetchone()[0]
        return 0 if got is None else got

    def update_books(self, books: list[Book], extend: bool = True) -> None:
        """
        Insert books into DB.
        If `extend` is True, existing books are extended with unknown
        metadata.
        """
        if extend:
            for book in books:
                existing = self.search_book(book.book_id)
                if existing is None:
                    continue
                book.merge(existing)

        new_books = [book.to_tuple() for book in books]

        with self.conn:
            self.conn.executemany(
                "REPLACE INTO books VALUES(" + ", ".join(["?"] * 10) + ")", new_books
            )

    # Pages

    def get_pages(self, doc_id: int) -> list[Page]:
        """
        Query pages using the doc_id.
        Returns a list of Page objects.
        """
        got = self.conn.execute(
            "SELECT pagesBlob FROM pages WHERE documentId = ?", (doc_id,)
        ).fetchone()

        if got is None:
            return []

        return from_blob(got[0], doc_id)

    def save_pages(self, pages: list[Page]) -> None:
        """
        Save pages into DB and update last page id in states.
        pages must be sorted by page_id.
        """
        docs = defaultdict(list)
        doc_last_page = defaultdict(lambda: 0)
        ori_last_page_id = last_page_id = self.get_last_page_id()

        for page in pages:
            if page.error > 0:
                continue
            assert page.page_id > doc_last_page[page.doc_id]
            assert page.page_id > ori_last_page_id

            doc_last_page[page.doc_id] = page.page_id
            if page.page_id > last_page_id:
                last_page_id = page.page_id
            docs[page.doc_id].append(page)

        to_replace = []
        for doc_id, doc_pages in docs.items():
            existing_pages = self.get_pages(doc_id)
            if len(existing_pages) > 0:
                to_replace.append((doc_id, to_blob(existing_pages + doc_pages)))
            else:
                to_replace.append((doc_id, to_blob(doc_pages)))

        with self.conn:
            self.conn.executemany("REPLACE INTO pages VALUES(?, ?)", to_replace)

        if ori_last_page_id != last_page_id:
            self.set_last_page_id(last_page_id)

    # Other tables

    def load_fronts_ext(self) -> None:
        """
        Construct front/ext <-> id dicts
        """
        if self.front_id is not None:
            return

        self.front_id, self.id_front = {}, {}
        self.ext_id, self.id_ext = {}, {}

        # construct front_id and id_front
        for row in self.conn.execute("SELECT * FROM fronts"):
            self.front_id[row[0]] = row[1]
            self.id_front[row[1]] = row[0]

        # construct ext_id and id_ext
        for row in self.conn.execute("SELECT * FROM extensions"):
            self.ext_id[row[1]] = row[0]
            self.id_ext[row[0]] = row[1]

    def set_last_page_id(self, _id: int) -> None:
        """
        Set last page id in states table
        """
        with self.conn:
            self.conn.execute("UPDATE states SET data = ? WHERE id = 0", (_id,))

    def get_last_page_id(self) -> int:
        """
        Get last page id in states table
        """
        got = self.conn.execute("SELECT data FROM states WHERE id = 0").fetchone()
        return 0 if got is None else got[0]
