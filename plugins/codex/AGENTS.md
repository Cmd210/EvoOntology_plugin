# EvoOntology — Codex Instructions

This project uses EvoOntology: a versioned, self-evolving ontology layer between
natural-language questions and the underlying data. The deterministic core lives
in the `evoontology` Python package; the Build/Evolve method lives in the shared
skills under `plugins/claude-code/skills/`.

## Entry points

- **Build** — when the user asks to "build the ontology" or runs `/evo-build`,
  execute the `build-semantic-layer` skill (see
  `plugins/claude-code/skills/build-semantic-layer/SKILL.md`). Default workspace
  is `<project-root>/.evoontology` (create it on first run). Publish `semantic_v0`
  after running `python -m evoontology.validate --root <workspace>`.
- **Evolve** — when the user asks to "evolve the ontology" or runs `/evo-evolve`,
  execute the `evolve-semantic-layer` skill (see
  `plugins/claude-code/skills/evolve-semantic-layer/SKILL.md`) following
  Diagnose → Attribute → Patch → Evaluate/Gate. Accept a candidate by promoting
  it to the next `semantic_vN` and switching `active.json`.

## Semantic MCP tools

The `evo-semantic` MCP server exposes two bounded navigation tools plus a
session manifest resource:

- `browse_semantics(query, kind, limit)` — discover concepts relevant to a need;
- `resolve_semantics(mentions, context)` — resolve concepts to grounded
  mappings, relations, constraints, and evidence.

Use them to ground analytical concepts before querying real data with native
tools. They are guidance, not final answers.

## Evolution reminder

Before a session, check whether evolution is due:

```bash
python -c "from evoontology import EvolutionTrigger; import json; print(json.dumps(EvolutionTrigger('.evoontology').check()))"
```

If `evolution_due` is true, remind the user that `/evo-evolve` is available.
Never start evolution automatically.
