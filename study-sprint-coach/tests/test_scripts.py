import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "study_sprint.py"


class StudySprintCliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def write_state(self, path, deadline="2026-09-07", minutes_per_day=90, topics=None):
        state = {
            "version": 1,
            "mode": "exam",
            "deadline": deadline,
            "minutes_per_day": minutes_per_day,
            "target_score": 85.0,
            "sources": [],
            "topics": topics or [],
            "sessions": [],
            "plan": {"as_of": None, "schedule": [], "backlog": []},
        }
        path.write_text(json.dumps(state), encoding="utf-8")

    def topic(self, topic_id, name, relevance, mastery, score_gain, minutes, **extra):
        return {
            "id": topic_id,
            "name": name,
            "relevance": relevance,
            "mastery": mastery,
            "mastery_attempts": 5,
            "score_gain": score_gain,
            "minutes": minutes,
            "remaining_minutes": minutes,
            "evidence": [{"source": "past-exam.md", "locator": "2024 Q2"}],
            "mastery_check": "5题至少4题正确",
            **extra,
        }

    def test_init_creates_manifest_with_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materials = root / "materials"
            materials.mkdir()
            content = b"# Calculus\n"
            (materials / "outline.md").write_bytes(content)
            state = root / "state.json"

            result = self.run_cli(
                "init", "--materials", str(materials), "--deadline", "2026-09-07",
                "--minutes-per-day", "120", "--target-score", "85", "--state", str(state),
                "--as-of", "2026-09-01",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            saved = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(saved["version"], 1)
            self.assertEqual(saved["sources"][0]["path"], "outline.md")
            self.assertEqual(saved["sources"][0]["status"], "ready")
            self.assertEqual(
                saved["sources"][0]["sha256"],
                hashlib.sha256(content).hexdigest(),
            )

    def test_invalid_init_creates_no_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materials = root / "materials"
            materials.mkdir()

            for deadline, minutes in (("2026-08-31", "120"), ("2026-09-07", "0")):
                state = root / f"state-{minutes}.json"
                result = self.run_cli(
                    "init", "--materials", str(materials), "--deadline", deadline,
                    "--minutes-per-day", minutes, "--target-score", "85", "--state", str(state),
                    "--as-of", "2026-09-01",
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(state.exists())

    def test_plan_prioritizes_and_backlogs_without_dropping_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state.json"
            topics = [
                self.topic("A", "A", 1.0, 0.2, 20.0, 60),
                self.topic("B", "B", 0.8, 0.5, 15.0, 30),
                self.topic("C", "C", 0.1, 0.5, 10.0, 15),
            ]
            self.write_state(state, deadline="2026-09-01", topics=[])
            topic_file = root / "topics.json"
            topic_file.write_text(json.dumps(topics), encoding="utf-8")

            result = self.run_cli(
                "plan", "--state", str(state), "--topics", str(topic_file),
                "--as-of", "2026-09-01",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            plan = json.loads(result.stdout)
            self.assertEqual([item["topic_id"] for item in plan["schedule"]], ["A", "B"])
            self.assertEqual([item["minutes"] for item in plan["schedule"]], [60, 30])
            self.assertEqual(plan["backlog"], [{"topic_id": "C", "topic_name": "C", "remaining_minutes": 15}])
            self.assertEqual(plan["schedule"][0]["date"], "2026-09-01")
            saved = json.loads(state.read_text(encoding="utf-8"))
            self.assertAlmostEqual(saved["topics"][0]["priority"], 1 * 0.8 * 20 / 60)
            self.assertAlmostEqual(saved["topics"][1]["priority"], 0.8 * 0.5 * 15 / 30)

    def test_plan_without_evidence_leaves_existing_state_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state.json"
            self.write_state(state, deadline="2026-09-01")
            before = state.read_bytes()
            topic_file = root / "topics.json"
            invalid = self.topic("A", "A", 1.0, 0.2, 20.0, 60, evidence=[])
            topic_file.write_text(json.dumps([invalid]), encoding="utf-8")

            result = self.run_cli(
                "plan", "--state", str(state), "--topics", str(topic_file),
                "--as-of", "2026-09-01",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(state.read_bytes(), before)

    def test_record_updates_mastery_and_changes_visible_plan_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state.json"
            topics = [
                self.topic("A", "A", 1.0, 0.2, 20.0, 60),
                self.topic("B", "B", 0.8, 0.5, 15.0, 30),
            ]
            self.write_state(state, deadline="2026-09-01", topics=topics)
            results = root / "results.json"
            results.write_text(json.dumps({
                "date": "2026-09-01",
                "items": [{"topic_id": "A", "correct": 5, "total": 5, "minutes_spent": 30}],
            }), encoding="utf-8")

            result = self.run_cli(
                "record", "--state", str(state), "--results", str(results),
                "--as-of", "2026-09-01",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            saved = json.loads(state.read_text(encoding="utf-8"))
            recorded = next(topic for topic in saved["topics"] if topic["id"] == "A")
            self.assertEqual(recorded["mastery"], 0.6)
            self.assertEqual(recorded["mastery_attempts"], 10)
            self.assertEqual(recorded["remaining_minutes"], 30)
            self.assertEqual(saved["sessions"], [json.loads(results.read_text(encoding="utf-8"))])
            self.assertEqual([item["topic_id"] for item in json.loads(result.stdout)["plan"]["schedule"]], ["B", "A"])

    def test_unknown_or_malformed_results_leave_existing_state_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state.json"
            self.write_state(state, topics=[self.topic("A", "A", 1.0, 0.2, 20.0, 60)])
            before = state.read_bytes()
            for payload in (
                {"date": "2026-09-01", "items": [{"topic_id": "X", "correct": 1, "total": 1, "minutes_spent": 0}]},
                {"date": "2026-09-01", "items": []},
            ):
                results = root / "results.json"
                results.write_text(json.dumps(payload), encoding="utf-8")
                result = self.run_cli(
                    "record", "--state", str(state), "--results", str(results),
                    "--as-of", "2026-09-01",
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(state.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
