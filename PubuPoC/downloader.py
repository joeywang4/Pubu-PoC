"""Book downloader"""
import math
import os
from shutil import rmtree
from requests import Session
from .fetcher import Fetcher
from .util import Mode


class Downloader(Fetcher):
    """Book downloader"""

    def __init__(self, path: str = "output/tmp/") -> None:
        super().__init__()
        self.path = path
        self.ignored_errors = []
        self.urls = []
        self.num_threads = 25

    def clean_up(self) -> None:
        """Delete tmp files if terminated"""
        if self.terminated:
            self.rmdir()
        return super().clean_up()

    def job_worker(self, job: tuple[int, int], thread_id: int) -> None:
        """Fetch images of pages"""
        with Session() as session:
            for i in range(job[0], job[1]):
                if self.terminated:
                    return
                self.progress[thread_id] = i
                url = self.urls[i]
                got = self.get(url, session)

                if got.status_code != 200:
                    self.terminated = True
                    return

                with open(f"{self.path}/{str(i + 1).rjust(4, '0')}.jpg", "wb") as ofile:
                    for chunk in got.iter_content(chunk_size=8192):
                        ofile.write(chunk)

    def rmdir(self):
        """Remove output dir"""
        try:
            rmtree(self.path)
        except FileNotFoundError:
            pass

    def mkdir(self):
        """Create output dir"""
        os.makedirs(self.path, exist_ok=True)

    def download(self, urls: list):
        """Clean up output dir and download files"""
        self.rmdir()
        self.mkdir()
        self.urls = urls
        self.workload.job_size = math.ceil(len(urls) / self.num_threads)
        self.start(Mode.FIXED, len(urls))
