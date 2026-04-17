"""
app/tools/vector_retriever.py
──────────────────────────────
Agent tool that performs semantic search in the vector store.
Claude calls this tool when it needs to find relevant paper content.
"""

from typing import Any, Dict, List, Optional

from app.tools.base import BaseTool
from app.vector_store.faiss_store import get_vector_store


class VectorRetrieverTool(BaseTool):

    @property
    def name(self) -> str:
        return "vector_retriever"

    @property
    def description(self) -> str:
        return (
            "Search the knowledge base of uploaded research papers using semantic similarity. "
            "Returns the most relevant text passages from papers that match your query. "
            "Use this to find specific information across all uploaded papers. "
            "Returns text chunks with paper title and relevance score."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query (e.g., 'transformer attention mechanism')"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 8, max: 20)",
                    "default": 8
                },
                "paper_id": {
                    "type": "string",
                    "description": "Optional: restrict search to a specific paper by its ID."
                },
                "paper_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: restrict search to these paper IDs only."
                }
            },
            "required": ["query"]
        }

    async def execute(
        self,
        query: str,
        top_k: int = 8,
        paper_id: Optional[str] = None,
        paper_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        try:
            store = get_vector_store()
            results = store.search(
                query=query,
                top_k=min(top_k, 20),
                paper_id=paper_id,
                project_paper_ids=paper_ids,
            )

            if not results:
                return {
                    "success": True,
                    "result": {
                        "found": 0,
                        "passages": [],
                        "message": "No relevant passages found. Try a different query."
                    }
                }

            return {
                "success": True,
                "result": {
                    "found": len(results),
                    "passages": results,
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e), "result": None}