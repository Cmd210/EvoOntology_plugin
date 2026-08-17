# EvoOntology — Codex Plugin

EvoOntology 的 Codex 适配层。与 Claude Code 插件共用同一套 `evoontology` 核心包和
Builder / Evolver skill，这里只放 Codex harness 所需的适配：全局指令（`AGENTS.md`）与
语义 MCP 接入示例。

## 组件

| 组件 | 位置 | 作用 |
| --- | --- | --- |
| 全局指令 | `AGENTS.md` | 注册 `/evo-build`、`/evo-evolve` 流程与语义工具用法 |
| MCP 接入 | `mcp.json.example` | 语义 MCP server 接入示例 |
| 共享 skill | `../claude-code/skills/` | Builder / Evolver 方法（与 Claude Code 共用） |

## 安装

### 普通用户

```bash
# 1. 安装 EvoOntology Core
pip install "git+https://github.com/Cmd210/EvoOntology_plugin.git"

# 2. 把 AGENTS.md 接入 Codex（任选其一）
#    —— 通过 Codex marketplace（仓库根的 .agents/plugins/marketplace.json）自动发现，
#       或手动复制 AGENTS.md：
cp plugins/codex/AGENTS.md ~/.codex/AGENTS.md          # 全局
# 或放入项目根作为项目级 AGENTS.md
```

### 开发者 / Benchmark

```bash
git clone https://github.com/Cmd210/EvoOntology_plugin.git
cd EvoOntology_plugin
pip install -e .    # 只装 Core
```

## 接入语义 MCP

把 `mcp.json.example` 的 `evo-semantic` 段合并进你的 Codex MCP 配置。默认 workspace 为
当前项目的 `.evoontology/`；如需指向别的 workspace，在 args 里追加 `"--store",
"<workspace-root>"`。

## 使用

安装后，在 Codex 会话中：

- 说「构建语义层」或 `/evo-build` —— 按 `build-semantic-layer` skill 构建 `semantic_v0`；
- 说「进化语义层」或 `/evo-evolve` —— 按 `evolve-semantic-layer` skill 执行
  诊断 → 归因 → 补丁 → Parent/Candidate gate。

实际构建 / 进化流程见 `../claude-code/skills/` 下的两份 SKILL.md，两者为同一份方法。
