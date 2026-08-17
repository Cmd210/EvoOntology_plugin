# 补全日志（Completion Log）

本文件记录将 `supplementary_materials/` 从「不完整的提交代码」补完为「与论文逻辑一致、可运行」的过程。

## 目标

按论文《EvoOntology: A Self-Evolving Ontology Layer for Data Agents》的执行逻辑，结合 ddr / insight-bench / bird 三个 benchmark 的实际执行情况，把三个 benchmark 的补充材料代码补成结构完整、断点引用可解析、与论文干净接口一致的版本。干净接口为：

- 语义 MCP 服务器只暴露 2 个工具：`browse_semantics(query, kind, limit)`、`resolve_semantics(mentions, context)`；
- 外加一个 session-manifest 资源（运行时生成的纯文本，只含 source/version 与工具使用指引）；
- 5 类序列化记录：Term / Mapping / Relation / Constraint / Evidence；
- 语义信息只通过这 2 个工具 + manifest 注入，不做第三工具 / 多版本 manifest 调参 / prompt 注入。

## A. 修复断点引用（可运行性阻塞项）

1. **新增 `bird/evaluation_worker.py`**：BIRD 并行批量评测的子进程入口，解析 `--job`/`--result`，读取 job JSON，加载 `ExperimentConfig`，创建 LLM provider 并异步跑 `run_single_question`。消除了 `run_evaluation.py` 默认并行路径引用缺失文件的崩溃点。
2. **修复 DDR 语义 MCP 启动参数**：`ddr/agent/data_agent.py` 的 R14_C1 块删除 `--data-path`/`--cik` 注入，只保留 `["--store", args.semantic_store]`。`ddr/tool_server/semantic_mcp.py` 本身只接受 `--store`，此前传入不接受的参数会导致 argparse 报错、服务器起不来。
3. **统一 InsightBench 资源 URI**：`insightbench/tool_server/semantic_mcp.py` 的 `list_resources`/`read_resource` 由 `insight-bench-semantic://manifest` 改为 `insight-bench-semantic://session-manifest`，与 README 及另两套保持一致（`mcp_client.py` 本就读取 `session-manifest`）。
4. **修正 DDR 过时默认 store 路径**：`ddr/config.py` 的 `SemanticConfig.store_path` 默认值 `./semantic_store/ddr_bench` → `./semantic_layer`，并同步 `--semantic-store` 帮助文本。

## B. 剥离实验残留（对齐论文干净接口）

### BIRD

- `agent/data_agent.py`：`SEMANTIC_TOOLS` 去掉 `get_related_concepts`，只留 `{"browse_semantics", "resolve_semantics"}`。
- `tceo/runtime.py`：删除 `manifest_v2..v7`、`_V1_MANIFEST_DBS`、`get_relevant_constraints`（C21）、`suggest_browse_hint`（C22）、`get_related()` 方法，以及 `execute()` 的 `get_related_concepts` 分支；只保留 `manifest/browse/resolve/enrich_schema/bind_schema/execute(browse+resolve)`。
- `run_evaluation.py`：删除 `manifest_style` v2–v7 分派与 C21/C22 prompt 注入块，统一用 `layer.manifest(db_id=db_id)`；删除 `--enable-related-for` 参数处理。
- `config.py`：删除 `SemanticConfig.manifest_style` 字段。

### DDR

- `agent/data_agent.py`：删除 semantic-trace 埋点（`_track_semantic_tool` / `_semantic_result_hash` / `_extract_semantic_ids` / `_extract_fact_names_from_resolve` 及 `_save_session_stats_json` 中的调用）、`get_concept` 追踪块与 `_current_concept` 赋值、`--ontology-server` CLI 参数及其 MCP 配置块、C11 富化路径中的 `_db_path` 注入；`concept=""` 固定；清理过时注释。
- `agent/prompt_manager.py`：删除被注释掉的旧 ontology 导航提示（get_database_overview/get_concept/get_skill）。
- `tool_server/base_mcp_server.py`：删除半移除的第三工具 `get_session_stats`（实现 + call_tool 分支）。
- `tceo/runtime.py`：`resolve` 对齐论文签名 `resolve(mentions, context)`，删除 `semantic_ids` 参数与死代码 `_intent`。
- `tool_server/semantic_mcp.py`：`resolve_semantics` schema 对齐为 `mentions`（required）+ `context`（string），去掉 `semantic_ids`。

### InsightBench

- `insightbench/tceo/retriever.py`：`resolve` 对齐 `resolve(mentions, context)`，删除 `semantic_ids`；同步 `execute_tool` 与 `tool_schemas`（去掉 `semantic_ids` 参数声明，补 `context`）；删除死代码 `_build_direct_result` 与空 section 注释块；清理因此不再使用的 `Term`/`Mapping`/`Relation`/`ColumnProfile` 导入。
- `insightbench/agents.py`：删除「Candidate 12」注释与空 stub `generate_notebook`/`generate_report`。

## C. semantic_v0 示例数据 fidelity

- `ddr/tceo/models.py` 与 `insightbench/insightbench/tceo/models.py`：`Term/Relation/Constraint/Mapping.from_dict` 的 `evidence` 字段兼容 list（示例数据将 `evidence` 序列化为证据 id 列表，原实现只认 dict，导致 Term→Evidence / Mapping→Evidence 关联丢失）。新增 `_evidence_from`（dict/list 兼容）与 `_mapping_evidence_refs`（依次读取 `evidence_refs` / `validation.evidence` / `evidence`）。
- `ddr/semantic_layer/versions/semantic_v0/mappings.json`：`semantic_filter` 由描述性自由文本改为干净 fact_name（`Revenues` / `NetIncomeLoss` / `OperatingIncomeLoss`），使 manifest 的「Financial Concept Reference」正确渲染 `Revenue → fact_name = 'Revenues'`。

## 验证结果

1. 语法校验：`cd supplementary_materials && python -m compileall -q bird ddr insightbench` → exit 0。
2. cruft 消缺（grep）：`get_related_concepts`、`manifest_v[2-7]`、`get_relevant_constraints`、`suggest_browse_hint`、`--ontology-server`、`get_session_stats`、`semantic_ids`、`manifest_style`、`enable-related-for`、`_track_semantic_tool`、`_current_concept` 等在语义路径中均不再出现；`bird/evaluation_worker.py` 存在；`--data-path` 仅保留在 sqlite/code 原生工具与 agent 自身 CLI（非语义 cruft）。
3. 冒烟测试（不依赖真实数据/模型）：
   - DDR：`DDRSemanticLayer` 加载 `semantic_layer`，`manifest()` 含 `fact_name = 'Revenues'` 且只声明 2 个工具；`resolve(mentions=["revenue"])` 返回 term 与 mapping 的 `evidence_refs` 非空。
   - BIRD：`BIRDSemanticLayer` 加载 formula_1（3 concepts / 3 mappings / 2 constraints）；`resolve(mentions=["driver"])` 返回 2 条 evidence 关联、1 条 mapping。
   - InsightBench：`InsightSemanticLayer` 加载 `semantic_layer`，`manifest()` 只声明 2 个工具；`resolve(mentions=["duration"])` 返回 term/relation/constraint 的 `evidence_refs` 非空。

## 范围外（本次未做）

- 不跑真实 benchmark（数据/模型凭据由用户本地提供）。
- 不补自动 builder+evolver 代码循环（实际为 skill 驱动 + 手工 curation，补充材料保留 skills 包即可）。
- 不重写 node/edge 建模（5 类序列化记录与论文 `semantic-schema.md` 一致）。
