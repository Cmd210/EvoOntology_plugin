# EvoOntology Product Runtime (`evo`)

The benchmark-independent core of EvoOntology, extracted from the three
benchmark adapters (`benchmarks/bird/`, `benchmarks/ddr/`, `benchmarks/insightbench/`). It provides the
versioned semantic store loader, the generic semantic runtime, and the
two-tool MCP server. Build and evolve analysis live in the plugin skills; this
package provides only the runtime.

## Layout

```
evo/
├── models.py        # Term / Mapping / Relation / Constraint / Evidence
├── store.py         # SemanticStore: load active.json -> versions/<v>/*.json
├── runtime.py       # SemanticLayer: manifest / browse / resolve / execute
└── mcp_server.py    # 2-tool MCP server + session-manifest resource
```

## Runtime entry point

```bash
# manual start (module form)
python -m evo.mcp_server --store <workspace>

# equivalent script form (used by plugin/mcp.json for auto-spawn)
python <path-to>/evo/mcp_server.py --store <workspace>
```

A workspace root contains `active.json` and `versions/<v>/` with the five
record files. The benchmark `semantic_layer/` directories are already valid
workspaces.

## MCP access

The server exposes `browse_semantics`, `resolve_semantics`, and the
`evo-semantic://session-manifest` resource. Wire it into a Data Agent via
`plugin/mcp.json` (see `plugin/README.md`).

## Validation

The publish-time gate lives in `plugin/scripts/validate.py`:

```bash
python plugin/scripts/validate.py --root <workspace>
```
