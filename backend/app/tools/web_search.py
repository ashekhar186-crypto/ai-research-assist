"""
app/tools/web_search.py
────────────────────────
Tool that searches Semantic Scholar API for academic papers.
Free API, no key required for basic use.

Library:
  - httpx: pip install httpx  (async HTTP client, better than requests for FastAPI)

Semantic Scholar API docs: https://api.semanticscholar.org/graph/v1
"""

from typing import Any, Dict, List
import httpx

from app.tools.base import BaseTool


SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"


class WebSearchTool(BaseTool):

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Search Semantic Scholar for academic papers related to a topic. "
            "Returns paper titles, abstracts, authors, year, and citation count. "
            "Use this to discover papers beyond what the user has uploaded, "
            "especially for literature reviews on broad topics."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Academic search query (e.g., 'BERT language model NLP')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum papers to return (default: 10, max: 20)",
                    "default": 10
                },
                "year_start": {
                    "type": "integer",
                    "description": "Filter papers from this year onwards"
                },
                "year_end": {
                    "type": "integer",
                    "description": "Filter papers up to this year"
                }
            },
            "required": ["query"]
        }

    async def execute(
        self,
        query: str,
        limit: int = 10,
        year_start: int = None,
        year_end: int = None,
    ) -> Dict[str, Any]:
        """Search Semantic Scholar and return structured paper data."""
        try:
            params = {
                "query": query,
                "limit": min(limit, 20),
                "fields": "title,abstract,authors,year,citationCount,externalIds,venue",
            }

            # Add year filter if provided
            if year_start or year_end:
                year_filter = ""
                if year_start:
                    year_filter += str(year_start)
                year_filter += "-"
                if year_end:
                    year_filter += str(year_end)
                params["year"] = year_filter

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{SEMANTIC_SCHOLAR_API}/paper/search",
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

            papers = []
            for paper in data.get("data", []):
                authors = [a.get("name", "") for a in paper.get("authors", [])]
                papers.append({
                    "title": paper.get("title", ""),
                    "abstract": (paper.get("abstract") or "")[:500] + "...",
                    "authors": authors,
                    "year": paper.get("year"),
                    "citation_count": paper.get("citationCount", 0),
                    "venue": paper.get("venue", ""),
                    "semantic_scholar_id": paper.get("paperId", ""),
                    "doi": (paper.get("externalIds") or {}).get("DOI", ""),
                })

            return {
                "success": True,
                "result": {
                    "total_found": data.get("total", 0),
                    "papers": papers,
                }
            }

        except httpx.HTTPError as e:
            return {"success": False, "error": f"HTTP error: {e}", "result": None}
        except Exception as e:
            return {"success": False, "error": str(e), "result": None}