# EvoOntology 插件

为 Data Agent 提供**自进化的语义层（Ontology Layer）**：在自然语言问题与数据库 schema
之间加一层可版本化、可自我改进的语义映射。本仓库 = `plugin/` 插件（内含 `evo/` 运行时），
外加 `benchmarks/` 下的三个 benchmark 接入示例。

## 快速开始

三步装好并跑起来：

1. **安装插件**（插件根是 `plugin/` 子目录）：

   ```bash
   git clone git@github.com:Cmd210/EvoOntology_plugin.git
   claude plugin install EvoOntology_plugin/plugin
   ```

   装完 `/evo-build`、`/evo-evolve` 两个命令与语义 MCP 自动就位。

2. **接入语义 MCP**：把 `plugin/.mcp.json` 里的 `<workspace-root>` 换成你的语义层
   workspace 绝对路径（含 `active.json` 的目录）。三个 benchmark 的 `semantic_layer/`
   目录天然就是合法 workspace，可直接用；也可用 `/evo-build` 从零构建。

3. **触发命令**：

   - `/evo-build` —— 构建初始语义层 `semantic_v0`；
   - `/evo-evolve` —— 触发一轮进化（诊断 → 归因 → 补丁 → Parent/Candidate 评估 → 发布
     下一版本）。

## 作用

Data Agent 直接查库时，常因自然语言与 schema 之间的 gap 而答错。本插件插入一层语义层，
Agent 在会话中用两个 MCP 工具查询：

- `browse_semantics(query, kind, limit)` —— 发现与当前问题相关的概念；
- `resolve_semantics(mentions, context)` —— 把选中概念解析为 grounding 的 Mapping，
  并带回关联记录。

语义层会自进化：`/evo-build` 构建初始 `semantic_v0`；`/evo-evolve` 依据历史任务轨迹走
「诊断 → 归因 → 补丁 → 评估 → 发布新版本」。

## 三个 benchmark 接入示例

`benchmarks/` 下是三个 benchmark 的接入示例，各含 Agent 实现、语义运行时、MCP server
与评估入口；其 `semantic_layer/` 目录是合法 workspace，可直接作为 `--store` / `--root`
使用。

| 目录 | 基准 | 任务类型 |
| --- | --- | --- |
| `benchmarks/bird/` | BIRD | text-to-SQL |
| `benchmarks/ddr/` | DDR | 自主数据分析 |
| `benchmarks/insightbench/` | InsightBench | 迭代分析 / 代码生成 |

运行 benchmark 另需 Python 3.10+、`python -m pip install "mcp>=1.0"`、按需
`python -m pip install -r benchmarks/<benchmark>/requirements.txt`。模型凭据从环境变量
读取，benchmark 数据需本地自备（见各 benchmark 目录的 README）。

## 文档

`USAGE.md`（完整使用指南）· `ARCHITECTURE.md`（架构设计）· `plugin/README.md`、
`plugin/evo/README.md`（组件说明）· `plugin/docs/`（版本命名 / 评估协议 / 轨迹格式）。
