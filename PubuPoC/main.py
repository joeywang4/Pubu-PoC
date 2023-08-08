"""The main module"""
from . import DB, RawPages, PageCrawler, Searcher, BookCrawler, Downloader, Book
from .util import Converter, gen_pdf, from_input


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
        self.searcher = Searcher(verbose)
        self.converter = Converter(output + "tmp/", change_decode)

    def get_hints(self, book: Book) -> list[tuple]:
        """
        Use sample pages as hints for search mode.
        Returns [(page number, page id), ...]
        """
        got = self.book_crawler.get(self.book_crawler.url1.format(book.book_id))
        try:
            pages = got.json()["book"]["pages"]
        except KeyError:
            return {}

        output = []
        for page in pages:
            output.append((page["pageNumber"], from_input(page["id"])))
        return sorted(output, key=lambda page: page[0])

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
        urls = [page.to_url(self.database) for page in pages]
        if len(urls) < book.pages:
            lack = book.pages - len(urls)
            if self.verbose:
                print(f"[!] Missing {lack} pages, continue in search mode")
            hints = self.get_hints(book)
            urls = self.searcher.search(hints, book.doc_id, book.pages)
            if urls is None or len(urls) < book.pages:
                print("[!] Search failed")
                return
        elif len(urls) > book.pages:
            if self.verbose:
                print(f"[!] Extra {len(urls) - book.pages} pages in local files.")
            urls = urls[: book.pages]

        # download pages
        if self.verbose:
            print(f"[*] Downloading {len(urls)} pages...")
        self.downloader.download(urls)
        if self.downloader.terminated:
            print("[!] Download page failed")
            return

        # convert images
        if self.verbose:
            print("[*] Converting images...")
        self.converter.convert(book.doc_id)

        # generate PDF
        if self.verbose:
            print("[*] Generating PDF...")
        gen_pdf(self.output + "/tmp", self.output, book.title)
        self.downloader.rmdir()
