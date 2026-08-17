# 版本命名与切换

## 版本命名

| 类型 | 命名 | 示例 |
| --- | --- | --- |
| 正式版本 | `semantic_vN`（N 单调递增） | `semantic_v0` 初始、`semantic_v1` 第 1 次 accept |
| 候选 | `vN-cK`（关联源版本 + 序号） | `v0-c1` = 从 v0 进化的第 1 个候选 |

accept 映射：`vN-cK` → `semantic_vN+1`。

## 切换

「切换版本」是 evolve skill 的操作步骤（改 `active.json` 指针），不设独立命令。
运行时 `store.py` 与命名约定无关：只读 version 字段并加载 `versions/<name>/`，
不校验命名格式。
