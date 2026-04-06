from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from unittest import TestCase
from unittest.mock import patch

from common.services.thread import thread_pool as thread_pool_module


class ThreadPoolServiceTest(TestCase):
    def tearDown(self):
        thread_pool_module.shutdown_thread_pool_executors(wait=False)

    def test_get_thread_pool_executor_reuses_and_requires_positive_workers(self):
        a = thread_pool_module.get_thread_pool_executor("test_pool", max_workers=2)
        b = thread_pool_module.get_thread_pool_executor("test_pool", max_workers=2)
        self.assertIs(a, b)
        self.assertIsInstance(a, ThreadPoolExecutor)

        with self.assertRaises(ValueError):
            thread_pool_module.get_thread_pool_executor("bad", max_workers=0)

    def test_distinct_names_are_distinct_executors(self):
        x = thread_pool_module.get_thread_pool_executor("p1", max_workers=1)
        y = thread_pool_module.get_thread_pool_executor("p2", max_workers=1)
        self.assertIsNot(x, y)

    def test_second_call_with_different_max_workers_logs_warning(self):
        thread_pool_module.get_thread_pool_executor("warn_pool", max_workers=2)
        with patch.object(thread_pool_module.logger, "warning") as mock_warn:
            thread_pool_module.get_thread_pool_executor("warn_pool", max_workers=9)
        mock_warn.assert_called_once()
        self.assertIn("ignoring max_workers", mock_warn.call_args[0][0])

    def test_shutdown_clears_pools(self):
        thread_pool_module.get_thread_pool_executor("gone", max_workers=1)
        thread_pool_module.shutdown_thread_pool_executors(wait=False)
        fresh = thread_pool_module.get_thread_pool_executor("gone", max_workers=3)
        self.assertIsInstance(fresh, ThreadPoolExecutor)

    def test_submit_runs_callable(self):
        ex = thread_pool_module.get_thread_pool_executor("run_pool", max_workers=2)
        fut = ex.submit(lambda: 7)
        self.assertEqual(fut.result(timeout=2), 7)
