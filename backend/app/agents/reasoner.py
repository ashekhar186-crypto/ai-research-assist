"""
reasoner.py — Claude API wrapper

Uses the ASYNC Anthropic client so it never blocks the FastAPI event loop.
"""
import asyncio
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import get_settings

settings = get_settings()


class ReasoningEngine:

    def __init__(self):
        # AsyncAnthropic — required inside async FastAPI routes
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL
        self.system_prompt = (
            "You are an elite academic researcher and scientific writer with deep expertise in "
            "producing top-tier, peer-reviewed publications accepted at venues such as NeurIPS, "
            "Nature, IEEE Transactions, ACM SIGKDD, Science, and The Lancet. "
            "Your writing is technically precise, analytically rigorous, and structurally sound. "
            "You use proper academic conventions: IMRaD structure, passive voice where appropriate, "
            "hedged language for claims, explicit limitations, and numbered citations like [1], [2]. "
            "You include quantitative results with specific metrics, statistical significance, "
            "and comparisons to baselines. LaTeX math notation ($\\mathcal{L}$, $f_\\theta$, etc.) "
            "is used where appropriate. "
            "CRITICAL: When asked for structured output, respond with ONLY valid JSON — "
            "no markdown code fences, no preamble, no commentary outside the JSON object."
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def think(self, prompt: str, max_tokens: int = None, cache_prefix: str = None) -> dict:
        """Single-turn Claude call with optional prompt caching.

        Args:
            prompt: The user prompt to send.
            max_tokens: Override default max_tokens for this call.
            cache_prefix: If given, the prefix of the prompt that should be cached.
                This string is sent as its own cache-enabled content block, and the
                remainder of the prompt as a second block. Subsequent calls with the
                SAME cache_prefix read cached tokens at 10% cost.
                Use for the shared ctx_str across Calls 1-7.
        """
        caching_on = settings.CLAUDE_USE_PROMPT_CACHING
        # ── Always cache the system prompt (reused across all 7+ calls) ──
        if caching_on:
            system_blocks = [
                {"type": "text", "text": self.system_prompt,
                 "cache_control": {"type": "ephemeral"}},
            ]
        else:
            system_blocks = self.system_prompt

        # ── Optionally cache a user-message prefix (ctx_str shared across calls)
        if caching_on and cache_prefix and prompt.startswith(cache_prefix):
            suffix = prompt[len(cache_prefix):]
            user_content = [
                {"type": "text", "text": cache_prefix,
                 "cache_control": {"type": "ephemeral"}},
                {"type": "text", "text": suffix or " "},
            ]
        else:
            user_content = prompt

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or settings.CLAUDE_MAX_TOKENS,
            system=system_blocks,
            messages=[{"role": "user", "content": user_content}],
        )
        return {
            "content": response.content[0].text,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cache_read_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
                "cache_creation_tokens": getattr(response.usage, "cache_creation_input_tokens", 0),
            },
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def think_with_tools(self, prompt: str, tools: list, history: list = None) -> dict:
        """Agentic multi-turn call with tool use. Returns {content, tools_used, usage}."""
        messages = []
        if history:
            for msg in history[-10:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })
        messages.append({"role": "user", "content": prompt})
        tools_used = []

        for _ in range(10):
            kwargs = {
                "model": self.model,
                "max_tokens": settings.CLAUDE_MAX_TOKENS,
                "system": self.system_prompt,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools

            response = await self.client.messages.create(**kwargs)

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tools_used.append(block.name)
                        from app.agents.tool_executor import get_tool_executor
                        result = await get_tool_executor().execute_tool(block.name, **block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        })
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                text = "".join(
                    block.text for block in response.content if hasattr(block, "text")
                )
                return {
                    "content": text,
                    "tools_used": tools_used,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                }

        return {"content": "Max iterations reached.", "tools_used": tools_used}
