# EvoOntology Plugin

This directory packages the Claude Code / Codex side of EvoOntology: the two
trigger commands (`/evo-build`, `/evo-evolve`), their skills, the semantic MCP
configuration, and the deterministic validation gate. It is the "Claude Code /
Codex Plugin" component described in `EvoOntology_产品化设计方案_v1.md`.

## Components

| Component | Location | Role |
| --- | --- | --- |
| Build command | `commands/evo-build.md` | `/evo-build` — build `semantic_v0` |
| Evolve command | `commands/evo-evolve.md` | `/evo-evolve` — trigger evolution |
| Builder skill | `skills/build-semantic-layer/` | initialize the ontology |
| Evolver skill | `skills/evolve-semantic-layer/` | diagnose, patch, and gate |
| MCP config | `mcp.json` | connect the semantic runtime to a Data Agent |
| Validate gate | `scripts/validate.py` | reference completeness + loadability |
| Docs | `docs/` | versioning / evaluation protocol / trajectory format |

## Trigger commands

`/evo-build` and `/evo-evolve` are the only trigger commands. They are not
deterministic Python operations — the actual build / evolution is performed by
the agent following the corresponding skill.

- `/evo-build` runs the Builder skill: read the workload, explore the data
  environment, generate the five semantic record types, validate, and publish
  `semantic_v0`.
- `/evo-evolve` runs the Evolver skill: read historical trajectories, diagnose
  and attribute problems, produce one local Candidate, run Parent/Candidate
  evaluation, and accept or reject. See `docs/evaluation-protocol.md` for the
  ground-truth / LLM-judge protocols and `docs/versioning.md` for version
  naming.

## MCP configuration

Edit `mcp.json` to fill the two placeholders:

- `<path-to>`: the absolute path to this `supplementary_materials/` directory;
- `<workspace-root>`: the ontology workspace (e.g. `benchmarks/ddr/semantic_layer`, or a
  product workspace).

The client spawns the server as
`python <path-to>/evo/mcp_server.py --store <workspace-root>`; no manual start
is needed. The server exposes `browse_semantics`, `resolve_semantics`, and the
`evo-semantic://session-manifest` resource.

## Validation gate

```bash
# deterministic preflight before publishing
python plugin/scripts/validate.py --root <workspace-root>
```

This script checks JSON validity, cross-record reference completeness, and
store loadability. It performs deterministic checks only; it never generates
or mutates semantic content.
