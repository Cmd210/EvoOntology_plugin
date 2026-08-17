# EvoOntology — Codex Plugin

自包含的 Codex 插件：内置 Builder / Evolver skills、项目指令和语义 MCP 接入，不引用
插件目录之外的文件。

## 组件

| 组件 | 位置 | 作用 |
| --- | --- | --- |
| 全局指令 | `AGENTS.md` | 注册 `/evo-build`、`/evo-evolve` 流程与语义工具用法 |
| MCP 接入 | `.mcp.json` | 自动启动语义 MCP server |
| Skills | `skills/` | Builder / Evolver 方法 |

## 安装

### 普通用户

```bash
# 1. 安装 EvoOntology Core
pip install "git+https://github.com/Cmd210/EvoOntology_plugin.git"

# 2. 从仓库 marketplace 安装本插件
codex plugin marketplace add .
codex plugin add evoontology-codex@evoontology
```

### 开发者 / Benchmark

```bash
git clone https://github.com/Cmd210/EvoOntology_plugin.git
cd EvoOntology_plugin
pip install -e .    # 只装 Core
```

## 接入语义 MCP

插件的 `.mcp.json` 自动注册 `evo-semantic`。默认 workspace 为当前项目的
`.evoontology/`；如需指向别的 workspace，在 args 里追加 `"--store", "<workspace-root>"`。

## 使用

安装后，在 Codex 会话中：

- 说「构建语义层」或 `/evo-build` —— 按 `build-semantic-layer` skill 构建 `semantic_v0`；
- 说「进化语义层」或 `/evo-evolve` —— 按 `evolve-semantic-layer` skill 执行
  诊断 → 归因 → 补丁 → Parent/Candidate gate。

实际构建 / 进化流程见本目录 `skills/` 下的两份 SKILL.md。
