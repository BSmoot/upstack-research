"""
Circuit breaker pattern for API resilience.

Prevents cascade failures by tracking consecutive failures and temporarily blocking
requests when a threshold is exceeded. Automatically attempts recovery after a timeout.
"""

import time
import logging
from enum import Enum
from typing import Optional


class CircuitState(Enum):
    """Circuit breaker states following the circuit breaker pattern."""
    CLOSED = "closed"      # Normal operation, requests allowed
    OPEN = "open"          # Failures exceeded threshold, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and request is blocked."""
    pass


class CircuitBreaker:
    """
    Circuit breaker for protecting against sustained API failures.

    State transitions:
    - CLOSED -> OPEN: When failure_count >= failure_threshold
    - OPEN -> HALF_OPEN: After recovery_timeout seconds
    - HALF_OPEN -> CLOSED: On first successful request
    - HALF_OPEN -> OPEN: On any failed request
    """

    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0
    ):
        """
        Initialize circuit breaker.

        Args:
            service_name: Name of the service being protected (for logging)
            failure_threshold: Number of consecutive failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
        """
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = CircuitState.CLOSED

        self.logger = logging.getLogger('research_orchestrator')

    def record_success(self) -> None:
        """Record successful request. Resets failure count and closes circuit from half-open."""
        was_half_open = self.state == CircuitState.HALF_OPEN

        self.failure_count = 0

        if was_half_open:
            self.state = CircuitState.CLOSED
            self.logger.info(
                f"[CircuitBreaker] {self.service_name}: Circuit closed after successful recovery"
            )

    def record_failure(self) -> None:
        """Record failed request. Opens circuit if threshold reached."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.logger.warning(
                f"[CircuitBreaker] {self.service_name}: Recovery attempt failed, circuit reopened"
            )
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.warning(
                f"[CircuitBreaker] {self.service_name}: Circuit opened after {self.failure_count} consecutive failures"
            )

    def can_execute(self) -> bool:
        """Check if request execution is allowed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.logger.info(
                    f"[CircuitBreaker] {self.service_name}: Circuit half-open, attempting recovery"
                )
                return True
            return False

        return True  # HALF_OPEN state

    def raise_if_open(self) -> None:
        """Raise CircuitBreakerOpenError if circuit is open."""
        if not self.can_execute():
            raise CircuitBreakerOpenError(
                f"Circuit breaker open for {self.service_name}. "
                f"Service unavailable after {self.failure_count} failures. "
                f"Retry after {self.recovery_timeout}s timeout."
            )

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = CircuitState.CLOSED
        self.logger.info(f"[CircuitBreaker] {self.service_name}: Circuit manually reset")
