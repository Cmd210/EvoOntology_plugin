# EvoOntology 产品化使用指南

本文档说明产品化完成后，如何实际使用 EvoOntology。产品化把散落在
`benchmarks/` 三个目录里的通用能力抽取为两个**新增、自包含**的部件：

- `evo/` —— benchmark 无关的产品运行时四件套（models / store / runtime / mcp_server）。
- `plugin/` —— Claude Code / Codex 侧封装（两个触发命令 + skills + MCP 配置 +
  validate 门禁）。

产品最终形态 = 一个运行时（evo 四件套）+ 一个 validate 脚本 + 两个 skill 命令，无 CLI。
智能分析全在 skill，Python 只做「运行时 + 最小确定性校验」。

本文所有命令均在 `supplementary_materials/` 目录下执行。

---

## 1. 前置条件

- Python 3.10+，且已安装 MCP 依赖：

  ```bash
  python -m pip install "mcp>=1.0"
  ```

- 一个合法的 ontology workspace（见下节布局）。三个 benchmark 的
  `semantic_layer/` 目录天然就是合法 workspace，可直接作为 `--store` / `--root` 使用。

---

## 2. 一个 workspace 长什么样

workspace 根目录（`<root>`）是语义层版本化存储：

```
<root>/
├── active.json          # {"version": "semantic_v0"}
├── config.yaml          # 集中配置（见 §4）
├── versions/            # 所有版本（正式 semantic_vN + 候选 vN-cK），每版本 5 个 JSON
├── trajectories/        # 任务轨迹 JSONL（进化诊断输入）
└── evolution/           # 进化记录（每轮问题地图、归因、gate 决策、知识更新）
```

每版本下是 5 个记录文件，对应论文 schema 的五类对象：Term / Mapping / Relation /
Constraint / Evidence。轨迹由 Data Agent 运行时（benchmark adapter 侧）在每次任务结束时
追加到 `trajectories/`；进化记录由 evolve skill 每轮进化结束时写入 `evolution/`。

---

## 3. 触发指令

| 指令 | 语义 | 执行者 |
| --- | --- | --- |
| `/evo-build` | 构建 semantic_v0：读数据、探索 schema、生成 5 类记录 | agent 按 build skill |
| `/evo-evolve` | 触发进化：诊断→归因→补丁→Parent/Candidate gate→落地 | agent 按 evolve skill |

两者都是**触发指令**，不是 Python 确定性操作；真正的构建 / 进化由 agent 按 skill 执行。
版本命名与切换约定见 `plugin/docs/versioning.md`（正式版本 `semantic_vN`、候选
`vN-cK`，accept 映射 `vN-cK` → `semantic_vN+1`）。

---

## 4. 配置（config.yaml）

所有可配项集中在 workspace 根目录的 `config.yaml`。它是**用户提供的部署配置**（从
`plugin/config.template.yaml` 复制填写），不是 builder / evolver 的产物。

```yaml
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

`evaluation.mode` 决定评估协议（见 `plugin/docs/evaluation-protocol.md`）。validate /
serve 不需要 config.yaml；只有走 evolve 评估（agent Step 4）时才需要用户先补
`<workspace>/config.yaml`。

---

## 5. MCP 接入

插件通过 `plugin/.mcp.json` 以脚本形式 spawn 服务，client 自动拉起、无需手动起服。安装后只需
把 `<workspace-root>` 占位符换成你的 ontology workspace 绝对路径（如
`benchmarks/ddr/semantic_layer`）；`${CLAUDE_PLUGIN_ROOT}` 由 client 自动展开为插件根目录：

```bash
python ${CLAUDE_PLUGIN_ROOT}/evo/mcp_server.py --store <workspace-root>
```

接入后 Data Agent 可见：

- 工具 `browse_semantics(query, kind, limit)` —— 发现相关概念；
- 工具 `resolve_semantics(mentions, context)` —— 解析概念到 grounding 的 mapping +
  关联的 relation / constraint / evidence；
- 资源 `evo-semantic://session-manifest` —— 会话开始时读取的简洁说明。

手动起服（验证用，脚本形式）：

```bash
python plugin/evo/mcp_server.py --store benchmarks/ddr/semantic_layer
```

模块形式（先 `pip install -e plugin/`）：

```bash
python -m evo.mcp_server --store benchmarks/ddr/semantic_layer
```

这两个工具返回的是元数据与指引，数据库查询与 Python 执行仍由 benchmark 原生工具负责。

---

## 6. validate 门禁

agent 发布前调用 `plugin/scripts/validate.py` 做确定性门禁（JSON 合法 / 引用完整 / 可加载）：

```bash
python plugin/scripts/validate.py --root benchmarks/ddr/semantic_layer
# → {"passed": true, "root": "...", "version": "semantic_v0", "errors": []}
```

validate 只做结构校验，不做数据库语义校验（表字段存在 / Mapping 可执行 / Evidence 可复现
是 Builder 探索阶段已做的事）。

---

## 7. 一个最小端到端流程

```bash
cd supplementary_materials

# 1. 触发构建 semantic_v0（在 Claude Code 里输入）
/evo-build

# 2. Data Agent 通过 MCP 接入（.mcp.json 声明，client 自动 spawn，无需手动起服）
#    .mcp.json 指向 ${CLAUDE_PLUGIN_ROOT}/evo/mcp_server.py --store <workspace>

# 3. 触发进化（在 Claude Code 里输入；或轨迹达到阈值后提示 due 时触发）
/evo-evolve        # agent 诊断→补丁→gate；accept 后 agent 自行发布（bash cp + 改 active.json）
```

agent 发布前调用 `plugin/scripts/validate.py` 做门禁。

---

## 8. 边界（第一版不做）

Web UI / SaaS / 多租户 / 消息队列 / 常驻 worker / 多 Candidate 并行 / 自动循环 / 高频改
schema 均不在本版范围。无人值守全自动进化需要常驻后台 worker，第一版只做「检测 + 提醒」，
由人触发。详见 `PRODUCTIZATION_LOG.md` 与 `EvoOntology_产品化设计方案_v1.md` 第 13 节。
