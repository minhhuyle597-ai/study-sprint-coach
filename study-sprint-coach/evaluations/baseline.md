# Baseline evaluation without Study Sprint Coach

Date: 2026-08-31

Method: three fresh-context agents received only the corresponding `query` from `scenarios.json`. They did not receive the proposed Skill, formula, output contract, or expected-behavior list.

## Scenario 1: capacity-plan

Observed behavior:

- Correctly recognized: `两天共 180 分钟`.
- Produced exactly 90 minutes per day and chose derivatives as the primary weakness.
- Said `极限不单独占时间` and reduced coverage rather than scheduling all 360 estimated minutes.
- Used generic activity names such as `分三类各做题` and `限时做一套导数大题`.

Failures against the evaluation:

- No file/page/question locators appeared in any time block, despite the supplied syllabus and past-exam evidence.
- It did not expose a backlog or state explicitly which requested full-review work was excluded.
- The table mixed day-total rows and subtask rows, making the fixed plan shape ambiguous.
- Completion checks were qualitative (`会设步骤、少算错`) rather than consistently measurable.

Baseline lesson: ordinary reasoning handles arithmetic and broad prioritization well. The Skill should not reteach those capabilities; it must add traceable evidence, explicit overflow, and a stable acceptance contract.

## Scenario 2: formula-explanation

Observed behavior:

- Began with a clear one-sentence meaning.
- Explained gradient geometrically and derived why the two gradients are parallel.
- Included an ASCII diagram, a mountain-path analogy, and a complete unit-circle example.

Verbatim strengths:

- `约束 g(x,y)=0 把你限制在一条曲线上，只能沿曲线走。`
- `两个都垂直于同一条曲线，必然平行或反平行。`

Failures against the evaluation:

- The answer dropped the supplied locator `[课程PPT，第18页]` instead of carrying it into the evidence block.
- It omitted common traps and a self-test.
- The constructed unit-circle example was not labeled as an agent-created illustration distinct from supplied material.
- It had no confidence or unsupported-claim state.

Baseline lesson: explanation quality can already be high. The Skill's value is the evidence boundary and reliable teaching slots, not longer prose.

## Scenario 3: adaptive-replan

Observed behavior:

- Correctly updated derivative mastery to `0.60` and integral mastery to `0.35`.
- Correctly reversed priority toward integration.
- Kept the new plan within 60 minutes: 45 minutes integration, 15 minutes derivatives.

Verbatim strength:

- `先不继续按“导数后积分”的原顺序；积分现在是主要短板。`

Failures against the evaluation:

- The answer calculated one update but created no durable state for the next cycle.
- The 45/15 allocation had no source locator, score-gain estimate, or machine-checkable priority value.
- The integration completion criterion (`做 3–5 题并订正`) did not state a passing threshold.
- It did not report what would happen if the 60-minute capacity could not include both topics.

Baseline lesson: a generic model can replan once when all state is in the prompt. The Skill must make the loop persistent, reproducible, evidence-backed, and capacity-safe across sessions.

## Minimal guidance justified by the baseline

The Skill needs only the following non-obvious additions:

1. Preserve source locators through analysis, planning, teaching, and review.
2. Use one fixed positive output recipe per response mode.
3. Surface capacity and backlog explicitly.
4. Require measurable mastery checks and delayed quiz answers.
5. Store state and update mastery before recalculating priority.
6. Label supplied facts, derived reasoning, and generated teaching examples separately.

## Forward evaluation with Study Sprint Coach

Date: 2026-08-31

Method: three fresh agents each ran one scenario after reading local `SKILL.md` and its directly referenced `references/output-contract.md`; they were prohibited from reading `evaluations/baseline.md`. Direct local loading simulated an installed Skill because the subagent attachment mechanism reported that the unpublished local Skill was not exposed. Failed attachment attempts were excluded. A separate fresh agent reran `adaptive-replan` after the fix.

- `capacity-plan` passed 4/4: respected the 180-minute cap, linked priorities to evidence, exposed an explicit backlog, and used measurable completion checks.
- `formula-explanation` passed 4/4: preserved the locator; explained symbols, geometry, and derivation; labeled the generated example; and included traps plus a delayed-answer self-test.
- The initial `adaptive-replan` forward run computed `0.60`/`0.35`, reprioritized the topics, and fit the plan into 60 minutes, but invented demo locators and therefore failed the source-integrity guardrail.
- After commit `b496c79`, a fresh `adaptive-replan` rerun passed 4/4: it explicitly used `未提供材料定位`, kept the plan within 60 minutes, and supplied measurable thresholds.

These observations support only the runs described above; no claim is made about unobserved performance.
