"""Count and calculate speed"""
import time


class Counter:
    """Record count and time to calculate speed"""

    def __init__(self) -> None:
        self.count = 0
        self.last_count = 0
        self.last_timestamp = 0
        self.history = []
        self.max_history = 100

    def start(self) -> None:
        """Reset counter"""
        self.count = self.last_count = 0
        self.last_timestamp = time.time()
        self.history = []

    def inc(self) -> None:
        """Increase counter"""
        self.count += 1

    def report(self) -> float:
        """Calculate current speed since last report"""
        count_diff = self.count - self.last_count
        now = time.time()
        time_diff = now - self.last_timestamp
        speed = count_diff / max(time_diff, 0.00001)

        # update last timestamp when older than 5 sec
        if time_diff >= 5 and len(self.history) > 0:
            prev_count, prev_time = self.history.pop(0)
            self.last_count = prev_count
            self.last_timestamp = prev_time

        if len(self.history) < self.max_history:
            self.history.append((self.count, now))

        return speed
