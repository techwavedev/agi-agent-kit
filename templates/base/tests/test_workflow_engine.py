#!/usr/bin/env python3
"""
Test: Workflow Engine
=====================

Unit tests for execution/workflow_engine.py:
1. list — returns all 4 playbooks from data/workflows.json
2. start — initialises state, sets step 0 as active
3. next — returns active step without advancing
4. complete — advances to next step and records notes
5. skip — marks step skipped and advances
6. status — progress bar reflects completed/skipped steps
7. abort — clears state file
8. complete to end — final step completion message
9. error paths — no active playbook, unknown playbook id

No external services required; runs fully offline.

Usage:
    python3 templates/base/tests/test_workflow_engine.py
"""

import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

# ─── Path Resolution ──────────────────────────────────────────────────────────

_test_dir = os.path.dirname(os.path.abspath(__file__))
_base_dir = os.path.dirname(_test_dir)            # templates/base
_project_root = os.path.dirname(os.path.dirname(_base_dir))  # repo root

# Try execution dir in templates/base first, then repo root
for _exec_dir in [
    os.path.join(_base_dir, "execution"),
    os.path.join(_project_root, "execution"),
]:
    if os.path.isfile(os.path.join(_exec_dir, "workflow_engine.py")):
        sys.path.insert(0, _exec_dir)
        break

import workflow_engine as we

# Path to the real workflows.json (data/ in project root)
_WORKFLOWS_JSON = Path(_project_root) / "data" / "workflows.json"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_args(**kwargs):
    """Build a simple namespace (simulates argparse output)."""
    defaults = {"json": False, "notes": "", "reason": ""}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


class WorkflowEngineTests(unittest.TestCase):

    def setUp(self):
        """Use a temporary state file so tests are isolated."""
        self._tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self._tmp.close()
        Path(self._tmp.name).unlink(missing_ok=True)  # Start absent
        self._state_patch = patch.object(we, "_STATE_FILE", Path(self._tmp.name))
        self._state_patch.start()

        # Point to the real workflows.json so tests work against actual data
        self._wf_patch = patch.object(we, "_WORKFLOWS_FILE", _WORKFLOWS_JSON)
        self._wf_patch.start()

    def tearDown(self):
        self._state_patch.stop()
        self._wf_patch.stop()
        Path(self._tmp.name).unlink(missing_ok=True)

    # ── 1. list ───────────────────────────────────────────────────────────────

    def test_list_returns_all_playbooks(self):
        args = _make_args(json=True)
        rc = we.cmd_list(args)
        self.assertEqual(rc, 0)

    def test_list_json_output(self):
        """JSON output contains the 4 expected playbook IDs."""
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        args = _make_args(json=True)
        with redirect_stdout(buf):
            rc = we.cmd_list(args)
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        ids = [p["id"] for p in data["playbooks"]]
        self.assertIn("ship-saas-mvp", ids)
        self.assertIn("security-audit-web-app", ids)
        self.assertIn("build-ai-agent-system", ids)
        self.assertIn("qa-browser-automation", ids)

    # ── 2. start ─────────────────────────────────────────────────────────────

    def test_start_creates_state(self):
        args = _make_args(id="ship-saas-mvp", json=True)
        rc = we.cmd_start(args)
        self.assertEqual(rc, 0)
        state = we._load_state()
        self.assertEqual(state["playbook_id"], "ship-saas-mvp")
        self.assertEqual(state["current_step"], 0)
        self.assertEqual(state["steps"][0]["status"], "active")

    def test_start_all_other_steps_pending(self):
        args = _make_args(id="ship-saas-mvp", json=True)
        we.cmd_start(args)
        state = we._load_state()
        for step in state["steps"][1:]:
            self.assertEqual(step["status"], "pending")

    def test_start_unknown_id_returns_1(self):
        args = _make_args(id="does-not-exist", json=True)
        rc = we.cmd_start(args)
        self.assertEqual(rc, 1)

    # ── 3. next ───────────────────────────────────────────────────────────────

    def test_next_no_active_playbook(self):
        args = _make_args(json=True)
        rc = we.cmd_next(args)
        self.assertEqual(rc, 2)

    def test_next_returns_active_step(self):
        import io
        from contextlib import redirect_stdout
        we.cmd_start(_make_args(id="qa-browser-automation", json=True))
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = we.cmd_next(_make_args(json=True))
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["step"]["index"], 0)
        self.assertEqual(data["step"]["status"], "active")

    def test_next_does_not_advance(self):
        we.cmd_start(_make_args(id="qa-browser-automation", json=True))
        we.cmd_next(_make_args(json=True))
        state = we._load_state()
        self.assertEqual(state["current_step"], 0)

    # ── 4. complete ───────────────────────────────────────────────────────────

    def test_complete_advances_step(self):
        we.cmd_start(_make_args(id="qa-browser-automation", json=True))
        rc = we.cmd_complete(_make_args(notes="done step 1", json=True))
        self.assertEqual(rc, 0)
        state = we._load_state()
        self.assertEqual(state["current_step"], 1)
        self.assertEqual(state["steps"][0]["status"], "complete")
        self.assertEqual(state["steps"][1]["status"], "active")

    def test_complete_records_notes(self):
        we.cmd_start(_make_args(id="qa-browser-automation", json=True))
        we.cmd_complete(_make_args(notes="my note", json=True))
        state = we._load_state()
        self.assertEqual(state["steps"][0]["agent_notes"], "my note")

    def test_complete_no_active_playbook(self):
        rc = we.cmd_complete(_make_args(json=True))
        self.assertEqual(rc, 2)

    # ── 5. skip ───────────────────────────────────────────────────────────────

    def test_skip_advances_step(self):
        we.cmd_start(_make_args(id="qa-browser-automation", json=True))
        rc = we.cmd_skip(_make_args(reason="n/a", json=True))
        self.assertEqual(rc, 0)
        state = we._load_state()
        self.assertEqual(state["steps"][0]["status"], "skipped")
        self.assertEqual(state["current_step"], 1)

    def test_skip_records_reason(self):
        we.cmd_start(_make_args(id="qa-browser-automation", json=True))
        we.cmd_skip(_make_args(reason="already done", json=True))
        state = we._load_state()
        self.assertIn("already done", state["steps"][0]["agent_notes"])

    # ── 6. status ─────────────────────────────────────────────────────────────

    def test_status_no_active_playbook(self):
        rc = we.cmd_status(_make_args(json=True))
        self.assertEqual(rc, 2)

    def test_status_progress(self):
        import io
        from contextlib import redirect_stdout
        we.cmd_start(_make_args(id="qa-browser-automation", json=True))
        we.cmd_complete(_make_args(notes="done", json=True))
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = we.cmd_status(_make_args(json=True))
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["completed"], 1)
        self.assertEqual(data["total_steps"], 3)

    # ── 7. abort ─────────────────────────────────────────────────────────────

    def test_abort_clears_state(self):
        we.cmd_start(_make_args(id="qa-browser-automation", json=True))
        rc = we.cmd_abort(_make_args(json=True))
        self.assertEqual(rc, 0)
        state = we._load_state()
        self.assertEqual(state, {})

    def test_abort_no_active_playbook(self):
        rc = we.cmd_abort(_make_args(json=True))
        self.assertEqual(rc, 2)

    # ── 8. complete to end ────────────────────────────────────────────────────

    def test_complete_all_steps_finishes_playbook(self):
        import io
        from contextlib import redirect_stdout
        playbook_id = "qa-browser-automation"
        we.cmd_start(_make_args(id=playbook_id, json=True))
        # Determine step count from the loaded playbook so the test stays
        # correct if the playbook definition ever changes.
        workflows = we._load_workflows()
        playbook = we._find_playbook(playbook_id, workflows)
        step_count = len(playbook["steps"])
        for _ in range(step_count):
            we.cmd_complete(_make_args(notes="done", json=True))
        # After completing all steps, status should show all done
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = we.cmd_status(_make_args(json=True))
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["completed"], step_count)
        self.assertEqual(data["total_steps"], step_count)

    def test_complete_on_finished_playbook_returns_3(self):
        playbook_id = "qa-browser-automation"
        we.cmd_start(_make_args(id=playbook_id, json=True))
        workflows = we._load_workflows()
        playbook = we._find_playbook(playbook_id, workflows)
        step_count = len(playbook["steps"])
        for _ in range(step_count):
            we.cmd_complete(_make_args(notes="done", json=True))
        rc = we.cmd_complete(_make_args(json=True))
        self.assertEqual(rc, 3)


# ─── Runner ───────────────────────────────────────────────────────────────────

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def run(self):
        suite = unittest.TestLoader().loadTestsFromTestCase(WorkflowEngineTests)
        for test in suite:
            try:
                test.setUp()
                try:
                    getattr(test, test._testMethodName)()
                    print(f"  ✅ {test._testMethodName}")
                    self.passed += 1
                except AssertionError as e:
                    print(f"  ❌ {test._testMethodName} — {e}")
                    self.failed += 1
                    self.errors.append((test._testMethodName, str(e)))
                except Exception as e:
                    print(f"  ❌ {test._testMethodName} — {type(e).__name__}: {e}")
                    self.failed += 1
                    self.errors.append((test._testMethodName, str(e)))
                finally:
                    test.tearDown()
            except Exception as e:
                print(f"  ❌ {test._testMethodName} — setup/teardown error: {e}")
                self.failed += 1

        total = self.passed + self.failed
        print(f"\n  {'✅' if self.failed == 0 else '❌'}  {self.passed}/{total} tests passed")
        return self.failed == 0


if __name__ == "__main__":
    print("\n🧪  Workflow Engine Tests\n")
    runner = TestResults()
    ok = runner.run()
    sys.exit(0 if ok else 1)
