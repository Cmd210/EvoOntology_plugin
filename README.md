# EvoOntology Supplementary Implementation

This package provides the implementation used to integrate EvoOntology with
BIRD, DDR, and InsightBench. For each benchmark, the baseline and semantic
conditions retain the same agent, model interface, native data tools, and
evaluation procedure. The semantic condition adds one read-only MCP server
and injects its manifest into the agent context.

## Method interface

Each semantic MCP server exposes the same two operations:

- `browse_semantics(query, kind, limit)` discovers relevant semantic records;
- `resolve_semantics(mentions, context)` retrieves grounded mappings and
  linked records for selected concepts.

The server also publishes a benchmark-specific session-manifest resource. The
agent reads its concise text when a semantic session starts. Semantic tools return
metadata and guidance; database queries and Python execution remain the
responsibility of the benchmark's native tools.

| Benchmark | Baseline execution | Native tool | Semantic MCP resource |
| --- | --- | --- | --- |
| BIRD | ReAct text-to-SQL agent | SQLite MCP server | `bird-semantic://session-manifest` |
| DDR | Autonomous analysis agent | Scenario-specific SQLite/code MCP servers | `ddr-semantic://session-manifest` |
| InsightBench | Iterative analysis/code-generation agent | Python execution tool | `insight-bench-semantic://session-manifest` |

## Package layout

Each benchmark directory includes its agent implementation, semantic runtime,
MCP server, baseline and semantic configuration, startup entry point,
evaluation entry point, and dependency specification.

The `semantic_layer/versions/semantic_v0/` directory under each benchmark is
an illustrative subset of the initial semantic layer. These examples follow
the submitted schema and preserve valid cross-record references, but contain
only a few representative Terms, Mappings, Relations, Constraints, and
Evidence records. They are intended to demonstrate structure and server
behavior rather than reproduce the full initialization used for all benchmark
instances.

The two manifest-related artifacts have distinct roles:

- `version_metadata.json` records the immutable store version, schema label,
  object counts, and example status; it is never inserted into an agent prompt.
- the MCP `session-manifest` resource is generated at runtime as bounded plain
  text containing only source/version information and tool-usage guidance.
  Detailed ontology records remain accessible only through the two MCP tools.

## Productized runtime (`evo` + `plugin`)

The benchmark-independent product core is extracted into the `evo/` package — a
four-file runtime (`models` / `store` / `runtime` / `mcp_server`) — and the
`plugin/` directory, which packages the two trigger commands (`/evo-build`,
`/evo-evolve`), their skills, and a validation gate. Build and evolve analysis
lives in the skills; the Python package provides only the runtime.

```bash
python <path-to>/evo/mcp_server.py --store <workspace>    # MCP server (spawned by client via plugin/mcp.json)
python plugin/scripts/validate.py --root <workspace>      # publish-time gate
```

The server is not started by hand in normal use — a Data Agent spawns it through
`plugin/mcp.json`. `python -m evo.mcp_server --store <workspace>` is the
equivalent manual form for local verification.

See `USAGE.md` for a full walkthrough, and `evo/README.md` / `plugin/README.md`
for component details.

## Environment

Python 3.10 or later is recommended. Install dependencies separately for each
benchmark:

```bash
python -m pip install -r bird/requirements.txt
python -m pip install -r ddr/requirements.txt
python -m pip install -r insightbench/requirements.txt
```

Model credentials are read from the environment variables named in the
example configuration files. Replace model placeholders and relative data
paths with values appropriate to the local evaluation environment.

Benchmark databases are not included because of submission size constraints.
Place locally obtained benchmark data at the relative paths documented in the
benchmark-specific README files.

## Verification

From this directory, the following command validates Python syntax:

```bash
python -m compileall -q bird ddr insightbench
```

Detailed startup and evaluation commands are provided in the README file for
each benchmark.
