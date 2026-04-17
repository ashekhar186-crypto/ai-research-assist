import asyncio
from app.tools.base import BaseTool
from app.tools.pdf_parser import PDFParserTool
from app.tools.vector_retriever import VectorRetrieverTool
from app.tools.web_search import WebSearchTool

class ToolExecutor:

    def __init__(self):
        self._tools: dict = {}
        for tool in [PDFParserTool(), VectorRetrieverTool(), WebSearchTool()]:
            self._tools[tool.name] = tool

    def get_all_tool_definitions(self) -> list:
        return [t.to_claude_tool_dict() for t in self._tools.values()]

    async def execute_tool(self, name: str, **kwargs) -> dict:
        if name not in self._tools:
            return {"error": f"Tool '{name}' not found"}
        try:
            result = self._tools[name].execute(**kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            return result
        except Exception as e:
            return {"error": str(e)}

_instance = None

def get_tool_executor() -> ToolExecutor:
    global _instance
    if _instance is None:
        _instance = ToolExecutor()
    return _instance
