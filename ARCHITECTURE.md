# EvoOntology 架构设计

## 1. 背景与结论

产品化后的 `evo` 包包含大量机械层（六命令 CLI、workspace、replay、trajectory、evaluate）。
这些本应由 evolve skill 的智能分析承担，而非确定性 Python 代码。精简后：

**产品最终形态 = 一个运行时（evo 四件套）+ 一个 validate 脚本 + 两个 skill 命令，无 CLI。**

- 运行时：`evo/mcp_server.py`，由 MCP client 读 `mcp.json` 自动 spawn，无 `serve` 命令。
- 校验：`plugin/scripts/validate.py`，只做引用完整性 + 可加载。
- 触发指令：`/evo-build`（构建 semantic_v0）、`/evo-evolve`（触发进化）。

智能分析全在 skill，Python 只做「运行时 + 最小确定性校验」。

## 2. 产品形态

产品由三部分组成：plugin（指令层）、evo（运行时）、workspace（版本化存储）。

```
plugin/（标准自包含目录）
  commands/evo-build.md          /evo-build（构建 semantic_v0）
  commands/evo-evolve.md         /evo-evolve（触发进化）
  skills/                        build / evolve 两个 skill（从上游移入，内容不动）
  docs/versioning.md             版本命名与切换约定
  docs/evaluation-protocol.md    评估协议（绝对评分 vs 相对比较 + LLM Judge）
  docs/trajectory-format.md      轨迹格式规范
  scripts/validate.py            引用完整性 + 可加载校验
  mcp.json                       Data Agent 接入语义层的 MCP 配置
  config.template.yaml           config.yaml 模板（用户复制填写，见 §4）

evo/（运行时四件套）
  models.py      5 类记录 dataclass（Term / Mapping / Relation / Constraint / Evidence）
  store.py       SemanticStore：active.json -> versions/<v>/ 下 5 个 JSON
  runtime.py     SemanticLayer：manifest / browse / resolve
  mcp_server.py  2-tool MCP server + session-manifest 资源

workspace（<root>/，语义层版本化存储）
  active.json      当前激活版本指针
  config.yaml      集中配置（见 §4）
  versions/        所有版本（正式 semantic_vN + 候选 vN-cK），每版本 5 个 JSON
  trajectories/    任务轨迹 JSONL（进化诊断输入）
  evolution/       进化记录（每轮问题地图、归因、gate 决策、知识更新）
```

三个 benchmark 的 `semantic_layer/` 目录天然就是 workspace（已有 `active.json` + `versions/`），
可直接作为 `<root>` 使用。workspace 不需要 `candidates/`、`evaluations/` 独立目录——候选用
`vN-cK` 命名直接放 `versions/`，评估结果与进化记录统一归 `evolution/`。轨迹由 Data Agent 运行时（benchmark adapter 侧）在每次任务结束时追加到 `trajectories/`，非 evo 运行时职责；`evolution/` 由 evolve skill 每轮进化结束时写入。

## 3. 触发指令、版本约定与自动触发

init 与 evolve 都是**触发指令**，不是 Python 确定性操作；真正的构建 / 进化由 agent 按
skill 执行。

| 指令 | 语义 | 执行者 |
| --- | --- | --- |
| `/evo-build` | 构建 semantic_v0：读数据、探索 schema、生成 5 类记录 | agent 按 build skill |
| `/evo-evolve` | 触发进化：诊断→归因→补丁→Parent/Candidate gate→落地 | agent 按 evolve skill |

### 版本命名与切换（写在 plugin/docs/versioning.md，不改 skill）

| 类型 | 命名 | 示例 |
| --- | --- | --- |
| 正式版本 | `semantic_vN`（N 单调递增） | `semantic_v0` 初始、`semantic_v1` 第 1 次 accept |
| 候选 | `vN-cK`（关联源版本 + 序号） | `v0-c1` = 从 v0 进化的第 1 个候选 |

accept 映射：`vN-cK` → `semantic_vN+1`。「切换版本」是 evolve skill 的操作步骤（改
`active.json` 指针），不设独立命令。运行时 `store.py` 与命名约定无关：只读 version 字段并
加载 `versions/<name>/`，不校验命名格式。

### 自动触发（阈值可配 + 提示 due）

系统不无人值守自动进化，只「检测 + 提醒」，由人触发：

```
累计新增轨迹数 >= evolution.trigger.min_new_trajectories
        ↓
判定 evolution due（该进化了）——由 agent 在会话中 / evolve 前检查，或脚本查询
        ↓
用户（或脚本）触发 /evo-evolve
        ↓
进化完成后重新计数
```

无人值守全自动需要常驻后台 worker，第一版不做。

## 4. 配置（config.yaml）

所有可配项集中在 workspace 根目录的 `config.yaml`（与 `active.json` 并列），不散落多文件。
`config.yaml` 是**用户提供的部署配置**，不是 builder / evolver 的产物——builder 只生成语义
内容（5 类记录），不生成它。产品提供 `plugin/config.template.yaml` 模板，用户初始化
workspace 时复制为 `<workspace>/config.yaml` 并填写（与 `mcp.json` 的填写方式一致）。

```yaml
# <workspace>/config.yaml
evaluation:
  mode: ground_truth          # 必须显式声明：ground_truth | llm_judge
  judge:                      # 仅 mode=llm_judge 需要；judge 必须独立于 Evolver
    provider: openai
    model: gpt-4o
    api_key_env: OPENAI_API_KEY   # 凭据引用环境变量，不硬编码、不随包分发

evolution:
  trigger:
    min_new_trajectories: 50   # 缺省不启用（不设则不提示 due）
```

- `evaluation.mode`：声明「是否有 GT」，**必须显式声明**——它决定评估协议，无法由系统或
  builder 推断。
- `evaluation.judge`：无 GT 时的 judge 模型；凭据用环境变量引用，不硬编码。
- `evolution.trigger.min_new_trajectories`：自动触发阈值，缺省不启用自动触发提醒（机制见 §3）。

## 5. 运行时的职责边界

三个动作的定位，决定了「为什么没有 CLI」：

| 动作 | 定位 | 结论 |
| --- | --- | --- |
| 起 MCP 服务 | MCP client 读 `mcp.json` 自动 spawn | 无 `serve` 命令，`mcp_server.py` 即入口 |
| 校验 | agent 发布前调用的确定性门禁 | 保留 `scripts/validate.py` |
| 发布 | evolve skill accept 后的步骤（bash `cp` + 改 `active.json`） | 无 `publish` 命令 |

validate 只做**结构校验**（JSON 合法、跨记录引用完整、MCP 可加载），不做数据库语义校验。
「表字段存在 / Mapping 可执行 / Evidence 可复现」需连库 + 执行查询，是 Builder 探索阶段
（方案 §5.2）已做的事，发布脚本不重复。

## 6. 评估协议（plugin/docs/evaluation-protocol.md 的内容）

EvoOntology 的评估按「是否有 ground truth」分两种协议（由 `evaluation.mode` 声明，见 §4）。
两种场景都可能出现 LLM，但角色不同——**有 GT 的 LLM 是 benchmark 的判分器，无 GT 的 LLM
才是 EvoOntology 的裁判**（本文「LLM Judge」专指后者）：

| 维度 | 有 GT（benchmark 判分器） | 无 GT（EvoOntology 裁判） |
| --- | --- | --- |
| 评判对象 | 单个答案 vs GT | Parent 答案 vs Candidate 答案 |
| 判据 | 与 GT 的符合度 | 两个答案的相对优劣 |
| 输入 | `(answer, gt)` | `(question, answer_A, answer_B)` |
| 输出 | `score`（绝对分） | `winner / reason / critical_error` |
| 需不需要 GT | 必须 | 不需要 |
| 匿名 | 不需要 | 必须匿名 A/B |
| 独立性 | 无（benchmark 的事） | 必须独立于 Evolver |
| 谁提供 | benchmark 的评分函数，agent 在 Step 4 调用 | config.yaml 声明的 judge 模型，agent 按协议调用 |

**分界点按「是否有 GT」切，不按「是否用 LLM」切**：只要存在 GT 就走绝对评分，`score_fn`
内部是精确匹配还是 LLM 判语义等价是 benchmark 的实现，EvoOntology 只拿分数；只有不存在 GT
时才轮到 EvoOntology 的 LLM Judge。

### 有 GT —— 绝对评分

每个答案相对 GT 打绝对分 `score_fn(answer, gt) -> float`，由 agent 在 evolve skill Step 4
调用 benchmark 的评分函数，聚合 Parent 分数 vs Candidate 分数，比较分数差决定 accept。

### 无 GT —— 相对比较（LLM Judge）

没有客观标尺、无法绝对打分，由 agent 在 Step 4 按协议调用 config.yaml 声明的独立 judge
模型，匿名比较 Parent 与 Candidate 的答案 `judge_fn(question, answer_A,
answer_B) -> verdict`。

**输入**：每个验证任务给 judge `question + answer_A + answer_B`，A/B 随机标记，judge 不知
哪个是 Parent、哪个是 Candidate。

**输出**：
```
{ winner: "A" | "B" | "tie",
  reason: 一句话归因,
  critical_error: bool }
```

**判据**（无 GT 时 judge 无法验证哪个是对的，只能判哪个更合理，引导它看四点）：
1. 是否答对了问题（有无偏题、答非所问）；
2. 结论是否自洽（有无内部矛盾、明显事实错误）；
3. 依据是否可核查（有无给出支撑结论的数据 / 概念 / 计算）；
4. 覆盖度（有无漏掉 question 的关键分析维度）。

`winner` = 综合四点更优的一方；`critical_error` = 出现「错误结论 / 自相矛盾 / 未回答 /
执行失败」等硬伤。

**防偏差**：匿名（A/B 随机标记，消除位置 / 标签偏好）+ 独立（judge 与 Evolver 隔离，不复用
同一模型实例 / 凭据 / 上下文，消除自评偏差）。

**聚合 gate**（门槛故意保守——无 GT 的 judge 信号弱，用强条件弥补）：

对 N 个验证任务统计：`W_c` = Candidate 胜出数、`W_p` = Parent 胜出数、`T` = 平局数、
`E_c` = Candidate 出现 critical_error 的任务数。

```
accept  ⇔  E_c == 0  且  W_c > W_p
否则     →  保留 Parent
```

- `E_c == 0`：Candidate 零硬伤（错误结论 / 自相矛盾 / 未回答 / 执行失败），任一则拒。
- `W_c > W_p`：Candidate 在可判定（非平局）任务上胜出严格多于 Parent；平局不算分，
  平局多时很难满足「严格多于」，自然落在「保留 Parent」。

第一版不叠加 swap 消偏（已匿名）、分维度判、多采样、confidence 字段；「judge 同时看工具
证据」降级为可选（轨迹未存工具调用结果时先只看答案）。

## 7. 轨迹格式（plugin/docs/trajectory-format.md 的内容）

轨迹不能太简洁（不够进化诊断用），也不能太复杂（无必要冗余）。记录粒度：

- `semantic_calls`：记 **input + result**（覆盖诊断需要知道「查了什么、命中什么」）。
- `native_tool_calls`：记**完整 result + 上限截断**——`result` 记完整返回，超阈值（约 2KB
  或 20 行）截断并置 `result_truncated: true`；`result_summary` 始终给稳定概览。
- `ontology_version`：**必填**，归因必须关联到具体版本。
- **不记推理过程（CoT）**：工具 I/O 序列本身就是可观察的推理轨迹，CoT 是模型内部状态、
  噪声与存储负担；真正的中间结论已沉淀进 `final_answer`，如需另存可加可选 `notes`。

字段：`task_id / question / ontology_version / semantic_calls / native_tool_calls /
final_answer / task_status / errors`（评估结果不落轨迹，归 `evolution/`，见 §2）。

## 8. 变更清单

### 删除

| 文件/目录 | 原因 |
| --- | --- |
| `evo/cli.py` | 六命令 argparse 子命令（serve/status/activate/rollback/replay） |
| `evo/__main__.py` | `python -m evo` CLI 入口，随 cli 删除 |
| `evo/workspace.py` | 版本切换/发布/轨迹的机械操作（Workspace 类）；版本化存储由 `store.py` 直读 `active.json` + `versions/` 承担 |
| `evo/validate.py` | 引用检查逻辑移到 `plugin/scripts/validate.py` |
| `evo/replay.py` | Parent/Candidate 对比是 agent 的实验，非运行时 |
| `evo/trajectory.py` | 轨迹 dataclass，格式规范改写入 docs |
| `evo/evaluate/` | GroundTruthEvaluator / LLMJudge / GateDecision（进化逻辑进 skill/docs） |
| `plugin/scripts/preflight.py` | 旧 validate 包装，被 `scripts/validate.py` 取代 |
| `plugin/scripts/publish_candidate.py` | 依赖 `evo.workspace`，发布是 skill 步骤 |
| `EvoOntology_builder_evolver_skills_v6/`（散目录） | 内容已移入 `plugin/skills/`，保留 `.zip` 存档 |

### 修改

1. `evo/__init__.py`：去掉 `from .workspace import Workspace` 及 `__all__` 里的
   `"Workspace"`，docstring 改为「运行时四件套」。
2. plugin 重构：
   - 建 `plugin/skills/`，移入 build / evolve 两个 skill（SKILL.md + references 不动）。
   - 建 `plugin/commands/evo-build.md`、`evo-evolve.md`。
   - 建 `plugin/docs/versioning.md`、`evaluation-protocol.md`、`trajectory-format.md`。
   - 建 `plugin/config.template.yaml`（config.yaml 模板）。
   - 重写 `plugin/scripts/validate.py`（引用完整性 + 可加载，基于 `evo.store`）。
   - `mcp_config.json` → `mcp.json`。
   - 删原 `EvoOntology_builder_evolver_skills_v6/` 散目录（保留 `.zip`）。
3. 文档同步：
   - `evo/README.md`：重写为「运行时四件套 + MCP 接入」。
   - `README.md`（根）：「Productized runtime」段改为「运行时 MCP + 两个 skill 命令」。
   - `USAGE.md`：删 CLI/workspace/评估器章节，改为「两个 skill 命令 + MCP 接入 + validate 门禁」。
   - `plugin/README.md`：删 Helper scripts 一节，明确 `/evo-build`、`/evo-evolve` 为仅有的触发指令。
   - `PRODUCTIZATION_LOG.md`：追加本次精简记录。

## 9. 使用方式

```bash
# 1. 触发构建 semantic_v0（用户在 Claude Code 里输入）
/evo-build

# 2. Data Agent 通过 MCP 接入（mcp.json 里声明，client 自动 spawn，无需手动起服）
#    mcp.json: python <path-to>/evo/mcp_server.py --store <workspace-root>

# 3. 触发进化（用户在 Claude Code 里输入；或轨迹达到阈值后提示 due 时触发）
/evo-evolve        # agent 诊断→补丁→gate；accept 后 agent 自行发布（bash cp + 改 active.json）
```

agent 发布前调用 `plugin/scripts/validate.py` 做门禁（引用完整性 + 可加载）。

## 10. 影响面

- **benchmark 目录不受影响**：已确认 `bird/`、`ddr/`、`insightbench/` 未 import evo 包。
- **git 历史保留**：被删代码在历史提交中可找回。
- **`python -m evo` 失效**：预期行为；运行时入口为 `python -m evo.mcp_server`。
- **四件套代码本身不改**，MCP 运行时行为不变。

## 11. 验证步骤

1. `python -m compileall -q evo plugin` → exit 0。
2. `python -c "from evo import SemanticStore, SemanticLayer, Term, Mapping, Relation, Constraint, Evidence"` → 成功。
3. 冒烟：`SemanticStore.load('ddr/semantic_layer')` + `manifest()` + `resolve(mentions=['revenue'])` 正常。
4. `python -m evo.mcp_server --store ddr/semantic_layer` 可起服（或 import 构造成功）。
5. `plugin/scripts/validate.py --root ddr/semantic_layer` → 引用完整性 + 可加载通过。
6. `git status` 复核改动只落在 `evo/`、`plugin/`、文档。

## 12. 执行顺序

1. 删 `evo/cli.py`、`__main__.py`、`workspace.py`、`validate.py`、`replay.py`、
   `trajectory.py`、`evaluate/`。
2. 改 `evo/__init__.py`。
3. plugin 重构：删 `plugin/scripts/preflight.py`、`publish_candidate.py`；建 `skills/`
   （移入两 skill）、`commands/`、`docs/`、`config.template.yaml`；重写 `scripts/validate.py`；
   `mcp_config.json` → `mcp.json`；删原散目录（保留 `.zip`）。
4. 改四份文档 + 更新 `PRODUCTIZATION_LOG.md`。
5. 跑第 11 节验证，git 存盘。
