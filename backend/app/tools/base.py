"""
app/tools/base.py
─────────────────
Abstract base class for all Agent Tools.
Every tool in the registry must implement this interface.

The Tool Executor discovers tools, passes their schemas to Claude,
then calls tool.execute() when Claude requests it.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """
    Every agent tool must inherit from BaseTool and implement:
      - name: str           — unique snake_case identifier
      - description: str    — what Claude sees when choosing tools
      - input_schema: dict  — JSON Schema of expected inputs
      - execute(**kwargs)   — the actual tool logic
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique snake_case name. Claude uses this to call the tool."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Clear description of what this tool does.
        Claude reads this to decide WHEN to use the tool.
        Be specific about inputs and what the tool returns.
        """
        ...

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """
        JSON Schema dict defining the tool's input parameters.
        This is sent to Claude via the tools parameter in the API call.

        Example:
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {"type": "integer", "description": "Number of results"}
                },
                "required": ["query"]
            }
        """
        ...

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with the provided arguments.

        Args:
            **kwargs: Arguments matching the input_schema

        Returns:
            Dict with at minimum:
                - "success": bool
                - "result": Any   (the actual output)
                - "error": str    (only if success=False)
        """
        ...

    def to_claude_tool_dict(self) -> Dict[str, Any]:
        """
        Convert this tool to the format expected by Claude's tools parameter.
        Called by ToolExecutor when building the tools list for Claude.
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }