import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "study_sprint.py"
OPENVINO_PROBE = Path(__file__).parents[1] / "scripts" / "openvino_probe.py"
OPENVINO_DEVICE_SOURCE = "https://docs.openvino.ai/nightly/openvino-workflow/running-inference/inference-devices-and-modes/query-device-properties.html"


class StudySprintCliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def write_state(self, path, deadline="2026-09-07", minutes_per_day=90, topics=None, **overrides):
        state = {
            "version": 1,
            "mode": "exam",
            "deadline": deadline,
            "minutes_per_day": minutes_per_day,
            "target_score": 85.0,
            "sources": [{
                "path": "past-exam.md",
                "kind": "md",
                "size": 1,
                "sha256": "0" * 64,
                "status": "ready",
            }],
            "topics": topics if topics is not None else [],
            "sessions": [],
            "plan": {"as_of": None, "schedule": [], "backlog": []},
        }
        state.update(overrides)
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

    def test_plan_rejects_non_finite_topic_numbers_without_changing_state(self):
        topic_json = """[{
            "id": "A",
            "name": "A",
            "relevance": RELEVANCE,
            "mastery": 0.2,
            "mastery_attempts": 5,
            "score_gain": SCORE_GAIN,
            "minutes": 60,
            "remaining_minutes": 60,
            "evidence": [{"source": "past-exam.md", "locator": "2024 Q2"}],
            "mastery_check": "5题至少4题正确"
        }]"""
        payloads = (
            topic_json.replace("RELEVANCE", "NaN").replace("SCORE_GAIN", "20.0"),
            topic_json.replace("RELEVANCE", "1.0").replace("SCORE_GAIN", "Infinity"),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state.json"
            topic_file = root / "topics.json"
            for payload in payloads:
                with self.subTest(payload=payload):
                    self.write_state(state, deadline="2026-09-01")
                    before = state.read_bytes()
                    topic_file.write_text(payload, encoding="utf-8")

                    result = self.run_cli(
                        "plan", "--state", str(state), "--topics", str(topic_file),
                        "--as-of", "2026-09-01",
                    )

                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(state.read_bytes(), before)

    def test_plan_requires_evidence_source_to_be_ready_manifest_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state.json"
            topic_file = root / "topics.json"
            cases = (
                ([], "past-exam.md"),
                ([{"path": "other.md", "kind": "md", "size": 1, "sha256": "0" * 64, "status": "ready"}], "past-exam.md"),
                ([{"path": "past-exam.md", "kind": "pdf", "size": 1, "sha256": "0" * 64, "status": "needs_extraction"}], "past-exam.md"),
                ([{"path": "past-exam.md", "kind": "bin", "size": 1, "sha256": "0" * 64, "status": "unsupported"}], "past-exam.md"),
            )
            for sources, evidence_source in cases:
                with self.subTest(sources=sources):
                    self.write_state(state, deadline="2026-09-01", sources=sources)
                    before = state.read_bytes()
                    topic_file.write_text(json.dumps([
                        self.topic("A", "A", 1.0, 0.2, 20.0, 60,
                                   evidence=[{"source": evidence_source, "locator": "2024 Q2"}]),
                    ]), encoding="utf-8")

                    result = self.run_cli(
                        "plan", "--state", str(state), "--topics", str(topic_file),
                        "--as-of", "2026-09-01",
                    )

                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(state.read_bytes(), before)

    def test_plan_rejects_invalid_state_schema_without_changing_state(self):
        invalid_overrides = (
            {"version": 2},
            {"mode": ""},
            {"minutes_per_day": True},
            {"target_score": float("nan")},
            {"sources": {}},
            {"sources": [{"path": "past-exam.md", "kind": "md", "size": 1,
                          "sha256": "0" * 64, "status": []}]},
            {"topics": {}},
            {"sessions": {}},
            {"plan": []},
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state.json"
            topic_file = root / "topics.json"
            topic_file.write_text(json.dumps([
                self.topic("A", "A", 1.0, 0.2, 20.0, 60),
            ]), encoding="utf-8")
            for override in invalid_overrides:
                with self.subTest(override=override):
                    self.write_state(state, **override)
                    before = state.read_bytes()

                    result = self.run_cli(
                        "plan", "--state", str(state), "--topics", str(topic_file),
                        "--as-of", "2026-09-01",
                    )

                    self.assertNotEqual(result.returncode, 0)
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertEqual(state.read_bytes(), before)

    def test_plan_after_deadline_leaves_existing_state_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state.json"
            topic_file = root / "topics.json"
            self.write_state(state, deadline="2026-09-01")
            before = state.read_bytes()
            topic_file.write_text(json.dumps([
                self.topic("A", "A", 1.0, 0.2, 20.0, 60),
            ]), encoding="utf-8")

            result = self.run_cli(
                "plan", "--state", str(state), "--topics", str(topic_file),
                "--as-of", "2026-09-02",
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

    def test_record_validates_state_provenance_and_deadline_without_changing_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state.json"
            results = root / "results.json"
            results.write_text(json.dumps({
                "date": "2026-09-01",
                "items": [{"topic_id": "A", "correct": 1, "total": 1, "minutes_spent": 0}],
            }), encoding="utf-8")
            cases = (
                ({"version": 2}, "2026-09-01"),
                ({"sources": []}, "2026-09-01"),
                ({}, "2026-09-02"),
            )
            for overrides, as_of in cases:
                with self.subTest(overrides=overrides, as_of=as_of):
                    self.write_state(
                        state,
                        deadline="2026-09-01",
                        topics=[self.topic("A", "A", 1.0, 0.2, 20.0, 60)],
                        **overrides,
                    )
                    before = state.read_bytes()

                    result = self.run_cli(
                        "record", "--state", str(state), "--results", str(results),
                        "--as-of", as_of,
                    )

                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(state.read_bytes(), before)


class OpenVinoProbeTests(unittest.TestCase):
    def load_probe(self):
        spec = importlib.util.spec_from_file_location("openvino_probe", OPENVINO_PROBE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_probe_reports_sorted_devices_for_available_openvino(self):
        class FakeOpenVino:
            __version__ = "2026.0"

            class Core:
                available_devices = ["GPU", "CPU"]

        result = self.load_probe().probe_openvino(lambda name: FakeOpenVino)

        self.assertEqual(result, {
            "available": True,
            "version": "2026.0",
            "devices": ["CPU", "GPU"],
            "source": OPENVINO_DEVICE_SOURCE,
        })

    def test_probe_reports_missing_openvino_without_claiming_acceleration(self):
        def missing_importer(name):
            raise ModuleNotFoundError("No module named 'openvino'")

        result = self.load_probe().probe_openvino(missing_importer)

        self.assertFalse(result["available"])
        self.assertTrue(result["error"].startswith("ModuleNotFoundError:"))
        self.assertIn("Do not claim CPU/GPU/NPU acceleration until devices are listed.", result["next_action"])

    def test_probe_reports_runtime_discovery_failure_without_propagating(self):
        class FailingOpenVino:
            @staticmethod
            def Core():
                raise RuntimeError("plugin discovery failed")

        result = self.load_probe().probe_openvino(lambda name: FailingOpenVino)

        self.assertFalse(result["available"])
        self.assertEqual(result["error"], "RuntimeError: plugin discovery failed")

    def test_probe_subprocess_always_returns_utf8_json(self):
        result = subprocess.run(
            [sys.executable, str(OPENVINO_PROBE)],
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
        payload = json.loads(result.stdout.decode("utf-8"))
        self.assertIs(type(payload.get("available")), bool)
        self.assertTrue(payload.get("source"))


if __name__ == "__main__":
    unittest.main()
