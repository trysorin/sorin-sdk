"""
Python `contextvars` propagate across `await` but NOT across raw threads
(ThreadPoolExecutor workers start with the default). This is expected Python
semantics — if an agent parallelizes tool execution via threads, each worker
starts with parent=None and those calls land as orphan roots, which is
correct. This test guards against accidental future changes that would
break that assumption.
"""

from concurrent.futures import ThreadPoolExecutor

from sorin._context import (
    clear_current_parent,
    get_current_parent,
    set_current_parent,
)


def _read_parent():
    return get_current_parent()


def test_parent_does_not_leak_into_threadpool():
    clear_current_parent()
    set_current_parent("main-thread-parent")

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_read_parent) for _ in range(4)]
        results = [f.result() for f in futures]

    # Each worker thread gets the default (None), not the main thread's value.
    assert all(r is None for r in results), f"expected None in threads, got {results}"

    # Main thread's value is untouched.
    assert get_current_parent() == "main-thread-parent"


def test_parent_cleared_between_tests():
    # Sanity check: after clear, parent is None.
    set_current_parent("something")
    clear_current_parent()
    assert get_current_parent() is None
