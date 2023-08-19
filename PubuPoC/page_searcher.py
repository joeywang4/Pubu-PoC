"""Search pages"""
import math
import sys
from enum import Enum
from urllib.parse import urlparse
from requests import Session
from .fetcher import Fetcher
from .util import to_input

SPACES = 150


class State(Enum):
    """State of the searcher"""

    INIT = 1  # searching pages within the range of hint
    LOWER = 2  # searching pages till page 1
    UPPER = 3  # searching pages till the last page
    DONE = 4


class Searcher(Fetcher):
    """Search pages"""

    def __init__(self, verbose: bool = False) -> None:
        super().__init__()
        self.state = State.INIT
        self.curr_id = 0
        self.hints = []  # [(page num, page id), ...]
        self.got = []  # [(page id, url), ...]
        self.lower_found = 0
        self.upper_found = 0
        self.doc_id = 0
        self.total_pages = 0
        self.verbose = verbose
        self.num_threads = 20

    def checkpoint(self, result: list[(int, str)], thread_id: int) -> None:
        """Save result to `got`"""
        if len(result) == 0:
            return

        # record number of found pages
        for page in result:
            if page[0] < self.hints[0][1]:
                self.lower_found += 1
            elif page[0] > self.hints[-1][1]:
                self.upper_found += 1

        if len(self.got) == 0:
            self.got = result
            return

        i = 0
        while (i < len(self.got)) and self.got[i][0] < result[0][0]:
            i += 1
        assert i == len(self.got) or (result[-1][0] < self.got[i][0])
        self.got = self.got[:i] + result + self.got[i:]
        if len(self.got) >= self.total_pages:
            self.terminated = True

    def job_worker(self, job: tuple[int, int], thread_id: int) -> [(int, str)]:
        """Fetch pages"""
        output = []

        with Session() as session:
            for page_id in range(job[0], job[1]):
                if self.terminated:
                    return output
                url = "https://www.pubu.com.tw/api/flex/3.0/page/"
                url += to_input(page_id)
                url += "/1/reader/jpg?productId=1"
                got = self.get(url, session)

                # GET result may be `None` when terminated
                if got is None:
                    return output
                if got.status_code == 200:
                    parsed = urlparse(got.text)
                    path = parsed.path.split("/")[1:]
                    doc_id = int(path[1])
                    if doc_id == self.doc_id:
                        output.append((page_id, got.text))

        return output

    def get_job(self) -> tuple[int, int]:
        """Dispatch jobs to threads"""
        if self.state == State.INIT:
            if self.curr_id > self.hints[-1][1]:
                self.state = State.LOWER
                self.curr_id = self.hints[0][1] - 1
                if self.verbose:
                    msg = f"[*] Switch to LOWER state, searching from {self.curr_id}"
                    print(msg.ljust(SPACES, " "))
            else:
                size = math.ceil(
                    (self.hints[-1][1] - self.hints[0][1]) / self.num_threads
                )
                job = (self.curr_id, min(self.curr_id + size, self.hints[-1][1] + 1))
                self.curr_id = job[1]
                return job

        if self.state == State.LOWER:
            if self.lower_found >= self.hints[0][0] - 1:
                if self.lower_found != self.hints[0][0] - 1:
                    msg = "[!] Found too many lower pages: "
                    msg += f"{self.lower_found} > {self.hints[0][0] - 1}"
                    print(msg.ljust(SPACES, " "))
                self.state = State.UPPER
                self.curr_id = self.hints[-1][1] + 1
                if self.verbose:
                    msg = f"[*] Switch to UPPER state, searching from {self.curr_id}"
                    print(msg.ljust(SPACES, " "))
            else:
                size = 10
                if self.hints[0][0] - 1 > 10 * self.num_threads:
                    size = 50
                job = (self.curr_id - size + 1, self.curr_id + 1)
                self.curr_id = job[0] - 1
                return job

        if self.state == State.UPPER:
            # all uppers are found
            if self.upper_found >= self.total_pages - self.hints[-1][0]:
                if self.upper_found != self.total_pages - self.hints[-1][0]:
                    msg = "[!] Found too many upper pages: "
                    msg += (
                        f"{self.upper_found} > {self.total_pages - self.hints[-1][0]}"
                    )
                    print(msg.ljust(SPACES, " "))
                self.state = State.DONE
                if self.verbose:
                    print("[*] Done searching".ljust(SPACES, " "))
                return None

            job_size = 50
            # switch to bigger job size when upper is not found
            if self.curr_id > (
                self.total_pages - self.hints[-1][0] + self.hints[-1][1]
            ):
                job_size = 200

            job = (self.curr_id, self.curr_id + job_size)
            self.curr_id = job[1]
            return job

        return None

    def status(self):
        progress = f"Searching ID: {self.curr_id}"
        if self.verbose:
            progress += f", {self.state} got: {len(self.got)}"
            progress += f" lower: {self.lower_found} upper: {self.upper_found}"
        progress += f", missing: {self.total_pages - len(self.got)} pages"
        progress += f" ({self.counter.report():.2f} req/s)"
        print("[*] " + progress, end="\r", file=sys.stdout, flush=True)

    def clean_up(self) -> None:
        """Overwrite original clean_up"""
        return

    def search(self, hints: list[(int, int)], doc_id=int, total_pages=int) -> [str]:
        """Search pages using hints"""
        self.state = State.INIT
        self.curr_id = hints[0][1]
        self.hints = hints
        self.got = []
        self.lower_found = self.upper_found = 0
        self.doc_id = doc_id
        self.total_pages = total_pages

        if self.verbose:
            print(f"[*] Begin searching with hints: {hints[0]} to {hints[-1]}")

        # start searching
        self.counter.start()
        self.spawn_threads()
        self.join_threads()
        print(SPACES * " ", end="\r", file=sys.stdout, flush=True)

        urls = [page[1] for page in self.got]
        return urls
