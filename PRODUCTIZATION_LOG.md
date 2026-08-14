# 产品化日志（Productization Log）

本文件记录将 EvoOntology 从「三个 benchmark 各自的补充材料」产品化为「一个
benchmark 无关的产品包」的过程，依据 `EvoOntology_产品化设计方案_v1.md` 的
第 3.4、11、12 节。

## 目标

把散落在 `bird/`、`ddr/`、`insightbench/` 里的通用能力抽取为独立的 `evo/`
产品包，提供：

- `evo` CLI（`serve` / `validate` / `replay` / `activate` / `status` / `rollback`）；
- 版本化 Ontology Workspace（`versions/`、`candidates/`、`trajectories/`、
  `evaluations/`、`active.json`）；
- 通用 Semantic Runtime MCP（Session Manifest + `browse_semantics` +
  `resolve_semantics`）；
- 标准化轨迹格式；
- 两类评估器（Ground-Truth Evaluator / LLM Judge）+ Parent/Candidate Replay
  + Accept/Reject Gate；
- Claude Code / Codex Plugin 封装（复用既有 skills + MCP 配置 + 辅助脚本 +
  使用说明）。

## 新增文件

### `evo/`（产品运行时与 CLI，自包含、benchmark 无关）

| 文件 | 作用 |
| --- | --- |
| `models.py` | 5 类记录 dataclass，字段对齐 `semantic-schema.md`；`evidence` 兼容 list/dict |
| `store.py` | `SemanticStore.load`：`active.json` → `versions/<v>/` 5 个 JSON |
| `runtime.py` | `SemanticLayer`：`manifest`/`browse`/`resolve`/`execute`（去除 DDR 财务硬编码） |
| `mcp_server.py` | 通用 2 工具 MCP + `evo-semantic://session-manifest` |
| `workspace.py` | `Workspace`：`activate`/`rollback`/`save_candidate`/`publish_candidate`/`record_trajectory`/`record_evaluation` |
| `trajectory.py` | 标准化轨迹格式 + `TrajectoryRecorder` |
| `validate.py` | 确定性校验：JSON 合法 / 引用完整 / 可加载 |
| `evaluate/` | `GroundTruthEvaluator` + `LLMJudge` + `GateDecision` |
| `replay.py` | `ReplayRunner`：Parent/Candidate 配对运行 + Gate |
| `cli.py` + `__main__.py` | `python -m evo` 入口 |

### `plugin/`（Claude Code / Codex Plugin 封装）

- `mcp_config.json` —— 语义 MCP 接入模板；
- `scripts/preflight.py` —— `evo validate` 的确定性包装；
- `scripts/publish_candidate.py` —— `evo activate --candidate` 的确定性包装；
- `README.md` —— `/evo-build` `/evo-evolve` 映射到既有 skills 的说明。

## 设计决策

1. **包名 `evo`、入口 `python -m evo`**，不引入 `console_scripts`，避免打包复杂度。
2. **自包含 canonical 包**：不 import 三个 benchmark 目录，但读同一套 5-JSON
   布局，因此 `evo validate/status/serve --root ddr/semantic_layer` 直接可用；
   benchmark 的 `semantic_layer/` 目录天然就是合法 workspace。
3. **replay/评估器可离线冒烟**：`run_fn`/`score_fn`/`judge_fn` 均可注入；CLI
   的 `replay` 内置 model-free 的 `offline_run_fn` + 启发式 judge/exact-match
   用于无数据/无凭据的冒烟，真实 benchmark runner 由用户经 Python API 接入。
4. **不改动三个 benchmark 目录**，产品包纯新增（surgical）。

## 边界（第一版暂不实现，方案第 13 节）

Web UI / SaaS / 多租户 / 消息队列 / 常驻 worker / 多 Candidate 并行 / 自动
循环 / 高频改 schema。第一版只做「单 Parent vs 单 Candidate」配对验证。

## 验证结果

1. 语法：`python -m compileall -q evo plugin` → exit 0。
2. `python -m evo validate --root ddr/semantic_layer` → `passed: true`；
   `--root insightbench/semantic_layer` → `passed: true`。
3. `python -m evo status --root ddr/semantic_layer` → active = `semantic_v0`，
   counts = 3 terms / 3 mappings / 0 relations / 0 constraints / 6 evidence。
4. 冒烟：`SemanticStore.load('ddr/semantic_layer')` + `manifest()` +
   `resolve(mentions=['revenue'])` → `evidence_refs` 非空、`coverage_status=supported`。
5. Workspace 往返：`save_candidate` → `publish_candidate`（semantic_v0→v1）→
   `rollback`（→v0）均通过。
6. `python -m evo replay`（parent vs 增补 mapping 的 candidate）→ Gate 正确
   accept（candidate_wins=1, parent_wins=0）；`evaluations/`、`trajectories/`
   落盘成功。
7. `python -m evo activate` / `rollback` 往返成功。

## 范围外（本次未做）

- 不跑真实 benchmark（数据/模型凭据本地提供）；真实 Data Agent runner /
  scoring / judge 经 Python API 注入（README 已说明接入点）。
- 不重写三个 benchmark 的 store/runtime/MCP（保持 adapter 角色，已提交于
  前一阶段 `8d534e3`）。
- 不实现自动触发/调度。

---

## 精简记录（slim）—— 依据 `ARCHITECTURE.md`

在上一阶段产品化的基础上进一步精简：去掉机械层（六命令 CLI、workspace、replay、
trajectory、evaluate），把这些本应由 skill 智能分析承担的部分移出 Python，只保留
「运行时四件套 + 最小确定性校验」。

### 最终形态

- 运行时四件套：`evo/models.py`、`store.py`、`runtime.py`、`mcp_server.py`（代码不改）。
- 校验门禁：`plugin/scripts/validate.py`（引用完整性 + 可加载，基于 `evo.store`）。
- 触发指令：`/evo-build`、`/evo-evolve`（`plugin/commands/`），智能分析由
  `plugin/skills/` 的两个 skill 承担。

### 删除

| 文件/目录 | 原因 |
| --- | --- |
| `evo/cli.py`、`__main__.py` | 六命令 argparse CLI，产品无 CLI |
| `evo/workspace.py` | 版本切换/发布/轨迹的机械操作，由 `store.py` 直读 + skill 步骤承担 |
| `evo/validate.py` | 引用检查逻辑移到 `plugin/scripts/validate.py` |
| `evo/replay.py` | Parent/Candidate 对比是 agent 的实验，非运行时 |
| `evo/trajectory.py` | 轨迹格式规范改写入 `plugin/docs/trajectory-format.md` |
| `evo/evaluate/` | 评估逻辑进 skill/docs（`plugin/docs/evaluation-protocol.md`） |
| `plugin/scripts/preflight.py` | 被 `scripts/validate.py` 取代 |
| `plugin/scripts/publish_candidate.py` | 依赖 workspace，发布是 skill 步骤 |
| `EvoOntology_builder_evolver_skills_v6/`（散目录） | 内容移入 `plugin/skills/`，保留 `.zip` 存档 |

### 新增 / 修改

- `evo/__init__.py`：去掉 `Workspace`，docstring 改为「运行时四件套」。
- `plugin/skills/`：移入 build / evolve 两个 skill（内容不动）。
- `plugin/commands/`：`evo-build.md`、`evo-evolve.md`。
- `plugin/docs/`：`versioning.md`、`evaluation-protocol.md`、`trajectory-format.md`。
- `plugin/config.template.yaml`：config.yaml 模板。
- `plugin/scripts/validate.py`：重写（引用完整性 + 可加载）。
- `mcp_config.json` → `mcp.json`。
- 文档同步：`evo/README.md`、根 `README.md`、`USAGE.md`、`plugin/README.md`。

### 验证结果

1. `python -m compileall -q evo plugin` → exit 0。
2. `from evo import SemanticStore, SemanticLayer, Term, Mapping, Relation, Constraint, Evidence` → 成功。
3. 冒烟：`SemanticStore.load('ddr/semantic_layer')` + `manifest()` +
   `resolve(mentions=['revenue'])` → version=semantic_v0、term=term.finance.revenue、
   evidence_refs 非空、coverage=supported。
4. `SemanticMCPServer('ddr/semantic_layer')` 构造成功（MCP 可起服）。
5. `plugin/scripts/validate.py --root ddr/semantic_layer` → passed: true；
   `--root insightbench/semantic_layer` → passed: true。
6. `git status` 复核改动只落在 `evo/`、`plugin/`、根文档与散目录存档。
