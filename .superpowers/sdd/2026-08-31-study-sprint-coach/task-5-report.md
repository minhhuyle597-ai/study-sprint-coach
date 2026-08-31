# Task 5 report: reproducible demo and submission documentation

## Status

Complete. The bounded documentation/demo deliverables were created without publishing, installing packages, or modifying the two competition PNG files.

## Files changed

- `study-sprint-coach/examples/demo-course/course-outline.md`
- `study-sprint-coach/examples/demo-course/lecture-notes.md`
- `study-sprint-coach/examples/demo-course/past-exam.md`
- `study-sprint-coach/examples/demo-course/topics.json`
- `study-sprint-coach/examples/demo-course/diagnostic-results.json`
- `study-sprint-coach/README.md`
- `study-sprint-coach/LICENSE`
- `submission/technical-article-draft.md`
- `submission/checklist.md`
- `.superpowers/sdd/2026-08-31-study-sprint-coach/task-5-report.md`

## Smoke test

The three required commands ran in a newly created system temporary directory. `init` exited 0 with no stdout.

Exact `plan` stdout:

```json
{"as_of": "2026-09-01", "schedule": [{"date": "2026-09-01", "topic_id": "derivatives", "topic_name": "导数应用", "minutes": 60, "evidence": [{"source": "lecture-notes.md", "locator": "标题：导数应用"}, {"source": "past-exam.md", "locator": "2024模拟卷 Q2"}], "mastery_check": "5题至少4题正确"}, {"date": "2026-09-02", "topic_id": "integrals", "topic_name": "积分方法", "minutes": 60, "evidence": [{"source": "lecture-notes.md", "locator": "标题：积分方法"}, {"source": "past-exam.md", "locator": "2024模拟卷 Q3"}], "mastery_check": "5题至少4题正确"}], "backlog": [{"topic_id": "limits", "topic_name": "极限", "remaining_minutes": 30}]}
```

Exact `record` stdout:

```json
{"version": 1, "mode": "exam", "deadline": "2026-09-02", "minutes_per_day": 60, "target_score": 85.0, "sources": [{"path": "course-outline.md", "kind": "md", "size": 765, "sha256": "1ef88f158de174f003dbd2db355aaca441e04526343d46818b2035e8bf3052e6", "status": "ready"}, {"path": "diagnostic-results.json", "kind": "json", "size": 297, "sha256": "dc31e255bc30b835af7a97c1033e2a48b89ae2083be1f6432830a5c63bd70c2e", "status": "ready"}, {"path": "lecture-notes.md", "kind": "md", "size": 784, "sha256": "3314b6bf4b2b19a4634d8173350ab0b5fe8c6fa9901180dc55d580dcc7674606", "status": "ready"}, {"path": "past-exam.md", "kind": "md", "size": 636, "sha256": "6406cd27b48f831e71ecab04fdc9609f381379d64c68955578de51580b419f6a", "status": "ready"}, {"path": "topics.json", "kind": "json", "size": 1523, "sha256": "8d956566f5700de214a752baab270e8f6afc5f232b06b0a5d8b0f254144c6f24", "status": "ready"}], "topics": [{"id": "integrals", "name": "积分方法", "relevance": 0.9, "mastery": 0.35, "mastery_attempts": 10, "score_gain": 30.0, "minutes": 60, "remaining_minutes": 60, "evidence": [{"source": "lecture-notes.md", "locator": "标题：积分方法"}, {"source": "past-exam.md", "locator": "2024模拟卷 Q3"}], "mastery_check": "5题至少4题正确", "content_notice": "合成、CC0/类公版演示内容；不是真实教师材料或历年试卷。", "priority": 0.29250000000000004}, {"id": "derivatives", "name": "导数应用", "relevance": 1.0, "mastery": 0.6, "mastery_attempts": 10, "score_gain": 25.0, "minutes": 60, "remaining_minutes": 0, "evidence": [{"source": "lecture-notes.md", "locator": "标题：导数应用"}, {"source": "past-exam.md", "locator": "2024模拟卷 Q2"}], "mastery_check": "5题至少4题正确", "content_notice": "合成、CC0/类公版演示内容；不是真实教师材料或历年试卷。", "priority": 0.16666666666666666}, {"id": "limits", "name": "极限", "relevance": 0.6, "mastery": 0.8, "mastery_attempts": 5, "score_gain": 15.0, "minutes": 30, "remaining_minutes": 30, "evidence": [{"source": "lecture-notes.md", "locator": "标题：极限"}, {"source": "past-exam.md", "locator": "2024模拟卷 Q1"}], "mastery_check": "3题至少2题正确", "content_notice": "合成、CC0/类公版演示内容；不是真实教师材料或历年试卷。", "priority": 0.059999999999999984}], "sessions": [{"_notice": "合成、CC0/类公版演示内容；不是真实教师材料或历年试卷。", "date": "2026-09-01", "items": [{"topic_id": "derivatives", "correct": 5, "total": 5, "minutes_spent": 60}, {"topic_id": "integrals", "correct": 1, "total": 5, "minutes_spent": 0}]}], "plan": {"as_of": "2026-09-02", "schedule": [{"date": "2026-09-02", "topic_id": "integrals", "topic_name": "积分方法", "minutes": 60, "evidence": [{"source": "lecture-notes.md", "locator": "标题：积分方法"}, {"source": "past-exam.md", "locator": "2024模拟卷 Q3"}], "mastery_check": "5题至少4题正确"}], "backlog": [{"topic_id": "limits", "topic_name": "极限", "remaining_minutes": 30}]}}
```

Assertions: 7/7 passed.

- All three commands exited 0.
- Initial first scheduled topic: `derivatives`.
- Initial backlog: `limits`, 30 minutes.
- Updated derivative mastery: `0.6`.
- Updated integration mastery: `0.35`.
- Updated derivative remaining minutes: `0`.
- Updated first scheduled topic: `integrals`.

## Full test summary

Command: `python -m unittest discover -s study-sprint-coach/tests -v`

```text
Ran 10 tests in 2.666s

OK
```

Exit code: 0. All ten named tests reported `ok`.

## Form-copy checks

- Recommended title: `证据驱动的学习冲刺教练`.
- Title length: 11 characters; required range: 10–30.
- Recommended summary length: 299 non-whitespace characters and 222 Han characters; both counting methods are within 200–300.
- The summary makes no model-speed, device-acceleration, score-improvement, or traffic claim.

## Placeholder and integrity scans

- Prohibited placeholder families: 0 matches.
- Allowed publication-only marker entries: 14 lines, limited to ModelScope Skill/article URLs, screenshots/recording, exact Agent tool/version, local model/device/latency, social URL, and traffic evidence.
- Synthetic-content notice: 5/5 demo files contain the synthetic, CC0/public-domain-like, non-real-material statement.
- Local Markdown link check: all repository-relative targets exist.
- Credential/private-path signature scan: 0 matches.
- `任务要求.png` SHA-256 remained `8088C28F912EFA43B6D8F22B2F6296B1699DBCF8AC3549C73BCBCD199ED03AA6`.
- `提交表单.png` SHA-256 remained `DEEABD39327F697519DB9EA6A2A10C56F0F87D821A5E63A1591F076961683A43`.

## Self-review

- Rechecked every topic value, attempt count, score gain, duration, evidence locator, and mastery check against the brief.
- Rechecked diagnostic date and both result items exactly.
- README commands use the package root and a temporary state path; schemas link to implementation/examples instead of duplicating source.
- README and article state only the Task 4 probe result: OpenVINO is unavailable with `ModuleNotFoundError`; no device or acceleration is claimed.
- Technical article covers all fourteen required sections, separates observed test/probe evidence from interpretation, and includes only official OpenVINO source URLs already recorded in Task 4.
- Submission checklist includes the required Skill/article artifacts, all form fields shown in the supplied evidence, propagation evidence, and final private-material/license checks.
- Standard MIT License uses year 2026 and holder `Study Sprint Coach contributors`.
- No package was installed and nothing was published.

## Concerns

- OpenVINO remains unavailable on this machine, so device discovery, model inference, and latency benchmarking remain unmeasured.
- Publication URLs, Agent screenshots/recording and exact version, local model measurements, and propagation metrics require the user's later account/hardware runs and remain explicitly labeled.
