"""Custom thread and HTTP fetcher"""
import random
import sys
import threading
import time
import requests
from .util import Counter, Workload, Mode

SPACES = 150


class Worker:
    """
    Use python threads to work on jobs.
    Threads will call `get_job` to get a new job to work on. After a job is
    done, `checkpoint` will work exclusively on the result returned by
    `job_worker`. When all jobs are done or terminated by the user, `clean_up`
    is called to clean up the resources.
    """

    def __init__(self) -> None:
        # Threading states/parameters
        self.num_threads = 10
        # delay when spawning each threads
        self.thread_delay = 0.1
        self.jobs_lock = threading.Lock()
        self.checkpoint_lock = threading.Lock()
        self.jobs = []
        self.threads = []
        self.terminated = False

    def status(self):
        """Print current status"""
        raise NotImplementedError

    def checkpoint(self, result, thread_id: int):
        """Handle output from a job worker"""
        raise NotImplementedError

    def job_worker(self, job, thread_id: int):
        """
        Work on a job.
        This function should stop a job immediately when
        `self.terminated` is set to True.
        """
        raise NotImplementedError

    def get_job(self):
        """Get a new job"""
        return None if len(self.jobs) == 0 else self.jobs.pop(0)

    def thread_worker(self, thread_id: int):
        """A thread fetches a job repeatedly until there is no job"""
        while True:
            # get a new job
            with self.jobs_lock:
                job = self.get_job()
            if job is None or self.terminated:
                return

            got = self.job_worker(job, thread_id)
            if self.terminated:
                return

            # run checkpoint to handle job_worker's output
            with self.checkpoint_lock:
                self.checkpoint(got, thread_id)

    def terminate_threads(self) -> None:
        """Stop threads"""
        if self.terminated:
            return
        self.terminated = True
        print(
            "[!] Received keyboard interrupt, terminating threads...".ljust(SPACES, " ")
        )

    def spawn_threads(self) -> None:
        """Create threads"""
        self.terminated = False
        try:
            for i in range(self.num_threads):
                thread = threading.Thread(
                    target=self.thread_worker, args=[i], daemon=True
                )
                self.threads.append(thread)
                thread.start()
                time.sleep(self.thread_delay)
        except KeyboardInterrupt:
            self.terminate_threads()

    def clean_up(self) -> None:
        """Clean up existing jobs"""
        self.threads = []

    def join_threads(self) -> None:
        """Wait threads to finish execution"""
        try:
            for thread in self.threads:
                while thread.is_alive():
                    self.status()
                    time.sleep(0.1)
        except KeyboardInterrupt:
            self.terminate_threads()

        if self.terminated:
            # Gracefully wait for threads to terminate
            try:
                for thread in self.threads:
                    thread.join()
            except KeyboardInterrupt:
                pass

        self.clean_up()


class Fetcher(Worker):
    """Use worker to send GET requests"""

    def __init__(self) -> None:
        super().__init__()

        self.retry_limit = 10
        self.retry_delay = (0.01, 0.3)
        # do not output error meesage for these error codes
        self.ignored_errors = [403, 404, 410]
        self.log = ""

        # stats
        self.workload = Workload()
        self.counter = Counter()
        self.progress = []

    def get(
        self, url: str, session=requests, headers: dict = {}
    ) -> requests.Response or None:
        """Send a GET request"""
        if self.terminated:
            return None

        for _ in range(self.retry_limit):
            res = session.get(url, headers=headers)
            if res.status_code == 200:
                break

            # error occurs
            if res.status_code not in self.ignored_errors:
                error_msg = f"[!] GET {url} failed, status code: {res.status_code}"
                if self.log == "":
                    print(error_msg.ljust(SPACES, " "))
                else:
                    with open(self.log, "a", encoding="utf-8") as ofile:
                        ofile.write(error_msg + "\n")

            # retry when server errors
            if res.status_code > 500 and not self.terminated:
                time.sleep(0.1 * random.randint(1, 10))
                latency = self.retry_delay[0]
                delay_diff = self.retry_delay[1] - self.retry_delay[0]
                latency += random.random() * delay_diff
                time.sleep(latency)
                continue

            # stop retry loop for 200 and 4XX responses
            break

        self.counter.inc()
        return res

    def checkpoint(self, result, thread_id: int):
        """Handle output from a job worker"""
        return

    def get_job(self) -> tuple[int, int] or None:
        """Get a job from workload"""
        return self.workload.get_job()

    def get_last_id(self) -> int:
        """Get the last avail ID from DB"""
        return -1

    def clean_up(self) -> None:
        """Print stats and reset states"""
        if self.workload.mode == Mode.UPDATE:
            msg = f"[*] Fetched {self.counter.count} requests."
            msg += f" Last id is now {self.get_last_id()}."
            print(msg.ljust(SPACES, " "))

        return super().clean_up()

    def status(self):
        """Report the current crawling status"""
        if self.workload.mode == Mode.FIXED:
            progress = f"{self.counter.count}/{self.workload.end_id}"
        else:
            # for Mode.UPDATE
            if self.num_threads <= 8:
                progress = ", ".join(
                    [f"T{i + 1}-{self.progress[i]}" for i in range(self.num_threads)]
                )
            else:
                progress = f"ID - {min(self.progress)}"
        progress += " (" + f"{self.counter.report():.2f}" + " req/s)"
        print("[*] Crawling: " + progress, end="\r", file=sys.stdout, flush=True)

    def start(self, mode: Mode = Mode.UPDATE, end_id: int = -1) -> None:
        """
        Init states and start crawling
        """
        self.progress = [0 for _ in range(self.num_threads)]
        self.workload.next_id = self.get_last_id() + 1
        self.workload.last_success_id = self.workload.next_id - 1
        self.workload.mode = mode
        if mode == Mode.FIXED:
            assert end_id > self.workload.next_id
            self.workload.end_id = end_id

        if mode == Mode.UPDATE:
            print(f"[*] Start fetching from ID: {self.workload.next_id}")
        self.counter.start()
        self.spawn_threads()
        self.join_threads()
        print(SPACES * " ", end="\r", file=sys.stdout, flush=True)
