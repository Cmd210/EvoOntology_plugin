---
description: 构建 semantic_v0——读数据、探索 schema、生成 5 类记录
---

## 输入上下文

本命令是触发指令，不是确定性操作；build 的实际执行者是按 skill 行动的 agent。agent 需要
三处输入，均来自当前项目上下文（由调用者提供）：

- **工作区根目录 `<workspace>`**：默认取当前项目的 `.evoontology/`（首次运行自动创建）；
  调用者可用 `--root <workspace>` 覆盖，指向别的 ontology workspace。
- **数据环境**：当前已挂载的只读数据工具（SQLite MCP / Python 执行等）+ benchmark 配置里
  声明的数据源路径。Builder 只读这些数据，不改数据本身。
- **工作量（workload）**：benchmark 数据集的构建划分（construction split）问题。按
  `skills/build-semantic-layer/references/semantic-layer-data-boundary.md` 的
  fold 划分与 70/30 构建/验证切分，Builder 只能读构建集，**不得读取留出（held-out）的
  验证/测试问题及其 ground truth**。

## 执行

执行 `build-semantic-layer` skill（`skills/build-semantic-layer/`），构建初始语义层。

按 skill 的 Builder Workflow 执行：Workload-Guided Probing → Evidence-Grounded
Commitment，产出 Term / Mapping / Relation / Constraint / Evidence 五类记录，发布为
`semantic_v0`。

发布前调用 `python -m evoontology.validate --root <workspace>` 做确定性门禁（引用完整性 +
可加载）。
