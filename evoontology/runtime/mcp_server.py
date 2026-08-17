"""Expose the ontology layer through the two paper-defined MCP tools.

This is the generic, benchmark-independent semantic MCP server. It serves the
active semantic version under a workspace root and publishes a
``session-manifest`` resource plus ``browse_semantics`` and
``resolve_semantics``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import mcp.types as types
from mcp.server import stdio
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

if __package__:
    from .runtime import SemanticLayer
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from evoontology.runtime.runtime import SemanticLayer

_RESOURCE_URI = "evo-semantic://session-manifest"


class SemanticMCPServer:
    def __init__(self, store_path: str):
        self.layer = SemanticLayer.load(store_path)
        self.server = Server("evo-semantic-mcp")
        self._register_handlers()

    def _register_handlers(self) -> None:
        @self.server.list_tools()
        async def list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="browse_semantics",
                    description="Discover semantic concepts relevant to an analytical need.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "kind": {
                                "type": "string",
                                "enum": [
                                    "term",
                                    "mapping",
                                    "relation",
                                    "constraint",
                                    "all",
                                ],
                            },
                            "limit": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 6,
                            },
                        },
                        "required": ["query"],
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="resolve_semantics",
                    description="Resolve selected concepts to grounded mappings and linked semantic objects.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "mentions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "maxItems": 5,
                            },
                            "context": {"type": "string"},
                        },
                        "required": ["mentions"],
                        "additionalProperties": False,
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(
            name: str, arguments: dict[str, Any]
        ) -> list[types.TextContent]:
            if name not in {"browse_semantics", "resolve_semantics"}:
                result = {"status": "error", "message": f"Unknown tool: {name}"}
            else:
                try:
                    result = self.layer.execute(name, arguments)
                except Exception as exc:
                    result = {"status": "error", "message": str(exc)}
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, default=str),
                )
            ]

        @self.server.list_resources()
        async def list_resources() -> list[types.Resource]:
            return [
                types.Resource(
                    uri=_RESOURCE_URI,
                    name="EvoOntology semantic session manifest",
                    mimeType="text/plain",
                )
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            if str(uri) != _RESOURCE_URI:
                raise ValueError(f"Unknown resource: {uri}")
            return self.layer.manifest()

    async def run(self) -> None:
        async with stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="evo-semantic-mcp",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


async def main() -> None:
    parser = argparse.ArgumentParser(description="EvoOntology semantic MCP server")
    parser.add_argument(
        "--store",
        default=None,
        help="Workspace root containing active.json (default: <cwd>/.evoontology)",
    )
    args = parser.parse_args()
    store = args.store or str(Path.cwd() / ".evoontology")
    await SemanticMCPServer(store).run()


if __name__ == "__main__":
    asyncio.run(main())
