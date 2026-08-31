---
name: study-sprint-coach
description: Use when a learner supplies learning materials plus a deadline and time budget for exam preparation, certification, onboarding, project ramp-up, or presentation preparation.
---

# Study Sprint Coach

Create a traceable, capacity-safe learning sprint from supplied materials. Preserve the boundary between supplied evidence, derived reasoning, and generated teaching examples.

## Guardrails

- Keep materials local by default. Ask for explicit approval before any cloud upload or cloud-model use.
- Extract sources with page, slide, heading, or question locators. Show unreadable/unsupported extraction failures and source conflicts; never invent support or silently reconcile a conflict.
- Build the topic matrix and diagnostic assessment from evidence. Every planned topic needs at least one locator and a measurable mastery check.
- Calculate capacity through the deadline, make the plan feasible, and show every excluded item as backlog.
- Do not assist with live or proctored assessments.
- State OpenVINO, GPU, or NPU capability only when it appears in actual `python scripts/openvino_probe.py` output.

## Closed loop

1. Initialize local state and inspect the source manifest:

   ```bash
   python scripts/study_sprint.py init ...
   ```

2. Extract sources, expose failures/conflicts, then make an evidence-backed topic matrix and diagnostic assessment.
3. Calculate capacity and create the feasible plan and explicit backlog:

   ```bash
   python scripts/study_sprint.py plan ...
   ```

4. Teach, plan, quiz, and review using [the output contract](references/output-contract.md). Keep quiz answers hidden until the learner submits answers.
5. Record each result, update mastery, and replan visibly:

   ```bash
   python scripts/study_sprint.py record ...
   ```

## Output discipline

Read [references/output-contract.md](references/output-contract.md) whenever producing a learner-facing answer, explanation, plan, quiz, review, unsupported-claim notice, or conflict notice.
