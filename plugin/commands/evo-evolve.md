---
description: 触发进化——诊断→归因→补丁→Parent/Candidate gate→落地
---

## 输入上下文

本命令是触发指令，不是确定性操作；evolve 的实际执行者是按 skill 行动的 agent。agent 需要
三处输入，均来自当前 benchmark 上下文（由调用者提供），不写入 `config.yaml`（那是持久部署
配置，不是任务级上下文）：

- **工作区根目录 `<workspace>`**：默认取当前 benchmark 的 `semantic_layer/`；调用者可
  用 `--root <workspace>` 覆盖，指向别的 ontology workspace（如产品 `.evoontology/`）。
- **数据环境**：当前已挂载的只读数据工具（SQLite MCP / Python 执行等）+ benchmark 配置里
  声明的数据源路径。Evolver 只读这些数据，不改数据本身。
- **工作量（workload）**：`<workspace>/trajectories/` 下累积的历史任务轨迹（进化诊断的
  输入），以及评估所需的验证集问题与 ground truth（按
  `docs/evaluation-protocol.md` 的有 GT / 无 GT 两条协议取用）。

## 执行

执行 `evolve-semantic-layer` skill（`skills/evolve-semantic-layer/`），触发一次进化循环。

按 skill 的 Evolution Loop 执行：Diagnose → Attribute → Patch → Evaluate/Gate。评估协议见
`docs/evaluation-protocol.md`（有 GT 绝对评分 / 无 GT LLM Judge 相对比较）。

accept 后按 `docs/versioning.md` 把候选 `vN-cK` 发布为 `semantic_vN+1`（改
`active.json` 指针）。
