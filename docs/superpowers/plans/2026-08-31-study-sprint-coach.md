# Study Sprint Coach Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify a publishable local-first Skill that converts evidence-backed course topics and assessment results into a capacity-constrained, adaptive study plan.

**Architecture:** A concise `SKILL.md` orchestrates document reading, evidence extraction, teaching, quizzes, and replanning. One standard-library Python CLI owns the atomic JSON state and scheduling formula; a second optional probe reports actual OpenVINO devices. A fixed output contract and three fresh-agent evaluations test behavior that source-code assertions cannot.

**Tech Stack:** Agent Skills Markdown, Python 3 standard library, `unittest`, optional OpenVINO runtime.

**Spec:** `docs/superpowers/specs/2026-08-31-study-sprint-coach-design.md`

## Global Constraints

- Default to local-only processing; cloud use requires explicit user approval.
- Do not plan a topic without at least one source locator.
- Do not overbook the available minutes through the deadline; return overflow as backlog.
- Keep one JSON state file and write it atomically.
- Use only Python standard library in required scripts; OpenVINO is optional and probed safely.
- Preserve the user-provided `任务要求.png` and `提交表单.png` unchanged.
- Use forward slashes in Skill documentation and relative paths inside the package.

---

### Task 1: Establish behavioral baseline

**Files:**
- Create: `study-sprint-coach/evaluations/scenarios.json`
- Create: `study-sprint-coach/evaluations/baseline.md`

**Interfaces:**
- Consumes: three realistic Chinese user prompts and synthetic course facts embedded in each prompt.
- Produces: a baseline record of missing citations, infeasible scheduling, weak formula explanations, and absent replanning behavior.

- [ ] **Step 1: Define three evaluations**

Create scenarios for: evidence-backed deadline planning, formula explanation with a supplied source locator, and replanning after a wrong-answer result. Each scenario includes observable expected behavior rather than exact prose.

- [ ] **Step 2: Run fresh agents without the Skill**

Dispatch one fresh-context agent per scenario. Do not provide the proposed Skill, output contract, formula, or expected answer.

- [ ] **Step 3: Record actual failures**

Write the observed behavior and exact shortcomings to `baseline.md`. These failures determine the minimum guidance in `SKILL.md`.

### Task 2: Create the minimal Skill contract

**Files:**
- Create: `study-sprint-coach/SKILL.md`
- Create: `study-sprint-coach/references/output-contract.md`
- Create: `study-sprint-coach/agents/openai.yaml`

**Interfaces:**
- Consumes: baseline failure patterns from Task 1 and the CLI commands from Task 3.
- Produces: an implicitly discoverable Skill that requires local evidence, diagnostic assessment, feasible planning, result recording, and fixed output shapes.

- [ ] **Step 1: Write `SKILL.md` against baseline failures**

Use frontmatter name `study-sprint-coach`. The description begins with `Use when` and names deadline-driven learning, supplied course materials, exam preparation, certification, onboarding, or project ramp-up without summarizing the workflow.

- [ ] **Step 2: Write the positive output recipes**

Define exact blocks for ordinary answers, formula explanations, plans, quizzes, and post-quiz reviews. Require source locators and explicit unsupported/conflicting-source states.

- [ ] **Step 3: Add Codex UI metadata**

Use:

```yaml
interface:
  display_name: "Study Sprint Coach"
  short_description: "Evidence-backed deadline learning plans"
  default_prompt: "Use $study-sprint-coach to build an evidence-backed study sprint from my local materials."
```

- [ ] **Step 4: Run structural validation**

Run the bundled `quick_validate.py` against `study-sprint-coach`. Expected: exit code 0 with no unfinished scaffold markers.

### Task 3: Implement state and adaptive planning with TDD

**Files:**
- Create: `study-sprint-coach/tests/test_scripts.py`
- Create: `study-sprint-coach/scripts/study_sprint.py`

**Interfaces:**
- Produces CLI commands:
  - `init --materials PATH --deadline YYYY-MM-DD --minutes-per-day INT --target-score NUMBER --state PATH`
  - `plan --state PATH --topics PATH --as-of YYYY-MM-DD`
  - `record --state PATH --results PATH --as-of YYYY-MM-DD`
- State JSON version is integer `1`.

- [ ] **Step 1: Write the failing initialization test**

```python
def test_init_creates_manifest_with_digest(self):
    material = self.materials / "outline.md"
    material.write_text("# Calculus\n", encoding="utf-8")
    result = self.run_cli("init", "--materials", self.materials,
                          "--deadline", "2026-09-07", "--minutes-per-day", "120",
                          "--target-score", "85", "--state", self.state)
    self.assertEqual(result.returncode, 0, result.stderr)
    data = json.loads(self.state.read_text(encoding="utf-8"))
    self.assertEqual(data["version"], 1)
    self.assertEqual(data["sources"][0]["sha256"],
                     hashlib.sha256(b"# Calculus\n").hexdigest())
```

- [ ] **Step 2: Run the test and verify RED**

Run: `python -m unittest study-sprint-coach/tests/test_scripts.py -v`

Expected: FAIL because `scripts/study_sprint.py` does not exist.

- [ ] **Step 3: Implement `init` minimally**

Validate deadline, minutes, target, and material directory; recursively scan files; hash bytes; classify text as `ready` and common binary document formats as `needs_extraction`; atomically write the state.

- [ ] **Step 4: Run the initialization test and verify GREEN**

Run the same unittest command. Expected: the initialization test passes.

- [ ] **Step 5: Write failing plan tests**

Use literal topic fixtures. Assert that priority order is `topic-a`, then `topic-b`; a topic without evidence is rejected; and capacity overflow appears in `backlog` rather than the schedule.

- [ ] **Step 6: Run plan tests and verify RED**

Expected: FAIL because `plan` is not implemented.

- [ ] **Step 7: Implement `plan` minimally**

Validate topic fields, calculate `relevance * (1 - mastery) * score_gain / minutes`, sort deterministically by negative priority then ID, fill each day's remaining minutes, and atomically update state.

- [ ] **Step 8: Run plan tests and verify GREEN**

Expected: all initialization and plan tests pass.

- [ ] **Step 9: Write failing record tests**

Start with topic A mastery `0.2`, attempts `5`, and result `5/5`. Assert updated mastery is `0.6`, topic B becomes the first priority, and malformed or unknown topic results leave the original state bytes unchanged.

- [ ] **Step 10: Run record tests and verify RED**

Expected: FAIL because `record` is not implemented.

- [ ] **Step 11: Implement `record` minimally**

Validate every result before mutating in memory, update weighted mastery and attempts, append the session, recalculate the plan using the supplied planning date, then atomically replace state.

- [ ] **Step 12: Run all script tests and verify GREEN**

Run: `python -m unittest discover -s study-sprint-coach/tests -v`

Expected: all tests pass with no warnings.

### Task 4: Add truthful OpenVINO capability reporting with TDD

**Files:**
- Modify: `study-sprint-coach/tests/test_scripts.py`
- Create: `study-sprint-coach/scripts/openvino_probe.py`

**Interfaces:**
- Produces: `probe_openvino(import_module=...) -> dict` and a JSON CLI report containing `available`, `version`, and `devices`, or `available: false` with an actionable reason.

- [ ] **Step 1: Write failing available and unavailable tests**

Use a specific fake importer returning an object whose `Core().available_devices` is `['CPU', 'GPU']`, and another importer raising `ModuleNotFoundError`. Assert exact structured results, not source text.

- [ ] **Step 2: Run tests and verify RED**

Expected: FAIL because `openvino_probe.py` does not exist.

- [ ] **Step 3: Implement the probe minimally**

Import `openvino`, read `__version__`, instantiate `Core`, and report sorted devices. Catch only import/runtime discovery errors and include the exception class and next action.

- [ ] **Step 4: Run all tests and verify GREEN**

Run: `python -m unittest discover -s study-sprint-coach/tests -v`

Expected: all tests pass.

### Task 5: Add reproducible demonstration and submission documentation

**Files:**
- Create: `study-sprint-coach/examples/demo-course/course-outline.md`
- Create: `study-sprint-coach/examples/demo-course/lecture-notes.md`
- Create: `study-sprint-coach/examples/demo-course/past-exam.md`
- Create: `study-sprint-coach/examples/demo-course/topics.json`
- Create: `study-sprint-coach/examples/demo-course/diagnostic-results.json`
- Create: `study-sprint-coach/README.md`
- Create: `study-sprint-coach/LICENSE`
- Create: `submission/technical-article-draft.md`
- Create: `submission/checklist.md`

**Interfaces:**
- Consumes: the CLI and Skill contract from Tasks 2–4.
- Produces: a synthetic, copyright-safe end-to-end demo and exact competition submission checklist.

- [ ] **Step 1: Add the synthetic course pack**

Use a small calculus topic set with explicit heading and question locators. Include one high-priority weak topic and one initially lower-priority topic that moves upward after results.

- [ ] **Step 2: Write reproducible CLI documentation**

Document setup, `init`, `plan`, `record`, OpenVINO probing, state fields, privacy behavior, limitations, and how to install the Skill in common Agent Skills directories.

- [ ] **Step 3: Write article and submission drafts**

Map evidence to all judging dimensions: real user problem, local workflow, adaptive loop, actual device probe, test evidence, Agent-tool screenshots, ModelScope Skill link, article link, and optional propagation link. Use explicit blanks only for links or measurements that require the user's later publication/hardware run, labeled `待实测填写` rather than pretending they exist.

- [ ] **Step 4: Run end-to-end smoke test**

Copy the demo course to a temporary directory, run `init`, `plan`, and `record`, then inspect that the first priority changes after the diagnostic result and no source outside the demo directory is referenced.

### Task 6: Forward-test and final verification

**Files:**
- Modify: `study-sprint-coach/evaluations/baseline.md`

**Interfaces:**
- Consumes: the completed Skill and the exact scenarios from Task 1.
- Produces: fresh-agent evidence that the Skill changes behavior and a complete local verification record.

- [ ] **Step 1: Run the three scenarios with the Skill**

Dispatch fresh agents with the Skill path and scenario only. Record whether each observable criterion passes, plus any new loophole.

- [ ] **Step 2: Refine only observed failures**

If a scenario fails, make the smallest guidance change, rerun the affected scenario, and preserve passing script behavior.

- [ ] **Step 3: Run complete verification**

Run:

```powershell
python -m unittest discover -s study-sprint-coach/tests -v
python C:/Users/chen/.codex/skills/.system/skill-creator/scripts/quick_validate.py study-sprint-coach
rg -n "TODO|TBD|PLACEHOLDER|example\.com|真实教材|真实真题" study-sprint-coach submission
```

Review `rg` hits manually; `待实测填写` is allowed only in the publication checklist/article for links, screenshots, model/device measurements, and traffic numbers that cannot exist before publication.

- [ ] **Step 4: Review requirements line by line**

Confirm the package contains code, documentation, tests, ModelScope-ready metadata, local-first behavior, evidence citations, closed-loop replanning, demo materials, article draft, and submission checklist.

