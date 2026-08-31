# Study Sprint Coach Design

## Goal

Build a ModelScope-compatible local-first Skill that turns course materials, a deadline, a daily time budget, and diagnostic results into an evidence-backed study plan that changes after each assessment.

The first and strongest scenario is university final-exam preparation. Certification, onboarding, project ramp-up, and presentation preparation reuse the same deadline-driven loop but are not required for the first release.

## User outcome

At every point the user can answer five questions:

1. What should I study next?
2. Why is it worth studying now?
3. Which source supports that decision?
4. What observable result counts as mastery?
5. How does a wrong answer change the remaining plan?

## Non-goals

- A general chat application or full web platform.
- A vector database, multi-agent framework, account system, or cloud service.
- Uploading private course materials by default.
- Predicting exam content without evidence from supplied materials.
- Helping with a live or proctored assessment.

## Core workflow

```text
materials + deadline + minutes/day + target
  -> source manifest and extraction check
  -> evidence-backed topic matrix
  -> diagnostic assessment
  -> priority and capacity calculation
  -> daily plan with completion criteria
  -> teaching and practice
  -> result recording
  -> mastery update and replanning
  -> final readiness report
```

The loop persists in one JSON state file. No database is needed.

## Competition deliverable

The repository contains one publishable Skill package with:

- `SKILL.md` and optional UI metadata;
- deterministic local scripts;
- a fixed output contract;
- synthetic demonstration materials;
- executable tests and behavioral evaluations;
- installation and reproduction documentation;
- a technical article draft and submission checklist.

The Skill must be demonstrated in at least one production Agent tool. OpenVINO support is reported from the actual local environment; the documentation never claims GPU or NPU acceleration without probe output.

## Package structure

```text
study-sprint-coach/
|-- SKILL.md
|-- README.md
|-- LICENSE
|-- agents/openai.yaml
|-- references/output-contract.md
|-- scripts/study_sprint.py
|-- scripts/openvino_probe.py
|-- tests/test_scripts.py
|-- evaluations/scenarios.json
|-- evaluations/baseline.md
`-- examples/demo-course/
    |-- course-outline.md
    |-- lecture-notes.md
    |-- past-exam.md
    |-- topics.json
    `-- diagnostic-results.json
```

Two scripts are sufficient: one owns study state and planning; one reports the real OpenVINO environment.

## State model

`study_state.json` is versioned and contains:

```json
{
  "version": 1,
  "mode": "exam",
  "deadline": "2026-09-07",
  "minutes_per_day": 120,
  "target_score": 85,
  "sources": [],
  "topics": [],
  "sessions": [],
  "plan": []
}
```

Each source records its relative path, file type, byte size, SHA-256 digest, and extraction status. Binary formats may require an Agent-native parser or local MarkItDown conversion; extraction failure is visible and blocks claims based on that source.

Each topic contains:

- stable ID and name;
- exam relevance in `[0, 1]`;
- current mastery in `[0, 1]` and the number of observations supporting it;
- estimated score gain and study minutes;
- at least one evidence locator such as file plus page, slide, heading, or question number;
- a concrete mastery check.

Topics without evidence are rejected from the priority plan.

## Priority and schedule

For topic `i`:

```text
priority_i = relevance_i * (1 - mastery_i) * score_gain_i / minutes_i
```

The scheduler sorts by descending priority and fills available daily minutes from the planning date through the deadline. It never silently overbooks. Topics that do not fit are returned as a visible backlog.

Assessment results update mastery using the previous observation count:

```text
new_mastery = (old_mastery * old_attempts + correct) / (old_attempts + total)
```

The scheduler then recalculates priorities. This is the minimum closed loop that proves wrong answers affect future work.

## Output contract

Ordinary answers use four blocks: conclusion, evidence, action, confidence.

Concept explanations add a diagram or analogy when useful. Formula explanations always include symbols, units or dimensions when applicable, relationships or derivation, one worked example, common traps, and a self-test.

Plans use a table with time, task, source, output, and acceptance check. Quizzes hide answers until submission. Reviews report score, cause of error, remediation, and the resulting plan change.

If evidence is absent, the output states that the supplied materials do not support the claim. Conflicting sources are shown side by side rather than silently resolved.

## Local-first and OpenVINO

- Course materials remain local by default.
- Network or cloud model use requires explicit user approval.
- `openvino_probe.py` reports package availability, version, and detected devices from the installed OpenVINO runtime.
- Device choice remains configurable (`AUTO`, `CPU`, `GPU`, or `NPU`) in later model integration; the first release records capability and does not pretend to benchmark unavailable hardware.

## Error handling

- Missing or unreadable materials: report each file and stop evidence-dependent planning.
- Unsupported binary format: mark `needs_extraction` and provide the exact next action.
- Invalid topic values or missing evidence: reject with field-specific errors.
- Deadline before the planning date or non-positive time budget: reject before state creation.
- Insufficient capacity: create a feasible plan plus explicit backlog.
- Malformed assessment results or unknown topic IDs: reject without changing state.

State writes are atomic: write a sibling temporary file and replace the destination only after successful serialization.

## Quality gates

1. Run three baseline scenarios without the Skill and record observable failures.
2. Write behavior tests before each script feature and observe the expected failure.
3. Implement only enough guidance and code to pass those tests.
4. Run the same scenarios with the Skill in a fresh agent context.
5. Run ModelScope/Codex structural validation, Python tests, CLI smoke tests, link/path checks, and a package scan for placeholders and private material.

## Acceptance criteria

- A synthetic course folder initializes a local state with stable source digests.
- An evidence-backed topic file produces a feasible plan and explicit backlog.
- A diagnostic result changes mastery and the next priority order.
- Invalid inputs do not corrupt an existing state file.
- The output contract produces concise cited answers, detailed formula treatment, hidden quiz answers, and visible plan changes.
- The Skill package validates and a fresh agent completes all three evaluation scenarios.
- Documentation explains installation, reproduction, privacy, limitations, and the exact competition submission artifacts.

