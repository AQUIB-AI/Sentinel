
"""
Sentinel - Self-Healing Retry Engine

Provides bounded retries with exponential backoff
and structured logging.
"""

import logging
import time

from typing import Callable, TypeVar


T = TypeVar("T")

LOGGER = logging.getLogger("sentinel.recovery")


def run_with_retry(
    operation: Callable[[], T],
    max_attempts: int = 3,
    delay_seconds: float = 2,
    backoff_multiplier: float = 2,
    retry_on: tuple = (Exception,),
) -> T:
    """
    Execute an operation with bounded automatic retries.

    Example:
        run_with_retry(
            lambda: load_dataset(),
            max_attempts=3,
            delay_seconds=2
        )
    """

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    if delay_seconds < 0:
        raise ValueError("delay_seconds cannot be negative")

    if backoff_multiplier < 1:
        raise ValueError("backoff_multiplier must be at least 1")

    if not retry_on or not all(
        isinstance(error, type) and issubclass(error, Exception)
        for error in retry_on
    ):
        raise ValueError("retry_on must contain Exception classes")

    current_delay = delay_seconds

    for attempt in range(1, max_attempts + 1):

        try:
            LOGGER.info(
                "Executing operation. Attempt %d/%d",
                attempt,
                max_attempts,
            )

            result = operation()

            if attempt > 1:
                LOGGER.info(
                    "Operation recovered successfully on attempt %d",
                    attempt,
                )
            else:
                LOGGER.info("Operation completed successfully.")

            return result

        except retry_on as error:

            LOGGER.exception(
                "Operation failed on attempt %d/%d: %s",
                attempt,
                max_attempts,
                error,
            )

            if attempt == max_attempts:
                LOGGER.error(
                    "Operation failed after all %d attempts.",
                    max_attempts,
                )
                raise

            LOGGER.warning(
                "Retrying in %.2f seconds...",
                current_delay,
            )

            if current_delay > 0:
                time.sleep(current_delay)

            current_delay *= backoff_multiplier

    raise RuntimeError("Unexpected retry engine termination")
