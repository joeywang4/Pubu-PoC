"""The main module"""
from . import DB, RawPages, PageCrawler, BookCrawler, Downloader
from .util import Converter, gen_pdf


class Main:
    """The main class"""

    def __init__(
        self,
        database: str = "data/pubu.db",
        raw_pages: str = "data/",
        output: str = "output/",
        verbose: bool = False,
        change_decode: bool = False,
    ) -> None:
        self.database = DB(database)
        self.raw_pages = RawPages(raw_pages)
        self.output = output
        self.verbose = verbose

        # sub-modules
        self.page_crawler = PageCrawler(self.database, self.raw_pages)
        self.book_crawler = BookCrawler(self.database)
        self.downloader = Downloader(output + "tmp/")
        self.converter = Converter(output + "tmp/", change_decode)

    def download(self, book_id: int) -> None:
        """Download a book"""
        if self.verbose:
            print(f"[*] Downloading book with book_id {book_id}")
        book = self.database.search_book(book_id)
        if book is None or book.error > 0:
            if self.verbose:
                cause = "not found in database" if book is None else "invalid"
                print(f"[!] Book is {cause}. Fetching online information...")

            book = self.book_crawler.job_worker([book_id, book_id + 1], 0)[0]
            if book.error > 0 or book.doc_id == 0 or book.pages == 0:
                print(f"[!] Online info is invalid - book info: {book.to_tuple()}")
                return

        if self.verbose:
            print(f"[*] Found book: {book.to_tuple()}")
            print("[*] Getting pages...")

        pages = self.database.get_pages(book.doc_id)
        if len(pages) < book.pages:
            lack = book.pages - len(pages)
            if self.verbose:
                print(f"[!] Missing {lack} pages, continue in search mode")
            raise NotImplementedError("Search mode is not implemented")
        elif len(pages) > book.pages:
            if self.verbose:
                print(f"[!] Extra {len(pages) - book.pages} pages in local files.")
            pages = pages[: book.pages]

        # download pages
        if self.verbose:
            print(f"[*] Downloading {len(pages)} pages...")
        self.downloader.download([page.to_url(self.database) for page in pages])

        # convert images
        if self.verbose:
            print("[*] Converting images...")
        self.converter.convert(book.doc_id)

        # generate PDF
        if self.verbose:
            print("[*] Generating PDF...")
        gen_pdf(self.output + "/tmp", self.output, book.title)
        self.downloader.rmdir()
