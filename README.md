# EvoOntology 插件

为 Data Agent 提供**自进化的语义层（Ontology Layer）**：在自然语言问题与数据库
schema 之间加一层可版本化、可自我改进的语义映射，Agent 在会话中通过 MCP 工具查询它。
本仓库是产品化核心包 = `evo/` 运行时 + `plugin/` 插件，外加三个 benchmark 的接入示例
（`bird/`、`ddr/`、`insightbench/`）。

## 作用

Data Agent（text-to-SQL / 数据分析 / 洞察生成）直接查库时，常因自然语言与 schema
之间的 gap 而答错。本插件插入一层语义层，Agent 会话中用两个 MCP 工具查询：

- `browse_semantics(query, kind, limit)` —— 发现与当前问题相关的概念；
- `resolve_semantics(mentions, context)` —— 把选中概念解析为 grounding 的 Mapping，
  并带回关联的 Relation / Constraint / Evidence。

服务同时暴露 `evo-semantic://session-manifest` 资源，Agent 在会话开始时读取简洁说明。
语义层会自进化：`/evo-build` 构建初始 `semantic_v0`；`/evo-evolve` 依据历史任务轨迹走
「诊断 → 归因 → 补丁 → Parent/Candidate gate → 发布新版本」，形成闭环。

## 组成

```
evo/                       运行时四件套：models / store / runtime / mcp_server
plugin/                    触发命令 + skills + validate 门禁 + mcp.json
bird/ ddr/ insightbench/   三个 benchmark 的接入示例（含合法 workspace）
```

## 安装

1. Python 3.10+；
2. 安装 MCP 依赖：`python -m pip install "mcp>=1.0"`；
3. 按需安装 benchmark 依赖：`python -m pip install -r <benchmark>/requirements.txt`。

`evo` 包无需单独安装，在仓库根目录下直接运行即可。

## 执行

### 1) 接入 Data Agent（MCP）

语义 MCP 服务是一个后台进程：加载指定 workspace 的语义层，通过 MCP 协议暴露
`browse_semantics` / `resolve_semantics` 两个工具供 Data Agent 调用。它由 MCP client
按 `plugin/mcp.json` 自动拉起，**正常使用无需手动起服**。

编辑 `plugin/mcp.json` 填入两个占位符：

- `<path-to>`：本目录的绝对路径；
- `<workspace-root>`：语义层 workspace 根目录（含 `active.json` 的目录，如
  `ddr/semantic_layer`，建议绝对路径）。

client 实际用脚本形式拉起服务：

```bash
python <path-to>/evo/mcp_server.py --store <workspace-root>
```

（可选）本地调试：想单独确认服务能否正常启动时，在本目录下用等价模块形式手动跑一次：

```bash
python -m evo.mcp_server --store <workspace-root>
```

两条命令做的是同一件事，`--store` 后面的参数就是语义层所在目录。这一步不属于接入流程，正常使用跳过即可。

### 2) 构建 / 进化

- `/evo-build`：构建 `semantic_v0`（读数据 → 探索 schema → 生成 Term / Mapping /
  Relation / Constraint / Evidence 五类记录 → 发布）；
- `/evo-evolve`：触发一轮进化（诊断 → 归因 → 补丁 → Parent/Candidate 评估 → 接受或
  拒绝；accept 后把候选发布为下一正式版本）。

两者是 Claude Code / Codex 的触发指令，智能分析由对应 skill 完成，非确定性 Python
操作。评估需在 `<workspace>/config.yaml` 里显式声明 `evaluation.mode`。

### 3) 发布门禁

每次发布前运行确定性校验（JSON 合法 / 引用完整 / 可加载）：

```bash
python plugin/scripts/validate.py --root <workspace-root>
```

## 文档

`USAGE.md`（完整使用指南）· `ARCHITECTURE.md`（架构设计）· `evo/README.md`、
`plugin/README.md`（组件说明）· `plugin/docs/`（版本命名 / 评估协议 / 轨迹格式）。

## 环境与验证

```bash
python -m compileall -q evo plugin                          # 语法检查
python plugin/scripts/validate.py --root ddr/semantic_layer # 门禁冒烟
```

模型凭据从环境变量读取；benchmark 数据需本地自备（见各 benchmark 目录的 README）。
