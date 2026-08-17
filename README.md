# EvoOntology

为 Data Agent 提供**自进化的语义层（Ontology Layer）**：在自然语言问题与数据库 schema
之间加一层可版本化、可自我改进的语义映射。

本仓库交付的是产品化形态：

```text
evoontology/   核心包（确定性能力：store / runtime / trajectory / trigger / evaluation）
plugins/       Claude Code 插件 + Codex 适配层（/evo-build、/evo-evolve 两命令）
benchmarks/    三个 benchmark 接入示例（bird / ddr_10k / insightbench）
tests/         核心路径测试
```

## 快速开始

```bash
# 1. 安装核心包（本目录，即 evoontology 根目录）
pip install -e .

# 2. 安装 Claude Code 插件（插件根是 plugins/claude-code/）
claude plugin install plugins/claude-code
```

装完 `/evo-build`、`/evo-evolve` 两个命令、builder / evolver 两个 skill、语义 MCP
与 Session Start 进化提醒自动就位。Codex 用户改走 `plugins/codex/`（见其 README）。

## 作用

Data Agent 直接查库时，常因自然语言与 schema 之间的 gap 而答错。EvoOntology 插入一层
语义层，Agent 在会话中用两个 MCP 工具查询：

- `browse_semantics(query, kind, limit)` —— 发现与当前问题相关的概念；
- `resolve_semantics(mentions, context)` —— 把选中概念解析为 grounding 的 Mapping，
  并带回关联的 Relation / Constraint / Evidence。

语义层会自进化：`/evo-build` 构建初始 `semantic_v0`；`/evo-evolve` 依据 Tool Call 级
历史任务轨迹走「诊断 → 归因 → 补丁 → Parent/Candidate 评估 → 发布新版本」。

## 目录

| 目录 | 内容 |
| --- | --- |
| `evoontology/` | 核心包：`ontology/`（五类记录 + 版本化 store）、`runtime/`（browse/resolve/MCP）、`trajectory/`（Tool Call 级轨迹）、`trigger/`（进化提醒）、`evaluation/`（GT / LLM Judge 调度） |
| `plugins/claude-code/` | Claude Code 插件：`.mcp.json`（零配置语义 MCP）、`commands/`、`skills/`、`hooks/`（Session Start 提醒）、`scripts/`（validate 门禁 + check-reminder） |
| `plugins/codex/` | Codex 适配层：`AGENTS.md`（全局指令）+ `mcp.json.example` |
| `benchmarks/` | 三个 benchmark 接入示例（各含 Data Agent / Native Tools / Runner / Evaluator） |
| `tests/` | 核心路径测试（store / runtime / trajectory / trigger / evaluation） |

## 语义 MCP（零配置）

`.mcp.json` 以模块形式 spawn 服务，client 自动拉起，无需手动起服、无需填写 workspace
路径。默认 workspace 为当前项目的 `.evoontology/`：

```bash
python -m evoontology.runtime.mcp_server
```

如需指向别的 workspace，追加 `--store <workspace-root>`。

## 三个 benchmark 接入示例

`benchmarks/` 下是三个 benchmark 的接入示例，各含 Agent 实现、语义运行时、MCP server
与评估入口；其确定性能力统一由仓库根的 `evoontology` 包提供，不重复维护。

| 目录 | 基准 | 任务类型 |
| --- | --- | --- |
| `benchmarks/bird/` | BIRD | text-to-SQL |
| `benchmarks/ddr_10k/` | DDR-10K | 自主数据分析 |
| `benchmarks/insightbench/` | InsightBench | 迭代分析 / 代码生成 |

运行 benchmark 另需 Python 3.10+、`python -m pip install "mcp>=1.0"`、按需
`python -m pip install -r benchmarks/<benchmark>/requirements.txt`。模型凭据从环境变量
读取，benchmark 数据需本地自备（见各 benchmark 目录的 README）。

## 测试

```bash
python -m pytest tests/
```

## 文档

`USAGE.md`（完整使用指南）· `plugins/claude-code/README.md`（插件组件）·
`plugins/claude-code/docs/`（版本命名 / 评估协议 / 轨迹格式）。
