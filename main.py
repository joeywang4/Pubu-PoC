"""Pubu PoC main file"""
import argparse
from PubuPoC import Main


def execute(args):
    """Execute using args"""
    main = Main(
        args.database, args.raw_pages, args.output, args.verbose, args.change_decode
    )

    if args.threads is not None:
        # set number of threads to fetchers
        main.page_crawler.num_threads = args.threads
        main.book_crawler.num_threads = args.threads
        main.downloader.num_threads = args.threads
        main.searcher = args.threads

    if args.update is not None:
        if args.update in ["all", "pages"]:
            main.page_crawler.start()

        if args.update in ["all", "books"]:
            main.book_crawler.start()

    for book in args.books:
        main.download(book)


if __name__ == "__main__":
    # handle cmd arguments
    parser = argparse.ArgumentParser(
        description="Pubu PoC: download books from pubu.com.tw"
    )
    parser.add_argument(
        "books", metavar="Book ID", type=int, nargs="*", help="A book's ID to download"
    )
    parser.add_argument(
        "-u",
        "--update",
        nargs="?",
        const="all",
        choices=["all", "pages", "books"],
        help="Update local books/pages database",
    )
    parser.add_argument("-t", "--threads", type=int, help="Number of threads")
    parser.add_argument(
        "--database", default="data/pubu.db", help="Path to local database file"
    )
    parser.add_argument(
        "--raw-pages", default="data/", help="Path to raw pages records"
    )
    parser.add_argument("-o", "--output", default="output/", help="Output folder path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "-c", "--change-decode", action="store_true", help="Change decode method"
    )

    _args = parser.parse_args()
    execute(_args)
