"""EvoOntology product runtime — the four-file core.

A benchmark-independent implementation of the productized EvoOntology layer:
``models`` (five record dataclasses), ``store`` (versioned store loader),
``runtime`` (generic semantic runtime: manifest / browse / resolve), and
``mcp_server`` (two-tool MCP server). Build / evolve analysis lives in the
plugin skills; this package provides only the runtime.

The three benchmark directories (bird / ddr / insightbench) remain the
benchmark adapters; this package is the extracted common core described in
``EvoOntology_产品化设计方案_v1.md``.
"""

from .models import Constraint, Evidence, Mapping, Relation, Term
from .runtime import SemanticLayer
from .store import SemanticStore

__version__ = "1.0.0"

__all__ = [
    "SemanticStore",
    "SemanticLayer",
    "Term",
    "Mapping",
    "Relation",
    "Constraint",
    "Evidence",
]
