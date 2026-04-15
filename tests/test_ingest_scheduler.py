#!/usr/bin/env python3
"""Tests for execution/ingest_scheduler.py (#129).

Covers:
    (a) crontab line generation
    (b) log directory creation on run-now
    (c) 30-day log retention pruning
    (d) failure captured to cross_agent_context
    (e) run-now invokes dispatcher with correct args

Runs standalone: `python3 tests/test_ingest_scheduler.py`
Also works under pytest.
"""
from __future__ import annotations

import datetime as _dt
import importlib
import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

# Ensure repo root is on sys.path so `execution.ingest_scheduler` imports cleanly.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Import the module under test.
from execution import ingest_scheduler as sched  # noqa: E402


def _reload_with_log_dir(tmp_log_dir: Path):
    """Point the module's LOG_DIR at a tmp path for isolation."""
    sched.LOG_DIR = tmp_log_dir
    return sched


# ─── (a) crontab line generation ──────────────────────────────────────────────


class TestCronLineGeneration(unittest.TestCase):
    def test_default_cron_expr_is_daily_at_3am(self):
        self.assertEqual(sched.DEFAULT_CRON_EXPR, "0 3 * * *")

    def test_build_cron_line_contains_dispatcher_invocation(self):
        line = sched.build_cron_line(config=Path("/tmp/cfg.json"))
        self.assertIn("0 3 * * *", line)
        self.assertIn("ingest_scheduler.py", line)
        self.assertIn("run-now", line)
        self.assertIn("/tmp/cfg.json", line)
        self.assertIn(">> .tmp/ingest/logs/cron.out", line)

    def test_build_crontab_block_includes_markers(self):
        block = sched.build_crontab_block(config=Path("/tmp/cfg.json"))
        self.assertIn(sched.CRON_MARKER_BEGIN, block)
        self.assertIn(sched.CRON_MARKER_END, block)
        # Block should have exactly one dispatcher invocation line between markers.
        lines = [
            ln for ln in block.splitlines()
            if ln and not ln.startswith("#")
        ]
        self.assertEqual(len(lines), 1)

    def test_strip_existing_block_is_idempotent(self):
        block = sched.build_crontab_block(config=Path("/tmp/cfg.json"))
        existing = "SHELL=/bin/bash\n" + block + "# unrelated\n"
        stripped = sched._strip_existing_block(existing)
        self.assertNotIn(sched.CRON_MARKER_BEGIN, stripped)
        self.assertIn("SHELL=/bin/bash", stripped)
        self.assertIn("# unrelated", stripped)


# ─── (c) 30-day log retention pruning ─────────────────────────────────────────


class TestLogRetention(unittest.TestCase):
    def setUp(self):
        self._orig_log_dir = sched.LOG_DIR
        self._tmp = Path(__file__).resolve().parent / "_tmp_logs"
        self._tmp.mkdir(parents=True, exist_ok=True)
        for p in self._tmp.glob("*.log"):
            p.unlink()
        sched.LOG_DIR = self._tmp

    def tearDown(self):
        for p in self._tmp.glob("*"):
            try:
                p.unlink()
            except OSError:
                pass
        self._tmp.rmdir()
        sched.LOG_DIR = self._orig_log_dir

    def test_prunes_logs_older_than_30_days(self):
        today = _dt.date(2026, 4, 14)
        old = today - _dt.timedelta(days=31)
        fresh = today - _dt.timedelta(days=5)
        boundary = today - _dt.timedelta(days=30)  # exactly 30 → keep
        (self._tmp / f"{old.isoformat()}.log").write_text("old")
        (self._tmp / f"{fresh.isoformat()}.log").write_text("fresh")
        (self._tmp / f"{boundary.isoformat()}.log").write_text("boundary")
        (self._tmp / "cron.out").write_text("not dated — keep")

        removed = sched.prune_old_logs(now=today, log_dir=self._tmp)
        names = {p.name for p in removed}
        self.assertIn(f"{old.isoformat()}.log", names)
        self.assertFalse((self._tmp / f"{old.isoformat()}.log").exists())
        self.assertTrue((self._tmp / f"{fresh.isoformat()}.log").exists())
        self.assertTrue((self._tmp / f"{boundary.isoformat()}.log").exists())
        self.assertTrue((self._tmp / "cron.out").exists())

    def test_prune_handles_missing_dir(self):
        missing = self._tmp / "nope"
        # Should not raise.
        removed = sched.prune_old_logs(log_dir=missing)
        self.assertEqual(removed, [])


# ─── (b) log dir creation + (e) run-now invokes dispatcher ────────────────────


class TestRunNow(unittest.TestCase):
    def setUp(self):
        self._orig_log_dir = sched.LOG_DIR
        self._tmp = Path(__file__).resolve().parent / "_tmp_run"
        self._tmp.mkdir(parents=True, exist_ok=True)
        for p in self._tmp.rglob("*"):
            if p.is_file():
                p.unlink()
        sched.LOG_DIR = self._tmp

    def tearDown(self):
        for p in list(self._tmp.rglob("*")):
            try:
                p.unlink()
            except OSError:
                pass
        try:
            self._tmp.rmdir()
        except OSError:
            pass
        sched.LOG_DIR = self._orig_log_dir

    def test_run_now_creates_log_dir_and_invokes_dispatcher(self):
        calls = []

        def fake_runner(cmd, *args, **kwargs):
            calls.append({"cmd": cmd, "kwargs": kwargs})
            # Simulate a dispatcher that writes to the log stream.
            stdout = kwargs.get("stdout")
            if stdout is not None and hasattr(stdout, "write"):
                stdout.write("dispatcher-ok\n")
            return types.SimpleNamespace(returncode=0)

        cfg = Path("/tmp/cfg.json")
        today = _dt.date(2026, 4, 14)
        rc = sched.run_now(cfg, runner=fake_runner, now=today)

        self.assertEqual(rc, 0)
        self.assertTrue(self._tmp.exists())
        log_file = self._tmp / f"{today.isoformat()}.log"
        self.assertTrue(log_file.exists(), "Expected dated log file to exist")
        contents = log_file.read_text()
        self.assertIn("dispatcher-ok", contents)
        self.assertIn("exit=0", contents)

        # (e) dispatcher called with correct config flag.
        self.assertEqual(len(calls), 1)
        cmd = calls[0]["cmd"]
        self.assertIn("--config", cmd)
        self.assertEqual(cmd[cmd.index("--config") + 1], str(cfg))
        self.assertTrue(str(cmd[1]).endswith("ingest_dispatcher.py"))

    def test_run_now_preserves_nonzero_exit_and_notifies(self):
        def failing_runner(cmd, *args, **kwargs):
            stdout = kwargs.get("stdout")
            if stdout is not None and hasattr(stdout, "write"):
                stdout.write("BOOM: token expired\n")
            return types.SimpleNamespace(returncode=7)

        notify_calls = []

        def fake_notify(exit_code, log_path, runner=None):
            notify_calls.append({"exit_code": exit_code, "log_path": log_path})

        with mock.patch.object(sched, "notify_failure", fake_notify):
            rc = sched.run_now(Path("/tmp/cfg.json"), runner=failing_runner,
                               now=_dt.date(2026, 4, 14))
        self.assertEqual(rc, 7, "Exit code from dispatcher must be preserved")
        self.assertEqual(len(notify_calls), 1)
        self.assertEqual(notify_calls[0]["exit_code"], 7)
        self.assertTrue(str(notify_calls[0]["log_path"]).endswith("2026-04-14.log"))


# ─── (d) failure captured to cross_agent_context ──────────────────────────────


class TestNotifyFailure(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(__file__).resolve().parent / "_tmp_notify"
        self._tmp.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        for p in list(self._tmp.rglob("*")):
            try:
                p.unlink()
            except OSError:
                pass
        try:
            self._tmp.rmdir()
        except OSError:
            pass

    def test_notify_failure_calls_cross_agent_store(self):
        log_path = self._tmp / "2026-04-14.log"
        log_path.write_text("auth expired: refresh token rejected\n" * 5)

        captured = []

        def fake_runner(cmd, *args, **kwargs):
            captured.append(cmd)
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")

        # Make sure CROSS_AGENT existence check passes by pointing to a real file.
        real_cross_agent = sched.CROSS_AGENT
        self.assertTrue(real_cross_agent.exists(),
                        "cross_agent_context.py must exist in repo")

        sched.notify_failure(7, log_path, runner=fake_runner)

        self.assertEqual(len(captured), 1)
        cmd = captured[0]
        self.assertEqual(cmd[0], sys.executable)
        self.assertTrue(cmd[1].endswith("cross_agent_context.py"))
        self.assertIn("store", cmd)
        self.assertIn("--agent", cmd)
        self.assertEqual(cmd[cmd.index("--agent") + 1], "claude")
        self.assertIn("--project", cmd)
        self.assertEqual(cmd[cmd.index("--project") + 1], "agi-agent-kit")
        self.assertIn("--action", cmd)
        action = cmd[cmd.index("--action") + 1]
        self.assertIn("ingest cron failure", action)
        self.assertIn("exit=7", action)
        self.assertIn("auth expired", action)

    def test_notify_failure_truncates_tail_to_2kb(self):
        log_path = self._tmp / "2026-04-14.log"
        log_path.write_text("x" * 10_000)
        captured = []

        def fake_runner(cmd, *args, **kwargs):
            captured.append(cmd)
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")

        sched.notify_failure(1, log_path, runner=fake_runner)
        action = captured[0][captured[0].index("--action") + 1]
        # action has wrapping text ("tail<<<", "exit=N" — note the 'x' in "exit")
        # so extract the tail slice between the markers and verify ITS length.
        self.assertLess(len(action), 10_000)
        start = action.index("tail<<<\n") + len("tail<<<\n")
        end = action.rindex("\n>>>")
        tail_slice = action[start:end]
        self.assertLessEqual(
            len(tail_slice), sched.LOG_TAIL_MAX_BYTES,
            "Log tail must be truncated to LOG_TAIL_MAX_BYTES",
        )
        self.assertEqual(
            tail_slice.count("x"), sched.LOG_TAIL_MAX_BYTES,
            "Tail slice should contain exactly LOG_TAIL_MAX_BYTES x's",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
