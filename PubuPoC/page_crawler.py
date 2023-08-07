"""Crawl pages"""
import random
from requests import Session
from .fetcher import Fetcher
from .page import Page, RawPages
from .db import DB


def to_input(page_id: int) -> str:
    """Tanslate page_id for API query"""
    if page_id < 10000:
        return str(page_id)

    digit_dict = {
        "1": "1",
        "4": "2",
        "0": "3",
        "8": "4",
        "9": "5",
        "2": "6",
        "5": "7",
        "7": "8",
        "3": "9",
        "6": "0",
    }
    str_id = str(page_id * 17 + 5)

    out = ""
    for char in str_id:
        if char in digit_dict:
            out += digit_dict[char]
        else:
            out += char
    out = out[2:] + out[:2]
    out = "".join([str(random.randint(0, 9)) + s for s in out])
    return out


class PageCrawler(Fetcher):
    """Crawl pages"""

    def __init__(self, database: DB, raw_pages: RawPages) -> None:
        super().__init__()
        self.url = (
            "https://www.pubu.com.tw/api/flex/3.0/page/{}/1/reader/jpg?productId=1"
        )
        self.database = database
        self.raw_pages = raw_pages
        self.num_threads = 20
        self.workload.job_size = 200

    def get_last_id(self) -> int:
        """Get last avail page id in DB"""
        return self.database.get_last_page_id()

    def clean_up(self) -> None:
        """Close raw files and sync to DB when not terminated"""
        if not self.terminated:
            self.raw_pages.sync_db(self.database)

        self.raw_pages.close()
        return super().clean_up()

    def checkpoint(self, result: list[Page], thread_id: int) -> None:
        """Save pages into raw page records"""
        for page in result:
            self.raw_pages.write_page(page)
            if page.error == 0 and page.page_id > self.workload.last_success_id:
                self.workload.last_success_id = page.page_id
        self.raw_pages.sync_db(self.database)

    def job_worker(self, job: tuple[int, int], thread_id: int) -> list[Page]:
        """Fetch pages"""
        output = []

        with Session() as session:
            for page_id in range(job[0], job[1]):
                if self.terminated:
                    return output
                self.progress[thread_id] = page_id
                url = self.url.format(to_input(page_id))
                got = self.get(url, session)

                # GET result may be `None` when terminated
                if got is None:
                    return output
                if got.status_code == 200:
                    page = Page.from_url(got.text, self.database, page_id)
                else:
                    page = Page(page_id, error=got.status_code)
                output.append(page)

        return output
