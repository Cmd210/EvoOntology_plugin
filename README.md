# EvoOntology 插件

为 Data Agent 提供**自进化的语义层（Ontology Layer）**：在自然语言问题与数据库 schema
之间加一层可版本化、可自我改进的语义映射。本仓库 = `evo/` 运行时 + `plugin/` 插件，外加
三个 benchmark 接入示例（`bird/`、`ddr/`、`insightbench/`）。

## 作用

Data Agent 直接查库时，常因自然语言与 schema 之间的 gap 而答错。本插件插入一层语义层，
Agent 在会话中用两个 MCP 工具查询：

- `browse_semantics(query, kind, limit)` —— 发现与当前问题相关的概念；
- `resolve_semantics(mentions, context)` —— 把选中概念解析为 grounding 的 Mapping，
  并带回关联记录。

语义层会自进化：`/evo-build` 构建初始 `semantic_v0`；`/evo-evolve` 依据历史任务轨迹走
「诊断 → 归因 → 补丁 → 评估 → 发布新版本」。

## 安装

1. Python 3.10+；
2. `python -m pip install "mcp>=1.0"`；
3. 按需 `python -m pip install -r <benchmark>/requirements.txt`。

`evo` 包无需单独安装，在本目录下直接运行。模型凭据从环境变量读取，benchmark 数据需本地
自备（见各 benchmark 目录的 README）。

## 使用

### 接入 Data Agent（MCP）

编辑 `plugin/mcp.json`，把两处占位符换成实际值：

- `<path-to>`：本目录的绝对路径；
- `<workspace-root>`：语义层 workspace 根目录（含 `active.json` 的目录，如
  `ddr/semantic_layer`）。

配置后，MCP client 会在 Agent 运行时自动拉起语义服务并连上，无需手动启动。

### 构建 / 进化

在 Claude Code / Codex 中输入：

- `/evo-build` —— 构建初始语义层 `semantic_v0`；
- `/evo-evolve` —— 触发一轮进化（诊断 → 归因 → 补丁 → Parent/Candidate 评估 → 发布
  下一版本）。

两者是触发指令，智能分析由对应 skill 完成。评估需在 `<workspace>/config.yaml` 里声明
`evaluation.mode`。

### 发布门禁

发布前运行确定性校验（JSON 合法 / 引用完整 / 可加载）：

```bash
python plugin/scripts/validate.py --root <workspace-root>
```

## 文档

`USAGE.md`（完整使用指南）· `ARCHITECTURE.md`（架构设计）· `evo/README.md`、
`plugin/README.md`（组件说明）· `plugin/docs/`（版本命名 / 评估协议 / 轨迹格式）。
