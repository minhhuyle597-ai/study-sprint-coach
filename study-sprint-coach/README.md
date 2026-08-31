# Study Sprint Coach｜学习冲刺教练

Study Sprint Coach 面向临近期末、认证或阶段验收的学习者：它把本地材料、截止日期、每日时间和诊断结果变成可追溯、不过载、会随测验变化的冲刺计划。区别于一次性的 PDF 摘要、题库或日程表，它为每个主题保留来源定位、显式显示容量与积压，并把答题结果写回状态后重新计算优先级。

## 包含内容

- `SKILL.md`：Agent 使用流程与边界。
- `references/output-contract.md`：回答、讲解、计划、测验和复盘的固定输出合约。
- `scripts/study_sprint.py`：标准库实现的初始化、排程、记录和原子写入。
- `scripts/openvino_probe.py`：如实报告本机 OpenVINO 可用性与设备。
- `examples/demo-course/`：明确标注为合成内容的可复现实例。
- `tests/` 与 `evaluations/`：行为测试及无 Skill 基线。

## 前置条件

- Python 3.10 或更高版本。
- 核心流程不需要第三方 Python 包。
- OpenVINO 为可选项；仅在本机已安装时，探测脚本才会读取 `Core().available_devices`。当前 Task 4 实测结果为 `ModuleNotFoundError: No module named 'openvino'`，因此本项目不声称发现了 CPU、GPU 或 NPU 设备，也不声称获得任何加速。

## 安装与 ModelScope 打包

将整个 `study-sprint-coach` 目录复制到 Agent 工具共用的 Skills 目录，例如 Windows 的 `%USERPROFILE%\.agents\skills\study-sprint-coach`，然后按所用 Agent 的 Skill 刷新方式重新加载。不要只复制 `SKILL.md`，因为脚本、引用、示例和测试共同构成可复现包。

发布到 ModelScope 时，以本目录为 Skill 包根目录；提交前保留 `SKILL.md`、`README.md`、`LICENSE`、`agents/`、`references/`、`scripts/`、`examples/`、`tests/` 和 `evaluations/`。发布动作及页面元数据需在用户自己的 ModelScope 账号中完成，本仓库不会自动上传材料。

## 可复现演示

在 `study-sprint-coach` 包根目录运行以下 PowerShell 命令。状态写入系统临时目录，不会修改已提交示例。

```powershell
$demoRoot = Join-Path ([System.IO.Path]::GetTempPath()) "study-sprint-coach-demo"
New-Item -ItemType Directory -Force -Path $demoRoot | Out-Null
$demoState = Join-Path $demoRoot "state.json"

python scripts/study_sprint.py init --materials examples/demo-course --deadline 2026-09-02 --minutes-per-day 60 --target-score 85 --state $demoState --as-of 2026-09-01
python scripts/study_sprint.py plan --state $demoState --topics examples/demo-course/topics.json --as-of 2026-09-01
python scripts/study_sprint.py record --state $demoState --results examples/demo-course/diagnostic-results.json --as-of 2026-09-02
python scripts/openvino_probe.py
```

初始两天容量为 120 分钟：先排导数应用，再排积分方法，极限以 30 分钟积压显示。记录合成诊断后，导数掌握度更新为 `0.6` 且剩余时间为 `0`；积分掌握度更新为 `0.35`，成为首个剩余计划主题。

## 数据与输出契约

- 状态字段、校验和原子写入以 [`scripts/study_sprint.py`](scripts/study_sprint.py) 中的 `initialize`、`validate_topics`、`validate_results` 和 `atomic_write` 为准。
- 主题输入示例见 [`examples/demo-course/topics.json`](examples/demo-course/topics.json)。
- 结果输入示例见 [`examples/demo-course/diagnostic-results.json`](examples/demo-course/diagnostic-results.json)。
- 学习者可见输出格式见 [`references/output-contract.md`](references/output-contract.md)。

Agent 从 PDF、PPT 或其他材料提取证据时，必须把页码、幻灯片号、Markdown 标题或题号一路保留到主题矩阵、计划、讲解与复盘中，例如“`lecture.pdf，第 12 页`”“`slides.pptx，第 18 张`”“`lecture-notes.md，标题：导数应用`”“`past-exam.md，2024模拟卷 Q2`”。如果本地解析器不可用，应标记为待提取，不得根据文件名补写结论。

## 隐私与学术诚信

材料默认留在本机；任何云上传或云模型调用都需用户明确同意。不要把私人讲义、学生信息、受限试卷或许可证不明的内容放入公开演示包。该 Skill 可用于备考与自测，不协助正在进行或受监考的考试，也不把生成内容伪装成教师原文。

## 当前限制

- 没有内置 OCR。
- 没有模型推理或性能基准。
- 不自动预测考试概率。
- 二进制文档需要 Agent 或本机已有的解析器；解析失败会阻止依赖该材料的结论。

OpenVINO 探测所依据的官方资料：

- [`Core().available_devices` 设备查询](https://docs.openvino.ai/nightly/openvino-workflow/running-inference/inference-devices-and-modes/query-device-properties.html)
- [OpenVINO 安装与 `Core()` 验证](https://docs.openvino.ai/nightly/get-started/install-openvino/install-openvino-pip.html)

## 测试

在仓库根目录运行 Task 4 报告使用的同一命令：

```powershell
python -m unittest discover -s study-sprint-coach/tests -v
```

Task 4 报告记录的当前基线为 10 个测试全部通过；文档变更后应再次运行上述命令，以最新输出为准。
