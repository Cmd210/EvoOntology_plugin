# EvoOntology 产品化开发设计方案

## 1. 产品目标

EvoOntology 是面向 Data Agent 的自进化 Ontology 工具。

它不重新实现 Data Agent，而是在 Data Agent 与底层数据之间提供一层可构建、可查询、可持续进化的语义层，沉淀：

- Term：业务概念
- Mapping：概念与真实数据的映射
- Constraint：必要的数据/业务约束
- Relation：概念关系
- Evidence：支撑语义定义的数据证据

一期需要跑通完整闭环：

```text
Build
→ Use
→ Record
→ Remind
→ Evolve
→ Evaluate
```

即：

```text
Claude Code / Codex 构建 Ontology
        ↓
Data Agent 使用 Ontology
        ↓
记录真实任务轨迹
        ↓
达到条件后提醒用户
        ↓
Claude Code / Codex 根据轨迹生成 Candidate
        ↓
Parent / Candidate 验证
        ↓
Accept / Reject
```

二期增加 Ontology 可视化。

---

# 2. 核心角色与职责

## Claude Code / Codex

承担 Builder 和 Evolver。

### Builder

负责：

```text
理解 Workload
→ 探索真实数据
→ 提取语义
→ 生成 Initial Ontology
```

### Evolver

负责：

```text
Diagnose
→ Attribute
→ Patch
→ Evaluate
```

Builder / Evolver 的智能逻辑通过 Skill 实现，不重新开发 Python Builder / Evolver Engine。

---

## Data Agent

负责实际任务执行。

通过：

```text
browse_semantics
resolve_semantics
```

获取 Ontology 信息，再使用 SQL、Python、File 等 Native Tools 查询真实数据。

Data Agent 不直接修改 Active Ontology。

---

## EvoOntology Core

只负责确定性能力：

- Ontology 存储和版本管理
- Semantic Runtime / MCP
- Trajectory 记录
- Evolution Trigger
- Evaluation 调度
- Candidate 发布与回滚
- 二期 Visualization

---

# 3. 整体架构

```text
┌──────────────────────────────────┐
│       Claude Code / Codex        │
│                                  │
│   Builder Skill   Evolver Skill  │
└────────┬───────────────┬─────────┘
         │               │
         ▼               ▼
┌──────────────────────────────────┐
│       EvoOntology Workspace      │
│                                  │
│ Versions / Trajectories / State  │
└────────────────┬─────────────────┘
                 │ Active Ontology
                 ▼
┌──────────────────────────────────┐
│       Semantic Runtime MCP       │
│                                  │
│ browse_semantics                 │
│ resolve_semantics                │
└────────────────┬─────────────────┘
                 ▼
┌──────────────────────────────────┐
│            Data Agent            │
│                                  │
│ Semantic Tools + Native Tools    │
└────────────────┬─────────────────┘
                 │
                 ▼
          Task Trajectory
                 │
                 └──────→ Evolver
```

一期仓库建议：

```text
EvoOntology/
├── evoontology/
│   ├── ontology/
│   ├── runtime/
│   ├── trajectory/
│   ├── evaluation/
│   └── trigger/
│
├── plugins/
│   ├── claude-code/
│   └── codex/
│
├── benchmarks/
│   ├── bird/
│   ├── ddr_10k/
│   └── insightbench/
│
├── tests/
├── pyproject.toml
└── README.md
```

---

# 4. Workspace 与版本管理

每个项目默认使用：

```text
<project-root>/.evoontology/
```

第一次 `/evo-build` 时自动创建：

```text
.evoontology/
├── active.json
├── versions/
├── trajectories/
└── state.json
```

### `versions/`

统一保存正式版本与 Candidate：

```text
semantic_v0/
semantic_v1/
candidate_v2/
```

### `active.json`

记录 Data Agent 当前使用的版本：

```json
{
  "active_version": "semantic_v1"
}
```

### `state.json`

保存 Trigger 和 Evolution Checkpoint。

用户不需要手工编辑这些文件。

---

# 5. Plugin 设计

同时支持：

```text
plugins/
├── claude-code/
└── codex/
```

两个 Plugin 共用同一：

- Ontology Schema
- EvoOntology Core
- Builder 方法
- Evolver 方法

只实现各自 Harness 必需的适配。

一期主要入口：

```text
/evo-build
/evo-evolve
```

Plugin 还负责：

- 自动连接 Semantic MCP
- Session Start 时检查 Evolution Reminder

产品默认零配置，不要求用户填写 Workspace 路径、Evaluation Mode、Judge Model 或 Trigger 参数。

---

# 6. Build 流程

用户执行：

```text
/evo-build
```

流程：

```text
自动创建 .evoontology
        ↓
读取代表性 Workload
        ↓
Claude / Codex 分析任务需求
        ↓
探索 Database / File / Document / Code
        ↓
生成 Term / Mapping / Evidence
以及必要的 Constraint / Relation
        ↓
最低可运行检查
        ↓
发布 semantic_v0
```

Builder 应采用 Workload-Guided 方式，不以穷举数据库 Schema 为目标。

优先保证：

```text
Term
Mapping
Evidence
```

的质量。

最低检查只包括：

- Ontology 可以解析
- 关键引用可以解析
- Runtime 可以加载

不增加额外 LLM 审查流程。

---

# 7. Runtime 与 Data Agent

Semantic MCP 一期只提供：

```text
Session Manifest
browse_semantics
resolve_semantics
```

Data Agent 执行逻辑：

```text
用户任务
    ↓
Data Agent
    ↓
需要语义帮助时调用 browse / resolve
    ↓
获得 Mapping / Constraint / Evidence
    ↓
使用 Native Tools 查询真实数据
    ↓
生成最终答案
```

Semantic Tool 不是强制调用路径。

三个 Benchmark 与普通项目必须共用同一套 Semantic Runtime，不分别维护重复的 `semantic_mcp.py`。

---

# 8. Trajectory 设计

Trajectory 同时服务于：

- Evolver Diagnose / Attribute
- Evolution Trigger
- 无 GT 场景下的 LLM Judge

因此需要记录到 Tool Call 粒度。

## 记录层级

```text
Trigger 粒度 = Task
Evolution 分析粒度 = Tool Call
```

一个完整 Data Agent Task 对应一条 Trajectory。

Trajectory 内按真实执行顺序记录全部：

- Semantic Tool Calls
- Native Tool Calls

每次调用至少记录：

```text
step
category
tool_name
arguments
result
error
```

推荐结构：

```json
{
  "task_id": "task_001",
  "question": "分析各地区净收入变化",
  "ontology_version": "semantic_v2",

  "tool_calls": [
    {
      "step": 1,
      "category": "semantic",
      "tool_name": "browse_semantics",
      "arguments": {},
      "result": {},
      "error": null
    },
    {
      "step": 2,
      "category": "native",
      "tool_name": "execute_sql",
      "arguments": {},
      "result": {},
      "error": null
    }
  ],

  "final_answer": "...",
  "status": "completed"
}
```

Tool Result 原则上记录 Data Agent 实际看到的结果。

对于超大输出，可以保留 preview + reference，不需要把大型结果全部重复写入主 Trajectory。

不记录 Hidden Chain of Thought、Token 级信息或复杂系统 Trace。

---

# 9. Evolution Trigger

Trigger 只负责：

> 判断是否应该提醒用户进行下一轮 Evolution。

不自动启动 Evolver。

一期支持：

```text
新增 Task Trajectory ≥ N
OR
距离上次 Evolution ≥ T
```

例如默认：

```text
10 个新 Task
或
7 天
```

Trigger 在两个时机检查：

```text
新 Trajectory 保存后
Session Start
```

达到条件：

```text
evolution_due = true
```

用户下次进入项目时收到提醒，由用户决定是否执行 `/evo-evolve`。

不实现 Cron、后台 Worker 或自动 Evolution。

用户需要修改阈值时，可直接告诉 Claude / Codex：

```text
以后每 20 个任务提醒我一次
```

由 Agent 更新内部状态，不要求修改配置文件。

---

# 10. Evolution 流程

用户执行：

```text
/evo-evolve
```

Evolver 读取：

```text
当前 Parent Ontology
+
上次 Evolution 后新增的 Task Trajectories
```

执行：

```text
Diagnose
→ Attribute
→ Patch
→ Evaluate
```

## Diagnose

基于 Task 和 Tool Call 级轨迹发现重复问题。

例如：

- Term 反复检索不到
- Mapping 错误
- resolve 返回内容不合理
- Semantic Tool 正确但 Data Agent 未采用结果
- Manifest 引导错误
- 当前 Schema 无法表达必要信息

如果没有明确问题：

```text
No Update
```

本轮结束。

## Attribute

判断主要问题属于：

```text
Content
Tool
Schema
```

每轮只要求：

```text
一个主要问题
+
一个主要归因
+
一个主要修改假设
```

不做多 Candidate Tournament。

## Patch

生成一个局部 Candidate，只修改解决当前问题所必需的内容。

## Candidate Check

只确认：

```text
可以解析
+
Runtime 可以加载
```

通过后直接进入效果验证。

---

# 11. Evaluation 总体设计

Evaluation 只解决：

> Candidate 是否优于 Parent？

统一流程：

```text
Parent + Validation Set
Candidate + Validation Set
        ↓
效果比较
        ↓
Accept / Reject
```

两组实验保持：

- 相同 Validation Set
- 相同 Data Agent
- 相同模型
- 相同 Prompt
- 相同 Tools
- 相同 Interaction Budget

系统自动选择 Evaluator：

```text
存在 Benchmark Evaluator
        ↓
Ground Truth Evaluation

不存在 Benchmark Evaluator
        ↓
LLM Judge
```

用户不需要配置 Evaluation Mode。

---

# 12. 有 Ground Truth 场景

用于：

```text
BIRD
DDR-10K
InsightBench
```

Benchmark 负责提供：

```text
Evolution Set
Validation Set
Held-out Test Set
Evaluator
```

### Evolution Set

用于：

- Builder
- Trajectory 收集
- Evolver 生成 Candidate

### Validation Set

Candidate 生成后用于 Parent / Candidate 比较。

### Held-out Test Set

最终 Ontology 冻结后用于最终测试。

Ground Truth 不提供给 Builder / Evolver。

Candidate 生成后：

```text
Parent Score
Candidate Score
```

如果 Candidate 达到 Benchmark 规定的提升条件：

```text
Accept
```

否则：

```text
Reject
```

---

# 13. 无 Ground Truth 场景

真实项目没有标准答案时，保持相同流程，只将 Benchmark Evaluator 替换为 LLM Judge。

历史任务划分为：

```text
Evolution Set
Validation Set
```

Evolution Set 用于生成 Candidate。

Validation Set 只用于验证 Candidate。

## LLM Judge 输入

每个 Validation Task 得到：

```text
Answer A
+
A 的关键 Tool Calls / Results

Answer B
+
B 的关键 Tool Calls / Results
```

A/B 匿名，不告诉 Judge：

- 哪个是 Parent
- 哪个是 Candidate
- Candidate 修改内容
- Evolver 的分析过程

Judge 综合判断：

- 是否完成任务
- 业务语义是否正确
- 数据使用是否正确
- 结论是否与 Tool Result 一致
- 是否存在明显错误或遗漏

输出：

```json
{
  "winner": "A",
  "confidence": 0.86,
  "reason": "..."
}
```

聚合：

```text
Candidate Wins
Parent Wins
Ties
```

Candidate 整体明显占优则 Accept，否则 Reject。

一期不做多 Judge Ensemble 或复杂加权评分。

默认 Judge 使用当前 Claude Code / Codex 的独立上下文，不要求用户另外配置 Judge API。

---

# 14. Evolution 完成后的处理

## Accept

```text
Candidate
→ 保存为新的 semantic_vN
→ 更新 active.json
```

## Reject

```text
active.json 保持 Parent
```

无论 Accept / Reject，只要本轮 Evolution 已完成，都更新：

```text
last_evolution_trajectory
last_evolution_time
evolution_due = false
```

下一轮只分析新增 Trajectory，避免重复使用同一批任务触发进化。

---

# 15. Benchmark 设计

仓库提供：

```text
benchmarks/
├── bird/
├── ddr_10k/
└── insightbench/
```

Benchmark 的目标是：

> 用户准备官方数据后，可以使用 EvoOntology Plugin 完整运行 Build → Use → Record → Evolve → Evaluate 流程。

每个 Benchmark 需要提供：

- README / 数据准备说明
- Data Agent
- Native Tools
- Runner
- Evaluator
- 必要的数据划分
- Trajectory 输出或最薄 Adapter

仓库不提供：

- Benchmark 原始大型数据
- 预构建 `semantic_v0`
- 预构建 evolved ontology

用户自行准备数据，然后使用 `/evo-build` 构建自己的 Ontology。

三个 Benchmark 应复用共享 Core 和 Semantic Runtime，不重复维护 EvoOntology 基础能力。

---

# 16. 一期开发范围

一期必须完成：

### Core

- Ontology save / load
- Active Version
- Candidate publish / rollback
- Semantic Runtime
- MCP Server
- Tool Call 级 Trajectory
- Trigger
- GT / LLM Judge Evaluation 调度

### Plugin

同时支持：

```text
Claude Code
Codex
```

实现：

```text
Build
Evolve
Semantic MCP
Evolution Reminder
```

### Benchmark

确保：

```text
BIRD
DDR-10K
InsightBench
```

可以在用户准备官方数据后正常运行完整 Plugin 流程。

---

# 17. 一期测试要求

至少覆盖以下核心路径。

## Core

```text
Ontology save/load
Active version
Candidate publish
Rollback
```

## Runtime

```text
未初始化时 MCP 能启动
初始化后 Runtime 能加载
browse 可调用
resolve 可调用
```

## Trajectory

验证：

```text
Tool Call 顺序
Tool Name
Arguments
Result
Error
Semantic / Native Category
```

均可正确记录。

## Trigger

验证：

```text
Task 数量触发
时间触发
Evolution 后 checkpoint 更新
```

## Plugin

Claude Code / Codex 均验证：

```text
Plugin 可加载
Skill 可发现
MCP 可启动
Reminder Hook 可执行
```

## Benchmark

每个 Benchmark 至少确保：

```text
Runner 可启动
Data Agent 可运行
Evaluator 可调用
Trajectory 可输出
```

---

# 18. 一期明确不做

Coding Agent 不应主动增加：

- Web Dashboard
- SaaS
- Database Backend
- Event Bus
- Queue
- Background Worker
- Cron Scheduler
- 自动后台 Evolution
- Candidate Tournament
- 多 Candidate 并行搜索
- 多 Judge Ensemble
- 第二层 LLM Reviewer
- 强制独立 Judge Provider
- 大型 Observability 系统
- Ontology 在线编辑

已有代码能够满足需求时应优先复用和抽取，不为了目录结构重新实现。

---

# 19. 二期：Ontology Visualization

一期稳定后增加可视化。

用户触发：

```text
/evo-visualize
```

读取 Active Ontology：

```text
Ontology
→ Graph Nodes / Edges
→ HTML Renderer
→ Interactive HTML
```

输出：

```text
.evoontology/
└── visualizations/
    └── semantic_vN.html
```

第一版支持：

- Term / Mapping / Relation / Constraint / Evidence 展示
- Table / Column 展示
- 搜索
- 类型过滤
- 缩放 / 拖动
- 邻居高亮
- 节点详情面板
- 当前版本信息

Visualization 只读，不修改 Ontology。

---

# 20. 推荐开发顺序

```text
1. 抽取共享 Ontology Store / Runtime / MCP

2. 统一 .evoontology Workspace

3. 整理 Claude Code Plugin

4. 实现 Codex Plugin

5. 统一 Tool Call 级 Trajectory

6. 实现 Trigger

7. 实现统一 Evaluation

8. 整理 BIRD / DDR-10K / InsightBench

9. 补核心测试与 README

10. 二期实现 Visualization
```

---

# 21. 一期完成标准

普通项目能够完整运行：

```text
安装 Plugin
→ /evo-build
→ 自动生成 Ontology
→ Data Agent 使用 browse / resolve
→ 自动记录 Tool Call 级 Trajectory
→ 达到条件后收到提醒
→ /evo-evolve
→ 生成 Candidate
→ LLM Judge Validation
→ Accept / Reject
```

Benchmark 能够完整运行：

```text
准备官方数据
→ 启用 Plugin
→ /evo-build
→ Data Agent
→ Trajectory
→ /evo-evolve
→ Benchmark Evaluator
→ Parent / Candidate 比较
```

整个默认流程不要求用户手工编辑配置文件。

---

# 22. 核心实现边界

整个产品只保留以下核心分工：

```text
Claude Code / Codex
负责 Build 和 Evolve

Data Agent
负责 Use

Trajectory
负责记录真实行为

Trigger
负责 Remind

Evaluator
负责判断 Candidate 是否更好

EvoOntology Core
负责连接以上流程
```

其中最重要的 Trajectory 边界为：

> **Task 是存储和 Trigger 的基本单位；Tool Call 是 Evolver Diagnose / Attribute 和 LLM Judge 的基本分析单位。**

一期所有开发都应围绕这一核心闭环展开，不增加不能直接服务该闭环的额外系统。