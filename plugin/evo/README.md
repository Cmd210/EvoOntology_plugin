# EvoOntology Product Runtime (`evo`)

EvoOntology 的 benchmark 无关运行时核心，从三个 benchmark adapter
（`benchmarks/bird/`、`benchmarks/ddr/`、`benchmarks/insightbench/`）抽取。提供版本化语义层加载
（`SemanticStore`）、通用语义运行时（`SemanticLayer`）、2-tool MCP server。构建 / 进化的智能分析
在 plugin 的 skill 里，本包只提供运行时。

## 布局

```
evo/
├── models.py        # Term / Mapping / Relation / Constraint / Evidence
├── store.py         # SemanticStore: 读 active.json -> versions/<v>/*.json
├── runtime.py       # SemanticLayer: manifest / browse / resolve / execute
└── mcp_server.py    # 2-tool MCP server + session-manifest 资源
```

## 启动方式

脚本形式（`.mcp.json` 自动 spawn 所用，无需安装）：

```bash
python ${CLAUDE_PLUGIN_ROOT}/evo/mcp_server.py --store <workspace>
# 或直接：python evo/mcp_server.py --store <workspace>
```

模块形式（需先 pip 安装，见下）：

```bash
python -m evo.mcp_server --store <workspace>
```

workspace 根含 `active.json` 与 `versions/<v>/` 五个记录文件；三个 benchmark 的
`semantic_layer/` 目录天然是合法 workspace。

## 安装（可选）

`pyproject.toml` 位于 `plugin/`（本目录的上级），`evo` 是其下的包：

```bash
pip install -e plugin/            # 从仓库根执行
# 或 cd plugin && pip install -e .
```

装好后即可以模块形式启动，并自动带上 `mcp>=1.0` 依赖。

## MCP 接入

server 暴露 `browse_semantics`、`resolve_semantics` 两个工具与
`evo-semantic://session-manifest` 资源，由 `plugin/.mcp.json` 接入 Data Agent。

## 校验

发布门禁在 `plugin/scripts/validate.py`：

```bash
python plugin/scripts/validate.py --root <workspace>
```
