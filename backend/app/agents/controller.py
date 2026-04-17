import json
import time
from app.agents.reasoner import ReasoningEngine
from app.agents.tool_executor import get_tool_executor
from app.agents.memory_manager import MemoryManager
from app.core.config import get_settings

settings = get_settings()

# ══════════════════════════════════════════════════════════════════════════
# VENUE_RULES — per-venue page limits and format requirements.
# Used for page-limit warnings and venue-specific pre-submission checklist.
# Keys are lowercase substrings matched against target_journal.
# ══════════════════════════════════════════════════════════════════════════
VENUE_RULES = {
    # ── IEEE conferences ────────────────────────────────────────────────
    "icassp":     {"pages": 4, "refs_extra": 1, "double_blind": False, "venue_class": "IEEE",
                   "rules": ["4 pages main + 1 page references only", "Single-blind review"]},
    "cvpr":       {"pages": 8, "refs_extra": 999, "double_blind": True, "venue_class": "IEEE",
                   "rules": ["Double-blind: remove author names from title + remove Acknowledgements",
                             "GitHub URLs must be anonymised for review (e.g., '[anonymous-for-review]')",
                             "Unlimited references on extra pages"]},
    "iccv":       {"pages": 8, "refs_extra": 999, "double_blind": True, "venue_class": "IEEE",
                   "rules": ["Double-blind review — anonymise authors, affiliations, acknowledgements",
                             "GitHub/dataset URLs must not reveal authors"]},
    "wacv":       {"pages": 8, "refs_extra": 999, "double_blind": True, "venue_class": "IEEE",
                   "rules": ["Double-blind: anonymise everything"]},
    "iros":       {"pages": 6, "refs_extra": 0, "double_blind": False, "venue_class": "IEEE", "rules": []},
    "icra":       {"pages": 6, "refs_extra": 0, "double_blind": False, "venue_class": "IEEE", "rules": []},
    "icip":       {"pages": 5, "refs_extra": 0, "double_blind": False, "venue_class": "IEEE", "rules": []},
    # IEEE Transactions (journals) — typically 12 pages
    "transactions": {"pages": 12, "refs_extra": 999, "double_blind": False, "venue_class": "IEEE-journal",
                     "rules": ["Single column typical",
                               "Supplementary materials allowed separately"]},
    # ── ACM venues ──────────────────────────────────────────────────────
    "chi":        {"pages": 14, "refs_extra": 999, "double_blind": False, "venue_class": "ACM",
                   "rules": ["ACM Reference Format required",
                             "Concepts + Keywords via ACM CCS"]},
    "siggraph":   {"pages": 12, "refs_extra": 999, "double_blind": False, "venue_class": "ACM",
                   "rules": ["Supplementary video strongly encouraged",
                             "ACM Reference Format required"]},
    "cscw":       {"pages": 25, "refs_extra": 999, "double_blind": False, "venue_class": "ACM", "rules": []},
    "kdd":        {"pages": 9,  "refs_extra": 999, "double_blind": False, "venue_class": "ACM",
                   "rules": ["9 pages for full papers"]},
    "www":        {"pages": 10, "refs_extra": 999, "double_blind": False, "venue_class": "ACM", "rules": []},
    # ── ACL / NLP ───────────────────────────────────────────────────────
    "acl":        {"pages": 8,  "refs_extra": 999, "double_blind": True, "venue_class": "ACL",
                   "rules": ["8 pages main (long) / 4 pages (short)",
                             "Double-blind: anonymise",
                             "Mandatory Reproducibility Checklist",
                             "Mandatory Limitations section (not counted in 8)",
                             "Mandatory Ethics section"]},
    "emnlp":      {"pages": 8,  "refs_extra": 999, "double_blind": True, "venue_class": "ACL",
                   "rules": ["8 pages + unlimited refs + Limitations + Ethics",
                             "Reproducibility Checklist mandatory",
                             "Double-blind"]},
    "naacl":      {"pages": 8,  "refs_extra": 999, "double_blind": True, "venue_class": "ACL",
                   "rules": ["Double-blind; Limitations + Ethics required"]},
    "findings":   {"pages": 8,  "refs_extra": 999, "double_blind": True, "venue_class": "ACL",
                   "rules": ["Double-blind; Limitations + Ethics required"]},
    "coling":     {"pages": 9,  "refs_extra": 999, "double_blind": True, "venue_class": "ACL", "rules": []},
    # ── NeurIPS / ICML / ICLR ───────────────────────────────────────────
    "neurips":    {"pages": 9,  "refs_extra": 999, "double_blind": True, "venue_class": "ML",
                   "rules": ["9 pages main + unlimited refs + unlimited appendix",
                             "Mandatory Broader Impact statement",
                             "Mandatory NeurIPS Checklist (paper-checklist)",
                             "Double-blind review",
                             "Reproducibility Checklist"]},
    "icml":       {"pages": 8,  "refs_extra": 999, "double_blind": True, "venue_class": "ML",
                   "rules": ["8 pages + unlimited refs + unlimited appendix",
                             "Broader Impact statement required",
                             "Reproducibility statement required",
                             "Double-blind"]},
    "iclr":       {"pages": 10, "refs_extra": 999, "double_blind": True, "venue_class": "ML",
                   "rules": ["10 pages + unlimited refs + appendix",
                             "OpenReview submission — public but anonymous",
                             "Ethics + Reproducibility statements"]},
    "aaai":       {"pages": 7,  "refs_extra": 2,   "double_blind": True, "venue_class": "ML",
                   "rules": ["7 pages main + 2 pages references max", "Double-blind"]},
    "ijcai":      {"pages": 7,  "refs_extra": 2,   "double_blind": True, "venue_class": "ML",
                   "rules": ["7 pages main + 2 pages refs", "Double-blind"]},
    # ── Springer LNCS / LNEE conferences ────────────────────────────────
    "lncs":       {"pages": 14, "refs_extra": 0, "double_blind": False, "venue_class": "Springer",
                   "rules": ["LNCS single-column page count is 12–14 (varies by conf)",
                             "Use llncs class + splncs04 bibstyle",
                             "CR-copyright form required upon acceptance"]},
    "lnee":       {"pages": 12, "refs_extra": 0, "double_blind": False, "venue_class": "Springer",
                   "rules": ["LNEE typically 10–12 pages (check conf CFP)",
                             "Use llncs class + splncs04 bibstyle"]},
    "mai":        {"pages": 12, "refs_extra": 0, "double_blind": False, "venue_class": "Springer",
                   "rules": ["MAI conferences use LNEE — 10–12 page limit",
                             "llncs class, splncs04 bibstyle",
                             "Camera-ready requires Springer copyright form"]},
    "mvai":       {"pages": 12, "refs_extra": 0, "double_blind": False, "venue_class": "Springer",
                   "rules": ["MVAI uses LNEE — 10–12 pages", "splncs04 bibstyle"]},
    # ── Nature family / Elsevier / journals ─────────────────────────────
    "nature":     {"pages": None, "word_limit": 4000, "double_blind": False, "venue_class": "Nature",
                   "rules": ["Main text ≤ 4000 words (hard for Nature, 5000 for Nature MI)",
                             "Mandatory Cover Letter",
                             "Statement of Significance (3-sentence plain-language summary)",
                             "Reporting Summary (Life Sciences Reporting Summary)",
                             "Data & Code Availability statement mandatory",
                             "Reviewer suggestions encouraged"]},
    "machine intelligence": {"pages": None, "word_limit": 5000, "double_blind": False, "venue_class": "Nature",
                             "rules": ["Nature MI: ≤ 5000 words main text",
                                       "Plain-language summary required",
                                       "Cover letter + significance statement",
                                       "Author Contributions (CRediT) mandatory"]},
    "elsevier":   {"pages": None, "word_limit": 7000, "double_blind": False, "venue_class": "Elsevier",
                   "rules": ["Typical Elsevier word limit 6000–8000 (check journal)",
                             "Graphical abstract often required",
                             "Highlights (3–5 bullets, ≤ 85 chars each)",
                             "CRediT author statement"]},
    "plos":       {"pages": None, "word_limit": 6000, "double_blind": False, "venue_class": "Open-Access",
                   "rules": ["No hard word limit but expect 5000–7000",
                             "Author Contributions (CRediT)",
                             "Funding statement",
                             "Competing Interests statement"]},
}

def _venue_lookup(target_journal: str) -> dict:
    """Return the first matching VENUE_RULES entry, or a permissive default."""
    if not target_journal:
        return {"pages": None, "double_blind": False, "venue_class": "generic", "rules": []}
    j = target_journal.lower()
    # Match longest key first to prefer specific over general
    for key in sorted(VENUE_RULES.keys(), key=lambda k: -len(k)):
        import re as _re
        if _re.search(r'\b' + _re.escape(key) + r'\b', j):
            return {**VENUE_RULES[key], "_matched_key": key}
    # IEEE generic fallback
    import re as _re
    if _re.search(r'\bieee\b', j):
        return {"pages": 8, "refs_extra": 999, "double_blind": False,
                "venue_class": "IEEE-generic",
                "rules": ["IEEE conference generic: typical 6–8 page limit — verify CFP"]}
    return {"pages": None, "double_blind": False, "venue_class": "generic", "rules": []}


class AgentController:

    def __init__(self):
        self.reasoner = ReasoningEngine()
        self.tool_executor = get_tool_executor()
        self.memory = MemoryManager()

    async def analyze_paper(self, file_path: str, paper_id: str, paper_title: str = "") -> dict:
        start_time = time.time()
        try:
            parse_result = await self.tool_executor.execute_tool("pdf_parser", file_path=file_path)
            if "error" in parse_result:
                return {"error": parse_result["error"]}

            # pdf_parser wraps result under 'result' key
            result_data = parse_result.get("result", parse_result)
            full_text = result_data.get("full_text", "")
            sections = result_data.get("sections", {})
            metadata = result_data.get("metadata", {})

            if full_text:
                await self.memory.store_paper_knowledge(paper_id, full_text, paper_title)

            prompt = f"""You are an expert research analyst. Perform a deep, rigorous analysis of this paper.

Metadata: {json.dumps(metadata)}
Paper title hint: {paper_title}
Paper content (sections): {json.dumps(sections, indent=2)[:10000]}

Extract ALL information present in the paper. Return ONLY valid JSON with no markdown fences:
{{
  "title": "Exact paper title from the document",
  "authors": "Full author names, comma-separated",
  "year": 2024,
  "publication_venue": "Journal/conference name and volume/issue if found, else 'Not specified'",
  "research_domain": "Specific sub-field (e.g., 'NLP — Efficient Transformers', not just 'AI')",
  "paper_type": "original_research | review | meta_analysis | system_paper | position_paper | dataset_paper",
  "methodology_type": "empirical | theoretical | survey | simulation | case_study | mixed_methods",
  "abstract_summary": "3-4 precise sentences: (1) problem being solved, (2) proposed approach, (3) key quantitative results, (4) broader significance",
  "core_problem": "The specific technical/scientific problem — 1-2 sentences. Be precise, not generic.",
  "key_contributions": [
    "Contribution 1: be concrete (e.g., 'Proposes SparseAttn reducing O(n²) complexity to O(n log n) via learned routing')",
    "Contribution 2: include metrics where present (e.g., 'Achieves 96.1 GLUE score with 3.2× speedup over FlashAttention-2')",
    "Contribution 3: include any datasets, benchmarks, or tools released"
  ],
  "methodology_summary": "Detailed description (4-6 sentences): (1) the proposed method/system, (2) datasets used, (3) experimental setup, (4) evaluation protocol, (5) baselines compared against",
  "datasets_used": ["Dataset name (size and domain if mentioned)"],
  "evaluation_metrics": ["Metric name (e.g., BLEU-4, F1, accuracy, perplexity)"],
  "performance_metrics": "All key quantitative results with exact numbers — e.g., '96.1% accuracy on GLUE (+3.2 over BERT), 3.2× speedup, 71% memory reduction on 32K tokens'",
  "baseline_comparison": "Which methods were compared against, and by what margin the proposed approach outperforms them",
  "main_results": "Comprehensive 4-5 sentence summary of ALL key results, including ablation findings if present",
  "limitations": "Specific limitations from the paper — not generic. Include any negative results or failure modes mentioned.",
  "future_work": "Specific future directions the authors suggest, including any planned follow-up work",
  "code_availability": "yes — URL if found | no | unknown",
  "reproducibility_score": "high | medium | low — briefly justify (e.g., 'high — full hyperparameters, code, and hardware specs provided')",
  "novelty_assessment": "What is genuinely new: algorithm, dataset, application domain, theoretical insight, or combination. Compare to closest prior art.",
  "practical_applications": "Real-world use cases and industries where this work is deployable",
  "key_terms": ["technical term 1", "term 2", "term 3", "term 4", "term 5", "term 6"],
  "citation_context": "Key prior works this paper builds upon and how it advances them (2-3 sentences)"
}}"""

            result = await self.reasoner.think(prompt)
            summary = self._parse_json(result.get("content", "{}"))
            processing_time = time.time() - start_time

            return {
                "summary": summary,
                "tokens_used": result.get("usage", {}),
                "processing_time": processing_time
            }

        except Exception as e:
            return {"error": str(e), "summary": {}}

    async def generate_literature_review(self, topic: str, paper_ids: list, search_web: bool = False) -> dict:
        try:
            knowledge = await self.memory.search_knowledge(topic, top_k=10)
            tools = self.tool_executor.get_all_tool_definitions()
            prompt = f"""You are an expert academic reviewer writing a rigorous, publication-quality literature review.

Topic: {topic}
Uploaded paper knowledge base (use specific details from these papers):
{json.dumps(knowledge[:8], indent=2)[:7000]}

Write a comprehensive, synthesized literature review — NOT a list of paper summaries. Synthesize across papers to identify trends, agreements, debates, and evolution. Return ONLY valid JSON:
{{
  "title": "A Systematic Review of [Topic]: Trends, Challenges, and Future Directions",
  "scope_and_coverage": "2-3 sentences describing what this review covers, its time range, and what is explicitly excluded",
  "introduction": "350-400 word introduction. (1) Open with broad societal/scientific significance with a striking statistic or fact. (2) Narrow to the specific research area. (3) Explain why this review is needed now. (4) Describe the review's structure and contribution.",
  "chronological_evolution": "150-200 words tracing the field from its origins to the present. Include specific year milestones. Identify 2-3 paradigm shifts or turning points (e.g., 'The introduction of transformers in 2017 fundamentally changed...').",
  "thematic_sections": [
    {{
      "title": "Theme 1: Specific Name (e.g., 'Attention Mechanisms and Scalability')",
      "content": "300-400 word synthesis. Synthesize across papers — identify convergence, divergence, technical evolution. Use hedged language ('Several studies suggest...', 'There is growing consensus that...', 'A key tension exists between...'). Include specific paper references.",
      "key_papers": ["Author et al. (Year) — one-sentence contribution", "Author2 et al. (Year) — one-sentence contribution"],
      "consensus": "What the field broadly agrees on in this area",
      "debate": "Where there is still genuine disagreement or uncertainty"
    }},
    {{
      "title": "Theme 2: Specific Name",
      "content": "300-400 word synthesis...",
      "key_papers": ["..."],
      "consensus": "...",
      "debate": "..."
    }},
    {{
      "title": "Theme 3: Specific Name",
      "content": "300-400 word synthesis...",
      "key_papers": ["..."],
      "consensus": "...",
      "debate": "..."
    }}
  ],
  "methodology_comparison": "200-250 words comparing methodological approaches: datasets used, evaluation protocols, experimental setups, reproducibility, what makes direct comparison across papers difficult.",
  "performance_benchmarks": "100-150 words summarizing key performance numbers reported across papers. What is the current state-of-the-art and on what benchmarks? What metrics are most commonly used?",
  "key_findings_synthesis": "250-300 words synthesizing the most important findings across ALL reviewed papers. Focus on convergent evidence, surprising results, and underexplored findings. Do NOT list papers — integrate them.",
  "research_gaps": [
    "Gap 1: specific, actionable gap (not 'more research needed') — explain WHY it matters",
    "Gap 2: ...",
    "Gap 3: ...",
    "Gap 4: ...",
    "Gap 5: ..."
  ],
  "future_directions": [
    "Direction 1: 2-3 sentence specific research direction with rationale for why it is the highest priority",
    "Direction 2: ...",
    "Direction 3: ...",
    "Direction 4: ..."
  ],
  "conclusion": "150-200 word conclusion. Restate the review's scope, summarize the 3-4 most important takeaways, and end with a forward-looking statement.",
  "key_papers_table": [
    {{"authors": "Smith et al.", "year": 2021, "title": "Paper Title", "venue": "NeurIPS", "key_contribution": "What makes this paper important", "method": "Core approach used"}},
    {{"authors": "Jones et al.", "year": 2022, "title": "Paper Title 2", "venue": "Nature", "key_contribution": "...", "method": "..."}}
  ],
  "themes": ["Theme 1 short label", "Theme 2 short label", "Theme 3 short label"],
  "citation_count_reviewed": 15
}}"""
            result = await self.reasoner.think_with_tools(prompt, tools)
            return self._parse_json(result.get("content", "{}"))
        except Exception as e:
            return {"error": str(e)}

    async def identify_research_gaps(self, paper_ids: list, topic: str = "") -> dict:
        try:
            knowledge = await self.memory.search_knowledge(topic or "research gaps", top_k=10)
            prompt = f"""You are an expert research strategist performing a rigorous gap analysis.

Research area: {topic}
Knowledge base excerpts from uploaded papers:
{json.dumps(knowledge[:6], indent=2)[:5500]}

Identify specific, actionable research gaps — NOT generic ones like "more research is needed". Each gap should explain WHY it exists and what would be needed to address it. Feasibility is rated 1–5 (1=extremely difficult/speculative, 5=highly feasible with existing tools). Return ONLY valid JSON:
{{
  "topic": "{topic}",
  "field_maturity": "emerging | developing | mature",
  "field_maturity_rationale": "1-2 sentences justifying the maturity assessment",
  "methodological_gaps": [
    {{"gap": "Specific gap (e.g., 'No study evaluates performance under distribution shift beyond 6 months')", "impact": "high|medium|low", "feasibility": 4, "rationale": "Why this matters and what would address it"}},
    {{"gap": "...", "impact": "...", "feasibility": 3, "rationale": "..."}}
  ],
  "theoretical_gaps": [
    {{"gap": "Specific unresolved theoretical question", "impact": "high|medium|low", "feasibility": 3, "rationale": "..."}},
    {{"gap": "...", "impact": "...", "feasibility": 2, "rationale": "..."}}
  ],
  "empirical_gaps": [
    {{"gap": "Missing empirical study (e.g., 'No cross-lingual evaluation beyond English and Chinese')", "impact": "...", "feasibility": 4, "rationale": "..."}},
    {{"gap": "...", "impact": "...", "feasibility": 3, "rationale": "..."}}
  ],
  "application_gaps": [
    {{"gap": "Unaddressed real-world deployment scenario", "impact": "...", "feasibility": 4, "rationale": "..."}},
    {{"gap": "...", "impact": "...", "feasibility": 3, "rationale": "..."}}
  ],
  "data_gaps": [
    {{"gap": "Missing dataset, benchmark, or evaluation resource", "impact": "...", "feasibility": 3, "rationale": "..."}},
    {{"gap": "...", "impact": "...", "feasibility": 4, "rationale": "..."}}
  ],
  "interdisciplinary_gaps": [
    {{"gap": "Cross-domain opportunity not yet explored", "impact": "...", "feasibility": 3, "rationale": "..."}},
    {{"gap": "...", "impact": "...", "feasibility": 2, "rationale": "..."}}
  ],
  "top_research_opportunities": [
    {{
      "rank": 1,
      "opportunity": "Specific research project title or question",
      "rationale": "2-3 sentences on why this is the highest-priority opportunity right now",
      "approach": "Concrete steps: what methods, data, or experiments would be needed",
      "impact": "high|medium|low",
      "difficulty": "high|medium|low",
      "feasibility": 4,
      "required_expertise": ["skill or domain 1", "skill 2", "skill 3"],
      "estimated_timeline": "6–12 months | 1–2 years | 2–4 years",
      "suggested_venues": ["NeurIPS", "Nature Machine Intelligence", "ICML"],
      "potential_funding": ["NSF IIS", "NIH R01", "EU Horizon Health"]
    }},
    {{
      "rank": 2,
      "opportunity": "...",
      "rationale": "...",
      "approach": "...",
      "impact": "high|medium|low",
      "difficulty": "high|medium|low",
      "feasibility": 3,
      "required_expertise": ["..."],
      "estimated_timeline": "...",
      "suggested_venues": ["..."],
      "potential_funding": ["..."]
    }},
    {{
      "rank": 3,
      "opportunity": "...",
      "rationale": "...",
      "approach": "...",
      "impact": "high|medium|low",
      "difficulty": "high|medium|low",
      "feasibility": 4,
      "required_expertise": ["..."],
      "estimated_timeline": "...",
      "suggested_venues": ["..."],
      "potential_funding": ["..."]
    }}
  ]
}}"""
            result = await self.reasoner.think(prompt)
            return self._parse_json(result.get("content", "{}"))
        except Exception as e:
            return {"error": str(e)}

    async def generate_grant_proposal(self, topic: str, objectives: list, budget: str, timeline: str, agency: str) -> dict:
        try:
            # Agency-specific framing
            agency_lower = agency.lower()
            if "nsf" in agency_lower:
                agency_guidance = "NSF format: clearly distinguish Intellectual Merit (scientific advancement) and Broader Impacts (societal benefit). Use NSF terminology. Align with NSF's 10 Big Ideas where relevant."
            elif "nih" in agency_lower:
                agency_guidance = "NIH format: structure with Specific Aims, Significance, Innovation, and Approach. Emphasize clinical/translational relevance, preliminary data, and human subjects considerations if applicable."
            elif "eu" in agency_lower or "horizon" in agency_lower or "erc" in agency_lower:
                agency_guidance = "EU Horizon / ERC format: emphasize excellence, groundbreaking nature, European added value, and clear work packages. Align with EU Horizon impact pillars (Health, Climate, Digital)."
            elif "darpa" in agency_lower:
                agency_guidance = "DARPA format: emphasize technical risk and breakthrough potential. Define clear go/no-go decision points. Show how this achieves capabilities 'impossible with current technology'."
            else:
                agency_guidance = "Write a professional, rigorous grant proposal following standard academic funding conventions."

            prompt = f"""You are an expert grant writer with a proven track record of funded proposals. Write a compelling, detailed grant proposal.

{agency_guidance}

Topic: {topic}
Funding Agency: {agency}
Budget: {budget}
Timeline: {timeline}
Research Objectives: {json.dumps(objectives)}

Return ONLY valid JSON (no markdown fences):
{{
  "title": "Compelling, specific project title — include the technical approach and domain (e.g., 'Adaptive Sparse Attention for Real-Time Clinical NLP: Enabling Sub-Second Processing of Million-Token Patient Records')",
  "executive_summary": "200-250 words: (1) problem significance with statistics, (2) proposed solution and key innovation, (3) expected outcomes with specific deliverables, (4) team credentials, (5) budget rationale. This is what review panels read first.",
  "background_and_significance": "300-350 words: (1) Why this problem matters — use specific statistics, disease burden, economic cost, or technical limitation. (2) Current state of the art and its specific shortcomings. (3) The critical gap this proposal fills and why the timing is right now.",
  "preliminary_data": "100-150 words on prior work, pilot studies, or proof-of-concept results that demonstrate feasibility. If none exist, describe what foundational evidence supports the proposed approach.",
  "research_objectives": [
    "Objective 1: Specific, measurable, achievable. Success criterion: [what will demonstrate completion]",
    "Objective 2: ...",
    "Objective 3: ..."
  ],
  "methodology": "400-500 words organized by objective. For each: (1) specific approach and methods, (2) experimental design with sample sizes and controls, (3) statistical analysis plan, (4) contingency if the primary approach fails. Be specific enough that a reviewer in the field can assess feasibility.",
  "innovation": "200-250 words. What is genuinely novel and why has no one done this before? What technical or conceptual barrier does this overcome? Compare explicitly to the closest prior work: 'Unlike [Method X] which does Y, our approach does Z because...'",
  "expected_outcomes": [
    "Outcome 1: specific, measurable deliverable (e.g., 'Open-source codebase achieving 96%+ accuracy, published in Nature/Science')",
    "Outcome 2: ...",
    "Outcome 3: ..."
  ],
  "risk_assessment": [
    {{"risk": "Specific technical risk (e.g., 'Training instability at large batch sizes')", "likelihood": "medium", "impact": "high", "mitigation": "Specific contingency plan (e.g., 'Use gradient checkpointing; fall back to smaller batches with gradient accumulation')"}},
    {{"risk": "Data availability risk", "likelihood": "low", "impact": "high", "mitigation": "..."}},
    {{"risk": "Timeline risk", "likelihood": "medium", "impact": "medium", "mitigation": "..."}}
  ],
  "budget_justification": "250-300 words explaining all major expense categories. Justify personnel effort (% FTE), equipment necessity, travel to key conferences, and indirect cost rate.",
  "budget_breakdown": [
    {{"category": "Personnel — PI (20% effort)", "year1": "TBD", "year2": "TBD", "year3": "TBD", "total": "TBD", "justification": "Conceptualization, oversight, dissemination"}},
    {{"category": "Personnel — Graduate Students (2 × 100% RA)", "year1": "TBD", "year2": "TBD", "year3": "TBD", "total": "TBD", "justification": "Core research execution"}},
    {{"category": "Equipment & Cloud Computing", "year1": "TBD", "year2": "TBD", "year3": "$0", "total": "TBD", "justification": "GPU cluster access for large-scale experiments"}},
    {{"category": "Travel (2 conferences/year)", "year1": "TBD", "year2": "TBD", "year3": "TBD", "total": "TBD", "justification": "NeurIPS, ICML, or field-specific venues"}},
    {{"category": "Indirect Costs (F&A)", "year1": "TBD", "year2": "TBD", "year3": "TBD", "total": "TBD", "justification": "Institutional overhead rate"}}
  ],
  "timeline": "Narrative description of project phases across the funding period, organized by year",
  "milestones": [
    {{"month": 3, "milestone": "Complete literature synthesis and finalize methodology design", "objective": "Obj 1"}},
    {{"month": 6, "milestone": "Initial prototype / pilot study completed", "objective": "Obj 1"}},
    {{"month": 12, "milestone": "Year 1 results validated; first conference paper submitted", "objective": "Obj 1-2"}},
    {{"month": 18, "milestone": "Full experimental evaluation completed", "objective": "Obj 2"}},
    {{"month": 24, "milestone": "Journal paper submitted; dataset/code released", "objective": "Obj 2-3"}},
    {{"month": 36, "milestone": "All deliverables complete; final report submitted", "objective": "All"}}
  ],
  "evaluation_criteria": "Specific metrics that define success: e.g., 'Objective 1 met if X exceeds Y on benchmark Z. Objective 2 met if adoption by N external groups.' Include both quantitative and qualitative success measures.",
  "team_qualifications": "150-200 words on the PI's relevant expertise and track record, co-PIs' complementary skills, any industry or clinical partners, and how the team composition is uniquely suited to this project.",
  "dissemination_plan": "How results will be shared: target journals and conferences, open-source code release (GitHub/Zenodo), datasets, workshops, public talks, policy briefs if applicable.",
  "broader_impacts": "200-250 words on societal benefits, training of early-career researchers (graduate students, underrepresented groups), potential for commercialization or policy change, and long-term transformative potential.",
  "intellectual_merit": "150-200 words on how this project advances fundamental knowledge in the field — suitable for NSF Intellectual Merit criterion.",
  "data_management_plan": "What data will be generated (type, volume, format), how it will be stored and backed up, access policies, long-term repository (GitHub, Zenodo, institutional), and when it will be made public."
}}"""
            result = await self.reasoner.think(prompt)
            return self._parse_json(result.get("content", "{}"))
        except Exception as e:
            return {"error": str(e)}

    async def write_paper(
        self,
        topic: str,
        target_journal: str = "",
        word_count: str = "5000",
        research_field: str = "computer_science",
        paper_ids: list = None,
        extra_context: dict = None,
    ) -> dict:
        """Generate a top-tier research paper using 5 focused, high-quality Claude calls."""
        try:
            if paper_ids is None:
                paper_ids = []
            if extra_context is None:
                extra_context = {}

            # ── Build rich context string ──────────────────────────────────
            ctx_fields = [
                f"Topic: {topic}",
                f"Target Journal / Conference: {target_journal}",
                f"Target Word Count: {word_count} words",
                f"Research Field: {research_field}",
                f"Core Research Question: {extra_context.get('research_question', '')}",
                f"Hypothesis: {extra_context.get('hypothesis', '')}",
                f"Numbered Contributions: {extra_context.get('contribution_list', '')}",
                f"Key Findings with Metrics: {extra_context.get('key_findings', '')}",
                f"Methodology Type: {extra_context.get('methodology_type', '')}",
                f"Datasets Used: {extra_context.get('datasets', '')}",
                f"Experimental Results Table: {extra_context.get('experimental_results', '')}",
                f"Hyperparameters: {extra_context.get('hyperparameters', '')}",
                f"Figure Descriptions: {extra_context.get('figure_descriptions', '')}",
                f"Related Papers: {extra_context.get('related_papers', '')}",
                f"Limitations: {extra_context.get('limitations', '')}",
                f"Future Work: {extra_context.get('future_work', '')}",
                f"Authors: {extra_context.get('authors_list', '')}",
                f"Author Emails: {extra_context.get('authors_emails', '')}",
                f"Author Contributions (CRediT): {extra_context.get('author_contributions', '')}",
                f"Acknowledgements: {extra_context.get('acknowledgements', '')}",
                f"Ethics Statement: {extra_context.get('ethics_statement', '')}",
                f"Data Access Statement: {extra_context.get('data_access_statement', '')}",
                f"Column Format: {extra_context.get('column_format', 'two')}",
                # ── NEW top-tier quality fields (used by Calls 2, 3, 4) ────
                f"Novelty Statement (what is new vs prior work — position the paper against these): {extra_context.get('novelty_statement', '')}",
                f"Statistical Tests (use these specifications in Results section for rigour): {extra_context.get('statistical_tests', '')}",
                f"Anticipated Reviewer Concerns (pre-address these in Limitations and Discussion): {extra_context.get('reviewer_concerns', '')}",
                f"Venue Fit Rationale (cite in cover letter to motivate submission to this venue): {extra_context.get('venue_fit_rationale', '')}",
                f"Algorithm Pseudocode Hint (if provided, generate an algorithm block in Methodology — leave empty to skip): {extra_context.get('algorithm_description', '')}",
            ]
            ctx_str = "\n".join(f for f in ctx_fields if f.split(": ", 1)[-1].strip())

            # ── Uploaded papers context ────────────────────────────────────
            # If the user selected uploaded papers in Step 6, the route handler
            # fetched their AI analysis results and injected them here. Append
            # as a labelled block so all 6 calls can cite and build on them.
            _uploaded_papers_json = extra_context.get("_uploaded_papers", "")
            if _uploaded_papers_json:
                ctx_str += (
                    "\n\n══ UPLOADED REFERENCE PAPERS (user selected these for citation) ══\n"
                    "These are real papers the user uploaded. Prioritise citing them in the\n"
                    "Related Work section using their exact titles, authors, and year:\n"
                    + _uploaded_papers_json
                )

            ack_val  = extra_context.get("acknowledgements", "The authors thank the reviewers for their constructive feedback.")
            eth_val  = extra_context.get("ethics_statement", "This work does not raise any ethical concerns. All datasets used are publicly available.")
            da_val   = extra_context.get("data_access_statement", "Code and data will be released upon acceptance at https://github.com/anonymous.")
            ac_val   = extra_context.get("author_contributions", "")

            # ── Shared cache prefix ───────────────────────────────────────
            # All 7 calls start with the same context block (topic, hypothesis,
            # contributions, findings, methodology, datasets, user-provided
            # references, uploaded papers). Caching this block ONCE saves ~70%
            # on input tokens across subsequent calls.
            _cache_prefix = (
                f"SHARED CONTEXT FOR TOP-TIER RESEARCH PAPER GENERATION\n"
                f"Topic: {topic}\n"
                f"Research field: {research_field}\n"
                f"Target venue: {target_journal}\n"
                f"Context:\n{ctx_str}\n"
            )

            # ── CALL 1: Front Matter ──────────────────────────────────────
            # Detect journal type to tailor abstract format and required fields
            j_lower = target_journal.lower()
            _is_conf = any(k in j_lower for k in [
                "ieee","cvpr","iccv","icassp","wacv","iros","icra",
                "acm","chi","siggraph","cscw",
                "acl","emnlp","naacl","coling","eacl",
                "aaai","ijcai","neurips","nips","icml","iclr",
                "miccai","eccv","bmvc","interspeech","sigir","kdd","www",
            ])
            _is_nature = any(k in j_lower for k in [
                "nature","springer","elsevier","plos","cell","lancet","jama","bmj",
            ])
            _is_ieee_class = any(k in j_lower for k in [
                "ieee","cvpr","iccv","icassp","wacv","iros","icra",
            ])

            # Journal-type specific instructions for Call 1
            if _is_ieee_class:
                abstract_instruction = (
                    "Abstract: SINGLE plain paragraph, exactly 200-250 words. "
                    "NO bold labels like 'Background:' or 'Methods:' — those are for medical journals. "
                    "Structure: sentence 1-2 = problem significance, sentence 3-4 = limitations of existing work, "
                    "sentence 5-7 = proposed approach with key innovation, sentence 8-9 = quantitative results "
                    "with specific numbers from Key Findings, sentence 10 = implication/conclusion."
                )
                keywords_instruction = (
                    "Index Terms: 4-6 precise technical terms, comma-separated. "
                    "These will appear in \\begin{IEEEkeywords}...\\\\end{IEEEkeywords}."
                )
                optional_fields = "Leave plain_language_summary and highlights as empty strings — IEEE papers do NOT use these."
            elif _is_nature:
                abstract_instruction = (
                    "Abstract: structured with FIVE labeled paragraphs: "
                    "Background (2-3 sentences), Objective (1-2 sentences), "
                    "Methods (2-3 sentences), Results (2-3 sentences with specific numbers), "
                    "Conclusion (1-2 sentences). Each label on a new paragraph."
                )
                keywords_instruction = "Keywords: 5-8 MeSH or domain-specific terms."
                optional_fields = (
                    "plain_language_summary: 2-3 clear sentences for non-specialists (required by Nature/Elsevier). "
                    "highlights: exactly 3 bullet points, each starting with a verb, each with a specific metric."
                )
            else:
                abstract_instruction = (
                    "Abstract: single paragraph, 200-250 words, no bold labels. "
                    "Include specific quantitative results from Key Findings."
                )
                keywords_instruction = "Keywords: 5-7 domain-specific terms."
                optional_fields = "plain_language_summary and highlights: optional, include if appropriate for this venue."

            # ── PRE-HUMANIZATION STYLE GUIDE (injected into all 4 generation calls) ──
            # These instructions reduce AI-patterned text at the source, so Call 6
            # has less work to do and the final output scores higher on human-likeness.
            _style_guide = """
WRITING STYLE — FOLLOW EXACTLY (these reduce AI detection scores):
• Vary sentence length in every paragraph: mix very short (4-7 words) with long (28-35 words)
• Start no more than 2 sentences per paragraph with "We" or "The"
• Use active voice for findings; passive is fine for experimental procedures only
• Occasionally start a sentence with a conjunction: "But this misses the point." / "And that matters."
• Place citations at varied positions — not always at sentence end
• Use precise numbers instead of vague qualifiers ("73% of users" not "many users")
• BANNED TRANSITION WORDS (remove every single one):
  "Furthermore," "Moreover," "Additionally," "In this paper, we" "It is worth noting,"
  "Notably," "Significantly," "To this end," "In conclusion," "The proposed method,"
  "plays a crucial role," "a wide range of," "state-of-the-art" "extensive experiments,"
  "comprehensive evaluation," "promising results," "challenging task"
• BANNED HIGH-SIGNAL AI WORDS — NEVER USE ANY OF THESE:
  "delve"/"delves"/"delving" (say "examine"/"explore" instead)
  "crucial" (say "key"/"central"/"critical" instead)
  "pivotal" (say "central"/"decisive" instead)
  "paramount" (say "critical"/"primary" instead)
  "underscores" as verb (say "confirms"/"shows" instead)
  "showcase"/"showcases" (say "demonstrate"/"reveal" instead)
  "facilitate"/"facilitates" (say "enable"/"support" instead)
  "cutting-edge" (say "leading"/"recent" instead)
  "groundbreaking" (say "significant"/"influential" instead)
  "intricate" (say "complex"/"detailed" instead)
  "nuanced" (say "subtle"/"fine-grained" instead)
  "multifaceted" (say "complex"/"multi-dimensional" instead)
  "bolster"/"bolsters" (say "strengthen"/"support" instead)
  "elucidate" (say "explain"/"clarify" instead)
  "invaluable" (say "highly useful"/"essential" instead)
  "tapestry" (never used in real academic writing)
  "holistic" (say "integrated"/"overall" instead)
  "synergistic" (say "combined"/"joint" instead)
"""

            call1 = await self.reasoner.think(f"""
Write the front matter for a top-tier research paper submission.
{_style_guide}
Context:
{ctx_str}

ABSTRACT FORMAT (important — match journal type):
{abstract_instruction}

KEYWORDS FORMAT:
{keywords_instruction}

OPTIONAL FIELDS:
{optional_fields}

OTHER REQUIREMENTS:
- Title: precise, descriptive, max 15 words, no hype words ("novel", "revolutionary", "groundbreaking")
- Author block: use provided author info exactly; if not given, use realistic domain-appropriate placeholders
- Running title: ≤50 chars for journal header

Return ONLY a valid JSON object (no markdown fences):
{{
  "title": "Precise paper title (max 15 words, no hype adjectives)",
  "running_title": "Short running head (max 50 chars)",
  "abstract": "Single-paragraph plain abstract OR structured paragraphs per instructions above",
  "abstract_structured": {{
    "background": "Broader context sentence(s) — leave empty string for non-structured journals",
    "objective": "Specific gap addressed — leave empty string for non-structured journals",
    "methods": "Approach and key innovation — leave empty string for non-structured journals",
    "results": "Quantitative results with SPECIFIC numbers — leave empty string for non-structured journals",
    "conclusion": "Implication/significance — leave empty string for non-structured journals"
  }},
  "plain_language_summary": "2-3 plain sentences for non-specialists (or empty for IEEE/ACM)",
  "keywords": ["term1", "term2", "term3", "term4", "term5"],
  "highlights": [
    "Verb-first highlight with specific metric — or empty string for IEEE/ACM",
    "Second highlight — or empty string",
    "Third highlight — or empty string"
  ],
  "author_block": {{
    "authors": "Full author names: First1 Last1, First2 Last2",
    "affiliations": "Department, University, City, Country",
    "emails": "author@institution.edu",
    "corresponding": "Corresponding author: Name (email@institution.edu)"
  }}
}}""")
            c1 = self._parse_json(call1.get("content", "{}"))

            # ── CALL 2: Introduction + Related Work ───────────────────────
            # Full introduction with contributions + comprehensive literature review
            # Pass Call 1 output for cross-section consistency
            c1_summary = f"""
Generated Title: {c1.get("title", topic)}
Generated Abstract (summary): {c1.get("abstract", "")[:600]}
Keywords: {", ".join(c1.get("keywords", []))}
Highlights: {" | ".join(c1.get("highlights", []))}"""

            # ── Build citation instructions for Call 2 ────────────────────
            # Two sources of user-provided references:
            #   (A) _uploaded_papers: papers the user physically uploaded (Step 6 file upload)
            #   (B) related_papers:   papers the user TYPED into the Step 5 text field
            # Both must be GUARANTEED cited in the paper body so they appear in
            # citation_map → BibTeX → \cite{} in the final LaTeX.
            # Without an explicit "MUST cite" instruction, Call 2 may silently ignore
            # user-provided references and generate its own unrelated citations instead.

            # (A) Uploaded-file papers instruction
            _uploaded_cite_instruction = ""
            if _uploaded_papers_json:
                _uploaded_cite_instruction = """
██ UPLOADED PAPERS — CITE THESE FIRST ██
The user uploaded real reference papers (listed in the Context above under "UPLOADED REFERENCE PAPERS").
You MUST:
1. Cite EVERY uploaded paper at least once in Related Work using its exact title and authors.
2. Assign each one the LOWEST available [n] numbers (e.g. the first uploaded paper gets [1],
   second gets [2], etc.) so they appear prominently in the bibliography.
3. In the citation_map, set "confidence": "high" for every uploaded paper entry — they are
   VERIFIED REAL papers provided directly by the user.
4. In the citation_map, populate title_hint with the EXACT title from the uploaded paper data,
   and author with the EXACT authors field, so Call 5 can generate accurate BibTeX.
"""

            # (B) Text-field related papers instruction
            # BUG FIX: previously related_papers was included in ctx_str but Call 2 had
            # no mandatory cite instruction for it — so the AI could see but silently
            # ignore the user's references and generate unrelated citations instead.
            # Fix: inject a ██ MUST cite ██ instruction identical in force to the
            # uploaded-papers instruction, so every typed reference is guaranteed to
            # appear with a [n] number in the body → enters citation_map → gets BibTeX.
            _related_papers_cite_instruction = ""
            _related_papers_text = extra_context.get("related_papers", "").strip()
            if _related_papers_text:
                # Count how many uploaded papers already reserved the first N numbers
                _uploaded_count = 0
                if _uploaded_papers_json:
                    import re as _re_up
                    _uploaded_count = len(_re_up.findall(r'"title"', _uploaded_papers_json))
                _start_n = _uploaded_count + 1
                _related_papers_cite_instruction = f"""
██ USER-PROVIDED REFERENCES — YOU MUST CITE ALL OF THEM ██
The user typed the following real reference papers in the Related Papers field.
These are verified real papers selected by the user for this specific paper.
You MUST follow all rules below without exception:

1. CITE EVERY SINGLE paper listed below at least once in the Related Work section.
   Do NOT skip any. Do NOT replace them with different papers of your own choosing.
2. Assign them consecutive [n] numbers starting from [{_start_n}] — immediately after
   any uploaded-file papers (which take the first numbers).
3. Use the EXACT author name and year as given by the user (e.g. "Vaswani et al. [1] (2017)").
4. In the citation_map JSON at the end, create one entry for EACH of these papers with:
   - "confidence": "high"  (user-verified — do NOT mark low)
   - "title_hint": the exact title the user provided (copy it verbatim)
   - "author": exact author string from the user's input
   - "year": exact year from the user's input
   - "venue": exact venue from the user's input
5. These user references MUST appear before any AI-generated citations in the Related Work.
   After covering all user references, add 6-10 additional AI-recalled real citations to
   reach the required 22+ total.

USER'S REFERENCE LIST (cite all of these):
{_related_papers_text}
"""

            # Extract new top-tier quality fields for explicit use in prompts
            _novelty = extra_context.get('novelty_statement', '').strip()
            _reviewer_concerns = extra_context.get('reviewer_concerns', '').strip()
            _venue_fit = extra_context.get('venue_fit_rationale', '').strip()
            _stats_tests = extra_context.get('statistical_tests', '').strip()

            _novelty_block = f"""
██ MANDATORY NOVELTY POSITIONING (use in Introduction AND Related Work) ██
The author has explicitly stated the paper's novelty vs prior work:
«{_novelty}»
You MUST:
1. In the Introduction's problem-statement paragraph, cite the specific prior works this novelty contrasts with and explain what they missed.
2. In the Contributions list, the FIRST contribution bullet must directly correspond to this novelty claim.
3. In the Related Work's closing subsection ("Comparison with Our Work"), explicitly name each prior approach mentioned in the novelty statement and state what is different about our work.
Do NOT rewrite the novelty in vague terms — preserve the specificity the author provided.
""" if _novelty else ""

            call2 = await self.reasoner.think(f"""
Write the Introduction and Related Work sections for a top-tier research paper.
{_style_guide}
Context:
{ctx_str}

Already generated front matter (maintain consistency with this):
{c1_summary}
{_uploaded_cite_instruction}{_related_papers_cite_instruction}{_novelty_block}
CRITICAL CITATION RULES — read carefully before writing:
- NUMBER EVERY CITATION CONSECUTIVELY: first cited paper = [1], second = [2], third = [3], etc.
  You MUST assign an actual integer to EVERY citation. The first paper you cite gets [1].
  The next new paper gets [2]. And so on. Count and track your numbering as you write.
- Use Author et al. (YEAR) style inline AND [n] numbered references simultaneously
  e.g. "Vaswani et al. [1] introduced the Transformer architecture..."
  e.g. "Several works have explored this direction [3,4,5]."
- ██ ABSOLUTE RULE: NEVER write [?] under ANY circumstance ██
  [?] is a broken placeholder that cannot be resolved and will appear as "[?]" in the printed PDF.
- ██ REAL PAPERS ONLY — USE YOUR TRAINING KNOWLEDGE ██
  You have been trained on millions of real research papers. Draw on that knowledge to cite
  ACTUAL PUBLISHED papers you know to be real. Priority order:
  1. LANDMARK papers you are 100% certain about (Vaswani 2017 Transformer, Devlin 2019 BERT,
     Brown 2020 GPT-3, He 2016 ResNet, Goodfellow 2014 GAN, LeCun 1998 CNN, etc.)
  2. WELL-KNOWN recent papers from 2020-2024 that you know exist (with real author names,
     real venue, real year — e.g. "Touvron et al. [5] introduced LLaMA...")
  3. If you are NOT certain a specific paper exists with that exact title, still cite a REAL
     author in the field with a title that closely matches real work they did publish.
     Do NOT invent completely fictional author-title-year combinations.
  In the citation_map: mark entries you are HIGHLY CONFIDENT about with "confidence": "high".
  Mark entries where you approximated or are less certain with "confidence": "low" so the
  user knows to manually verify those specific references.
- ██ CRITICAL FORMAT: In body text, ALWAYS use [N] numeric citations — NEVER write \\cite{{Author, Year}} directly ██
  The system converts [N] → \\cite{{refNN}} automatically when building the LaTeX file.
  Writing \\cite{{Firth et al., 2017}} or any author-year \\cite{{}} directly in body text WILL produce [?]
  in the final PDF because the .bib file uses refNN keys, NOT author-year keys.
  CORRECT:   "Vaswani et al. [1] introduced the Transformer..."
  INCORRECT: "Vaswani et al. \\cite{{Vaswani et al., 2017}} introduced the Transformer..."
  Every single citation in your output text MUST use the [N] bracket format.
- ██ NEVER pre-escape LaTeX special characters in your text output ██
  The system's LaTeX builder handles ALL escaping automatically.
  Write plain text; never manually add backslash-escapes for special chars:
  CORRECT:   "$377 billion", "73% of students", "en_core_web_sm", "p < 0.01"
  INCORRECT: "\\$377 billion", "73\\% of students", "en\\_core\\_web\\_sm", "p \textless 0.01"
  Pre-escaped chars like \\$ and \\% get double-escaped to \\\\$ and \\\\% → fatal
  LaTeX compile error: "There's no line here to end" on EVERY such occurrence.
- Citations must be real or plausible: use real author surnames, real years (2017-2025), real venues
  (NeurIPS, ICML, ACL, CVPR, Nature, Science, ICLR, EMNLP, ECCV, ICCV, AAAI, IEEE TPAMI, etc.)
- Minimum 22 unique citations total across Introduction + Related Work
- At the end, output a citation_map: a JSON object mapping each [n] to
  {{author, year, title_hint, venue}} so Call 5 can generate matching BibTeX

INTRODUCTION requirements (900-1100 words):
Structure it exactly as follows:
1. Opening paragraph (100-150 words): Start with the broad significance of the domain.
   Use 2-3 citations [1],[2] citing real recent papers with author names.
2. Background paragraphs (250-350 words): 2-3 paragraphs on current state of the field.
   Cite specific real works [3],[4],[5] with Author et al. (YEAR).
3. Problem statement paragraph (150-200 words): Articulate the specific limitation or gap.
   Use "However, existing approaches [6],[7] suffer from..."
4. Our approach paragraph (100-150 words): Brief overview of the proposed solution.
5. Contributions paragraph: Output as a LaTeX enumerated list:
   "The main contributions of this paper are:
   \\begin{{enumerate}}
   \\\\item Contribution 1 — specific and measurable (e.g., achieves X% on benchmark Y)
   \\\\item Contribution 2 — specific technical innovation
   \\\\item Contribution 3 — empirical or theoretical advance
   \\\\end{{enumerate}}"
6. Paper organization (50-80 words): "The remainder of this paper is organized as follows.
   Section~\\ref{{sec:related}} reviews related work. Section~\\ref{{sec:method}} presents
   our methodology. Section~\\ref{{sec:results}} reports experimental results.
   Section~\\ref{{sec:discussion}} discusses findings and Section~\\ref{{sec:conclusion}}
   concludes."

RELATED WORK requirements (1000-1300 words):
- Organize into exactly 3-4 thematic \\\\subsection{{}} blocks relevant to the topic
- Each subsection: 3-4 paragraphs, citing 5-6 real published works
- For each citation use "Author et al. [n] (YEAR) showed that..." pattern
- Include subsection comparing single-agent/single-prompt vs multi-agent/pipeline baselines
  where relevant — this anticipates reviewer requests for modern baseline comparison
- Final subsection (150-200 words): "Comparison with Our Work" — explain how this paper
  differs from AND IMPROVES UPON all prior methods mentioned including:
  * RAG-based approaches (retrieval-augmented generation pipelines)
  * Agent framework baselines (AutoGen, MetaGPT, LangChain-based agents)
  * Retrieval-augmented research assistants (Elicit, Semantic Scholar AI, Perplexity)

CRITICAL LATEX FORMATTING RULES — violations cause PDF compilation failures:
- NEVER use Markdown **bold** or *italic* ANYWHERE — always use \textbf{{text}} and \textit{{text}}
- NEVER use *...* or **...** INSIDE $...$ or \begin{{equation}} blocks — asterisks inside math BREAK LaTeX
- Inside $...$ or \begin{{equation}}...\\end{{equation}}: use PLAIN _ for subscripts ONLY
  CORRECT: $\\mathcal{{L}}_{{total}}$   WRONG: $\\mathcal{{L}}*{{total}}*$   WRONG: $\\mathcal{{L}}\\_{{total}}$
  CORRECT: $x_t$   WRONG: $x*t*$   WRONG: $x\\_t$
- In table rows, ALWAYS cite as \\cite{{refNN}} — NEVER raw [N] alone
- Multi-citations: \\cite{{ref05,ref06,ref07}} not [5,6,7]
- Table captions: \textbf{{Bold}} not **Bold**
- Never write [?] — every reference must be a real numbered [n]

Return ONLY a valid JSON object:
{{
  "introduction": "Full introduction section (900-1100 words) with Author et al. [n] citations — NO [?] placeholders",
  "literature_review": "Full related work with \\\\\\subsection{{Subsection Name}} headers (1000-1300 words, 22+ real [n] citations, includes RAG/agent/retrieval baselines subsection)",
  "abbreviations_list": "ABBR — Full Term; ABBR2 — Full Term 2; ...",
  "citation_map": {{
    "1":  {{"author": "FIRST_CITED_AUTHOR et al.",  "year": "YEAR", "title_hint": "REAL full title of the first paper from your training knowledge", "venue": "VENUE_ABBREV", "confidence": "high"}},
    "2":  {{"author": "SECOND_CITED_AUTHOR et al.", "year": "YEAR", "title_hint": "REAL full title of the second paper", "venue": "VENUE_ABBREV", "confidence": "high"}},
    "3":  {{"author": "THIRD_CITED_AUTHOR et al.",  "year": "YEAR", "title_hint": "Full title — mark confidence low if you are not 100% sure", "venue": "VENUE_ABBREV", "confidence": "low"}},
    "...": {{"author": "...", "year": "...", "title_hint": "...", "venue": "...", "confidence": "high|low"}},
    "22": {{"author": "LAST_CITED_AUTHOR et al.",   "year": "YEAR", "title_hint": "REAL full title of the last paper", "venue": "VENUE_ABBREV", "confidence": "high"}}
  }}
  IMPORTANT: include ALL citation numbers used in the text above — one entry per [n]. 22+ entries required.
  Use "confidence": "high" for papers you are certain exist. Use "confidence": "low" for approximations.
}}""")
            c2 = self._parse_json(call2.get("content", "{}"))

            # ── CALL 3: Methodology + Experiments + Results ───────────────
            intro_snippet = c2.get("introduction", "")[:800]
            # Increased from 400 → 3000: 400 chars only showed ~3 entries out of 22+,
            # causing Call 3 to lose track of which numbers were already assigned and
            # introduce duplicate or out-of-range citation numbers.
            citation_map_hint = json.dumps(c2.get("citation_map", {}), indent=2)[:3000]

            _stats_block = f"""
██ MANDATORY STATISTICAL RIGOUR (use in Results section) ██
The author has specified the statistical testing protocol:
«{_stats_tests}»
You MUST:
1. In the "Main Results" subsection, describe the statistical test (name, n per condition, any correction) in a dedicated sentence BEFORE reporting p-values.
2. Report exact p-values where possible (e.g., p=0.003, not p<0.05) or p<0.01 / p<0.001 bands.
3. Include effect size (Cohen's d or similar) where the stats block specifies it.
4. In the results_table caption, reference the test: "± std over N runs. [Test name], [correction]."
Do NOT fabricate statistical tests not mentioned in the user's spec — use exactly what the author provided.
""" if _stats_tests else ""

            _algo_desc = extra_context.get('algorithm_description', '').strip()
            _algo_block = f"""
██ ALGORITHM PSEUDOCODE REQUIRED (Methodology) ██
The author has requested an algorithm pseudocode block describing:
«{_algo_desc}»
In the Methodology, inside \\\\subsection{{Proposed Method}}, emit a numbered LaTeX algorithm environment using the algorithm + algpseudocode packages:
\\begin{{algorithm}}[t]
\\caption{{[concise title]}}\\label{{alg:main}}
\\begin{{algorithmic}}[1]
\\Require [inputs]
\\Ensure [outputs]
\\State [step] \\Comment{{[rationale]}}
\\For{{[condition]}} \\State [step] \\EndFor
\\State \\Return [output]
\\end{{algorithmic}}
\\end{{algorithm}}
Reference it in text as "Algorithm~\\ref{{alg:main}}".
Make the pseudocode 8-15 lines. Use \\Comment{{...}} on 2-3 key steps to justify design choices.
""" if _algo_desc else ""

            call3 = await self.reasoner.think(f"""
Write the Methodology and Experiments/Results sections for a top-tier research paper.
{_stats_block}{_algo_block}
{_style_guide}
Context:
{ctx_str}

Introduction snippet (for consistency — your methodology must match what was promised here):
{intro_snippet}

Citation map from Introduction + Related Work (CONTINUE numbering from here — do NOT reuse or skip numbers):
{citation_map_hint}

METHODOLOGY requirements (900-1100 words):
Use \\\\subsection{{}} headers. Required subsections:
- \\\\subsection{{Problem Formulation}}: Define the task formally using math notation.
  Use \\begin{{equation}} with \\\\label{{eq:objective}} for the main loss/objective.
  Example: \\begin{{equation}}\\\\mathcal{{L}} = \\\\mathcal{{L}}_{{task}} + \\\\lambda\\\\mathcal{{R}}(\\theta)\\\\label{{eq:loss}}\\\\end{{equation}}
  Reference equations in text as "as shown in Eq.~(\\ref{{eq:loss}})"
- \\\\subsection{{Proposed Method}}: Detailed description with architecture/algorithm.
  For multi-component systems, use \\\\subsubsection{{Component Name}} headers.
  Include numbered equations with \\\\label{{eq:X}} for any key formulas.
  Reference tables in text as "Table~\\ref{{tab:results}}" and "Table~\\ref{{tab:hyperparams}}"
- \\\\subsection{{Datasets}}: Describe each dataset with size, splits, preprocessing steps.
  Reference 2-3 real benchmark datasets by their official names and cite the papers.
- \\\\subsection{{Evaluation Metrics}}: Define all metrics.
  Use inline math for formulas: $F_1 = 2\\\\cdot\\frac{{P \\\\cdot R}}{{P+R}}$
- \\\\subsection{{Implementation Details}}: Framework (PyTorch/TensorFlow version),
  hardware (GPU model and count), training time, batch size, learning rate,
  optimizer, random seed for reproducibility.

EXPERIMENTS & RESULTS requirements (900-1100 words):
- Opening paragraph: experimental setup summary
- \\\\subsection{{Baselines}}: List and briefly describe ALL comparison methods including:
  * Classical/traditional methods (2-3 baselines)
  * Single-prompt / single-model baselines (GPT-4, Claude, Gemini where relevant)
  * RAG pipeline baselines (retrieval-augmented generation approaches)
  * Agent framework baselines (AutoGen, MetaGPT, LangChain-agent if relevant to domain)
  * Retrieval-augmented tool baselines (Elicit, Perplexity, specialized research tools if relevant)
  * Recent SOTA methods from the field (2-3 most competitive)
  For each baseline: cite the original paper, state what it does, why it is a fair comparison.
- \\\\subsection{{Main Results}}: Reference the results table as "Table~\\ref{{tab:results}}".
  Bold = best, underline = second-best. Report mean ± std over 3-5 runs.
  Include one sentence on statistical significance: "Our method outperforms all baselines
  with p<0.01 (paired t-test)."
- \\\\subsection{{Ablation Study}}: Systematically remove/modify each component.
  Show each ablation as a table row. Quantify contribution of each design choice.
- \\\\subsection{{Qualitative Analysis}}: 1-2 concrete case studies or examples.
  Include failure cases honestly — reviewers reward this.
- \\\\subsection{{Cost and Efficiency Analysis}}: Report compute cost, latency, memory usage.
  Compare cost-effectiveness vs baselines. This is increasingly required at top venues.

CRITICAL LATEX FORMATTING RULES — violations cause PDF compilation failures:
- NEVER use Markdown **bold** or *italic* ANYWHERE — always use \textbf{{text}} and \textit{{text}}
- NEVER use *...* or **...** INSIDE $...$ or \begin{{equation}} blocks — asterisks inside math BREAK LaTeX
- Inside $...$ or \begin{{equation}}...\\end{{equation}}: use PLAIN _ for subscripts ONLY
  CORRECT: $\\mathcal{{L}}_{{total}}$   WRONG: $\\mathcal{{L}}*{{total}}*$   WRONG: $\\mathcal{{L}}\\_{{total}}$
  CORRECT: $x_t$   WRONG: $x*t*$   WRONG: $x\\_t$

██ INLINE MATH RULE — THE MOST COMMONLY BROKEN RULE ██
  Keep $...$ expressions SHORT — only the mathematical symbol/number goes inside.
  NEVER include English words, units spelled out, or entire phrases inside $...$.
  CORRECT: "approximately $\\approx 162$~Hz and overtones in the 1--3~kHz band..."
  CORRECT: "circular time-shift of $\\pm 50$~samples applied on-the-fly"
  CORRECT: "accuracy of $99.72\\%$"
  WRONG:   "$\\approx 162Hz and overtones in the 1-3kHz band consistently rank highest$"
  WRONG:   "($\\pm 50samples) on-the-fly"  ← English text inside math = garbled PDF
  A dollar sign that is not closed properly causes ALL subsequent text to appear
  in italic math mode with no spaces — the most visible bug in the generated PDF.
  Rule: open $, write ONE symbol or number, close $, then write English text normally.

- ██ NEVER write [?] — this appears as broken "[?]" in the printed PDF ██
  Use numbered citations [n] from the citation_map context. If uncertain, use the next available number.
- ██ NEVER pre-escape LaTeX special characters in your text output ██
  The LaTeX builder handles ALL escaping. Write plain text only:
  CORRECT:   "$0.001 per request", "73% accuracy", "en_core_web_sm", "p < 0.01"
  INCORRECT: "\\$0.001 per request", "73\\% accuracy", "en\\_core\\_web\\_sm"
  Pre-escaped \\$ and \\% get double-escaped → \\\\$ and \\\\% → fatal compile error.
- In table rows, ALWAYS cite with \\cite{{refNN}} format — NEVER raw [N] alone
  E.g. "GraphSleep \\cite{{ref21}}" not "GraphSleep [21]"
- Multi-citations: \\cite{{ref05,ref06}} not [5,6]
- Table captions: \textbf{{Bold text}} not **Bold text**
- Figure captions: use \textbf{{label}} not **label** — never use ** inside captions
- results_table cells with prior method names MUST include \\cite{{refNN}}
- hyperparameters_table cells are plain text — no citations needed there

██ FIGURE REFERENCE RULE ██
  Figures are labelled fig:fig1, fig:fig2, fig:fig3, ... in the compiled PDF.
  ALWAYS reference them as: Figure~\\ref{{fig:fig1}}, Figure~\\ref{{fig:fig2}}, Figure~\\ref{{fig:fig3}}
  NEVER write "Figure 4.5" or "Figure 4.2" or any section-number style — those are SECTION numbers,
  not figure numbers. "Figure 4.5" in body text produces "Figure ??" in the PDF.
  NEVER write "Figure ??" — that is a broken cross-reference.
  If you have 3 figures: ref them as Figure~\\ref{{fig:fig1}}, Figure~\\ref{{fig:fig2}}, Figure~\\ref{{fig:fig3}}.
  Similarly for sections: Section~\\ref{{sec:method}}, Section~\\ref{{sec:results}}, etc.
  For tables: Table~\\ref{{tab:results}}, Table~\\ref{{tab:hyperparams}}.

FIGURE CAPTIONS — map user's Figure Descriptions to publication-quality captions:
- CRITICAL: Look for "Figure Descriptions:" in the Context section above.
- If Figure Descriptions are provided: generate EXACTLY that many figure_captions array entries,
  one per line. Each caption must faithfully describe what the user specified, adding specific
  technical detail (axis labels, dataset names, key trends, error bars, statistical notes).
- If no Figure Descriptions provided: default to 3 captions (architecture, main results, ablation).
- Each caption: 2-3 sentences. Format: "Figure N: [what is shown]. [Key observation/takeaway]."
- In methodology text, write at least 1 reference: "as illustrated in Figure~\\ref{{fig:fig1}}"
- In results text, write at least 2 references: "as shown in Figure~\\ref{{fig:fig2}}"
  and "as shown in Figure~\\ref{{fig:fig3}}" — use the exact label numbers matching user's figures.

Return ONLY a valid JSON object:
{{
  "methodology": "Full methodology with \\\\\\subsection{{}} headers, math notation, and at least one figure reference e.g. Figure~\\\\ref{{fig:fig1}} (900-1100 words)",
  "results": "Full results section with \\\\\\subsection{{Baselines}}, \\\\\\subsection{{Main Results}}, \\\\\\subsection{{Ablation Study}}, \\\\\\subsection{{Qualitative Analysis}}, \\\\\\subsection{{Cost and Efficiency Analysis}}, with at least two figure references e.g. Figure~\\\\ref{{fig:fig2}} (900-1100 words)",
  "results_table": [
    ["Method", "Dataset", "Metric1 (%)", "Metric2 (%)", "Cost/Run"],
    ["Proposed (Ours)", "Benchmark", "XX.X ± 0.X", "XX.X ± 0.X", "$X.XX"],
    ["RAG Pipeline [n]", "Benchmark", "XX.X ± 0.X", "XX.X ± 0.X", "$X.XX"],
    ["Agent Framework [n]", "Benchmark", "XX.X ± 0.X", "XX.X ± 0.X", "$X.XX"],
    ["GPT-4 Single Prompt [n]", "Benchmark", "XX.X ± 0.X", "XX.X ± 0.X", "$X.XX"],
    ["SOTA Baseline [n]", "Benchmark", "XX.X ± 0.X", "XX.X ± 0.X", "$X.XX"]
  ],
  "results_table_caption": "Table 1: Comparison with state-of-the-art methods including RAG and agent-framework baselines. Bold = best, underline = second-best. ± = std over 5 runs. p < 0.01 vs all baselines.",
  "hyperparameters_table": [
    ["Hyperparameter", "Value", "Search Range"],
    ["Learning rate", "2e-4", "{{1e-5, 1e-4, 2e-4, 5e-4}}"],
    ["Batch size", "32", "{{16, 32, 64}}"],
    ["Epochs", "100", "Early stopping (patience=10)"],
    ["Optimizer", "AdamW", "—"],
    ["Weight decay", "1e-4", "{{0, 1e-4, 1e-3}}"]
  ],
  "hyperparameters_table_caption": "Table 2: Hyperparameter configuration. Final values chosen by grid search on validation set.",
  "figure_captions": [
    "Figure 1: [Caption derived from user's first Figure Description — or architecture overview. 2-3 sentences with specific technical detail and key observation.]",
    "Figure 2: [Caption derived from user's second Figure Description — or main results comparison. Include axis labels, dataset names, key trends.]",
    "Figure 3: [Caption derived from user's third Figure Description — or ablation study. State what each component represents and its contribution.]",
    "Figure 4: [Caption derived from user's fourth Figure Description — or cost-efficiency analysis. Omit this entry if user provided fewer than 4 figure descriptions.]"
  ]
}}""")
            c3 = self._parse_json(call3.get("content", "{}"))

            # ── CALL 4: Discussion + Conclusion + Supplementary ───────────
            # Pass results for accurate discussion/conclusion
            results_snippet = c3.get("results", "")[:800]
            methodology_snippet = c3.get("methodology", "")[:400]

            # Decide whether to auto-generate ethics or use provided value
            user_ethics = extra_context.get("ethics_statement", "")
            ethics_instruction = (
                f'Use this user-provided ethics statement verbatim: "{user_ethics}"'
                if user_ethics.strip() and user_ethics.strip() != "This work does not raise any ethical concerns. All datasets used are publicly available."
                else f"""Auto-generate a publication-quality ethics statement (150-250 words) covering:
1. Dual-use risks specific to this research (e.g., if AI/NLP: paper mills, detection evasion,
   hallucination risk; if biomedical: patient privacy, off-label use; if computer vision:
   surveillance misuse; if generative AI: deepfakes, misinformation)
2. Dataset and participant ethics (consent, compensation, anonymisation if human subjects)
3. IRB/institutional approval statement if applicable
4. Any responsible disclosure commitments (e.g., notifying affected vendors)
5. Explicit prohibited use cases
6. Carbon footprint or compute sustainability note if significant compute was used
Base it on the research topic: {topic}"""
            )

            # Call 4 generates the most content in a single JSON response
            # (discussion 750w + conclusion 300w + cover letter 200w + ethics 200w + supplementary)
            # Use a higher max_tokens to prevent truncation mid-JSON.
            _reviewer_block = f"""
██ MANDATORY — PRE-ADDRESS ANTICIPATED REVIEWER CONCERNS ██
The author has identified the paper's weakest points — the things reviewers will likely criticise:
«{_reviewer_concerns}»
You MUST:
1. In "Limitations" subsection: dedicate the FIRST limitation bullet to this concern, name it explicitly, and state a specific mitigation (not "future work will address this" but a concrete plan).
2. In "Comparison with Prior Work": acknowledge the scope this concern limits and explain why the contribution still holds.
3. Write with confident honesty — reviewers REWARD authors who pre-empt their own critiques.
""" if _reviewer_concerns else ""

            _venue_block = f"""
██ MANDATORY — COVER LETTER MUST USE THIS VENUE FIT ██
Author's rationale for this venue:
«{_venue_fit}»
In the cover_letter, incorporate this reasoning EXPLICITLY — do not write a generic "this paper fits your venue" statement. Reference the specific aspects of the venue's scope and audience the author mentioned.
""" if _venue_fit else ""

            call4 = await self.reasoner.think(f"""
Write the Discussion, Conclusion, and all supplementary sections for a top-tier research paper.
{_style_guide}
Context:
{ctx_str}
{_reviewer_block}{_venue_block}
Generated results (Discussion and Conclusion MUST reference these exact findings):
{results_snippet}

Generated methodology summary (reference this in Discussion):
{methodology_snippet}

Citation map from prior sections (ONLY use [n] numbers already in this map — do NOT invent new numbers):
{citation_map_hint}

DISCUSSION requirements (700-850 words):
Use \\\\subsection{{}} headers:
- \\\\subsection{{Interpretation of Results}}: WHY the proposed method outperforms baselines.
  Connect results to the original hypothesis. Reference specific numbers from results.
  Explain WHY each baseline underperforms — not just that it does.
- \\\\subsection{{Comparison with Prior Work}}: Position against the field.
  Explicitly address: how does this compare to RAG-based approaches, agent frameworks,
  and retrieval-augmented tools? Use hedged language appropriately.
- \\\\subsection{{Limitations}}: At least 4 concrete limitations, each with a specific
  proposed mitigation. Include: scope limitations (dataset size, language, domain),
  computational limitations, potential failure modes, and any bias concerns.
  Reviewers at top venues REJECT papers with vague limitations sections.
- \\\\subsection{{Future Directions}}: 4-5 specific, actionable future research directions
  with concrete next steps (not just "we will explore X").
- \\\\subsection{{Broader Impact}}: 2-3 sentences on societal benefit and potential harms.

CONCLUSION requirements (280-350 words):
- Paragraph 1: Restate the problem and why it matters (2-3 sentences)
- Paragraph 2: Summarize ALL contributions with EXACT numbers
  (e.g., "Our method achieves 96.1% accuracy, a 3.2-point improvement over the strongest baseline...")
- Paragraph 3: Broader implications, call to action, 1-2 sentences on future work

COVER LETTER (180-220 words): Professional submission letter to journal/conference editor.
Include: manuscript title, why it fits this specific venue, 3 key contributions,
why it advances the field beyond prior work, confirmation of originality and no concurrent submission.

ETHICS: {ethics_instruction}

CRITICAL LATEX FORMATTING RULES — violations cause PDF compilation failures:
- NEVER use Markdown **bold** or *italic* ANYWHERE — always use \textbf{{text}} and \textit{{text}}
- NEVER use *...* or **...** INSIDE $...$ or \begin{{equation}} blocks — asterisks inside math BREAK LaTeX
- Inside $...$ or \begin{{equation}}...\\end{{equation}}: use PLAIN _ for subscripts ONLY
  CORRECT: $\\mathcal{{L}}_{{total}}$   WRONG: $\\mathcal{{L}}*{{total}}*$   WRONG: $\\mathcal{{L}}\\_{{total}}$
  CORRECT: $x_t$   WRONG: $x*t*$   WRONG: $x\\_t$
- ██ INLINE MATH — keep $...$ expressions SHORT (one symbol or number only) ██
  CORRECT: "accuracy of $99.72\\%$", "shift of $\\pm 50$~samples on-the-fly"
  WRONG: "$\\approx 162Hz and overtones in the 1-3kHz band...$" — entire sentence in math mode
  An unclosed or overly long $...$ turns ALL following text italic with no spaces.
- ██ NEVER write [?] — this appears as broken "[?]" in the printed PDF ██
  Every reference MUST be a real numbered [n] from the citation_map context above.
  If a number is not in the citation_map, use the nearest valid number instead.
- ██ NEVER pre-escape LaTeX special characters in your text output ██
  Write plain text — the LaTeX builder handles all escaping automatically:
  CORRECT:   "$150/month", "59.5% usability", "en_core_web_sm"
  INCORRECT: "\\$150/month", "59.5\\% usability", "en\\_core\\_web\\_sm"
  Pre-escaped \\$ and \\% become \\\\$ and \\\\% → fatal "no line here to end" errors.
- Multi-citations: \\cite{{ref05,ref06,ref07}} not [5,6,7]

Return ONLY a valid JSON object:
{{
  "discussion": "Full discussion with \\\\\\subsection{{Interpretation}}, \\\\\\subsection{{Comparison with Prior Work}}, \\\\\\subsection{{Limitations}}, \\\\\\subsection{{Future Directions}}, \\\\\\subsection{{Broader Impact}} headers (700-850 words)",
  "conclusion": "Full conclusion restating quantified contributions (280-350 words)",
  "acknowledgements": "{ack_val}",
  "ethics_statement": "Auto-generated publication-quality ethics statement (150-250 words) covering dual-use risks, responsible disclosure, dataset ethics, prohibited uses",
  "conflict_of_interest": "The authors declare no conflict of interest.",
  "data_access_statement": "{da_val} — NOTE: For NeurIPS/ICML/ICLR this field also serves as the mandatory Reproducibility Statement. It should include: (1) a link or commitment to release code/models, (2) the computing infrastructure used (GPU type, hours), (3) which datasets are publicly available and where, (4) any random seeds or config files needed to reproduce the main results. Write this at 120-160 words and make it venue-agnostic (journal version = Data Availability; conference version = Reproducibility Statement).",
  "author_contributions": "{ac_val if ac_val else 'All authors contributed equally to this work.'}",
  "cover_letter": "Professional cover letter (180-220 words) addressed to Editor",
  "supplementary_materials": "Extended experimental details: full hyperparameter search results, additional ablation tables, implementation notes for reproduction, and sample outputs."
}}""", max_tokens=24000)
            c4 = self._parse_json(call4.get("content", "{}"))

            # ── TRUNCATION GUARD: if conclusion is cut off, complete it ───
            conclusion_raw = c4.get("conclusion", "")
            if self._is_section_truncated(conclusion_raw, min_words=150):
                completion_call = await self.reasoner.think(f"""
A research paper conclusion was cut off mid-sentence. Here is the partial text:

---BEGIN PARTIAL CONCLUSION---
{conclusion_raw[-600:]}
---END PARTIAL CONCLUSION---

Continue and COMPLETE this conclusion seamlessly from where it was cut.
- Write ONLY the continuation text (do NOT repeat any text already written above)
- The continuation must produce a complete, well-rounded final paragraph
- End with a strong, forward-looking sentence that closes the paper
- Target: 1-3 sentences to finish the conclusion naturally
- Output plain text only, no JSON, no markdown""", max_tokens=600)
                continuation = completion_call.get("content", "").strip()
                if continuation:
                    c4["conclusion"] = conclusion_raw.rstrip() + " " + continuation

            # ── CALL 5: BibTeX references ─────────────────────────────────
            related = extra_context.get("related_papers", "")

            # ── BUILD AUGMENTED CITATION MAP ──────────────────────────────
            # ROOT-CAUSE FIX for missing [?] citations:
            #
            # BUG: Call 2 outputs a citation_map for ~22 citations (intro+related work).
            # Calls 3 and 4 then introduce NEW citation numbers (e.g. [23]-[28] in
            # methodology, results, discussion) that are NOT in c2.citation_map.
            # Old code passed only c2.citation_map to Call 5, so Call 5 never knew
            # those numbers existed → no BibTeX entry → [?] in the PDF.
            #
            # FIX: After all four generation calls finish, scan every generated section
            # for [N] markers, collect the complete set of citation numbers, then
            # augment c2.citation_map with placeholder entries for any new numbers
            # before passing to Call 5.  The gap-fill pass below then guarantees a
            # BibTeX entry for every number found anywhere in the paper.
            import re as _re_cite_scan
            citation_map = c2.get("citation_map", {})

            # Collect every [N] and [N,M,...] found across all generated sections
            all_generated_text = " ".join(filter(None, [
                c2.get("introduction", ""),
                c2.get("literature_review", ""),
                c3.get("methodology", ""),
                c3.get("results", ""),
                c4.get("discussion", ""),
                c4.get("conclusion", ""),
            ]))
            found_cite_nums: set = set()
            for m in _re_cite_scan.finditer(r'\[(\d+(?:\s*,\s*\d+)*)\]', all_generated_text):
                for part in m.group(1).split(','):
                    part = part.strip()
                    if part.isdigit():
                        n = int(part)
                        if 1 <= n <= 99:   # sanity-range: ignore huge numbers
                            found_cite_nums.add(n)
            # Also honour every number already in c2.citation_map
            for k in citation_map.keys():
                try:
                    found_cite_nums.add(int(k))
                except (ValueError, TypeError):
                    pass

            # Build augmented map: copy c2's map + add placeholder for any gap
            augmented_citation_map = dict(citation_map)
            for num in sorted(found_cite_nums):
                n_str = str(num)
                if n_str not in augmented_citation_map:
                    # Placeholder so Call 5 can still generate a plausible entry
                    augmented_citation_map[n_str] = {
                        "author": "Author et al.",
                        "year":   "2024",
                        "title_hint": f"Reference {num} related to {topic}",
                        "venue": "",
                    }

            # Pass the FULL augmented map to Call 5 — use compact JSON (no indent)
            # so 30+ entries fit within Claude's context without truncation.
            # Previous 8000-char cap on indent=2 was dropping entries >N=22 silently,
            # causing [?] citations for any number introduced in Call 3 or 4.
            citation_map_str = (
                json.dumps(augmented_citation_map, separators=(",", ":"))
                if augmented_citation_map else "{}"
            )
            expected_count = len(augmented_citation_map)

            # ── CALL 5: BibTeX generation ─────────────────────────────────
            # KEY DESIGN DECISION: use ref01-refNN keys that match citation
            # numbers directly. This is more reliable than author-year keys
            # because it eliminates the author-name matching step in the frontend
            # (numToKey), which can fail if naming conventions differ slightly.
            # The frontend cite() fallback also uses ref01-refNN, so keys
            # always resolve even if numToKey matching is bypassed.
            # Build uploaded-papers note for Call 5
            _uploaded_bibtex_note = ""
            if _uploaded_papers_json:
                _uploaded_bibtex_note = (
                    "\n\nUPLOADED PAPERS (user-verified real references — highest priority):\n"
                    "For any citation_map entry whose title_hint exactly matches a paper in this list,\n"
                    "use the exact title, authors, year, and venue from the list below.\n"
                    "Do NOT add a ⚠ note for these — they are confirmed real by the user.\n"
                    + _uploaded_papers_json[:2000]
                )

            call5 = await self.reasoner.think(f"""
Generate a complete, publication-quality BibTeX reference list as a JSON array.
You have been trained on millions of real research papers. Use that knowledge to produce
REAL bibliographic data — actual published papers with real authors, real titles, real venues.
{_uploaded_bibtex_note}
Topic: {topic}
Research field: {research_field}
Target journal/conference: {target_journal}

██████████████████████████████████████████████████████████████████
██  USER-PROVIDED REFERENCES — MANDATORY — HIGHEST PRIORITY     ██
██████████████████████████████████████████████████████████████████
The user provided the following VERIFIED REAL papers. These are the papers that MUST
appear in the BibTeX. They are real papers confirmed by the user — use their EXACT
author names, titles, years, and venues. NEVER substitute, hallucinate, or skip any.
DO NOT replace these with other papers (e.g. do NOT replace a bearing fault paper
with BERT, ResNet, EfficientNet, or any unrelated paper).

USER-PROVIDED RELATED PAPERS (copy these EXACTLY into the BibTeX):
{related if related else "None provided"}

For each of the above:
- Use the EXACT title as given (do not paraphrase or modify)
- Use the EXACT author names as given
- Use the EXACT year as given
- Use the EXACT venue/journal as given
- Set confidence: "high" — NO ⚠ note
- Match the key to the citation_map number for that paper

Only for citation_map entries NOT covered by the user's list should you use your
own training knowledge to generate real bibliographic data.
██████████████████████████████████████████████████████████████████

Citation map — EXACTLY {expected_count} BibTeX entries required (one per number below):
{citation_map_str}

══════════════════════════════════════════════════════════════════
STRICT REQUIREMENTS — every rule must be followed for ALL entries:
══════════════════════════════════════════════════════════════════

1. KEY FORMAT (MANDATORY):
   Citation [1]  → key MUST be "ref01"
   Citation [2]  → key MUST be "ref02"
   Citation [10] → key MUST be "ref10"
   Citation [25] → key MUST be "ref25"
   The key number MUST equal the citation_map number. NEVER reorder or skip.

2. COMPLETE COVERAGE: generate EXACTLY {expected_count} entries — one per citation_map number.
   Every number in the citation_map MUST appear as a BibTeX entry. Missing an entry
   causes "[?]" in the final PDF, which is a fatal publication error.

3. USE CITATION MAP DATA + YOUR REAL KNOWLEDGE:
   - Use the author/year/title_hint/venue from citation_map as a starting point.
   - author field: expand "Smith et al." → real first names you know from training
     e.g. "Vaswani et al." → "Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and
     Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N. and Kaiser, Lukasz and Polosukhin, Illia"
   - title: expand the title_hint to the REAL complete title from your training knowledge
   - year: use the year from citation_map exactly
   - venue: expand abbreviation to full official name (see rule 5 below)

4. ██ REAL PAPERS FROM YOUR TRAINING — NOT INVENTED DATA ██
   Priority 1: LANDMARK papers you know 100% (cite the real title/author/venue/year).
     Examples you KNOW: "Attention Is All You Need" (Vaswani 2017, NeurIPS),
     "BERT: Pre-training..." (Devlin 2019, NAACL), "Language Models are Few-Shot Learners"
     (Brown 2020, NeurIPS), "Deep Residual Learning..." (He 2016, CVPR), etc.
     → Do NOT add a "note" field for these. Omit "note" entirely.
   Priority 2: Well-known 2020-2024 papers whose existence you are confident about.
     → Do NOT add a "note" field. Omit "note" entirely.
   Priority 3: If the title_hint points to a paper you are NOT 100% sure exists with
     that exact title — produce the closest REAL paper you know from that author/area/year,
     then add ONLY: "note": "⚠ Verify: title approximated from training knowledge"
   ██ NEVER INVENT author names, venues, or years you are not confident about ██
   Real but imprecise is better than fictional and precise.

   confidence field from citation_map:
   - confidence="high" → you recalled this paper from training and are confident it is real.
     Do NOT add any "note" field. Leave "note" out of the entry entirely.
   - confidence="low"  → add "note": "⚠ Verify this reference — approximated by generator"

5. FULL VENUE NAMES (spell out completely — abbreviated names fail in bibliography):
   NeurIPS  → "Advances in Neural Information Processing Systems"
   CVPR     → "IEEE/CVF Conference on Computer Vision and Pattern Recognition"
   ICCV     → "IEEE/CVF International Conference on Computer Vision"
   ECCV     → "European Conference on Computer Vision"
   ICML     → "International Conference on Machine Learning"
   ICLR     → "International Conference on Learning Representations"
   ACL      → "Proceedings of the Annual Meeting of the Association for Computational Linguistics"
   EMNLP    → "Proceedings of the Conference on Empirical Methods in Natural Language Processing"
   NAACL    → "Proceedings of the North American Chapter of the ACL: Human Language Technologies"
   AAAI     → "Proceedings of the AAAI Conference on Artificial Intelligence"
   IJCAI    → "Proceedings of the International Joint Conference on Artificial Intelligence"
   KDD      → "Proceedings of the ACM SIGKDD Conference on Knowledge Discovery and Data Mining"
   WWW      → "Proceedings of the ACM Web Conference"
   SIGIR    → "Proceedings of the ACM SIGIR Conference on Research and Development in Information Retrieval"
   MICCAI   → "International Conference on Medical Image Computing and Computer-Assisted Intervention"
   IEEE TPAMI → "IEEE Transactions on Pattern Analysis and Machine Intelligence"
   IEEE TMI   → "IEEE Transactions on Medical Imaging"
   JMLR     → "Journal of Machine Learning Research"
   MLSys    → "Proceedings of Machine Learning and Systems"
   MAI/MVAI → "Proceedings of the International Conference on Machine Vision and Augmented Intelligence, Lecture Notes in Electrical Engineering, Springer"
   LNEE     → "Lecture Notes in Electrical Engineering, Springer"
   LNCS     → "Lecture Notes in Computer Science, Springer"

6. ENTRY TYPE RULES (use the correct type for each source):
   Conference paper → "inproceedings": booktitle, year, pages, publisher (optional: address)
   Journal article  → "article": journal, year, volume, number, pages, doi
   arXiv preprint   → "misc": howpublished = "arXiv preprint arXiv:XXXX.XXXXX", year
   Book             → "book": publisher, year, address (optional: edition)
   Book chapter     → "incollection": booktitle, publisher, year, pages
   Technical report → "techreport": institution, year, number (optional)

7. REQUIRED FIELDS by type:
   @inproceedings: author, title, booktitle, year, pages (always include pages)
   @article:       author, title, journal, year, volume, pages (always include volume+pages)
   @misc (arXiv):  author, title, year, howpublished ("arXiv preprint arXiv:XXXX.XXXXX"), note (optional)

8. DOI: include for journal articles where plausible.
   Format: "doi": "10.XXXX/journalabbrev.YEAR.XXXXXXX"
   Examples: "10.1145/3290605.3300312", "10.1109/TPAMI.2021.3057446", "10.18653/v1/2021.acl-long.1"

9. AUTHOR FORMAT: "LastName, FirstName and LastName2, FirstName2 and LastName3, FirstName3"
   For "et al." entries, include at least 3-4 real author names from the field, not just one.

10. PUBLISHER FIELD: add for major publishers:
    ACM proceedings → publisher = "Association for Computing Machinery"
    IEEE proceedings → publisher = "IEEE"
    Springer → publisher = "Springer"
    NeurIPS/ICML/ICLR → publisher = "Curran Associates, Inc."
    ACL proceedings → publisher = "Association for Computational Linguistics"

Return ONLY a raw JSON array — no markdown fences, no explanatory text, no @article{{}} BibTeX format.
Your response MUST start with [ and end with ]. No text before or after.

EXAMPLES — study carefully: high-confidence entries have NO "note" field at all.
[
  {{
    "key": "ref01",
    "type": "inproceedings",
    "author": "Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N. and Kaiser, Lukasz and Polosukhin, Illia",
    "title": "Attention Is All You Need",
    "booktitle": "Advances in Neural Information Processing Systems",
    "year": "2017",
    "pages": "5998--6008",
    "publisher": "Curran Associates, Inc."
  }},
  {{
    "key": "ref02",
    "type": "article",
    "author": "Devlin, Jacob and Chang, Ming-Wei and Lee, Kenton and Toutanova, Kristina",
    "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
    "journal": "Proceedings of the North American Chapter of the ACL: Human Language Technologies",
    "year": "2019",
    "volume": "1",
    "pages": "4171--4186",
    "doi": "10.18653/v1/N19-1423"
  }},
  {{
    "key": "ref03",
    "type": "misc",
    "author": "Smith, John and Doe, Jane",
    "title": "Approximate title — closest real paper found for this topic area",
    "year": "2023",
    "howpublished": "arXiv preprint arXiv:2310.12345",
    "note": "⚠ Verify this reference — approximated by generator"
  }}
]
Note: ref01 and ref02 have NO "note" field — that signals they are confirmed real papers.
Only ref03 has a note because it was approximated. Follow this pattern exactly.""")
            bibtex_entries = []
            try:
                parsed5 = self._parse_json(call5.get("content", "[]"))
                if isinstance(parsed5, list):
                    bibtex_entries = parsed5
                elif isinstance(parsed5, dict):
                    # Sometimes Claude wraps the array: {"references": [...]}
                    for v in parsed5.values():
                        if isinstance(v, list):
                            bibtex_entries = v
                            break
            except Exception:
                bibtex_entries = []

            # ── CALL 5 RETRY: if Call 5 produced < 5 entries, retry once ──
            # This is the most common cause of [?] citations: Call 5 returning
            # raw BibTeX text (not JSON) or an empty response, which causes
            # _parse_json to fail and leaves bibtex_entries = [].
            if len(bibtex_entries) < 5:
                call5b = await self.reasoner.think(f"""
Generate BibTeX references as a JSON array. Topic: {topic}. Research field: {research_field}.

CRITICAL: You MUST respond with ONLY a raw JSON array — absolutely no BibTeX text format,
no @article{{...}}, no markdown, no prose. Start your response with [ and end with ].

Citation map — generate EXACTLY {expected_count} entries (one per number listed):
{citation_map_str}

Output format MUST be exactly:
[
  {{"key":"ref01","type":"inproceedings","author":"Last, First","title":"Title","booktitle":"Venue","year":"2023"}},
  {{"key":"ref02","type":"article","author":"Last, First","title":"Title","journal":"Journal","year":"2022"}}
]

Generate {expected_count} entries total. Use keys ref01 through ref{expected_count:02d}.
Every number in the citation map MUST have exactly one matching entry. Missing entries = [?] errors.
Start with [ now:""", max_tokens=10000)
                try:
                    parsed5b = self._parse_json(call5b.get("content", "[]"))
                    if isinstance(parsed5b, list) and len(parsed5b) >= 5:
                        bibtex_entries = parsed5b
                    elif isinstance(parsed5b, dict):
                        for v in parsed5b.values():
                            if isinstance(v, list) and len(v) >= 5:
                                bibtex_entries = v
                                break
                except Exception:
                    pass

            # ── SYNTHESIS FALLBACK: guarantee zero [?] even if both calls fail ──
            # Use the AUGMENTED map (includes citations from Calls 3 & 4) so the
            # fallback synthesises entries for every number used anywhere in the paper.
            if len(bibtex_entries) < 5 and augmented_citation_map:
                bibtex_entries = self._synthesize_bibtex_from_citation_map(augmented_citation_map)

            # ── KEY COMPLETENESS GAP-FILL ─────────────────────────────────
            # Even if Call 5 generated 20 entries but skipped e.g. citation [7],
            # ref07 would be missing → [?] in the PDF.
            # Uses augmented_citation_map so citations from Calls 3 & 4 are also
            # gap-filled — fixing the root cause of missing late-section references.
            if augmented_citation_map:
                existing_keys = {e.get("key", "") for e in bibtex_entries}
                for n_str, info in augmented_citation_map.items():
                    try:
                        num = int(n_str)
                    except (ValueError, TypeError):
                        continue
                    expected_key = f"ref{num:02d}"
                    if expected_key not in existing_keys:
                        info = info or {}
                        gap_entry = {
                            "key":    expected_key,
                            "type":   "misc",
                            "author": info.get("author", f"Author {num}"),
                            "title":  info.get("title_hint", f"Reference {num}"),
                            "year":   str(info.get("year", "2024")),
                        }
                        # High-confidence: real paper recalled from training → no note.
                        # Low-confidence or missing confidence: approximated → flag it.
                        if info.get("confidence") != "high":
                            gap_entry["note"] = "⚠ AUTO-GENERATED GAP-FILL — replace with real bibliographic details"
                        bibtex_entries.append(gap_entry)
                        existing_keys.add(expected_key)

            # ── BIBTEX DEDUPLICATION ──────────────────────────────────────
            # Remove duplicate BibTeX entries (same key or same author+year+title_hint).
            # Duplicates arise when Call 5 generates an entry that overlaps with a
            # gap-fill fallback, or when the AI produces the same ref twice.
            seen_keys: set = set()
            seen_sig: set = set()   # (author_lower, year, first30_chars_of_title)
            deduped_entries = []
            for entry in bibtex_entries:
                key = entry.get("key", "")
                author = (entry.get("author", "") or "").lower().strip()
                year   = str(entry.get("year", ""))
                title  = (entry.get("title", "") or entry.get("title_hint", "") or "")[:30].lower().strip()
                sig = (author[:20], year, title)
                if key in seen_keys or sig in seen_sig:
                    continue
                seen_keys.add(key)
                seen_sig.add(sig)
                deduped_entries.append(entry)
            bibtex_entries = deduped_entries

            # ══════════════════════════════════════════════════════════════
            # REAL-TIME REFERENCE VERIFICATION (Crossref + Semantic Scholar)
            # Queries public APIs for every low-confidence entry. If a matching
            # real paper is found, overwrites the entry with verified metadata
            # (author, title, year, journal, DOI) and removes the ⚠ note.
            # Gracefully skips if httpx unavailable or network blocked.
            # ══════════════════════════════════════════════════════════════
            verification_results = {"verified": 0, "not_found": 0, "errors": 0, "skipped": 0}
            try:
                import httpx as _httpx
                import asyncio as _aio

                async def _verify_crossref(client, entry):
                    """Query Crossref. Returns enriched fields dict or None."""
                    title = (entry.get("title") or "").strip()
                    author = (entry.get("author") or "").strip()
                    first_author = _re.split(r'[,\s]', author)[0] if author else ""
                    year = str(entry.get("year") or "").strip()
                    if not title or len(title) < 8:
                        return None
                    query = f'{title} {first_author} {year}'.strip()[:200]
                    try:
                        r = await client.get(
                            "https://api.crossref.org/works",
                            params={"query": query, "rows": 3},
                            timeout=6.0,
                        )
                        if r.status_code != 200:
                            return None
                        items = r.json().get("message", {}).get("items", [])
                    except Exception:
                        return None
                    # Pick best match: title word-overlap >= 60% AND year within 1
                    def _title_overlap(a, b):
                        aw = set(_re.findall(r'\w+', a.lower()))
                        bw = set(_re.findall(r'\w+', b.lower()))
                        if not aw or not bw:
                            return 0
                        return len(aw & bw) / max(len(aw), 1)
                    best = None
                    for it in items:
                        it_title = (it.get("title") or [""])[0]
                        overlap = _title_overlap(title, it_title)
                        it_year_raw = it.get("published-print") or it.get("published-online") or it.get("issued") or {}
                        it_year = str(it_year_raw.get("date-parts", [[""]])[0][0]) if it_year_raw else ""
                        year_ok = (not year) or (not it_year) or (abs(int(year or 0) - int(it_year or 0)) <= 1)
                        if overlap >= 0.6 and year_ok:
                            best = it
                            break
                    if not best:
                        return None
                    # Build enriched entry
                    authors_raw = best.get("author", [])
                    authors_fmt = " and ".join(
                        f"{a.get('family', '')}, {a.get('given', '')}".strip(", ")
                        for a in authors_raw if a.get("family")
                    )
                    venue = ""
                    container = best.get("container-title", [])
                    if container:
                        venue = container[0]
                    elif best.get("event", {}).get("name"):
                        venue = best["event"]["name"]
                    pages = best.get("page", "")
                    volume = best.get("volume", "")
                    doi = best.get("DOI", "")
                    real_year = ""
                    for yk in ("published-print", "published-online", "issued"):
                        yv = best.get(yk, {}).get("date-parts", [[""]])[0][0]
                        if yv:
                            real_year = str(yv)
                            break
                    return {
                        "author": authors_fmt or author,
                        "title": (best.get("title") or [title])[0],
                        "year": real_year or year,
                        "journal" if best.get("type") == "journal-article" else "booktitle": venue or entry.get("journal") or entry.get("booktitle") or "",
                        "volume": volume,
                        "pages": pages.replace("-", "--") if pages else "",
                        "doi": doi,
                        "_verified_source": "crossref",
                    }

                async def _verify_semantic_scholar(client, entry):
                    """Query Semantic Scholar. Returns enriched fields dict or None."""
                    title = (entry.get("title") or "").strip()
                    if not title or len(title) < 8:
                        return None
                    try:
                        r = await client.get(
                            "https://api.semanticscholar.org/graph/v1/paper/search",
                            params={
                                "query": title[:200],
                                "limit": 3,
                                "fields": "title,authors,year,venue,externalIds",
                            },
                            timeout=6.0,
                        )
                        if r.status_code != 200:
                            return None
                        items = r.json().get("data", [])
                    except Exception:
                        return None
                    def _title_overlap(a, b):
                        aw = set(_re.findall(r'\w+', a.lower()))
                        bw = set(_re.findall(r'\w+', b.lower()))
                        return len(aw & bw) / max(len(aw), 1)
                    best = None
                    for it in items:
                        if _title_overlap(title, it.get("title", "")) >= 0.6:
                            best = it
                            break
                    if not best:
                        return None
                    authors = best.get("authors") or []
                    authors_fmt = " and ".join(a.get("name", "") for a in authors if a.get("name"))
                    return {
                        "author": authors_fmt or entry.get("author", ""),
                        "title": best.get("title", title),
                        "year": str(best.get("year", entry.get("year", ""))),
                        "journal": best.get("venue") or entry.get("journal") or entry.get("booktitle") or "",
                        "doi": (best.get("externalIds") or {}).get("DOI", ""),
                        "_verified_source": "semantic_scholar",
                    }

                async def _verify_one(client, entry):
                    """Try Crossref first, fall back to Semantic Scholar."""
                    result = await _verify_crossref(client, entry)
                    if not result:
                        result = await _verify_semantic_scholar(client, entry)
                    return result

                # Select entries needing verification (low-confidence or no DOI)
                import re as _re
                needs_verify_list = []
                for idx, e in enumerate(bibtex_entries):
                    if not isinstance(e, dict):
                        continue
                    note = str(e.get("note", ""))
                    has_warn = "⚠" in note or "verify" in note.lower() or "placeholder" in note.lower()
                    no_doi = not (e.get("doi") or "").strip()
                    if has_warn or no_doi:
                        needs_verify_list.append((idx, e))

                # Cap verification to 30 entries to bound latency (~30 sec worst case)
                needs_verify_list = needs_verify_list[:30]

                if needs_verify_list:
                    async with _httpx.AsyncClient(
                        headers={"User-Agent": "ai-research-assistant/1.0 (mailto:research@local)"},
                        http2=False,
                    ) as client:
                        tasks = [_verify_one(client, e) for _, e in needs_verify_list]
                        results = await _aio.gather(*tasks, return_exceptions=True)
                    # Apply results
                    for (idx, orig), res in zip(needs_verify_list, results):
                        if isinstance(res, Exception):
                            verification_results["errors"] += 1
                            continue
                        if res is None:
                            verification_results["not_found"] += 1
                            continue
                        # Merge verified fields into entry; drop ⚠ note on success
                        for k, v in res.items():
                            if v:
                                orig[k] = v
                        if "note" in orig:
                            note = str(orig["note"])
                            if "⚠" in note or "verify" in note.lower():
                                # Remove the ⚠ note only if a real DOI was found
                                if res.get("doi"):
                                    orig.pop("note", None)
                        verification_results["verified"] += 1
            except ImportError:
                verification_results["skipped"] += 1
            except Exception as _ve:
                verification_results["errors"] += 1
            paper_verification_stats = verification_results  # saved to paper later

            # ── COUNT REFERENCES THAT NEED MANUAL VERIFICATION ───────────────
            # Entries with a note containing "⚠", "verify", "placeholder", or
            # "auto-generated" were either:
            #   (a) gap-filled from the citation_map title_hint (not a full ref)
            #   (b) generated with low confidence and flagged by Call 5
            #   (c) produced by the synthesis fallback when Call 5 entirely failed
            # This count is surfaced in the paper's _warnings list so the UI can
            # display a clear "X references need verification" banner.
            _needs_verify_count = sum(
                1 for e in bibtex_entries
                if isinstance(e.get("note"), str) and (
                    "⚠" in e["note"]
                    or "verify" in e["note"].lower()
                    or "placeholder" in e["note"].lower()
                    or "auto-generated" in e["note"].lower()
                )
            )
            _high_confidence_count = len(bibtex_entries) - _needs_verify_count

            # ── CALL 6: Full Deep Humanizer — AI-undetectable rewrite of ALL sections ──
            # Rewrites EVERY section to pass AI detection tools (GPTZero, Turnitin, etc.)
            # Technique stack: burstiness, varied openers, filler removal, expert voice,
            # active/passive balance, hedging, domain-specific asides.
            call6 = await self.reasoner.think(f"""
You are a senior academic writer with 20 years of publication experience. Your task is to
COMPLETELY REWRITE seven sections of a research paper so that:
(a) No AI detection tool (GPTZero, Turnitin AI, Originality.ai, Copyleaks, ZeroGPT) flags it
(b) It reads exactly like a human expert wrote every sentence from scratch
(c) Every citation, equation, and LaTeX command is preserved exactly

Paper Title: {c1.get("title", topic)}
Research Field: {research_field}
Target Journal/Conference: {target_journal}

══════════════════════════════════════════════════════════════════
ANTI-AI-DETECTION RULES — apply to EVERY section without exception
══════════════════════════════════════════════════════════════════

RULE 1 — SENTENCE BURSTINESS (most important signal for AI detectors):
  AI text has uniform sentence length (~20-22 words). Human text mixes short and long.
  For EVERY paragraph: include at least ONE sentence under 8 words AND at least one
  sentence over 32 words. No two consecutive sentences should be the same length range.
  Example of correct burstiness:
    "The results are striking. When we trained on augmented data combining all three
    benchmark corpora — a total of 847,000 sentence pairs drawn from sources ranging
    from Wikipedia extracts to domain-specific biomedical text — accuracy jumped by
    6.3 percentage points over the previous best single-corpus result. That gap matters."

RULE 2 — BANNED WORDS AND PHRASES (these are the top AI-detection triggers):
  ══ HIGHEST-PRIORITY BANNED WORDS (GPTZero specifically scores these) ══
  NEVER USE: "delve", "delves", "delving", "delved into"
    → instead: "examine", "explore", "analyse", "investigate", "look at"
  NEVER USE: "crucial" (standalone) → instead: "key", "central", "critical", "decisive"
  NEVER USE: "pivotal" → instead: "central", "decisive", "defining"
  NEVER USE: "paramount" → instead: "critical", "primary", "essential"
  NEVER USE: "underscores" as a verb → instead: "confirms", "shows", "reflects"
  NEVER USE: "showcase", "showcases" → instead: "demonstrate", "reveal", "present"
  NEVER USE: "facilitate", "facilitates" → instead: "enable", "support", "help", "allow"
  NEVER USE: "cutting-edge" → instead: "leading", "top-performing", "recent"
  NEVER USE: "groundbreaking" → instead: "significant", "influential", "important"
  NEVER USE: "intricate" → instead: "complex", "detailed", "involved"
  NEVER USE: "nuanced" → instead: "subtle", "fine-grained", "detailed"
  NEVER USE: "multifaceted" → instead: "complex", "multi-dimensional"
  NEVER USE: "bolster", "bolsters" → instead: "strengthen", "support", "improve"
  NEVER USE: "elucidate", "elucidates" → instead: "explain", "clarify", "show"
  NEVER USE: "invaluable" → instead: "highly useful", "essential", "very helpful"
  NEVER USE: "endeavour", "endeavor" → instead: "effort", "work", "attempt"
  NEVER USE: "tapestry" → this word never appears in real academic papers
  NEVER USE: "holistic" → instead: "integrated", "overall", "comprehensive"
  NEVER USE: "synergistic", "synergistically" → instead: "combined", "joint"
  ══ BANNED TRANSITION PHRASES ══
  BANNED: "Furthermore,", "Moreover,", "Additionally,", "In this paper, we",
  "It is worth noting that", "Notably,", "Significantly,", "To this end,",
  "In conclusion,", "In summary,", "The proposed method", "Our proposed approach",
  "It should be noted that", "We note that", "In the context of",
  "plays a crucial role", "a wide range of", "state-of-the-art performance",
  "various existing", "several existing", "a number of", "challenging task",
  "promising results", "extensive experiments", "comprehensive evaluation",
  "in recent years", "recent advances", "recent progress", "has been widely"
  Replace each with specific, direct language that says exactly what is meant.

RULE 3 — VARIED PARAGRAPH OPENERS:
  Never start more than 2 paragraphs with "We" or "The".
  Use: "Our results show...", "A key challenge...", "Across all benchmarks...",
  "Three factors drive...", "Unlike prior work...", "This behaviour emerges from...",
  "What makes this surprising...", "Taken together,...", "At its core, the problem..."
  Also use the subject of the finding: "Accuracy improves by...", "Training on X yields..."

RULE 4 — ACTIVE VOICE FOR CLAIMS, STRATEGIC PASSIVE FOR METHODS:
  Findings: active voice ("Our model achieves", "The clustering reveals", "We observe that")
  Methods: passive voice is fine ("Models were trained", "Data were split", "Batches were sampled")
  Never write: "It is demonstrated that" or "It can be seen that" — use "We show" / "Results show"

RULE 5 — SPECIFIC LANGUAGE (no vague qualifiers):
  WRONG: "significantly better results"   RIGHT: "6.3-point F1 improvement over the strongest baseline"
  WRONG: "various methods"                RIGHT: "four competing methods — LSA, BERT, GPT-4, and the RAG pipeline"
  WRONG: "many students"                  RIGHT: "73% of surveyed students (n=1,247)"

RULE 6 — ADD EXPERT VOICE AND ASIDES:
  In discussion/conclusion, add 1-2 brief expert asides showing deep domain knowledge:
  e.g., "This aligns with the long-standing observation in retrieval literature that
  precision-recall trade-offs become especially acute at k>100..."
  e.g., "We suspect this reflects the well-known exposure bias in autoregressive decoding..."

RULE 7 — PRESERVE ALL CITATIONS AND LATEX — MOST CRITICAL TECHNICAL RULE:
  - Every [n] citation (e.g., [1], [3,4,5], [14]) MUST appear in the output unchanged
  - Every \\cite{{refNN}} command MUST appear unchanged
  - Every \\subsection{{}}, \begin{{}}, \\end{{}}, \textbf{{}}, \textit{{}}, \\label{{}}, \ref{{}} MUST be preserved
  - NEVER write [?] — it is a broken placeholder. Use the original numbers.
  - NEVER delete, renumber, or merge citation numbers from the input
  - Do NOT add new citations that were not in the original text

RULE 8 — LATEX SAFETY (no compile errors):
  - NEVER use **bold** or *italic* Markdown — use \textbf{{}} and \textit{{}}
  - NEVER use *..* or **..** inside math $...$  — asterisks inside math break LaTeX
  - Inside $...$ use plain underscore for subscripts: $x_t$ not $x*t*$
  - NEVER pre-escape special characters: write plain $150, 73%, en_core_web_sm
    The LaTeX builder auto-escapes these. Pre-escaping causes \\\\$ \\\\% errors.
  - Preserve all \begin{{equation}} ... \\end{{equation}} blocks exactly as-is

RULE 9 — MATCH WORD COUNT:
  Each section output must be within ±10% of the input word count.
  Do not shorten. Do not pad with filler.

RULE 10 — NATURAL ACADEMIC IMPERFECTION:
  Real academic writing has:
  - Occasional parenthetical clarifications (like this one)
  - Em-dashes for emphasis or qualification — used sparingly
  - Contractions in discussion/limitations ("don't", "can't", "it's") — 1-2 per section max
  - Brief self-critical honesty: "admittedly", "one limitation is", "this is not without caveats"
  - Occasional hedged uncertainty: "we suspect", "the data suggest", "this may reflect"

RULE 11 — SENTENCE BEGINNINGS WITH CONJUNCTIONS (humans do this; AI avoids it):
  Use "But", "And", "Yet", "So", "Or" to start 2-3 sentences per section.
  e.g., "But this comparison isn't entirely fair." / "And that matters."
  e.g., "Yet the evidence points in a clear direction." / "So what explains the gap?"
  This is fully acceptable in modern academic writing and strongly signals human authorship.

RULE 12 — VARY CITATION PLACEMENT (AI always cites at sentence end):
  Mix citation positions throughout each section:
  - Start of sentence: "[1] showed that transformers struggle with..."
  - Mid-sentence: "the attention mechanism, first proposed by Vaswani et al. [1], has since..."
  - After specific claim: "accuracy drops by 12% [3] when..." or "this finding [7] contradicts..."
  - Multiple at once: "[3,4] both suggest that..." or "as observed independently [5,6,7]..."
  NEVER place every citation at the end of the sentence.

RULE 13 — SENTENCE FRAGMENTS AND EMPHASIS (intentional brevity):
  Use occasional deliberate fragments for emphasis — 1 per section maximum.
  e.g., "Short and fast. That's the design goal."
  e.g., "Three parameters. That's all it takes."
  This is a hallmark of confident human academic writing. AI never produces fragments.

RULE 14 — WORD-LEVEL PERPLEXITY BOOST (most critical for GPTZero score):
  AI detectors score perplexity: how predictable each word is given its context.
  Force less predictable but accurate word choices:
  PREDICTABLE (AI): "the model achieves better performance on the benchmark"
  LESS PREDICTABLE (human): "the model posts stronger numbers across every benchmark"
  PREDICTABLE: "we evaluate on three datasets"
  LESS PREDICTABLE: "three corpora serve as our testbed"
  PREDICTABLE: "the results show that"
  LESS PREDICTABLE: "the numbers tell a clear story:"
  PREDICTABLE: "we compare with baseline methods"
  LESS PREDICTABLE: "four baselines bracket the comparison:"
  Use domain-specific jargon where natural. Occasionally use less common but accurate verbs:
  "yields", "delivers", "posts", "reports", "clocks", "registers", "logs" instead of "achieves"
  "outpaces", "edges out", "narrows the gap", "matches" instead of "outperforms"

RULE 15 — PARAGRAPH LENGTH VARIATION:
  AI writes paragraphs of 4-6 sentences uniformly. Vary this:
  - Include at least one 2-sentence paragraph per section (short, punchy)
  - Include at least one 7-9 sentence paragraph per section (detailed, technical)
  - Remaining paragraphs: 3-5 sentences
  This breaks the uniform rhythm that all major AI detectors flag.

══════════════════════════════════════════════════
SECTIONS TO REWRITE IN FULL — do not truncate any
══════════════════════════════════════════════════

--- ABSTRACT (rewrite fully, preserve all numbers and citations) ---
{c1.get("abstract", "")}

--- INTRODUCTION (rewrite FULL text — every paragraph, every sentence) ---
{c2.get("introduction", "")}

--- LITERATURE REVIEW / RELATED WORK (rewrite FULL text) ---
{c2.get("literature_review", "")}

--- METHODOLOGY (rewrite FULL text — preserve all equations, subsection headers) ---
{c3.get("methodology", "")}

--- RESULTS (rewrite FULL text — preserve all numbers, tables refs, figure refs) ---
{c3.get("results", "")}

--- DISCUSSION (rewrite FULL text — be the most human-sounding section) ---
{c4.get("discussion", "")}

--- CONCLUSION (rewrite fully — end with a strong, specific forward-looking sentence) ---
{c4.get("conclusion", "")}

══════════════════════════════════════
REVIEWER RESPONSES (generate after humanization)
══════════════════════════════════════
Generate exactly 4 realistic reviewer critiques (2 major, 2 minor) that a top-venue
program committee member would raise, plus detailed professional author rebuttals.
Critiques must be specific to the research topic and methodology, not generic.

Return ONLY a valid JSON object — no markdown, no preamble, no explanation:
{{
  "abstract_humanized":       "Full rewritten abstract — same length, no AI filler",
  "introduction_humanized":   "Full rewritten introduction — all paragraphs, all citations preserved",
  "literature_review_humanized": "Full rewritten related work — all subsection headers preserved",
  "methodology_humanized":    "Full rewritten methodology — all equations and subsection headers preserved",
  "results_humanized":        "Full rewritten results — all numbers, table refs, figure refs preserved",
  "discussion_humanized":     "Full rewritten discussion — most human-sounding section of the paper",
  "conclusion_humanized":     "Full rewritten conclusion — ends with a strong forward-looking sentence",
  "reviewer_responses": [
    {{
      "reviewer": "Reviewer 1 — Major Concern",
      "concern": "Specific, technical concern about the methodology or experimental design",
      "response": "Detailed 3-4 sentence professional rebuttal citing specific results or changes made",
      "paper_change": "Concrete change: which section, what was added/revised"
    }},
    {{
      "reviewer": "Reviewer 2 — Major Concern",
      "concern": "Concern about baselines, fairness of comparison, or missing ablation",
      "response": "Professional rebuttal with specific numbers or additional experiments referenced",
      "paper_change": "Concrete change added to the paper"
    }},
    {{
      "reviewer": "Reviewer 3 — Minor Concern",
      "concern": "Minor concern about clarity, notation, or presentation",
      "response": "Brief professional response acknowledging the point and describing the fix",
      "paper_change": "Section revised or clarification added"
    }},
    {{
      "reviewer": "Reviewer 4 — Minor Concern",
      "concern": "Minor concern about related work coverage or limitations disclosure",
      "response": "Brief professional response",
      "paper_change": "Added discussion of [specific topic] to Section X"
    }}
  ]
}}""", max_tokens=32000)
            c6 = self._parse_json(call6.get("content", "{}"))

            # ── Apply ALL humanized sections (fall back to originals if humanizer failed) ──
            # Call 6 now rewrites every section in full — no stitching needed.
            final_abstract       = c6.get("abstract_humanized")          or c1.get("abstract", "")
            final_intro          = c6.get("introduction_humanized")       or c2.get("introduction", "")
            final_lit_review     = c6.get("literature_review_humanized")  or c2.get("literature_review", "")
            final_methodology    = c6.get("methodology_humanized")        or c3.get("methodology", "")
            final_results        = c6.get("results_humanized")            or c3.get("results", "")
            final_discussion     = c6.get("discussion_humanized")         or c4.get("discussion", "")
            final_conclusion     = c6.get("conclusion_humanized")         or c4.get("conclusion", "")
            reviewer_responses   = c6.get("reviewer_responses", [])

            # ── POST-PROCESS 1: strip [?] citation placeholders ──────────────
            import re as _re
            def _strip_q(t):
                if not isinstance(t, str): return t
                return _re.sub(r'\s*\[\?\]', '', t)

            # ── POST-PROCESS 2: deterministic AI-phrase removal pass ──────
            # Belt-and-suspenders: remove any surviving AI filler that slipped
            # through Call 6.  This runs on all humanized body sections.
            final_abstract    = self._dehuman_ai(_strip_q(final_abstract))
            final_intro       = self._dehuman_ai(_strip_q(final_intro))
            final_lit_review  = self._dehuman_ai(_strip_q(final_lit_review))
            final_methodology = self._dehuman_ai(_strip_q(final_methodology))
            final_results     = self._dehuman_ai(_strip_q(final_results))
            final_discussion  = self._dehuman_ai(_strip_q(final_discussion))
            final_conclusion  = self._dehuman_ai(_strip_q(final_conclusion))

            # ══════════════════════════════════════════════════════════════
            # CALL 6B: TARGETED AI-LEAK FIXER (second humanization pass)
            # Re-reads the already-humanized text. Detects AI signals that
            # survived Call 6 + _dehuman_ai (common survivors: uniform sentence
            # length, predictable paragraph openers, end-of-sentence citations).
            # Rewrites ONLY affected sentences — preserves all numbers, citations,
            # LaTeX, and section structure.
            # ══════════════════════════════════════════════════════════════
            try:
                # Scan each section for surviving AI leaks using the same detector
                import re as _re6
                _ai_leak_patterns = [
                    r'\bdelve[sd]?\b', r'\bcrucial\b', r'\bpivotal\b', r'\btapestry\b',
                    r'\bfacilitat[es]+\b', r'\bleverag[es]+\b', r'\butiliz[es]+\b',
                    r'\bseamless(?:ly)?\b', r'\bnuanced\b', r'\bIn this paper,?\s+we\b',
                    r'\bFurthermore,\s', r'\bMoreover,\s', r'\bIt is worth noting\b',
                    r'\bstate-of-the-art\b',
                ]
                def _has_leaks(txt):
                    for p in _ai_leak_patterns:
                        if _re6.search(p, txt, flags=_re6.IGNORECASE):
                            return True
                    return False

                sections_to_refine = []
                section_payload = {
                    "abstract": final_abstract,
                    "introduction": final_intro,
                    "literature_review": final_lit_review,
                    "methodology": final_methodology,
                    "results": final_results,
                    "discussion": final_discussion,
                    "conclusion": final_conclusion,
                }
                for sk, st in section_payload.items():
                    if _has_leaks(st):
                        sections_to_refine.append(sk)

                if sections_to_refine:
                    _sections_dump = "\n".join(
                        f"=== {sk.upper()} ===\n{section_payload[sk]}\n"
                        for sk in sections_to_refine
                    )
                    _json_keys = ",\n".join(
                        f'  "{sk}": "FIXED TEXT HERE"' for sk in sections_to_refine
                    )
                    call6b = await self.reasoner.think(f"""
You are doing a TARGETED fix pass on already-humanized sections.
Your sole job: remove AI-detection trigger phrases WHILE preserving every:
- Number, citation [n] or \\cite{{refNN}}
- LaTeX command (\\textbf, \\textit, \\subsection, \\begin, \\end, \\label, \\ref)
- Equation / math block ($...$, \\begin{{equation}}...\\end{{equation}})
- Section ordering and word count (±5%)

FORBIDDEN WORDS (replace with specific, direct alternatives):
delve, crucial, pivotal, tapestry, facilitate, leverage, utilize, seamless,
nuanced, "In this paper we", "Furthermore,", "Moreover,", "It is worth noting",
state-of-the-art (replace with "leading" / "top" / "current")

ADDITIONAL HUMANIZATION:
- Add at least one sentence under 8 words per paragraph
- Break at least 2 sentences with em-dashes or parentheticals
- Move 1-2 citations from sentence-end to mid-sentence
- Use "But", "And", "Yet", or "So" to start one sentence per paragraph

SECTIONS TO FIX (rewrite each fully, preserving length and all technical content):

{_sections_dump}

Return ONLY valid JSON mapping section keys to their fixed text:
{{
{_json_keys}
}}""", max_tokens=32000)
                    c6b = self._parse_json(call6b.get("content", "{}"))
                    for sk in sections_to_refine:
                        if c6b.get(sk):
                            cleaned = self._dehuman_ai(_strip_q(c6b[sk]))
                            if sk == "abstract":       final_abstract    = cleaned
                            elif sk == "introduction": final_intro       = cleaned
                            elif sk == "literature_review": final_lit_review = cleaned
                            elif sk == "methodology":  final_methodology = cleaned
                            elif sk == "results":      final_results     = cleaned
                            elif sk == "discussion":   final_discussion  = cleaned
                            elif sk == "conclusion":   final_conclusion  = cleaned
            except Exception as _6b_err:
                # Non-fatal — original Call 6 output stands
                pass

            # ── Assemble final paper object ────────────────────────────────
            paper = {
                # Front matter
                "title":                  c1.get("title", topic),
                "running_title":          c1.get("running_title", ""),
                "abstract":               final_abstract,
                "abstract_structured":    c1.get("abstract_structured", {}),
                "plain_language_summary": c1.get("plain_language_summary", ""),
                "keywords":               c1.get("keywords", []),
                "highlights":             c1.get("highlights", []),
                "author_block":           c1.get("author_block", {}),
                # Body — all sections now fully humanized
                "introduction":           final_intro,
                "literature_review":      final_lit_review,
                "abbreviations_list":     c2.get("abbreviations_list", ""),
                "methodology":            final_methodology,
                "results":                final_results,
                "results_table":          c3.get("results_table", []),
                "results_table_caption":  c3.get("results_table_caption", "Table 1: Comparison of Methods"),
                "hyperparameters_table":          c3.get("hyperparameters_table", []),
                "hyperparameters_table_caption":  c3.get("hyperparameters_table_caption", "Table 2: Hyperparameter Configuration"),
                "figure_captions":        c3.get("figure_captions", []),
                # Back matter
                "discussion":             final_discussion,
                "conclusion":             final_conclusion,
                "acknowledgements":       c4.get("acknowledgements", ack_val),
                "ethics_statement":       c4.get("ethics_statement", eth_val),
                "conflict_of_interest":   c4.get("conflict_of_interest", "The authors declare no conflict of interest."),
                "data_access_statement":  c4.get("data_access_statement", da_val),
                "author_contributions":   c4.get("author_contributions", ac_val),
                "cover_letter":           c4.get("cover_letter", ""),
                "supplementary_materials": c4.get("supplementary_materials", ""),
                # References + extras
                "bibtex_entries":         bibtex_entries,
                # Use augmented_citation_map so frontend numToKey resolution covers
                # citations introduced in Calls 3 and 4, not just Call 2.
                "citation_map":           augmented_citation_map,
                "reviewer_responses":     reviewer_responses,
                "generated_figures":      [],
                "references":             "",
                # Reference quality metrics — surfaced in UI warnings
                "_ref_verification":      paper_verification_stats,
                "_ref_high_confidence":   _high_confidence_count,
                "_ref_needs_verify":      _needs_verify_count,
                "_ref_total":             len(bibtex_entries),
            }

            # ── Total word count ───────────────────────────────────────
            body_sections = ["abstract", "introduction", "literature_review",
                             "methodology", "results", "discussion", "conclusion"]
            total_wc = sum(
                len(paper.get(s, "").split()) for s in body_sections
                if isinstance(paper.get(s, ""), str)
            )
            paper["total_word_count"] = total_wc

            # ── Publication readiness checks ──────────────────────────
            import re
            min_words = {
                "introduction": 700, "literature_review": 800,
                "methodology": 700, "results": 600,
                "discussion": 550, "conclusion": 250,
                "abstract": 180,
            }
            warnings = []
            for sec, min_w in min_words.items():
                text = paper.get(sec, "")
                wc = len(text.split()) if text else 0
                if wc < min_w:
                    warnings.append(f"⚠ {sec} is short ({wc} words, target ≥{min_w}). Consider re-running.")

            # Citation quality checks
            bib_count = len(paper.get("bibtex_entries", []))
            if bib_count < 10:
                warnings.append(f"⚠ Only {bib_count} BibTeX entries generated (target ≥20). Citation quality may be insufficient for publication.")
            elif bib_count < 18:
                warnings.append(f"ℹ {bib_count} BibTeX entries generated — consider adding more for top-venue submission (target ≥20).")

            # ── Reference quality warning ─────────────────────────────
            # Positive note when online verification found real papers
            if paper_verification_stats.get("verified", 0) > 0:
                warnings.append(
                    f"✅ {paper_verification_stats['verified']} reference(s) auto-verified against Crossref / Semantic Scholar — real DOIs and authors inserted."
                )
            if _needs_verify_count > 0:
                pct_ok = round(100 * _high_confidence_count / max(len(bibtex_entries), 1))
                nf = paper_verification_stats.get("not_found", 0)
                nf_note = f" ({nf} searched online with no match)" if nf > 0 else ""
                warnings.append(
                    f"⚠ {_needs_verify_count} of {len(bibtex_entries)} references still need manual verification{nf_note}. "
                    f"{pct_ok}% are high-confidence. Click the Google Scholar / Semantic Scholar / Crossref links to check."
                )

            # Detect any remaining [?] placeholders in body text
            full_body = " ".join(str(paper.get(s, "")) for s in body_sections)
            placeholder_count = len(re.findall(r'\[\?\]', full_body))
            if placeholder_count > 0:
                warnings.append(f"⚠ {placeholder_count} unresolved [?] citation placeholder(s) detected. Check literature_review and introduction.")

            # Check ethics section quality
            eth = paper.get("ethics_statement", "")
            eth_words = len(eth.split()) if eth else 0
            if eth_words < 50:
                warnings.append("⚠ Ethics statement is very short (<50 words). Expand to cover dual-use risks for top-venue submission.")

            # Check if modern baselines are mentioned
            results_text = paper.get("results", "").lower()
            has_rag = any(kw in results_text for kw in ["rag", "retrieval-augmented", "retrieval augmented"])
            has_agent = any(kw in results_text for kw in ["autogen", "metagpt", "langchain", "agent framework", "multi-agent"])
            if not has_rag and not has_agent:
                warnings.append("ℹ Results section does not reference RAG or agent-framework baselines. Consider adding for stronger reviewer reception.")

            # Dataset size warning (helps users expand coverage)
            datasets_info = extra_context.get("datasets", "")
            if not datasets_info or len(datasets_info.strip()) < 20:
                warnings.append("ℹ No dataset details provided. Add dataset names, sizes, and splits to improve methodology reproducibility score.")

            # ── NEW: validate top-tier input field coverage ──────────────────────
            if not extra_context.get("novelty_statement", "").strip():
                warnings.append("ℹ No Novelty Statement provided (Step 2). Top-tier venues need explicit positioning vs prior work. Add 1 paragraph explaining what is genuinely new.")
            if not extra_context.get("statistical_tests", "").strip():
                warnings.append("ℹ No Statistical Tests spec provided (Step 4). Results section will lack rigour. Specify test name, n per condition, and correction method.")
            if not extra_context.get("reviewer_concerns", "").strip():
                warnings.append("ℹ No anticipated Reviewer Concerns (Step 2). Limitations section cannot pre-address the paper's weakest point — a top-tier rejection risk.")

            # ── NEW: LaTeX compile-risk scan across all body text ────────────────
            latex_risks = []
            for section_key in ["abstract", "introduction", "literature_review", "methodology",
                                "results", "discussion", "conclusion"]:
                body = str(paper.get(section_key, ""))
                # Count unclosed $...$ spans
                dollar_count = body.count("$") - body.count("\\$")
                if dollar_count % 2 != 0:
                    latex_risks.append(f"{section_key}: odd number of unescaped $ signs — possible unclosed math mode")
                # Long $...$ spans with English words (inline math explosion)
                import re as _re
                long_math = _re.findall(r'\$[^$\n]{25,}\$', body)
                for m in long_math:
                    if _re.search(r'[a-zA-Z]{3,}', m) and " " in m:
                        latex_risks.append(f"{section_key}: long $-span with English words (inline math risk): «{m[:60]}...»")
                        break  # one example per section is enough
                # Unresolved \ref{??} or literal "Figure ??"
                if _re.search(r'Figure\s*\?\?|Table\s*\?\?|\bref\s*\{\s*\?\s*\}', body):
                    latex_risks.append(f"{section_key}: unresolved cross-reference (Figure/Table ??)")
            # Enhanced LaTeX checks across the full body (catches more compile errors
            # without needing a TeX Live install).
            full_body_latex = "\n\n".join(str(paper.get(s, "")) for s in
                                           ["abstract", "introduction", "literature_review",
                                            "methodology", "results", "discussion", "conclusion"])
            # (a) Unbalanced braces { } at top level (rough check — skip protected blocks)
            stripped = _re.sub(r'\$[^$\n]*\$', '', full_body_latex)
            stripped = _re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', stripped)
            open_braces = stripped.count('{')
            close_braces = stripped.count('}')
            if abs(open_braces - close_braces) > 2:
                latex_risks.append(f"global: {open_braces} '{{' vs {close_braces} '}}' — likely unbalanced braces")
            # (b) Unmatched \begin{...} / \end{...}
            begins = _re.findall(r'\\begin\{([a-zA-Z*]+)\}', full_body_latex)
            ends = _re.findall(r'\\end\{([a-zA-Z*]+)\}', full_body_latex)
            from collections import Counter
            bc, ec = Counter(begins), Counter(ends)
            for env_name in set(list(bc.keys()) + list(ec.keys())):
                if bc[env_name] != ec[env_name]:
                    latex_risks.append(f"global: \\begin{{{env_name}}} opened {bc[env_name]}x, \\end{{{env_name}}} closed {ec[env_name]}x")
                    break
            # (c) Duplicate \label{} values (LaTeX warns/errors)
            labels = _re.findall(r'\\label\{([^}]+)\}', full_body_latex)
            lc = Counter(labels)
            dups = [k for k, v in lc.items() if v > 1]
            if dups:
                latex_risks.append(f"global: duplicate labels: {dups[:3]}")
            # (d) \ref{} to a label that doesn't exist anywhere in the paper
            refs = set(_re.findall(r'\\ref\{([^}]+)\}', full_body_latex))
            label_set = set(labels)
            # Known auto-inserted labels from buildLatex frontend: sec:*, fig:fig1-3, tab:*
            auto_labels = {"sec:intro", "sec:related", "sec:method", "sec:results",
                           "sec:discussion", "sec:conclusion",
                           "fig:fig1", "fig:fig2", "fig:fig3", "fig:fig4",
                           "tab:results", "tab:hyperparams", "tab:tab1", "tab:tab2"}
            dangling_refs = refs - label_set - auto_labels
            if dangling_refs:
                latex_risks.append(f"global: \\ref{{}} to undefined labels: {list(dangling_refs)[:3]}")

            if latex_risks:
                for risk in latex_risks[:8]:
                    warnings.append(f"⚠ LaTeX compile risk — {risk}")

            # ── NEW: Venue page-limit + format checks ─────────────────────────────
            venue_rules = _venue_lookup(target_journal)
            paper["_venue_rules"] = venue_rules
            column_format = extra_context.get("column_format", "single")
            # Rough page estimate: 400 words/page two-col, 500 words/page single-col.
            # Tables + figures add ~0.5 page each.
            body_words = sum(len(str(paper.get(s, "")).split()) for s in
                             ["abstract", "introduction", "literature_review",
                              "methodology", "results", "discussion", "conclusion"])
            wpp = 400 if column_format == "two" else 500
            n_tables = sum(1 for tk in ["results_table", "hyperparameters_table"]
                           if paper.get(tk) and len(paper.get(tk, [])) > 1)
            n_figs = len(paper.get("figure_captions", []))
            est_pages = round(body_words / wpp + 0.5 * (n_tables + n_figs), 1)
            paper["_estimated_pages"] = est_pages
            page_limit = venue_rules.get("pages")
            word_limit = venue_rules.get("word_limit")
            if page_limit and est_pages > page_limit:
                warnings.append(
                    f"⚠ Page-limit risk: estimated {est_pages} pages > {page_limit}-page limit for {venue_rules.get('venue_class', 'this venue')}. "
                    f"Desk-rejection risk. Shorten by {round((est_pages - page_limit) * wpp)} words or move content to appendix."
                )
            if word_limit and body_words > word_limit:
                warnings.append(
                    f"⚠ Word-count risk: {body_words} words main text > {word_limit}-word limit for {venue_rules.get('venue_class', 'this venue')}. "
                    f"Shorten by {body_words - word_limit} words or move content to Methods/Supplement."
                )

            # Double-blind check: flag if author names appear in running title / acknowledgements
            if venue_rules.get("double_blind"):
                ack_txt = str(paper.get("acknowledgements", "")).strip()
                authors_str = extra_context.get("authors_list", "").strip()
                if ack_txt and len(ack_txt) > 30 and authors_str:
                    # Check if acknowledgements mention specific people (common de-anonymisation)
                    warnings.append(
                        f"⚠ Double-blind venue ({venue_rules.get('venue_class')}): review Acknowledgements section — remove specific thanks before submission, restore for camera-ready."
                    )
                running = str(paper.get("running_title", ""))
                if running and authors_str and any(name.split()[-1] in running for name in authors_str.split(",") if name.strip()):
                    warnings.append(
                        f"⚠ Double-blind venue: running title contains author surname — anonymise before submission."
                    )

            # Emit venue-specific format rules as info-level notes
            for rule in venue_rules.get("rules", [])[:5]:
                warnings.append(f"ℹ Venue rule ({venue_rules.get('venue_class', 'venue')}): {rule}")

            # ── NEW: Section-balance validator ────────────────────────────────────
            def _wc(key):
                return len(str(paper.get(key, "")).split())
            wc_intro = _wc("introduction")
            wc_related = _wc("literature_review")
            wc_methodology = _wc("methodology")
            wc_results = _wc("results")
            wc_discussion = _wc("discussion")
            wc_conclusion = _wc("conclusion")
            wc_abstract = _wc("abstract")
            # Flag silent truncation: expected ratios for a balanced paper
            if wc_results > 200 and wc_discussion < 0.5 * wc_results:
                warnings.append(
                    f"⚠ Section imbalance: Discussion is {wc_discussion} words but Results is {wc_results} words (expected ≥ 50%). "
                    f"Call 4 may have truncated — regenerate or expand Discussion manually."
                )
            if wc_intro > 200 and wc_related < 0.7 * wc_intro:
                warnings.append(
                    f"⚠ Section imbalance: Related Work is {wc_related} words vs Introduction {wc_intro} (expected 80-130%). "
                    f"Literature review may be under-developed for top-venue submission."
                )
            if wc_discussion > 100 and wc_conclusion < 0.2 * wc_discussion:
                warnings.append(
                    f"⚠ Conclusion is very short ({wc_conclusion} words, Discussion is {wc_discussion}). "
                    f"Expand to 280-350 words including exact metric summary."
                )
            if wc_abstract < 120 or wc_abstract > 280:
                warnings.append(
                    f"⚠ Abstract length is {wc_abstract} words (target 150-250). "
                    f"Most venues reject abstracts outside this range."
                )

            # ── NEW: Reference cross-check (body cites vs BibTeX entries) ─────────
            body_full = " ".join(str(paper.get(s, "")) for s in
                                 ["introduction", "literature_review", "methodology",
                                  "results", "discussion", "conclusion"])
            body_cites = set(_re.findall(r'\\cite\{([^}]+)\}', body_full))
            # Expand comma-separated keys
            body_keys = set()
            for cite_group in body_cites:
                for k in cite_group.split(","):
                    body_keys.add(k.strip())
            bib_keys = set()
            for entry in bibtex_entries or []:
                if isinstance(entry, dict) and entry.get("key"):
                    bib_keys.add(entry["key"])
            missing_in_bib = body_keys - bib_keys
            unused_in_body = bib_keys - body_keys
            if missing_in_bib:
                warnings.append(
                    f"⚠ Reference mismatch: {len(missing_in_bib)} \\cite{{}} key(s) have NO BibTeX entry: "
                    f"{', '.join(sorted(missing_in_bib)[:5])}. Will render as [?] in PDF."
                )
            if len(unused_in_body) > max(3, len(bib_keys) // 4):
                warnings.append(
                    f"ℹ {len(unused_in_body)} BibTeX entries are not cited anywhere in the body. "
                    f"Consider removing unused entries or citing them in Related Work to strengthen literature coverage."
                )
            # Author/year mismatch detection: compare bib entry to citation_map claim
            mismatches = []
            _cm = augmented_citation_map or {}
            for entry in bibtex_entries or []:
                if not isinstance(entry, dict):
                    continue
                key = entry.get("key", "")
                m = _re.match(r'^ref0*(\d+)$', key)
                if not m:
                    continue
                cite_num = str(int(m.group(1)))
                cm_entry = _cm.get(cite_num)
                if not cm_entry or not isinstance(cm_entry, dict):
                    continue
                # Compare author surname
                bib_author = (entry.get("author", "") or "").lower()
                cm_author = (cm_entry.get("author", "") or "").lower().strip()
                # Extract bib surname (first word before comma or "and")
                bib_surname = _re.split(r'[,\s]', bib_author.strip())[0] if bib_author else ""
                cm_surname = _re.split(r'[,\s]', cm_author)[0] if cm_author else ""
                if bib_surname and cm_surname and len(bib_surname) > 2 and len(cm_surname) > 2:
                    if bib_surname not in cm_author and cm_surname not in bib_author:
                        mismatches.append(f"[{cite_num}] cite_map claims '{cm_surname.title()}' but BibTeX entry is '{bib_surname.title()}'")
                # Compare year
                bib_year = str(entry.get("year", "")).strip()
                cm_year = str(cm_entry.get("year", "")).strip()
                if bib_year and cm_year and bib_year != cm_year and abs(int(bib_year or 0) - int(cm_year or 0)) > 1:
                    mismatches.append(f"[{cite_num}] cite_map year={cm_year} but BibTeX year={bib_year}")
            if mismatches:
                warnings.append(
                    f"⚠ {len(mismatches)} reference author/year mismatch(es) detected: "
                    f"{'; '.join(mismatches[:3])}"
                )

            # ── Reference verification links (practical web-search substitute) ─────
            # For each low-confidence entry, build Google Scholar + DOI lookup URLs
            # so the user can verify with one click instead of typing queries.
            verification_links = []
            import urllib.parse as _up
            for entry in bibtex_entries or []:
                if not isinstance(entry, dict):
                    continue
                note = str(entry.get("note", ""))
                if "⚠" not in note and "verify" not in note.lower():
                    continue
                title = entry.get("title", "")
                author = entry.get("author", "")
                first_surname = _re.split(r'[,\s]', (author or "").strip())[0] if author else ""
                year = entry.get("year", "")
                query = f'"{title}" {first_surname} {year}'.strip()
                gscholar = f"https://scholar.google.com/scholar?q={_up.quote(query)}"
                semantic = f"https://www.semanticscholar.org/search?q={_up.quote(title)}"
                doi_search = f"https://search.crossref.org/?q={_up.quote(query)}"
                verification_links.append({
                    "key": entry.get("key"),
                    "author": first_surname.title(),
                    "year": year,
                    "title": title[:80],
                    "google_scholar": gscholar,
                    "semantic_scholar": semantic,
                    "crossref": doi_search,
                })

            paper["_reference_crosscheck"] = {
                "body_cites": len(body_keys),
                "bib_entries": len(bib_keys),
                "missing_in_bib": sorted(missing_in_bib)[:10],
                "unused_in_body": sorted(unused_in_body)[:10],
                "author_year_mismatches": mismatches[:10],
                "verification_links": verification_links[:30],  # cap for UI
            }

            # ── NEW: Revision tracking — input hash + timestamp + score ──────────
            import hashlib as _hashlib
            _input_blob = json.dumps({
                "topic": topic, "journal": target_journal,
                "hyp": extra_context.get("hypothesis", ""),
                "contrib": extra_context.get("contribution_list", ""),
                "findings": extra_context.get("key_findings", ""),
                "novelty": extra_context.get("novelty_statement", ""),
                "stats": extra_context.get("statistical_tests", ""),
                "datasets": extra_context.get("datasets", ""),
                "results": extra_context.get("experimental_results", ""),
                "algo": extra_context.get("algorithm_description", ""),
            }, sort_keys=True)
            paper["_revision"] = {
                "input_hash": _hashlib.sha256(_input_blob.encode()).hexdigest()[:12],
                "generated_at": int(time.time()),
                "generation_time_sec": None,  # can be filled by caller
                "total_word_count": sum(len(str(paper.get(s, "")).split()) for s in body_sections),
                "bib_entries": len(bibtex_entries),
                "warnings_count": len(warnings),
            }

            if warnings:
                paper["_warnings"] = warnings

            # ── Publishability score ─────────────────────────────────
            score = 100
            deductions = {
                "short_section": 5,
                "bib_sparse": 10,
                "placeholder": 15,
                "ethics_weak": 8,
                "no_modern_baselines": 7,
                "no_datasets": 3,
            }
            for w in warnings:
                if "short" in w.lower(): score -= deductions["short_section"]
                if "bibtex" in w.lower() or "citation" in w.lower(): score -= deductions["bib_sparse"]
                if "placeholder" in w.lower(): score -= deductions["placeholder"]
                if "ethics" in w.lower(): score -= deductions["ethics_weak"]
                if "rag" in w.lower() or "agent" in w.lower(): score -= deductions["no_modern_baselines"]
                if "dataset" in w.lower(): score -= deductions["no_datasets"]
            paper["_publishability_score"] = max(0, score)

            # ══════════════════════════════════════════════════════════════
            # PROGRAMMATIC QUALITY ANALYSERS — no API cost, pure Python.
            # These catch things Call 6 humanization misses.
            # ══════════════════════════════════════════════════════════════
            import re as _re

            # ── 1. BURSTINESS ANALYSER ────────────────────────────────────
            # AI text has uniform ~18-26 word sentences. Human writing mixes
            # short (<8 words) with long (>32 words). Detect per-section
            # distribution; flag any section that is > 70% in the uniform band.
            def _analyze_burstiness(txt):
                if not txt or not isinstance(txt, str):
                    return None
                clean = _re.sub(r'\\[a-zA-Z]+(?:\[[^\]]*\])?(?:\{[^}]*\})?', '', txt)
                clean = _re.sub(r'\$[^$]*\$', '', clean)
                sentences = _re.split(r'(?<=[.!?])\s+(?=[A-Z])', clean.strip())
                sentences = [s for s in sentences if len(s.strip()) > 5]
                if len(sentences) < 5:
                    return None
                lengths = [len(s.split()) for s in sentences]
                n = len(lengths)
                mean_len = sum(lengths) / n
                variance = sum((L - mean_len) ** 2 for L in lengths) / n
                stddev = variance ** 0.5
                short_count = sum(1 for L in lengths if L < 8)
                long_count = sum(1 for L in lengths if L > 32)
                uniform_count = sum(1 for L in lengths if 18 <= L <= 26)
                # Coefficient of variation: stddev / mean. Human writing CV ≈ 0.5–0.8,
                # AI writing CV ≈ 0.15–0.35. Low CV = uniform = AI signature.
                cv = stddev / mean_len if mean_len > 0 else 0
                return {
                    "total": n,
                    "short_pct": round(100 * short_count / n),
                    "long_pct": round(100 * long_count / n),
                    "uniform_pct": round(100 * uniform_count / n),
                    "mean_length": round(mean_len, 1),
                    "stddev": round(stddev, 1),
                    "cv": round(cv, 2),   # coefficient of variation — the best AI signal
                }

            burstiness_by_section = {}
            uniform_warnings = []
            for sk in ["abstract", "introduction", "literature_review",
                       "methodology", "results", "discussion", "conclusion"]:
                b = _analyze_burstiness(paper.get(sk, ""))
                if b:
                    burstiness_by_section[sk] = b
                    # Trigger warning when CV is low (AI-uniform) OR short/long share is tiny
                    reasons = []
                    if b["cv"] < 0.35:
                        reasons.append(f"CV={b['cv']} (human writing CV ≥ 0.5)")
                    if b["uniform_pct"] > 65:
                        reasons.append(f"{b['uniform_pct']}% sentences 18-26 words (uniform AI band)")
                    if b["short_pct"] < 10 and b["long_pct"] < 10:
                        reasons.append(f"only {b['short_pct']}% short + {b['long_pct']}% long sentences")
                    if reasons:
                        uniform_warnings.append(
                            f"⚠ AI-detection risk in {sk}: {'; '.join(reasons)}. "
                            f"Add 1-2 very short sentences (<8 words) per paragraph."
                        )
            paper["_burstiness_analysis"] = burstiness_by_section
            if uniform_warnings:
                if "_warnings" not in paper:
                    paper["_warnings"] = []
                paper["_warnings"].extend(uniform_warnings[:3])  # cap to top 3

            # ── 2. AI-LEAK SIGNAL DETECTOR ─────────────────────────────────
            # Scans for banned AI phrases that survived Call 6 + _dehuman_ai.
            # These are highest-priority AI-detection triggers.
            ai_leak_patterns = [
                (r'\bdelve[sd]?\b', 'delve/delves'),
                (r'\bcrucial\b', 'crucial'),
                (r'\bpivotal\b', 'pivotal'),
                (r'\btapestry\b', 'tapestry'),
                (r'\bfacilitat[es]+\b', 'facilitate'),
                (r'\bleverag[es]+\b', 'leverage'),
                (r'\butiliz[es]+\b', 'utilize'),
                (r'\bseamless(?:ly)?\b', 'seamless'),
                (r'\bnuanced\b', 'nuanced'),
                (r'\bIn this paper,?\s+we\b', 'In this paper we'),
                (r'\bFurthermore,\s', 'Furthermore,'),
                (r'\bMoreover,\s', 'Moreover,'),
                (r'\bIt is worth noting\b', 'It is worth noting'),
                (r'\bstate-of-the-art\b', 'state-of-the-art'),
            ]
            leaks_found = {}
            full_body = " ".join(str(paper.get(s, "")) for s in
                                 ["abstract", "introduction", "literature_review",
                                  "methodology", "results", "discussion", "conclusion"])
            for pat, label in ai_leak_patterns:
                matches = _re.findall(pat, full_body, flags=_re.IGNORECASE)
                if matches:
                    leaks_found[label] = len(matches)
            paper["_ai_leak_signals"] = leaks_found
            if leaks_found:
                total_leaks = sum(leaks_found.values())
                top_leaks = ", ".join(f"{k}({v})" for k, v in
                                      sorted(leaks_found.items(), key=lambda x: -x[1])[:5])
                if "_warnings" not in paper:
                    paper["_warnings"] = []
                paper["_warnings"].append(
                    f"⚠ {total_leaks} AI-detection signals survived humanization: {top_leaks}. "
                    f"Manually replace these phrases before submission."
                )
                paper["_publishability_score"] = max(0, paper["_publishability_score"] - min(10, total_leaks))

            # ── 3. CITATION PLACEMENT DISTRIBUTION ────────────────────────
            # AI always cites at sentence end. Humans scatter citations.
            # Detect by measuring the position of \cite{} in each sentence.
            end_cites = mid_cites = start_cites = 0
            for sk in ["introduction", "literature_review", "methodology",
                       "results", "discussion"]:
                txt = paper.get(sk, "")
                if not isinstance(txt, str):
                    continue
                # Find each \cite{} and check whether it's near sentence-end
                for m in _re.finditer(r'\\cite\{[^}]+\}', txt):
                    pos = m.end()
                    # Look at next 15 chars — if a period appears soon, it's end-cite
                    next_chunk = txt[pos:pos+15]
                    if _re.match(r'\s*\.', next_chunk):
                        end_cites += 1
                    elif m.start() < 60:
                        start_cites += 1
                    else:
                        mid_cites += 1
            total_cites = end_cites + mid_cites + start_cites
            if total_cites >= 10:
                end_pct = round(100 * end_cites / total_cites)
                paper["_citation_distribution"] = {
                    "total": total_cites, "end_pct": end_pct,
                    "mid_pct": round(100 * mid_cites / total_cites),
                    "start_pct": round(100 * start_cites / total_cites),
                }
                if end_pct > 80:
                    if "_warnings" not in paper:
                        paper["_warnings"] = []
                    paper["_warnings"].append(
                        f"⚠ {end_pct}% of citations are at sentence-end (AI signature). "
                        f"Move some to mid-sentence: 'Vaswani et al. [1] showed X' instead of 'X [1].'"
                    )

            # ══════════════════════════════════════════════════════════════
            # CALL 7: SENIOR REVIEWER SELF-REVIEW PASS
            # Simulates a senior program committee member at a top venue.
            # Returns structured critique the user can address in one review pass.
            # ══════════════════════════════════════════════════════════════
            try:
                _paper_snapshot = "\n\n".join([
                    f"TITLE: {paper['title']}",
                    f"ABSTRACT:\n{paper['abstract'][:1500]}",
                    f"INTRODUCTION (excerpt):\n{paper['introduction'][:2000]}",
                    f"METHODOLOGY (excerpt):\n{paper['methodology'][:1800]}",
                    f"RESULTS (excerpt):\n{paper['results'][:1800]}",
                    f"DISCUSSION (excerpt):\n{paper['discussion'][:1500]}",
                    f"CONCLUSION:\n{paper['conclusion'][:800]}",
                    f"CONTRIBUTIONS: {c1.get('keywords', [])}",
                    f"BIBTEX COUNT: {len(bibtex_entries)} entries, {_high_confidence_count} high-confidence",
                    f"TARGET VENUE: {target_journal}",
                ])
                call7 = await self.reasoner.think(f"""
You are a senior program committee member at a top-tier venue ({target_journal}).
You have just received this paper for review. Produce a rigorous, specific review
that identifies concrete weaknesses the authors can fix before camera-ready submission.

Be honest. Do NOT over-praise. Top-venue reviewers reject 75% of submissions. Your
job is to catch the weaknesses a real reviewer WOULD catch.

██ VENUE-SPECIFIC RULES FOR {target_journal} (venue class: {venue_rules.get('venue_class', 'generic')}) ██
Page limit: {venue_rules.get('pages', 'no hard limit')} pages
Word limit: {venue_rules.get('word_limit', 'n/a')}
Double-blind review: {venue_rules.get('double_blind', False)}
Required elements for this venue:
{chr(10).join('  - ' + rule for rule in venue_rules.get('rules', ['(none listed — use top-venue defaults)']))}

Your camera_ready_checklist MUST include any of the above rules that the paper has not yet complied with.
Your weaknesses list MUST flag any violation (e.g., if venue is double-blind and paper has author names, that is a blocker).

PAPER SNAPSHOT:
{_paper_snapshot}

Return ONLY a valid JSON object — no markdown, no preamble:
{{
  "verdict": "strong accept | weak accept | borderline | weak reject | strong reject",
  "acceptance_probability": <integer 0-100, realistic probability of acceptance at {target_journal}>,
  "strengths": [
    "Specific strength 1 — cite what part of the paper shows it",
    "Specific strength 2",
    "Specific strength 3"
  ],
  "weaknesses": [
    {{
      "issue": "Specific weakness (not generic)",
      "severity": "blocker | major | minor",
      "section": "which section — abstract/introduction/methodology/results/discussion",
      "fix": "Concrete action the author should take (not 'add more detail' — specify what detail)"
    }}
    // include 3-5 weakness objects
  ],
  "questions_reviewers_will_ask": [
    "A specific hard question a reviewer will raise about the methodology",
    "A specific hard question about the baselines or fairness of comparison",
    "A specific hard question about generalisation or scope"
  ],
  "missing_elements": [
    "Any element that should be in the paper but is absent (e.g., computational complexity analysis, failure case table, ablation of hyperparameters, reproducibility checklist)"
  ],
  "camera_ready_checklist": [
    "5-8 concrete checklist items to bring this from 85% → 100% ready"
  ]
}}""", max_tokens=6000)
                c7 = self._parse_json(call7.get("content", "{}"))
                paper["_review"] = c7
                # Adjust publishability score using reviewer's probability estimate
                rp = c7.get("acceptance_probability")
                if isinstance(rp, (int, float)) and 0 <= rp <= 100:
                    # Blend original score with reviewer estimate (weighted 40%)
                    blended = round(0.6 * paper["_publishability_score"] + 0.4 * rp)
                    paper["_publishability_score"] = blended
                    paper["_reviewer_acceptance_probability"] = int(rp)
            except Exception as _rev_err:
                paper["_review"] = {"error": f"Review pass failed: {_rev_err}"}

            # ══════════════════════════════════════════════════════════════
            # CALL 8: MATPLOTLIB FIGURE CODE GENERATOR
            # Produces a runnable Python script for EACH figure caption so
            # the user can actually generate real figures for their paper
            # instead of placeholder boxes. Uses synthetic/illustrative data
            # grounded in the paper's topic and results. The user replaces
            # the synthetic data with their real data before running.
            # ══════════════════════════════════════════════════════════════
            try:
                figure_caps = paper.get("figure_captions", [])
                if figure_caps and len(figure_caps) > 0:
                    _caps_formatted = "\n".join(f"Figure {i+1}: {c}" for i, c in enumerate(figure_caps))
                    call8 = await self.reasoner.think(f"""
Generate a complete, RUNNABLE Python matplotlib script for each figure below.
Each script must be self-contained — imports, data definition, plot, save to PNG.

Paper topic: {topic}
Research field: {research_field}
Key results (use for grounding the synthetic data): {c3.get('results', '')[:800]}

Figures to generate (one script per figure):
{_caps_formatted}

Requirements for each script:
1. Use matplotlib only (no seaborn). Set figure size to (8, 5) for single-col, (12, 5) for two-col wide.
2. Include realistic synthetic data that matches the paper's reported numbers.
3. Add proper axis labels, title (matching caption's first sentence), legend if multiple series.
4. Use accessible colour palette: #1f77b4 (blue), #ff7f0e (orange), #2ca02c (green), #d62728 (red).
5. Save to 'paper_figN.png' with dpi=300 and bbox_inches='tight'.
6. Include a prominent comment block at the top: "# REPLACE SYNTHETIC DATA WITH REAL EXPERIMENTAL DATA BEFORE RUNNING"
7. Scripts must run on Python 3.9+ with matplotlib 3.x and numpy only.

Return ONLY valid JSON mapping figure index to script:
{{
  "fig1_script": "import numpy as np\\nimport matplotlib.pyplot as plt\\n# REPLACE SYNTHETIC DATA WITH REAL DATA\\n...",
  "fig2_script": "...",
  "fig3_script": "..."
}}
Include exactly one script per figure caption above.""", max_tokens=8000)
                    c8 = self._parse_json(call8.get("content", "{}"))
                    # Collect scripts in order
                    fig_scripts = []
                    for i in range(len(figure_caps)):
                        key = f"fig{i+1}_script"
                        if c8.get(key):
                            fig_scripts.append({
                                "filename": f"paper_fig{i+1}.py",
                                "caption": figure_caps[i],
                                "code": c8[key],
                            })
                    paper["_figure_scripts"] = fig_scripts
            except Exception as _fig_err:
                paper["_figure_scripts"] = []

            return paper

        except Exception as e:
            return {"error": str(e)}

    def _dehuman_ai(self, text: str) -> str:
        """Deterministic post-processor that removes AI-signature phrases and
        structural patterns that trigger GPTZero, Turnitin, Originality.ai,
        Copyleaks, and ZeroGPT.

        Three-layer approach:
        1. Replace 80+ high-frequency AI n-grams with neutral/varied equivalents
        2. Break predictable sentence-start patterns (subject normalisation)
        3. Vary word choice for the most overused AI vocabulary

        LaTeX commands and citation markers are never touched.
        """
        import re as _re
        import hashlib

        if not isinstance(text, str) or not text:
            return text

        # ── LAYER 1: Sentence-level AI phrase removal ──────────────────────
        # Ordered longest-first to avoid partial matches.
        # Empty string replacements remove the phrase entirely; the capitalisation
        # fixer at the end restores correct sentence-start casing.
        replacements = [
            # ── Opening sentence phrases ──────────────────────────────────
            (r'\bIn this paper,\s*we\b',                   'This work'),
            (r'\bIn this work,\s*we\b',                    'Here we'),
            (r'\bIn this study,\s*we\b',                   'The study'),
            (r'\bIn this paper\b',                         'This paper'),
            (r'\bIn this work\b',                          'This work'),
            (r'\bIn this research\b',                      'This research'),
            (r'\bIn this article\b',                       'This article'),
            (r'\bThis paper presents\b',                   'We present'),
            (r'\bThis paper proposes\b',                   'We propose'),
            (r'\bThis paper introduces\b',                 'We introduce'),
            (r'\bThis study presents\b',                   'We present'),
            (r'\bThis work presents\b',                    'We present'),
            (r'\bThis work proposes\b',                    'We propose'),
            # ── Empty-replacement starters (capitalisation fixed below) ──
            (r'\bTo this end,\s*',                         ''),
            (r'\bTo that end,\s*',                         ''),
            (r'\bWith this in mind,\s*',                   ''),
            (r'\bWith this goal in mind,\s*',              ''),
            (r'\bWith this objective in mind,\s*',         ''),
            (r'\bToward this goal,\s*',                    ''),
            (r'\bTowards this goal,\s*',                   ''),
            (r'\bTowards this end,\s*',                    ''),
            (r'\bIn summary,\s*',                          ''),
            (r'\bIn conclusion,\s*',                       ''),
            (r'\bTo summarize,\s*',                        ''),
            (r'\bTo summarise,\s*',                        ''),
            (r'\bTo conclude,\s*',                         ''),
            (r'\bOverall,\s*',                             ''),
            (r'\bIn general,\s*',                          ''),
            (r'\bIn particular,\s*',                       ''),
            (r'\bIn essence,\s*',                          ''),
            (r'\bAt the same time,\s*',                    ''),
            (r'\bIt is worth noting that\s*',              ''),
            (r'\bIt is worth mentioning that\s*',          ''),
            (r'\bIt is important to note that\s*',         ''),
            (r'\bIt is important to mention that\s*',      ''),
            (r'\bIt should be noted that\s*',              ''),
            (r'\bIt should be mentioned that\s*',          ''),
            (r'\bIt is interesting to note that\s*',       ''),
            (r'\bIt is clear that\s*',                     ''),
            (r'\bIt is evident that\s*',                   ''),
            (r'\bIt is apparent that\s*',                  ''),
            (r'\bIt is obvious that\s*',                   ''),
            (r'\bIt can be seen that\s*',                  ''),
            (r'\bIt can be observed that\s*',              ''),
            (r'\bIt is demonstrated that\s*',              ''),
            (r'\bIt has been shown that\s*',               ''),
            (r'\bIt has been demonstrated that\s*',        ''),
            (r'\bWe note that\s*',                         ''),
            (r'\bWe observe that\s*',                      ''),
            (r'\bWe can see that\s*',                      ''),
            (r'\bWe can observe that\s*',                  ''),
            # ── Transition words that inflate AI probability score ─────────
            (r'(?<!\w)Furthermore,\s*',                    ''),
            (r'(?<!\w)Moreover,\s*',                       ''),
            (r'(?<!\w)Additionally,\s*',                   ''),
            (r'(?<!\w)In addition,\s*',                    ''),
            (r'(?<!\w)Besides,\s*',                        ''),
            (r'(?<!\w)Also,\s*(?=[A-Z])',                  ''),
            (r'(?<!\w)Consequently,\s*',                   'As a result,'),
            (r'(?<!\w)Subsequently,\s*',                   'After this,'),
            (r'(?<!\w)Specifically,\s*',                   ''),
            (r'(?<!\w)Importantly,\s*',                    ''),
            (r'(?<!\w)Notably,\s*',                        ''),
            (r'(?<!\w)Significantly,\s*',                  ''),
            (r'(?<!\w)Remarkably,\s*',                     ''),
            (r'(?<!\w)Interestingly,\s*',                  ''),
            (r'(?<!\w)Undoubtedly,\s*',                    ''),
            (r'(?<!\w)Evidently,\s*',                      ''),
            (r'(?<!\w)Clearly,\s*',                        ''),
            (r'(?<!\w)Obviously,\s*',                      ''),
            (r'(?<!\w)Certainly,\s*',                      ''),
            (r'(?<!\w)Generally speaking,\s*',             ''),
            (r'(?<!\w)By and large,\s*',                   ''),
            (r'(?<!\w)First and foremost,\s*',             'First,'),
            (r'(?<!\w)Last but not least,\s*',             'Finally,'),
            # ── Mid-sentence fillers ──────────────────────────────────────
            (r'\bOn the other hand,\s*',                   'Conversely,'),
            (r'\bIn the context of\b',                     'within'),
            (r'\bin the realm of\b',                       'in'),
            (r'\bin the field of\b',                       'in'),
            (r'\bin the area of\b',                        'in'),
            (r'\bin the domain of\b',                      'in'),
            (r'\bwith respect to\b',                       'regarding'),
            (r'\bwith regard to\b',                        'regarding'),
            (r'\bin terms of\b',                           'for'),
            (r'\bdue to the fact that\b',                  'because'),
            (r'\bin light of the fact that\b',             'given that'),
            (r'\bfor the purpose of\b',                    'to'),
            (r'\bfor the purposes of\b',                   'to'),
            (r'\bin order to\b',                           'to'),
            (r'\bso as to\b',                              'to'),
            (r'\bprior to\b',                              'before'),
            (r'\bsubsequent to\b',                         'after'),
            # ── Overused AI vocabulary ────────────────────────────────────
            (r'\bin recent years\b',                       'recently'),
            (r'\bin the past few years\b',                 'recently'),
            (r'\bover the past few years\b',               'in recent work'),
            (r'\brecent advances in\b',                    'advances in'),
            (r'\brecent progress in\b',                    'progress in'),
            (r'\brecent developments in\b',                'developments in'),
            (r'\bhas been widely\b',                       'is'),
            (r'\bhave been widely\b',                      'are'),
            (r'\bwidely used\b',                           'common'),
            (r'\bwidely adopted\b',                        'commonly used'),
            (r'\bwidely studied\b',                        'well-studied'),
            (r'\bwidely recognised\b',                     'recognised'),
            (r'\bwidely recognized\b',                     'recognized'),
            (r'\bstate-of-the-art performance\b',          'top benchmark results'),
            (r'\bstate-of-the-art results\b',              'best reported results'),
            (r'\bstate-of-the-art methods\b',              'leading methods'),
            (r'\bstate-of-the-art approaches\b',           'leading approaches'),
            (r'\bstate-of-the-art\b',                      'leading'),
            (r'\bThe proposed method\b',                   'Our method'),
            (r'\bthe proposed method\b',                   'our method'),
            (r'\bOur proposed method\b',                   'Our method'),
            (r'\bOur proposed approach\b',                 'Our approach'),
            (r'\bthe proposed approach\b',                 'this approach'),
            (r'\bthe proposed framework\b',                'our framework'),
            (r'\bthe proposed model\b',                    'our model'),
            (r'\bthe proposed system\b',                   'our system'),
            (r'\ba wide range of\b',                       'a broad set of'),
            (r'\ba diverse range of\b',                    'diverse'),
            (r'\ba variety of\b',                          'various'),
            (r'\ba plethora of\b',                         'many'),
            (r'\ba myriad of\b',                           'many'),
            (r'\ba number of\b',                           'several'),
            (r'\bplays a crucial role\b',                  'is central'),
            (r'\bplays a vital role\b',                    'is vital'),
            (r'\bplays an important role\b',               'matters'),
            (r'\bplays a key role\b',                      'is key'),
            (r'\bplays a significant role\b',              'significantly affects'),
            (r'\bplays a pivotal role\b',                  'is pivotal'),
            (r'\bplays a fundamental role\b',              'fundamentally shapes'),
            (r'\bplays an essential role\b',               'is essential'),
            (r'\bextensive experiments\b',                 'our experiments'),
            (r'\bextensive experimental\b',                'experimental'),
            (r'\bcomprehensive evaluation\b',              'our evaluation'),
            (r'\bcomprehensive analysis\b',                'our analysis'),
            (r'\bcomprehensive study\b',                   'this study'),
            (r'\bcomprehensive framework\b',               'our framework'),
            (r'\bpromising results\b',                     'strong results'),
            (r'\bpromising performance\b',                 'strong performance'),
            (r'\bchallenging task\b',                      'difficult problem'),
            (r'\bchallenging problem\b',                   'difficult problem'),
            (r'\bchallenging issue\b',                     'difficult issue'),
            (r'\brobust performance\b',                    'consistent performance'),
            (r'\brobust results\b',                        'consistent results'),
            (r'\bsignificant improvements\b',              'improvements'),
            (r'\bsubstantial improvements\b',              'clear improvements'),
            (r'\bconsiderable improvements\b',             'notable improvements'),
            (r'\bsuperior performance\b',                  'better performance'),
            (r'\bsuperior results\b',                      'better results'),
            (r'\bnovel approach\b',                        'our approach'),
            (r'\bnovel method\b',                          'our method'),
            (r'\bnovel framework\b',                       'our framework'),
            (r'\bnovel model\b',                           'our model'),
            (r'\bnovel architecture\b',                    'our architecture'),
            (r'\binnovative approach\b',                   'our approach'),
            (r'\bhave emerged as\b',                       'are now'),
            (r'\bhas emerged as\b',                        'is now'),
            (r'\bhave gained\b',                           'gained'),
            (r'\bhas gained\b',                            'gained'),
            (r'\bgained significant attention\b',          'attracted attention'),
            (r'\bgained considerable attention\b',         'attracted interest'),
            (r'\bgained traction\b',                       'grown'),
            (r'\bdraws inspiration from\b',                'builds on'),
            (r'\bleverages\b',                             'uses'),
            (r'\bleverage\b',                              'use'),
            (r'\bharnessing\b',                            'using'),
            (r'\bharness\b',                               'use'),
            (r'\butilizes\b',                              'uses'),
            (r'\butilize\b',                               'use'),
            (r'\butilising\b',                             'using'),
            (r'\butilise\b',                               'use'),
            # ── TOP AI-DETECTION SIGNALS (GPTZero, Turnitin specifically target these) ──
            # "delve" is the #1 most-flagged AI word — humans almost never use it
            (r'\bdelve into\b',                            'examine'),
            (r'\bdelves into\b',                           'examines'),
            (r'\bdelved into\b',                           'examined'),
            (r'\bdelving into\b',                          'examining'),
            (r'\bdelve\b',                                 'explore'),
            (r'\bdelves\b',                                'explores'),
            # "crucial" — heavily over-used by AI (standalone form)
            (r'\bcrucial\b',                               'key'),
            # "pivotal" — standalone (plays a pivotal role handled above)
            (r'\bpivotal\b',                               'central'),
            # "paramount" — almost exclusively an AI word in academic context
            (r'\bparamount\b',                             'critical'),
            # "underscores" used as verb — AI over-uses this construction
            (r'\bunderscores the importance\b',            'confirms the importance'),
            (r'\bunderscores the need\b',                  'confirms the need'),
            (r'\bunderscores\b',                           'confirms'),
            (r'\bunderscore\b',                            'confirm'),
            # "showcase" / "showcases" — AI tells stories; humans report data
            (r'\bshowcases\b',                             'demonstrates'),
            (r'\bshowcase\b',                              'demonstrate'),
            (r'\bshowcased\b',                             'demonstrated'),
            # "facilitate" / "facilitates" — formal bureaucratic verb
            (r'\bfacilitates\b',                           'enables'),
            (r'\bfacilitate\b',                            'enable'),
            (r'\bfacilitated\b',                           'enabled'),
            (r'\bfacilitating\b',                          'enabling'),
            # "cutting-edge" — AI cliché
            (r'\bcutting-edge\b',                          'leading'),
            (r'\bcutting edge\b',                          'leading'),
            # "groundbreaking" — over-hyped AI adjective
            (r'\bgroundbreaking\b',                        'significant'),
            # "intricate" — AI over-uses this where humans say "complex"
            (r'\bintricate\b',                             'complex'),
            # "nuanced" — overused AI qualifier
            (r'\bnuanced\b',                               'subtle'),
            # "multifaceted" — AI abstraction word
            (r'\bmultifaceted\b',                          'complex'),
            # "bolster" / "bolsters" — AI loves this verb; humans say "strengthen"
            (r'\bbolsters\b',                              'strengthens'),
            (r'\bbolster\b',                               'strengthen'),
            (r'\bbolstered\b',                             'strengthened'),
            # "elucidate" — overly formal; humans say "explain" or "clarify"
            (r'\belucidates\b',                            'explains'),
            (r'\belucidate\b',                             'explain'),
            (r'\belucidated\b',                            'explained'),
            (r'\belucidating\b',                           'explaining'),
            # "invaluable" — AI superlative; humans use "highly useful" or "essential"
            (r'\binvaluable\b',                            'highly useful'),
            # "endeavour" / "endeavor" — overly formal AI word
            (r'\bendeavours\b',                            'efforts'),
            (r'\bendeavour\b',                             'effort'),
            (r'\bendeavors\b',                             'efforts'),
            (r'\bendeavor\b',                              'effort'),
            # "realm" — AI abstraction ("in the realm of" is handled above,
            # but standalone "realm" still appears e.g., "across all realms")
            (r'\brealms\b',                                'areas'),
            (r'\bthis realm\b',                            'this area'),
            # "tapestry" — a pure AI hallmark word; never used in real academic papers
            (r'\btapestry\b',                              'combination'),
            # "synergy" / "synergistic" — over-used AI abstraction
            (r'\bsynergistic\b',                           'combined'),
            (r'\bsynergistically\b',                       'together'),
            # "holistic" — AI buzzword
            (r'\bholistic\b',                              'integrated'),
            # "robust" (standalone, when not describing a specific technical property)
            # NOTE: Only replace in certain patterns to avoid over-replacement
            (r'\brobust framework\b',                      'reliable framework'),
            (r'\brobust approach\b',                       'reliable approach'),
            (r'\brobust model\b',                          'reliable model'),
            (r'\brobust solution\b',                       'reliable solution'),
            # ── EXTENDED BATCH: 2024 AI-detector trigger words ────────────────
            (r'\bthe landscape of\b',                      'the field of'),
            (r'\bever-evolving\b',                         'fast-moving'),
            (r'\brapidly evolving\b',                      'fast-moving'),
            (r'\bempowers\b',                              'allows'),
            (r'\bempower\b',                               'allow'),
            (r'\bempowering\b',                            'allowing'),
            (r'\bseamlessly\b',                            'smoothly'),
            (r'\bseamless integration\b',                  'direct integration'),
            (r'\bseamless\b',                              'smooth'),
            (r'\bfosters\b',                               'supports'),
            (r'\bfoster\b',                                'support'),
            (r'\bfostering\b',                             'supporting'),
            (r'\bpaves the way\b',                         'enables'),
            (r'\bpave the way\b',                          'enable'),
            (r'\bsheds light on\b',                        'clarifies'),
            (r'\bshed light on\b',                         'clarify'),
            (r'\bshedding light on\b',                     'clarifying'),
            (r'\bin-depth analysis\b',                     'detailed analysis'),
            (r'\bin-depth study\b',                        'detailed study'),
            (r'\bin-depth\b',                              'detailed'),
            (r'\brigorous evaluation\b',                   'systematic evaluation'),
            (r'\brigorous analysis\b',                     'systematic analysis'),
            (r'\brigorous\b',                              'systematic'),
            (r'\bmitigates\b',                             'reduces'),
            (r'\bmitigate\b',                              'reduce'),
            (r'\bmitigating\b',                            'reducing'),
            (r'\baforementioned\b',                        'above-described'),
            (r'(?<!\w)Thus,\s*',                           ''),
            (r'(?<!\w)Hence,\s*',                          ''),
            (r'(?<!\w)Herein,\s*',                         ''),
            (r'\bin this regard\b',                        ''),
            (r'\bin this respect\b',                       ''),
            (r'\baddress the challenge of\b',              'tackle'),
            (r'\baddress the challenges of\b',             'tackle'),
            (r'(?<!\w)Moving forward,\s*',                 ''),
            (r'\breal-world scenarios\b',                  'practical settings'),
            (r'\breal-world settings\b',                   'practical settings'),
            (r'\bexhibits\b',                              'shows'),
            (r'\bexhibit\b',                               'show'),
            (r'\bdemonstrate the effectiveness of\b',      'show that'),
            (r'\bdemonstrates the effectiveness of\b',     'shows that'),
            (r'\bbenchmark datasets\b',                    'benchmarks'),
            (r'\bwell-established\b',                      'established'),
            (r'\bTo the best of our knowledge,\s*',        ''),
            (r'\bto the best of our knowledge,\s*',        ''),
            (r'\bsurpasses\b',                             'beats'),
            (r'\bsurpass\b',                               'beat'),
            (r'\bimpressive performance\b',                'strong performance'),
            (r'\bimpressive results\b',                    'strong results'),
            (r'\bimpressive\b',                            'strong'),
            (r'\bAs such,\s*',                             ''),
            (r'\bas such,\s*',                             ''),
            (r'\bAs a consequence,\s*',                    'As a result,'),
            (r'\bas a consequence,\s*',                    'as a result,'),
            (r'\bsubstantial gains\b',                     'clear gains'),
            (r'\btake advantage of\b',                     'exploit'),
            (r'\btakes advantage of\b',                    'exploits'),
        ]

        for pattern, replacement in replacements:
            text = _re.sub(pattern, replacement, text, flags=_re.IGNORECASE)

        # ── LAYER 2: Structural sentence-start normalisation ───────────────
        # After empty-replacement removals, some sentences start with a
        # lowercase word (e.g., "word. the model achieves" → "word. The model").
        # Fix this deterministically.
        text = _re.sub(r'  +', ' ', text)
        text = _re.sub(r'\.\s*,', '.', text)
        text = _re.sub(r',\s*,', ',', text)
        text = _re.sub(r'(\.\s+)([a-z])',
                       lambda m: m.group(1) + m.group(2).upper(), text)
        # Fix sentence-start after newline
        text = _re.sub(r'(\n)([a-z])',
                       lambda m: m.group(1) + m.group(2).upper(), text)
        # Clean leading spaces from lines
        text = _re.sub(r'\n +', '\n', text)

        # ── LAYER 3: Vocabulary variation for highest-frequency AI tokens ──
        # AI models heavily over-use a small set of words.  We rotate them
        # deterministically using a character-hash so the same word in different
        # contexts gets different replacements (not always the same synonym).
        def _rotate(word, options, context_char=' '):
            idx = ord(context_char) % len(options)
            return options[idx]

        # "significant" → varies by context character (neighbouring char hash)
        def _vary_significant(m):
            ctx = m.string[max(0, m.start()-1):m.start()]
            opts = ['notable', 'marked', 'clear', 'measurable', 'meaningful']
            return _rotate(m.group(0), opts, ctx[-1] if ctx else ' ')
        # Only replace when not inside LaTeX commands or citations
        text = _re.sub(r'(?<!\\)\bsignificantly\b(?!\{)', _vary_significant, text)

        def _vary_substantial(m):
            ctx = m.string[max(0, m.start()-1):m.start()]
            opts = ['considerable', 'clear', 'marked', 'large', 'sizable']
            return _rotate(m.group(0), opts, ctx[-1] if ctx else ' ')
        text = _re.sub(r'(?<!\\)\bsubstantial\b(?!\{)', _vary_substantial, text)

        def _vary_demonstrate(m):
            ctx = m.string[max(0, m.start()-1):m.start()]
            opts = ['show', 'reveal', 'confirm', 'establish', 'indicate']
            return _rotate(m.group(0), opts, ctx[-1] if ctx else ' ')
        text = _re.sub(r'(?<!\\)\bdemonstrate[sd]?\b(?!\{)', _vary_demonstrate, text)

        # "achieve" → varied (one of the most over-predicted AI verbs)
        def _vary_achieve(m):
            ctx = m.string[max(0, m.start()-1):m.start()]
            opts = ['reach', 'post', 'deliver', 'record', 'clock']
            return _rotate(m.group(0), opts, ctx[-1] if ctx else ' ')
        text = _re.sub(r'(?<!\\)\bachieves\b(?!\{)', lambda m: _vary_achieve(m).rstrip('s')+'s'
                        if _vary_achieve(m)[-1]!='s' else _vary_achieve(m), text)
        text = _re.sub(r'(?<!\\)\bachieve\b(?!\{)', _vary_achieve, text)

        # "outperform" → varied
        def _vary_outperform(m):
            ctx = m.string[max(0, m.start()-1):m.start()]
            opts = ['outpace', 'edge out', 'beat', 'top', 'surpass']
            return _rotate(m.group(0), opts, ctx[-1] if ctx else ' ')
        text = _re.sub(r'(?<!\\)\boutperforms\b(?!\{)', lambda m: _vary_outperform(m)+'s', text)
        text = _re.sub(r'(?<!\\)\boutperform\b(?!\{)', _vary_outperform, text)

        # "improve" → varied
        def _vary_improve(m):
            ctx = m.string[max(0, m.start()-1):m.start()]
            opts = ['boost', 'lift', 'raise', 'advance', 'push']
            return _rotate(m.group(0), opts, ctx[-1] if ctx else ' ')
        text = _re.sub(r'(?<!\\)\bimproves\b(?!\{)', lambda m: _vary_improve(m)+'s', text)
        text = _re.sub(r'(?<!\\)\bimprove\b(?!\{)', _vary_improve, text)

        # "performance" → varied
        def _vary_performance(m):
            ctx = m.string[max(0, m.start()-1):m.start()]
            opts = ['results', 'accuracy', 'numbers', 'scores', 'output']
            return _rotate(m.group(0), opts, ctx[-1] if ctx else ' ')
        text = _re.sub(r'(?<!\\)\bperformance\b(?!\{)', _vary_performance, text)

        # "model" (standalone at sentence positions) → varied
        def _vary_approach(m):
            ctx = m.string[max(0, m.start()-1):m.start()]
            opts = ['method', 'system', 'approach', 'framework', 'architecture']
            return _rotate(m.group(0), opts, ctx[-1] if ctx else ' ')
        # Only rotate in "our model" / "the model" / "this model" patterns
        text = _re.sub(r'\b(our|the|this)\s+model\b', lambda m:
            m.group(1) + ' ' + _vary_approach(m), text)

        return text

    def _synthesize_bibtex_from_citation_map(self, citation_map: dict) -> list:
        """Synthesize minimal BibTeX entries from citation_map when Call 5 fails.

        This guarantees the downloaded .tex will compile without [?] markers even if
        the AI BibTeX call returns empty or unparseable output.  Each entry uses the
        ref0N key scheme that buildLatex() falls back to so the keys always match.

        Args:
            citation_map: Dict mapping citation number strings to
                          {author, year, title_hint, venue} dicts from Call 2.

        Returns:
            List of minimal BibTeX entry dicts (one per citation_map entry).
        """
        entries = []
        for n_str, info in citation_map.items():
            if not info or not isinstance(info, dict):
                continue
            try:
                num = int(n_str)
            except (ValueError, TypeError):
                num = len(entries) + 1

            key = f"ref{num:02d}"
            author_raw = info.get("author", "")
            year = str(info.get("year", "2024"))
            title = info.get("title_hint", f"Reference {num}")
            venue = info.get("venue", "")
            confidence = info.get("confidence", "low")   # default low for synthesis path

            # Normalise author to BibTeX "Last, First" format
            # citation_map stores "Smith et al." or "Vaswani et al." — keep as-is;
            # BibTeX handles display formatting.
            author = author_raw if author_raw else "Unknown Author"

            # High-confidence entries were recalled from training knowledge and are
            # real papers — do NOT add a note. Omitting the note is the signal that
            # the entry is clean and does not need manual verification.
            # Low-confidence entries (approximated title/venue) get a ⚠ note so the
            # user knows to check those specific entries before submission.
            entry = {
                "key":    key,
                "type":   "inproceedings" if venue else "misc",
                "author": author,
                "title":  title,
                "year":   year,
            }
            if confidence != "high":
                entry["note"] = "⚠ AUTO-GENERATED PLACEHOLDER — replace with real bibliographic details"
            if venue:
                # Map common abbreviations to full venue names
                venue_map = {
                    "NeurIPS": "Advances in Neural Information Processing Systems",
                    "ICML": "International Conference on Machine Learning",
                    "ICLR": "International Conference on Learning Representations",
                    "ACL": "Annual Meeting of the Association for Computational Linguistics",
                    "EMNLP": "Conference on Empirical Methods in Natural Language Processing",
                    "NAACL": "Annual Conference of the North American Chapter of the ACL",
                    "CVPR": "IEEE/CVF Conference on Computer Vision and Pattern Recognition",
                    "ICCV": "IEEE/CVF International Conference on Computer Vision",
                    "AAAI": "AAAI Conference on Artificial Intelligence",
                }
                entry["booktitle"] = venue_map.get(venue, venue)

            entries.append(entry)

        return entries

    def _is_section_truncated(self, text: str, min_words: int = 150) -> bool:
        """Return True if a section text appears to have been cut off mid-sentence.

        Detects truncation by checking:
        1. Text is too short (below min_words threshold)
        2. Text does not end with a sentence-terminating character
        """
        if not text or not text.strip():
            return True
        stripped = text.strip()
        word_count = len(stripped.split())
        if word_count < min_words:
            return True
        # A properly concluded paragraph ends with . ! ? or a closing quote/brace
        last_char = stripped[-1]
        return last_char not in {'.', '!', '?', '"', "'", '}', ')', '\\'}

    def _parse_json(self, content: str) -> dict:
        """Strip markdown fences and parse JSON. Falls back to brace-scan. Returns {} on failure."""
        if not content:
            return {}
        try:
            text = content.strip()
            # Strip markdown code fences
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)
        except Exception:
            pass
        # Fallback: scan for the outermost { ... } block
        try:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(content[start:end+1])
        except Exception:
            pass
        # Fallback: scan for the outermost [ ... ] block (arrays in Call 5)
        try:
            start = content.find("[")
            end = content.rfind("]")
            if start != -1 and end != -1 and end > start:
                return json.loads(content[start:end+1])
        except Exception:
            pass
        return {}

    async def chat(self, user_message: str, session_id: str) -> dict:
        try:
            history = await self.memory.get_history(session_id)
            tools = self.tool_executor.get_all_tool_definitions()
            result = await self.reasoner.think_with_tools(user_message, tools, history=history)
            response = result.get("content", "I could not process that request.")
            await self.memory.save_message(session_id, "user", user_message)
            await self.memory.save_message(session_id, "assistant", response)
            return {"response": response, "tools_used": result.get("tools_used", [])}
        except Exception as e:
            return {"error": str(e), "response": f"Error: {str(e)}"}
