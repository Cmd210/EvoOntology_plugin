# EvoOntology Plugin

把 EvoOntology 打包成 Claude Code 插件：提供 `/evo-build`、`/evo-evolve` 两个命令、
builder / evolver 两个 skill，以及语义 MCP 运行时。安装后命令与 skill 自动就位，语义
MCP 由 `.mcp.json` 自动接入。

## 组件

| 组件 | 位置 | 作用 |
| --- | --- | --- |
| Build 命令 | `commands/evo-build.md` | `/evo-build` 构建 `semantic_v0` |
| Evolve 命令 | `commands/evo-evolve.md` | `/evo-evolve` 触发进化 |
| Builder skill | `skills/build-semantic-layer/` | 构建初始语义层 |
| Evolver skill | `skills/evolve-semantic-layer/` | 诊断 → 归因 → 补丁 → gate |
| MCP 配置 | `.mcp.json` | 语义 MCP server 自动接入 |
| 运行时 | `evo/` | 四件套（models / store / runtime / mcp_server） |
| 校验门禁 | `scripts/validate.py` | 引用完整性 + 可加载 |

## 安装

本目录就是插件根（清单在 `.claude-plugin/plugin.json`）。用本地路径安装：

```bash
claude plugin install /path/to/EvoOntology_plugin/plugin
```

或先 clone 仓库，再安装其 `plugin/` 子目录。

> 注意：清单放在 `plugin/` 子目录而非仓库根，因此 `claude plugin install <git-url>`
> 直接安装不适用（git 安装会找仓库根的清单）。请 clone 后安装 `plugin/` 子目录，或把
> 本目录单独作为仓库发布。

## 使用

安装后可用两个触发命令：

- `/evo-build` —— 读数据、探索 schema、生成五类记录，发布 `semantic_v0`；
- `/evo-evolve` —— 诊断 → 归因 → 补丁 → Parent/Candidate gate → 落地。

两者是触发指令，实际构建 / 进化由 agent 按对应 skill 执行。

### 接入语义 MCP

`.mcp.json` 以脚本形式 spawn 语义服务，client 自动拉起：

```json
{
  "mcpServers": {
    "evo-semantic": {
      "command": "python",
      "args": ["${CLAUDE_PLUGIN_ROOT}/evo/mcp_server.py", "--store", "<workspace-root>"]
    }
  }
}
```

安装后把 `<workspace-root>` 换成你的 ontology workspace 绝对路径（含 `active.json` 的目录，
如本仓库 `benchmarks/ddr/semantic_layer`）。`${CLAUDE_PLUGIN_ROOT}` 由 Claude Code 在
spawn 时展开为插件根目录，无需手填。

接入后 Data Agent 可见 `browse_semantics`、`resolve_semantics` 两个工具与
`evo-semantic://session-manifest` 资源。

## 发布门禁

发布前运行确定性校验（JSON 合法 / 引用完整 / 可加载）：

```bash
python plugin/scripts/validate.py --root <workspace-root>
```

只做结构校验，不做数据库语义校验。

## 运行时安装（可选）

`evo/` 运行时默认被 `.mcp.json` 以脚本形式直接调用，无需安装。若想作为 Python 包使用：

```bash
pip install -e plugin/
python -m evo.mcp_server --store <workspace>   # 模块形式启动
```
