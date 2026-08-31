# 从“一次性总结”到可复现闭环：用 Study Sprint Coach 做证据驱动的学习冲刺

## 1. 先说结论：学生缺的不是更多内容，而是可验证的下一步

临近期末时，学生通常同时面对材料分散、时间不足和自我判断失真。普通摘要能压缩内容，题库能增加练习，日程表能分配时间，但三者往往没有共同状态：答错一道题之后，计划不会自动解释“为什么下一小时应该改变”。Study Sprint Coach 的最小答案是一个本地闭环：保留证据定位，按容量排程，记录测验结果，再用同一组确定性规则重排。

本项目不声称预测真实考题，也不声称提高了尚未测量的分数或速度。它提供的是可复现机制：任何人都能用合成材料运行同一组命令，检查初始优先级、积压和测验后的计划变化。

## 2. 竞赛对齐：为什么“PDF 总结 + 测验 + 计划”仍不够

Production AI Skills 大赛强调真实生产力场景、Agent 工具落地、工程实现与 Intel AI PC 讨论。学习冲刺符合真实场景，但只有生成摘要、出题和列计划还不够：来源可能丢失，计划可能超额，测验可能没有进入下一轮状态，也可能把生成例题误写成教师材料。

因此本 Skill 把差异点收敛为四个可检查约束：每个计划主题有定位；时间容量不可透支；超出部分必须进入积压；测验先更新掌握度，再重算优先级。AI PC 价值体现在材料默认本地处理和可探测的本机运行环境，而不是在没有设备证据时宣称 GPU/NPU 加速。

## 3. 无 Skill 基线：模型会推理，但不会自动守住契约

项目在 [`evaluations/baseline.md`](../study-sprint-coach/evaluations/baseline.md) 记录了三个新上下文基线：容量计划、公式讲解和自适应重排。

- 容量计划能算出两天共 180 分钟，也会优先照顾薄弱项，但没有保留文件/题号定位，没有显式积压，验收标准偏定性。
- 公式讲解能给出几何推导、类比和例题，却丢失唯一课件定位，也没有标注例题是生成示例。
- 自适应重排能算出导数 `0.60`、积分 `0.35` 并调整顺序，但没有持久状态，分配也缺少来源和机器可检查的优先级。

这些观察支持一个克制的设计结论：无需再造聊天平台或向量数据库，只需补上定位、固定输出、显式积压、可测验阈值和持久闭环。

## 4. 架构：一份状态、两个脚本、一个闭环

核心数据流如下：

```text
本地材料 + 截止日期 + 每日分钟数
  -> 来源清单与 SHA-256
  -> 有证据的主题矩阵
  -> 优先级与容量排程
  -> 学习/测验结果
  -> 掌握度更新
  -> 重新排程与显式积压
```

[`scripts/study_sprint.py`](../study-sprint-coach/scripts/study_sprint.py) 负责 `init`、`plan` 和 `record`；[`scripts/openvino_probe.py`](../study-sprint-coach/scripts/openvino_probe.py) 只负责如实报告本机 OpenVINO 环境。学习者回答则遵循 [`references/output-contract.md`](../study-sprint-coach/references/output-contract.md)。没有数据库、服务端或必装第三方包。

## 5. 证据矩阵与优先级公式

每个主题至少包含：稳定 ID、名称、考试相关度、当前掌握度、既有观测数、估计得分增益、所需分钟、证据定位和可判定掌握标准。没有证据的主题不进入计划。

主题 `i` 的优先级为：

```text
priority_i = relevance_i * (1 - mastery_i) * score_gain_i / minutes_i
```

其中 `relevance_i` 是 0 到 1 的材料相关度；`mastery_i` 是 0 到 1 的当前掌握度；`score_gain_i` 是该主题的估计得分增益；`minutes_i` 是预计学习分钟数。公式偏向“材料更相关、当前更薄弱、潜在增益更高、单位时间成本更低”的主题。它是透明排序规则，不是考试概率模型。

例如合成导数主题的数值为 `1.0 × (1 - 0.2) × 25 ÷ 60 = 0.3333…`，高于合成积分主题的 `0.9 × (1 - 0.5) × 30 ÷ 60 = 0.225`，因此先排导数。证据同时保留为 `lecture-notes.md，标题：导数应用` 和 `past-exam.md，2024模拟卷 Q2`。

## 6. 确定性状态、原子写入与隐私

初始化会按相对路径排序材料，并记录文件类型、字节数、SHA-256 与提取状态。主题校验、结果校验和计划计算均在替换状态文件前完成。写入时先在目标目录创建同级临时文件，刷新并 `fsync`，最后用 `os.replace` 原子替换；输入无效时，旧状态字节保持不变。

材料默认留在本机。云上传或云模型调用必须取得用户明确同意；受限试卷、私人讲义、学生信息和许可证不明内容不得进入公开演示包。二进制文件若没有可用本地解析器，会显示 `needs_extraction`，而不是根据文件名猜测内容。

## 7. 固定输出合约：公式讲透，冲突并列

普通回答固定包含结论、证据、行动和置信度。公式讲解额外包含一句记忆、图示或类比、符号与量纲、关系/推导、例题、常见误区、自测和证据。计划表固定包含时间、任务、来源、产出和验收检查；测验提交前隐藏答案，提交后才评分、归因并重排。

公式解释不能只给结论。例如讲 `priority_i` 时，应说明每个符号的范围与单位，指出除以分钟数代表单位时间收益，并用一组数值复算。来源冲突也不能静默选择：若 `course-outline.md，评分结构` 写积分 40%，而教师勘误 `notice.md，标题：期末范围修订` 写积分 30%，输出应并列两条原主张，说明受影响主题，将结论标为低置信度，并请求权威版本确认。

## 8. 合成端到端演示：测验前后计划如何改变

下面的虚构大学微积分材料是 Study Sprint Coach 原创合成演示内容，随本包按 MIT License 分发；不是真实教师材料或历年试卷。在包根目录运行：

```powershell
$demoRoot = Join-Path ([System.IO.Path]::GetTempPath()) "study-sprint-coach-demo"
New-Item -ItemType Directory -Force -Path $demoRoot | Out-Null
$demoState = Join-Path $demoRoot "state.json"
python scripts/study_sprint.py init --materials examples/demo-course --deadline 2026-09-02 --minutes-per-day 60 --target-score 85 --state $demoState --as-of 2026-09-01
python scripts/study_sprint.py plan --state $demoState --topics examples/demo-course/topics.json --as-of 2026-09-01
python scripts/study_sprint.py record --state $demoState --results examples/demo-course/diagnostic-results.json --as-of 2026-09-02
```

初始容量为两天各 60 分钟：导数和积分分别占 60 分钟，极限留下 30 分钟积压。合成诊断记录导数 `5/5`、用时 60 分钟，积分 `1/5`、用时 0 分钟。更新公式为：

```text
new_mastery = (old_mastery * old_attempts + correct) / (old_attempts + total)
```

导数更新为 `(0.2×5+5)/(5+5)=0.6`，剩余分钟归零；积分更新为 `(0.5×5+1)/(5+5)=0.35`。在 2026-09-02 重排后，积分成为首个剩余计划主题，极限仍是 30 分钟积压。这证明的是规则闭环，不是学习效果因果结论。

## 9. TDD 证据：从失败到最小通过

Task 3 报告记录了 `init`、`plan`、`record` 的 RED-GREEN 过程：对应阶段先出现预期失败，再分别达到 2、4、6 个测试通过；非有限数修复先复现 `NaN` 和 `Infinity` 被错误接受，再以聚焦回归通过，最终完整套件为 7 个测试通过。Task 4 为 OpenVINO 探测新增 3 个测试，先因脚本缺失而失败。最终统一修复新增来源、状态、日期与探测子进程回归，当前完整套件为 15 个测试通过（`Ran 15 tests`，`OK`）。历史 Task 报告保留各阶段当时的测试数。

从仓库根目录复现：

```powershell
python -m unittest discover -s study-sprint-coach/tests -v
```

## 10. OpenVINO 实测：没有安装就不写“已加速”

Task 4 在当前本机运行 `python scripts/openvino_probe.py` 的实际结果是：

```json
{"available": false, "error": "ModuleNotFoundError: No module named 'openvino'", "next_action": "Install or repair the local OpenVINO runtime, then rerun this probe. Do not claim CPU/GPU/NPU acceleration until devices are listed.", "source": "https://docs.openvino.ai/nightly/get-started/install-openvino/install-openvino-pip.html"}
```

因此设备发现没有运行，本项目不声称 CPU、GPU 或 NPU 加速，也没有模型时延数据。探测 API 依据 OpenVINO 官方的 [`Core().available_devices` 设备查询文档](https://docs.openvino.ai/nightly/openvino-workflow/running-inference/inference-devices-and-modes/query-device-properties.html)，安装验证依据[官方 pip 安装说明](https://docs.openvino.ai/nightly/get-started/install-openvino/install-openvino-pip.html)。

待实测填写：本地模型名称、模型版本、目标设备、输入规模、预热次数、测量轮数与时延统计。

## 11. 在 Qoder、WorkBuddy 或 TRAE Work 中复现

1. 将完整 `study-sprint-coach` 目录放入所用 Agent 的 Skills 目录并刷新 Skill。
2. 新建干净会话，要求 Agent 使用 Study Sprint Coach 读取 `examples/demo-course`，截止日期设为 `2026-09-02`，每日 60 分钟，目标 85 分。
3. 在内置终端依次运行第 8 节的 `init`、`plan`、`record` 命令。
4. 对照终端 JSON 检查初始首主题、30 分钟积压、更新后掌握度与首个剩余主题。
5. 运行完整单元测试和 OpenVINO 探测，把命令、输出与 Agent 最终回答一起录制。

待实测填写：最终采用的 Agent 工具名称与精确版本。

截图/录屏镜头清单：Skill 目录与加载状态；合成材料声明；初始化来源清单；初始计划与 `limits` 30 分钟积压；`record` 前后掌握度；更新后 `integrals` 位于首位；15 个测试的最新完整输出；OpenVINO 实际探测输出；隐私与学术诚信提示；ModelScope Skill 页面和 Learn 文章页面。

待实测填写：上述截图文件、录屏文件及其公开链接。

## 12. 商业与生产力价值：从期末复习受控扩展

对学生，价值是把“我该学什么”转为带来源、时间和通过阈值的下一步；对课程助教或培训负责人，价值是获得可审查的计划与复盘记录，而不是不可追踪的自由文本。核心状态是普通 JSON，规则是确定性脚本，便于版本管理、审计和嵌入既有 Agent 工作流。

同一闭环可受控扩展到认证备考、员工 onboarding、项目 ramp-up 和演示准备：把“考试相关度”解释为任务相关度，把得分增益换成业务影响估计，仍要求来源定位、容量上限和可判定验收。扩展前需要针对新领域重新定义证据与掌握标准，不能直接把考试公式当作已验证的业务决策模型。

## 13. 限制与下一步测量

当前版本没有内置 OCR、模型推理、模型基准或自动考试概率预测；PDF、PPT、DOCX、XLSX 等二进制材料必须依赖可用的本地解析器。OpenVINO 当前未安装，因此没有设备列表或加速数据。

下一步按证据推进：先在指定 Agent 工具完成录屏复现；再选定一个公开或授权数据集，记录计划完成率、验收题通过率和人工核对定位准确率；只有在本机成功列出设备并固定模型、输入和测量方法后，才比较 CPU/GPU/NPU 或 AUTO 的时延与资源占用。

## 14. 仓库、Skill 与竞赛标签

- 仓库内 Skill 包：[`study-sprint-coach/`](../study-sprint-coach/)
- 待实测填写：ModelScope Skill URL。
- 待实测填写：ModelScope Learn 文章 URL。
- Skill 发布标签：`AI PC`。
- Learn 专题：`Intel AI PC`。
- 传播标签：`#英特尔 #openvino #魔搭 #agentic #skills`，并按活动要求关联 OpenVINO 中文社区与魔搭 ModelScope 社区。
- 待实测填写：小红书或其他社交平台作品 URL 与截至统计时点的阅读量/流量证据。
