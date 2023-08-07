"""Manage workload"""
from enum import Enum


class Mode(Enum):
    """Crawler execution modes"""

    FIXED = 1
    UPDATE = 2
    SEARCH = 3


class Workload:
    """Generate jobs for threads"""

    def __init__(self) -> None:
        self.job_size = 50
        self.mode = Mode.UPDATE
        # next id to fetch
        self.next_id = -1
        self.end_id = -1
        # state in update mode
        self.last_success_id = -1
        self.max_error = 100000

    def clean_up(self) -> None:
        """Reset states"""
        self.next_id = self.end_id = self.last_success_id = -1

    def get_job(self) -> tuple[int, int] or None:
        """Get next job for a worker"""
        if self.mode == Mode.FIXED:
            assert self.end_id != -1
            # get next job until `end_id`
            if self.next_id >= self.end_id:
                return None
            next_job = (self.next_id, min(self.next_id + self.job_size, self.end_id))
            self.next_id = next_job[1]
            return next_job

        if self.mode == Mode.UPDATE:
            if self.next_id - self.last_success_id > self.max_error:
                return None
            self.next_id += self.job_size
            return (self.next_id - self.job_size, self.next_id)

        raise NotImplementedError(f"[!] Mode {self.mode} is not supported")
