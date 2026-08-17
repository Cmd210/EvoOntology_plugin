#!/usr/bin/env python3
"""Session-start evolution reminder hook.

Checks ``<cwd>/.evoontology`` for an evolution-due condition and prints a
one-line reminder to stdout. Claude Code injects hook stdout into the session
context, so the agent sees the reminder without any user action.

Silently exits when the workspace is not yet initialized (no ``state.json``)
or when evolution is not due.
"""

from __future__ import annotations

from pathlib import Path

from evoontology import EvolutionTrigger


def main() -> int:
    workspace = Path.cwd() / ".evoontology"
    if not (workspace / "state.json").is_file():
        return 0

    result = EvolutionTrigger(str(workspace)).check()
    if not result["evolution_due"]:
        return 0

    print(
        f"EvoOntology: evolution is due ({result['reason']}). "
        f"Run /evo-evolve to review and improve the semantic layer."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
