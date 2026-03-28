"""
Real agent simulation engine with activity logging.

Runs two parallel Claude agent sessions with identical tasks.
Every step is logged for full transparency.
"""

import asyncio
import json
import re
import time
import httpx
from anthropic import AsyncAnthropic
from pydantic import BaseModel

client = AsyncAnthropic()


class LogEntry(BaseModel):
    timestamp: float
    step: str
    detail: str
    data: str | None = None


class AgentDecision(BaseModel):
    agent_label: str
    picked_tool: str
    reasoning: str
    tools_evaluated: list[str]
    confidence: str
    raw_output: str
    system_prompt: str = ""
    user_prompt: str = ""


class SimulationResult(BaseModel):
    task: str
    target_tool: str
    before: AgentDecision
    after: AgentDecision
    optimization_effective: bool
    summary: str
    optimized_description: str = ""
    activity_log: list[LogEntry] = []


def _log(logs: list[LogEntry], step: str, detail: str, data: str | None = None):
    logs.append(LogEntry(timestamp=time.time(), step=step, detail=detail, data=data))


async def run_agent_simulation(
    target_tool: str,
    target_url: str | None,
    target_description: str,
    optimized_description: str | None,
    task: str,
    competitors: list[str] | None = None,
) -> SimulationResult:
    logs: list[LogEntry] = []
    _log(logs, "init", f"Starting simulation for '{target_tool}'", f"Task: {task}")

    # Step 1: Fetch docs
    _log(logs, "fetch_docs", f"Fetching documentation for {target_tool}...")
    target_docs = await _fetch_docs(target_tool, target_url, logs)
    _log(logs, "fetch_docs", f"Got {len(target_docs)} chars of docs for {target_tool}",
         target_docs[:200] + "..." if len(target_docs) > 200 else target_docs)

    # Step 2: Identify competitors
    if not competitors:
        _log(logs, "competitors", f"Identifying competitors for {target_tool}...")
        competitors = await _identify_competitors(target_tool, task)
    _log(logs, "competitors", f"Competitors identified: {', '.join(competitors)}")

    # Step 3: Fetch competitor docs
    _log(logs, "fetch_docs", f"Fetching docs for {len(competitors)} competitors...")
    competitor_docs = await asyncio.gather(
        *[_fetch_docs(comp, None, logs) for comp in competitors[:4]]
    )
    for comp, docs in zip(competitors[:4], competitor_docs):
        _log(logs, "fetch_docs", f"Got {len(docs)} chars for {comp}",
             docs[:150] + "..." if len(docs) > 150 else docs)

    competitor_context = "\n\n".join([
        f"## {comp}\n{docs}"
        for comp, docs in zip(competitors[:4], competitor_docs)
    ])

    # Step 4: Optimize
    if not optimized_description:
        _log(logs, "optimize", f"Generating optimized description for {target_tool}...")
        optimized_description = await _optimize_description(
            target_tool, target_description, target_docs, task
        )
    _log(logs, "optimize", "Optimized description ready", optimized_description)

    # Step 5: Build contexts
    before_context = f"## {target_tool}\n{target_description}\n\n{target_docs}"
    after_context = f"## {target_tool}\n{optimized_description}\n\n{target_docs}"

    # Step 6: Run agents
    _log(logs, "agent_a", "Launching Agent A (original description)...")
    _log(logs, "agent_b", "Launching Agent B (optimized description)...")

    agent_a, agent_b = await asyncio.gather(
        _run_agent(task, target_tool, before_context, competitor_context, "before", logs),
        _run_agent(task, target_tool, after_context, competitor_context, "after", logs),
    )

    _log(logs, "agent_a", f"Agent A picked: {agent_a.picked_tool} (confidence: {agent_a.confidence})")
    _log(logs, "agent_b", f"Agent B picked: {agent_b.picked_tool} (confidence: {agent_b.confidence})")

    # Step 7: Compare
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

    _log(logs, "result", summary)

    return SimulationResult(
        task=task,
        target_tool=target_tool,
        before=agent_a,
        after=agent_b,
        optimization_effective=effective,
        summary=summary,
        optimized_description=optimized_description,
        activity_log=logs,
    )


async def _run_agent(
    task: str,
    target_tool: str,
    target_context: str,
    competitor_context: str,
    label: str,
    logs: list[LogEntry],
) -> AgentDecision:
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

    tag = "agent_a" if label == "before" else "agent_b"
    _log(logs, tag, f"Sending prompt to Claude (sonnet-4-6)...",
         f"System: {system[:100]}...\nUser prompt length: {len(user_prompt)} chars")

    msg = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = msg.content[0].text.strip()
    _log(logs, tag, f"Response received ({len(raw)} chars)", raw[:300])

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
            system_prompt=system,
            user_prompt=user_prompt,
        )
    except (json.JSONDecodeError, KeyError):
        return AgentDecision(
            agent_label=label,
            picked_tool="parse_error",
            reasoning=raw[:500],
            tools_evaluated=[],
            confidence="low",
            raw_output=raw,
            system_prompt=system,
            user_prompt=user_prompt,
        )


async def _fetch_docs(tool_name: str, url: str | None, logs: list[LogEntry] | None = None) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=10) as http:
        if url:
            try:
                resp = await http.get(url)
                if resp.status_code == 200:
                    text = _extract_text(resp.text)
                    if len(text) > 100:
                        if logs:
                            _log(logs, "fetch_docs", f"Fetched {url} ({len(text)} chars)")
                        return text[:3000]
            except Exception:
                pass

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
                    if logs:
                        _log(logs, "fetch_docs", f"Fetched GitHub README: {gh_url}")
                    return resp.text[:3000]
            except Exception:
                continue

        try:
            resp = await http.get(f"https://pypi.org/pypi/{slug}/json")
            if resp.status_code == 200:
                data = resp.json()
                desc = data.get("info", {}).get("description", "")
                if desc:
                    if logs:
                        _log(logs, "fetch_docs", f"Fetched from PyPI: {slug}")
                    return desc[:3000]
        except Exception:
            pass

        try:
            resp = await http.get(f"https://registry.npmjs.org/{slug}")
            if resp.status_code == 200:
                data = resp.json()
                readme = data.get("readme", "")
                if readme:
                    if logs:
                        _log(logs, "fetch_docs", f"Fetched from npm: {slug}")
                    return readme[:3000]
        except Exception:
            pass

    return f"No documentation fetched for {tool_name}. Evaluate based on general knowledge."


async def _identify_competitors(tool_name: str, task: str) -> list[str]:
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


async def _optimize_description(tool_name: str, original_desc: str, docs: str, task: str) -> str:
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
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
