"""
Real agent simulation engine.

Runs two parallel Claude agent sessions with identical tasks:
- Agent A: sees original tool/service description + real competitor docs
- Agent B: sees optimized tool/service description + same competitors
Both agents browse real docs, evaluate, and recommend which tool to use.
"""

import asyncio
import json
import re
import httpx
from anthropic import AsyncAnthropic
from pydantic import BaseModel

client = AsyncAnthropic()


class AgentDecision(BaseModel):
    agent_label: str  # "before" or "after"
    picked_tool: str
    reasoning: str
    tools_evaluated: list[str]
    confidence: str  # "high" | "medium" | "low"
    raw_output: str


class SimulationResult(BaseModel):
    task: str
    target_tool: str
    before: AgentDecision
    after: AgentDecision
    optimization_effective: bool
    summary: str


async def run_agent_simulation(
    target_tool: str,
    target_url: str | None,
    target_description: str,
    optimized_description: str | None,
    task: str,
    competitors: list[str] | None = None,
) -> SimulationResult:
    """Run two parallel agent sessions comparing before/after optimization."""

    # Step 1: Fetch real documentation
    target_docs = await _fetch_docs(target_tool, target_url)

    # Step 2: Identify and fetch competitor docs
    if not competitors:
        competitors = await _identify_competitors(target_tool, task)

    competitor_docs = await asyncio.gather(
        *[_fetch_docs(comp, None) for comp in competitors[:4]]  # limit to 4 competitors
    )
    competitor_context = "\n\n".join([
        f"## {comp}\n{docs}"
        for comp, docs in zip(competitors[:4], competitor_docs)
    ])

    # Step 3: Optimize description if not provided
    if not optimized_description:
        optimized_description = await _optimize_description(
            target_tool, target_description, target_docs, task
        )

    # Step 4: Build before/after contexts
    before_context = f"## {target_tool}\n{target_description}\n\n{target_docs}"
    after_context = f"## {target_tool}\n{optimized_description}\n\n{target_docs}"

    # Step 5: Run two agents in parallel
    agent_a, agent_b = await asyncio.gather(
        _run_agent(
            task=task,
            target_tool=target_tool,
            target_context=before_context,
            competitor_context=competitor_context,
            label="before",
        ),
        _run_agent(
            task=task,
            target_tool=target_tool,
            target_context=after_context,
            competitor_context=competitor_context,
            label="after",
        ),
    )

    # Step 6: Determine if optimization was effective
    target_lower = target_tool.lower()
    before_picked = target_lower in agent_a.picked_tool.lower()
    after_picked = target_lower in agent_b.picked_tool.lower()

    effective = after_picked and not before_picked

    if effective:
        summary = f"Optimization worked: {target_tool} was NOT picked before but WAS picked after optimization."
    elif before_picked and after_picked:
        summary = f"{target_tool} was picked in both cases. Optimization reinforced existing selection."
    elif not before_picked and not after_picked:
        summary = f"{target_tool} was not picked in either case. The tool may need deeper improvements beyond description optimization."
    else:
        summary = f"Unexpected: {target_tool} was picked before but not after. Review the optimization."

    return SimulationResult(
        task=task,
        target_tool=target_tool,
        before=agent_a,
        after=agent_b,
        optimization_effective=effective,
        summary=summary,
    )


async def _run_agent(
    task: str,
    target_tool: str,
    target_context: str,
    competitor_context: str,
    label: str,
) -> AgentDecision:
    """Run a single agent session that evaluates tools for a task."""

    system = """You are an expert developer agent. When given a task, you evaluate available tools, frameworks, and services to recommend the BEST option.

Your evaluation process:
1. Understand the task requirements
2. Review each available tool's documentation and capabilities
3. Compare: features, ease of use, community support, documentation quality, ecosystem
4. Make a definitive recommendation with clear reasoning

Be specific and decisive. Pick ONE winner."""

    user_prompt = f"""Task: {task}

Here are the available tools/frameworks/services. Evaluate each one and recommend the BEST choice for this task.

{target_context}

{competitor_context}

---

After reviewing all options, respond in this exact JSON format:
{{
  "picked_tool": "name of your top recommendation",
  "reasoning": "2-3 sentences explaining why you picked this",
  "tools_evaluated": ["list", "of", "all", "tools", "you", "considered"],
  "confidence": "high" or "medium" or "low"
}}

Respond with ONLY the JSON, no other text."""

    msg = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = msg.content[0].text.strip()

    try:
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        data = json.loads(raw)
        return AgentDecision(
            agent_label=label,
            picked_tool=data.get("picked_tool", "unknown"),
            reasoning=data.get("reasoning", ""),
            tools_evaluated=data.get("tools_evaluated", []),
            confidence=data.get("confidence", "medium"),
            raw_output=raw,
        )
    except (json.JSONDecodeError, KeyError):
        return AgentDecision(
            agent_label=label,
            picked_tool="parse_error",
            reasoning=raw[:500],
            tools_evaluated=[],
            confidence="low",
            raw_output=raw,
        )


async def _fetch_docs(tool_name: str, url: str | None) -> str:
    """Fetch real documentation for a tool from the web."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=10) as http:
        # Try provided URL first
        if url:
            try:
                resp = await http.get(url)
                if resp.status_code == 200:
                    text = _extract_text(resp.text)
                    if len(text) > 100:
                        return text[:3000]
            except Exception:
                pass

        # Try GitHub README
        slug = tool_name.lower().replace(" ", "-")
        github_urls = [
            f"https://raw.githubusercontent.com/{slug}/{slug}/main/README.md",
            f"https://raw.githubusercontent.com/{slug}/{slug}/master/README.md",
            f"https://raw.githubusercontent.com/tiangolo/{slug}/master/README.md",
        ]
        for gh_url in github_urls:
            try:
                resp = await http.get(gh_url)
                if resp.status_code == 200:
                    return resp.text[:3000]
            except Exception:
                continue

        # Try PyPI
        try:
            resp = await http.get(f"https://pypi.org/pypi/{slug}/json")
            if resp.status_code == 200:
                data = resp.json()
                desc = data.get("info", {}).get("description", "")
                if desc:
                    return desc[:3000]
        except Exception:
            pass

        # Try npm
        try:
            resp = await http.get(f"https://registry.npmjs.org/{slug}")
            if resp.status_code == 200:
                data = resp.json()
                readme = data.get("readme", "")
                if readme:
                    return readme[:3000]
        except Exception:
            pass

    return f"No documentation fetched for {tool_name}. Evaluate based on general knowledge."


async def _identify_competitors(tool_name: str, task: str) -> list[str]:
    """Use Claude to identify real competitors for a tool."""
    msg = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": f"""List 4 real competing tools/frameworks/services for "{tool_name}" when the task is: "{task}"

Return ONLY a JSON array of strings with tool names, e.g. ["Express", "Django", "Flask", "Spring Boot"]
No markdown fencing."""}],
    )
    try:
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(raw)
    except Exception:
        return ["Alternative A", "Alternative B", "Alternative C", "Alternative D"]


async def _optimize_description(
    tool_name: str,
    original_desc: str,
    docs: str,
    task: str,
) -> str:
    """Generate an optimized description using real docs context."""
    msg = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": f"""Rewrite this tool/framework description to maximize its chances of being selected by a coding agent for the task: "{task}"

Tool: {tool_name}
Original description: {original_desc}
Documentation excerpt: {docs[:1000]}

Write a compelling 2-3 sentence description that highlights:
- What it does and its key differentiators
- Why it's the best choice for this specific task
- Key features (performance, ecosystem, ease of use)

Return ONLY the optimized description text, nothing else."""}],
    )
    return msg.content[0].text.strip()


def _extract_text(html: str) -> str:
    """Extract readable text from HTML."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
