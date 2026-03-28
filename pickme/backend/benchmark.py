import json
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from models import BenchmarkResult, BenchmarkReport

anthropic_client = AsyncAnthropic()

def _get_openai_client() -> AsyncOpenAI:
    return AsyncOpenAI()


async def run_benchmark(target_name: str, prompt: str, context_before: str, context_after: str | None = None) -> BenchmarkReport:
    results = []

    claude_before = await _ask_claude(prompt, context_before)
    claude_pick_before = _calculate_pick_rate(target_name, claude_before)
    claude_result = BenchmarkResult(
        llm_name="Claude", pick_rate_before=claude_pick_before, raw_responses=[claude_before],
    )
    if context_after:
        claude_after = await _ask_claude(prompt, context_after)
        claude_result.pick_rate_after = _calculate_pick_rate(target_name, claude_after)
        claude_result.raw_responses.append(claude_after)
    results.append(claude_result)

    try:
        gpt_before = await _ask_gpt(prompt, context_before)
        gpt_pick_before = _calculate_pick_rate(target_name, gpt_before)
        gpt_result = BenchmarkResult(
            llm_name="GPT", pick_rate_before=gpt_pick_before, raw_responses=[gpt_before],
        )
        if context_after:
            gpt_after = await _ask_gpt(prompt, context_after)
            gpt_result.pick_rate_after = _calculate_pick_rate(target_name, gpt_after)
            gpt_result.raw_responses.append(gpt_after)
        results.append(gpt_result)
    except Exception:
        pass

    return BenchmarkReport(target_name=target_name, prompt_used=prompt, results=results)


async def run_tool_selection_proof(
    task_prompt: str,
    tool_before: dict,
    tool_after: dict,
) -> dict:
    tools = [
        {
            "name": tool_before.get("name", "tool_a"),
            "description": tool_before.get("description", ""),
            "input_schema": tool_before.get("inputSchema", {"type": "object", "properties": {}}),
        },
        {
            "name": tool_after.get("name", "tool_b"),
            "description": tool_after.get("description", ""),
            "input_schema": tool_after.get("inputSchema", {"type": "object", "properties": {}}),
        },
    ]

    message = await anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": task_prompt}],
        tools=tools,
    )

    tool_used = None
    for block in message.content:
        if block.type == "tool_use":
            tool_used = block.name
            break

    return {
        "task": task_prompt,
        "tool_before": tool_before.get("name"),
        "tool_after": tool_after.get("name"),
        "picked": tool_used,
        "picked_optimized": tool_used == tool_after.get("name"),
        "response": [b.text if hasattr(b, "text") else str(b) for b in message.content],
    }


async def _ask_claude(prompt: str, context: str) -> str:
    msg = await anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {prompt}"}],
    )
    return msg.content[0].text


async def _ask_gpt(prompt: str, context: str) -> str:
    resp = await _get_openai_client().chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {prompt}"}],
    )
    return resp.choices[0].message.content or ""


def _calculate_pick_rate(target_name: str, response: str) -> float:
    target_lower = target_name.lower()
    words = response.lower()
    mentions = words.count(target_lower)
    return min(mentions / 3.0, 1.0)
