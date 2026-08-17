from __future__ import annotations

import os
import logging
import threading
import time
from typing import Optional


class CircuitBreaker:
    """Prevents hammering a down site, with error-type awareness.

    States:
      closed   — normal operation, requests allowed
      open     — N consecutive failures tripped; requests blocked for cooldown
      half-open — cooldown expired; one probe request allowed

    Error types (configurable via env vars):
      - block:   503/CAPTCHA/429 — short threshold, long cooldown
      - timeout: connection timeout — medium threshold
      - generic:  all other failures — default threshold/cooldown

    Thread-safe via _lock. Use allow_request() before each call,
    record_failure() / record_success() after.
    """

    # Per-error-type thresholds/cooldowns (overridable via env)
    _DEFAULT_CONFIG = {
        "block": {
            "threshold": int(os.environ.get("CB_BLOCK_THRESHOLD", "5")),
            "cooldown": int(os.environ.get("CB_BLOCK_COOLDOWN", "900")),
        },
        "timeout": {
            "threshold": int(os.environ.get("CB_TIMEOUT_THRESHOLD", "10")),
            "cooldown": int(os.environ.get("CB_TIMEOUT_COOLDOWN", "300")),
        },
    }

    def __init__(self, threshold: int = 10, cooldown: float = 900.0,
                 logger: Optional[logging.Logger] = None):
        self._lock = threading.Lock()
        self._failures: dict[str, int] = {"block": 0, "timeout": 0, "generic": 0}
        self._open_until: float = 0.0
        self._logger = logger or logging.getLogger("circuit_breaker")
        self._state = "closed"
        self._config = {
            "block": self._DEFAULT_CONFIG["block"].copy(),
            "timeout": self._DEFAULT_CONFIG["timeout"].copy(),
            "generic": {"threshold": threshold, "cooldown": cooldown},
        }

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    @property
    def consecutive_failures(self) -> int:
        with self._lock:
            return sum(self._failures.values())

    def allow_request(self) -> bool:
        with self._lock:
            if self._state == "closed":
                return True
            if self._state == "open":
                if time.monotonic() >= self._open_until:
                    self._state = "half-open"
                    self._logger.info("Circuit breaker → half-open (cooldown expired)")
                    return True
                return False
            return True

    def record_failure(self, error_type: str = "generic"):
        with self._lock:
            cfg = self._config.get(error_type, self._config["generic"])
            self._failures[error_type] = self._failures.get(error_type, 0) + 1
            total = sum(self._failures.values())
            if total >= cfg["threshold"]:
                was_open = self._state == "open"
                self._state = "open"
                self._open_until = time.monotonic() + cfg["cooldown"]
                if not was_open:
                    self._logger.warning(
                        "Circuit breaker → OPEN after %d failures (type=%s, cooldown=%.0fs)",
                        total, error_type, cfg["cooldown"],
                    )

    def record_success(self):
        with self._lock:
            if self._state == "half-open":
                self._logger.info("Circuit breaker → closed (probe succeeded)")
            self._state = "closed"
            self._failures = {"block": 0, "timeout": 0, "generic": 0}
            self._open_until = 0.0

    def wait_until_allowed(self, poll: float = 5.0, stop_event: Optional[threading.Event] = None) -> bool:
        while not self.allow_request():
            remaining = max(0, self._open_until - time.monotonic())
            self._logger.info("Circuit breaker open — waiting %.0fs more", remaining)
            gap = min(poll, remaining) if remaining > 0 else poll
            if stop_event:
                if stop_event.wait(gap):
                    return False
            else:
                time.sleep(gap)
        return True

    def reset(self):
        with self._lock:
            self._state = "closed"
            self._failures = {"block": 0, "timeout": 0, "generic": 0}
            self._open_until = 0.0
