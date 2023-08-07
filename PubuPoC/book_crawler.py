"""Crawl books"""
import re
from requests import Session, Response
from bs4 import BeautifulSoup
from .book import Book
from .fetcher import Fetcher
from .db import DB


def remove_space(_str):
    """Recursively remove extra spaces"""
    return re.sub(r"\s{2,}", " ", _str)


def parse_book(res1: Response, res2: Response, book_id: int) -> Book or None:
    """Generate a book from fetch result"""
    # GET result may be `None` when terminated
    if res1 is None or res2 is None:
        return None

    book = Book()
    book.book_id = book_id
    # res1
    if res1.status_code != 200:
        book.error = res1.status_code
    else:
        got = res1.json()
        book.doc_id = got["book"]["documentId"]
        book.pages = got["book"]["totalPage"]
        book.title = got["book"]["title"]

    # res2
    soup = BeautifulSoup(res2.text, "html.parser")
    tags = soup.find("section", "info-block")
    if tags is None:
        return book

    # Get author and publisher
    author = tags.find("div", "info-name").find("div", "d-flex")
    author = author.findAll("p")
    author_0 = author[0].find("a")
    if author_0 is not None:
        book.author = remove_space(author_0.text)
    author_1 = author[1].find("a")
    if author_1 is not None:
        book.publisher = remove_space(author_1.text)

    # Get price
    tags = tags.findAll("div", "price")
    tags = [int(t.text[3:]) for t in tags]
    book.price = min(tags)

    # Get breadcrumb
    breadcrumbs = soup.find("ol", "breadcrumb").findAll("a")[1:]
    if len(breadcrumbs) > 0:
        book.type = "/".join([t.text for t in breadcrumbs])

    # Get book cover
    cover = soup.find("div", "cover").find("img")
    if cover is not None:
        book.cover = cover["data-src"]

    return book


class BookCrawler(Fetcher):
    """Crawl books"""

    def __init__(self, database: DB) -> None:
        super().__init__()
        self.database = database
        self.url1 = (
            "https://www.pubu.com.tw/api/flex/3.0/book/{}?referralType=ORDER_ITEM"
        )
        self.url2 = "https://www.pubu.com.tw/ebook/{}"
        self.workload.job_size = 20
        self.workload.max_error = 1000

    def get_last_id(self) -> int:
        """Get last success book id in DB"""
        return self.database.get_max_book_id()

    def checkpoint(self, result: list[Book], thread_id: int) -> None:
        """Save books into DB"""
        for book in result:
            if book.error == 0 and book.book_id > self.workload.last_success_id:
                self.workload.last_success_id = book.book_id
        self.database.update_books(result)

    def job_worker(self, job: tuple[int, int], thread_id: int) -> list[Book]:
        """Fetch books"""
        output = []

        with Session() as session:
            for book_id in range(job[0], job[1]):
                if self.terminated:
                    return output
                self.progress[thread_id] = book_id
                url1 = self.url1.format(book_id)
                url2 = self.url2.format(book_id)
                got1 = self.get(url1, session)
                got2 = self.get(url2, session)

                book = parse_book(got1, got2, book_id)
                if book is None:
                    return output
                output.append(book)

        return output
