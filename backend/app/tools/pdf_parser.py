"""
app/tools/pdf_parser.py
───────────────────────
Tool that extracts structured text from PDF files.

Libraries:
  - PyMuPDF (fitz): pip install PyMuPDF
    Best PDF library for text extraction with layout preservation.
  - pdfminer.six: pip install pdfminer.six
    Fallback for complex multi-column layouts.
"""

import re
from typing import Any, Dict, List, Optional
import fitz  # PyMuPDF — imported as 'fitz' (historical name)

from app.tools.base import BaseTool


class PDFParserTool(BaseTool):

    @property
    def name(self) -> str:
        return "pdf_parser"

    @property
    def description(self) -> str:
        return (
            "Extracts text content from a PDF file. "
            "Returns the full text organized by page and detected section "
            "(Abstract, Introduction, Methodology, Results, Conclusion, References). "
            "Use this when you need to read the content of an uploaded research paper."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the PDF file on disk."
                },
                "extract_metadata": {
                    "type": "boolean",
                    "description": "If true, also extract PDF metadata (title, author, etc.).",
                    "default": True
                }
            },
            "required": ["file_path"]
        }

    async def execute(self, file_path: str, extract_metadata: bool = True) -> Dict[str, Any]:
        """
        Open a PDF, extract text page by page, detect academic sections,
        and return a structured dict.
        """
        try:
            doc = fitz.open(file_path)
            pages_text = []
            full_text = ""

            # ── Extract text page by page ─────────────────────────────────
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # get_text("text") returns plain text preserving reading order
                page_text = page.get_text("text")
                pages_text.append({
                    "page": page_num + 1,
                    "text": page_text.strip()
                })
                full_text += page_text + "\n"

            doc.close()

            # ── Detect sections ───────────────────────────────────────────
            sections = self._detect_sections(full_text)

            # ── Extract metadata ──────────────────────────────────────────
            metadata = {}
            if extract_metadata:
                metadata = self._extract_metadata(file_path, full_text)

            return {
                "success": True,
                "result": {
                    "full_text": full_text,
                    "pages": pages_text,
                    "sections": sections,
                    "metadata": metadata,
                    "page_count": len(pages_text),
                    "character_count": len(full_text),
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e), "result": None}

    def _detect_sections(self, text: str) -> Dict[str, str]:
        """
        Use regex to detect standard academic paper sections.
        Returns dict of section_name -> section_text.
        """
        sections = {}

        # Section heading patterns (case-insensitive)
        section_patterns = [
            ("abstract",     r"(?i)\babstract\b"),
            ("introduction", r"(?i)\b1[\.\s]+introduction\b|\bintroduction\b"),
            ("related_work", r"(?i)\brelated\s+work\b|\bliterature\s+review\b"),
            ("methodology",  r"(?i)\bmethodology\b|\bmethods?\b|\b2[\.\s]+method"),
            ("results",      r"(?i)\bresults?\b|\bexperiments?\b|\b4[\.\s]+result"),
            ("discussion",   r"(?i)\bdiscussion\b"),
            ("conclusion",   r"(?i)\bconclusion\b"),
            ("references",   r"(?i)\breferences\b|\bbibliography\b"),
        ]

        lines = text.split("\n")

        current_section = "preamble"
        sections[current_section] = []

        for line in lines:
            # Check if this line is a section heading
            for section_name, pattern in section_patterns:
                stripped = line.strip()
                if re.match(pattern, stripped) and len(stripped) < 80:
                    current_section = section_name
                    if section_name not in sections:
                        sections[section_name] = []
                    break
            sections.setdefault(current_section, []).append(line)

        # Join lines back into text per section
        return {k: "\n".join(v).strip() for k, v in sections.items() if v}

    def _extract_metadata(self, file_path: str, text: str) -> Dict[str, Any]:
        """Extract title, authors, year from PDF metadata or text heuristics."""
        try:
            doc = fitz.open(file_path)
            meta = doc.metadata
            doc.close()

            # Try PDF metadata first
            title = meta.get("title", "")
            author = meta.get("author", "")

            # Fallback: first non-empty line is often the title
            if not title:
                for line in text.split("\n"):
                    line = line.strip()
                    if len(line) > 20 and len(line) < 200:
                        title = line
                        break

            # Extract year with regex (4-digit year 1900-2099)
            year_match = re.search(r"\b(19|20)\d{2}\b", text[:3000])
            year = int(year_match.group()) if year_match else None

            return {
                "title": title,
                "authors": author,
                "year": year,
                "subject": meta.get("subject", ""),
                "keywords": meta.get("keywords", ""),
            }
        except Exception:
            return {}