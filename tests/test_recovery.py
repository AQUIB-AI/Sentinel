
import pytest

from src.sentinel.recovery.retry import run_with_retry


def test_successful_operation():
    result = run_with_retry(
        lambda: "Pipeline completed",
        max_attempts=3,
        delay_seconds=0,
    )

    assert result == "Pipeline completed"


def test_operation_recovers_after_failures(monkeypatch):
    attempts = {"count": 0}

    def unstable_operation():
        attempts["count"] += 1

        if attempts["count"] < 3:
            raise ConnectionError("Temporary database failure")

        return "Recovered successfully"

    monkeypatch.setattr(
        "src.sentinel.recovery.retry.time.sleep",
        lambda seconds: None,
    )

    result = run_with_retry(
        unstable_operation,
        max_attempts=3,
        delay_seconds=0,
    )

    assert result == "Recovered successfully"
    assert attempts["count"] == 3


def test_operation_fails_after_all_retries(monkeypatch):
    attempts = {"count": 0}

    def failing_operation():
        attempts["count"] += 1
        raise ValueError("Permanent pipeline failure")

    monkeypatch.setattr(
        "src.sentinel.recovery.retry.time.sleep",
        lambda seconds: None,
    )

    with pytest.raises(ValueError):
        run_with_retry(
            failing_operation,
            max_attempts=3,
            delay_seconds=0,
        )

    assert attempts["count"] == 3


def test_retry_delay_increases_exponentially(monkeypatch):
    delays = []

    def fake_sleep(seconds):
        delays.append(seconds)

    attempts = {"count": 0}

    def unstable_operation():
        attempts["count"] += 1

        if attempts["count"] < 3:
            raise RuntimeError("Temporary failure")

        return "Success"

    monkeypatch.setattr(
        "src.sentinel.recovery.retry.time.sleep",
        fake_sleep,
    )

    run_with_retry(
        unstable_operation,
        max_attempts=3,
        delay_seconds=2,
        backoff_multiplier=2,
    )

    assert delays == [2, 4]


def test_invalid_attempt_count():
    with pytest.raises(ValueError):
        run_with_retry(
            lambda: "Success",
            max_attempts=0,
        )


def test_invalid_delay():
    with pytest.raises(ValueError):
        run_with_retry(
            lambda: "Success",
            delay_seconds=-1,
        )


def test_non_retryable_exception_is_not_retried(monkeypatch):
    attempts = {"count": 0}

    def failing_operation():
        attempts["count"] += 1
        raise ValueError("Invalid input")

    monkeypatch.setattr(
        "src.sentinel.recovery.retry.time.sleep",
        lambda seconds: None,
    )

    with pytest.raises(ValueError):
        run_with_retry(
            failing_operation,
            max_attempts=3,
            delay_seconds=0,
            retry_on=(ConnectionError,),
        )

    assert attempts["count"] == 1
