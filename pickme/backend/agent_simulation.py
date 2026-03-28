"""
Real agentic simulation with visible tool use.

The agent gets tools (web_search, read_docs, evaluate) and we watch it
work through the problem step by step — like a real Claude Code session.
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
    actor: str  # "system" | "agent_a" | "agent_b" | "tool"
    type: str   # "thinking" | "tool_call" | "tool_result" | "decision" | "info"
    content: str
    data: str | None = None


class AgentDecision(BaseModel):
    agent_label: str
    picked_tool: str
    reasoning: str
    tools_evaluated: list[str]
    confidence: str
    session_log: list[LogEntry] = []


class SimulationResult(BaseModel):
    task: str
    target_tool: str
    before: AgentDecision
    after: AgentDecision
    optimization_effective: bool
    summary: str
    optimized_description: str = ""
    activity_log: list[LogEntry] = []


# Tools the agent can use
AGENT_TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for information about tools, frameworks, and services. Use this to find and compare options.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_documentation",
        "description": "Read the documentation or README for a specific tool or framework. Returns the content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "Name of the tool/framework"},
                "url": {"type": "string", "description": "Optional URL to fetch docs from"},
            },
            "required": ["tool_name"],
        },
    },
    {
        "name": "make_recommendation",
        "description": "Make your final tool recommendation after evaluating all options. Call this when you've done enough research.",
        "input_schema": {
            "type": "object",
            "properties": {
                "picked_tool": {"type": "string", "description": "Name of recommended tool"},
                "reasoning": {"type": "string", "description": "2-3 sentences explaining your choice"},
                "tools_evaluated": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "All tools you considered",
                },
                "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            },
            "required": ["picked_tool", "reasoning", "tools_evaluated", "confidence"],
        },
    },
]


async def run_agent_simulation(
    target_tool: str,
    target_url: str | None,
    target_description: str | None,
    optimized_description: str | None,
    task: str | None,
    competitors: list[str] | None = None,
) -> SimulationResult:
    return await _run_simulation_impl(
        target_tool, target_url, target_description, optimized_description,
        task, competitors, None,
    )


async def _run_simulation_impl(
    target_tool: str,
    target_url: str | None,
    target_description: str | None,
    optimized_description: str | None,
    task: str | None,
    competitors: list[str] | None,
    q: asyncio.Queue | None,
) -> SimulationResult:
    logs: list[LogEntry] = []
    _log(logs, "system", "info", f"Starting simulation for '{target_tool}'", queue=q)

    # Auto-generate missing fields from just the tool name
    if not target_description or not task:
        _log(logs, "system", "info", f"Auto-generating context for '{target_tool}'...", queue=q)
        auto = await _auto_fill(target_tool)
        if not target_description:
            target_description = auto.get("description", f"A tool called {target_tool}")
            _log(logs, "system", "info", f"Generated description: {target_description}", queue=q)
        if not task:
            task = auto.get("task", f"Build something using {target_tool}")
            _log(logs, "system", "info", f"Generated task: {task}", queue=q)

    _log(logs, "system", "info", f"Task: {task}", queue=q)

    # Optimize description if not provided
    if not optimized_description:
        _log(logs, "system", "info", "Generating optimized description...", queue=q)
        optimized_description = await _optimize_description(target_tool, target_description, task)
        _log(logs, "system", "info", "Optimized description ready", optimized_description, q)

    # Run both agents in parallel
    _log(logs, "system", "info", "Launching Agent A (original) and Agent B (optimized) in parallel...", queue=q)

    agent_a, agent_b = await asyncio.gather(
        _run_agentic_session(
            task=task,
            target_tool=target_tool,
            target_description=target_description,
            target_url=target_url,
            label="agent_a",
            log_queue=q,
        ),
        _run_agentic_session(
            task=task,
            target_tool=target_tool,
            target_description=optimized_description,
            target_url=target_url,
            label="agent_b",
            log_queue=q,
        ),
    )

    # Merge session logs into activity log
    all_session_logs = []
    for entry in agent_a.session_log:
        all_session_logs.append(entry)
    for entry in agent_b.session_log:
        all_session_logs.append(entry)
    all_session_logs.sort(key=lambda e: e.timestamp)
    logs.extend(all_session_logs)

    _log(logs, "agent_a", "decision", f"Agent A picked: {agent_a.picked_tool}", queue=q)
    _log(logs, "agent_b", "decision", f"Agent B picked: {agent_b.picked_tool}", queue=q)

    # Compare
    target_lower = target_tool.lower()
    before_picked = target_lower in agent_a.picked_tool.lower()
    after_picked = target_lower in agent_b.picked_tool.lower()
    effective = after_picked and not before_picked

    if effective:
        summary = f"Optimization worked: {target_tool} was NOT picked before but WAS picked after optimization."
    elif before_picked and after_picked:
        summary = f"{target_tool} was picked in both cases. Optimization reinforced existing selection."
    elif not before_picked and not after_picked:
        summary = f"{target_tool} was not picked in either case. Deeper improvements needed."
    else:
        summary = f"Unexpected: {target_tool} was picked before but not after."

    _log(logs, "system", "info", summary, queue=q)

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


async def _run_agentic_session(
    task: str,
    target_tool: str,
    target_description: str,
    target_url: str | None,
    label: str,
    log_queue: asyncio.Queue | None = None,
) -> AgentDecision:
    """Run a multi-turn agentic session where the agent uses tools to research and decide."""
    session_log: list[LogEntry] = []
    q = log_queue
    agent_name = "Agent A (original)" if label == "agent_a" else "Agent B (optimized)"

    system = f"""You are a developer agent evaluating tools for a project. You have access to web search and documentation reading tools.

Your process:
1. First, search for relevant tools and frameworks for the task
2. Read documentation for the most promising options (at least 2-3)
3. Compare them based on: features, performance, ecosystem, documentation quality, ease of use
4. Make your final recommendation using the make_recommendation tool

The user has suggested considering "{target_tool}": {target_description}

Be thorough — search, read docs, then decide. Always use make_recommendation at the end."""

    messages = [{"role": "user", "content": f"I need to {task}. Research the best tools/frameworks for this and make a recommendation. Start by searching for options."}]

    _lq(session_log, q, label, "thinking", f"{agent_name} starting session...",
         f"System: {system[:150]}...")

    max_turns = 8
    decision = None

    for turn in range(max_turns):
        msg = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=system,
            messages=messages,
            tools=AGENT_TOOLS,
        )

        # Process response blocks
        assistant_content = []
        for block in msg.content:
            if hasattr(block, "text") and block.text:
                _lq(session_log, q, label, "thinking", block.text)
                assistant_content.append({"type": "text", "text": block.text})

            elif block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": tool_name,
                    "input": tool_input,
                })

                if tool_name == "make_recommendation":
                    _lq(session_log, q, label, "decision",
                         f"Recommendation: {tool_input.get('picked_tool', '?')}",
                         json.dumps(tool_input, indent=2))
                    decision = AgentDecision(
                        agent_label=label,
                        picked_tool=tool_input.get("picked_tool", "unknown"),
                        reasoning=tool_input.get("reasoning", ""),
                        tools_evaluated=tool_input.get("tools_evaluated", []),
                        confidence=tool_input.get("confidence", "medium"),
                        session_log=session_log,
                    )
                    return decision

                elif tool_name == "web_search":
                    query = tool_input.get("query", "")
                    _lq(session_log, q, label, "tool_call", f"web_search(\"{query}\")")
                    result = await _handle_web_search(query)
                    _lq(session_log, q, label, "tool_result", f"Search returned {len(result)} chars",
                         result[:300] + "..." if len(result) > 300 else result)

                    messages.append({"role": "assistant", "content": assistant_content})
                    messages.append({"role": "user", "content": [
                        {"type": "tool_result", "tool_use_id": block.id, "content": result}
                    ]})
                    assistant_content = []

                elif tool_name == "read_documentation":
                    t_name = tool_input.get("tool_name", "")
                    t_url = tool_input.get("url")
                    _lq(session_log, q, label, "tool_call",
                         f"read_documentation(\"{t_name}\"" + (f", url=\"{t_url}\")" if t_url else ")"))
                    result = await _fetch_docs(t_name, t_url)
                    _lq(session_log, q, label, "tool_result",
                         f"Docs for {t_name}: {len(result)} chars",
                         result[:300] + "..." if len(result) > 300 else result)

                    messages.append({"role": "assistant", "content": assistant_content})
                    messages.append({"role": "user", "content": [
                        {"type": "tool_result", "tool_use_id": block.id, "content": result}
                    ]})
                    assistant_content = []

        if msg.stop_reason == "end_turn":
            # Agent finished without making a recommendation — extract from text
            if assistant_content:
                messages.append({"role": "assistant", "content": assistant_content})
            break

    # If no explicit decision was made, parse the last text response
    if decision is None:
        _lq(session_log, q, label, "thinking", "Session ended without explicit recommendation, inferring from conversation...")
        decision = AgentDecision(
            agent_label=label,
            picked_tool="undecided",
            reasoning="Agent did not make an explicit recommendation within the turn limit.",
            tools_evaluated=[],
            confidence="low",
            session_log=session_log,
        )

    return decision


async def _handle_web_search(query: str) -> str:
    """Simulate web search by fetching real results."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=10) as http:
        # Search PyPI
        results = []
        try:
            resp = await http.get(f"https://pypi.org/search/?q={query}", headers={"Accept": "text/html"})
            if resp.status_code == 200:
                # Extract package names from search results
                names = re.findall(r'class="package-snippet__name">([^<]+)</span>', resp.text)
                descs = re.findall(r'class="package-snippet__description">([^<]+)</p>', resp.text)
                for name, desc in zip(names[:5], descs[:5]):
                    results.append(f"- {name.strip()}: {desc.strip()}")
        except Exception:
            pass

        # Search npm
        try:
            resp = await http.get(f"https://registry.npmjs.org/-/v1/search?text={query}&size=5")
            if resp.status_code == 200:
                data = resp.json()
                for obj in data.get("objects", [])[:5]:
                    pkg = obj.get("package", {})
                    results.append(f"- {pkg.get('name', '?')}: {pkg.get('description', 'No description')}")
        except Exception:
            pass

        # Search GitHub
        try:
            resp = await http.get(
                f"https://api.github.com/search/repositories?q={query}&sort=stars&per_page=5",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            if resp.status_code == 200:
                data = resp.json()
                for repo in data.get("items", [])[:5]:
                    stars = repo.get("stargazers_count", 0)
                    results.append(f"- {repo.get('full_name', '?')} ({stars} stars): {repo.get('description', '')}")
        except Exception:
            pass

    if results:
        return f"Search results for '{query}':\n" + "\n".join(results)
    return f"No results found for '{query}'. Try a different search query or evaluate based on your knowledge."


async def _fetch_docs(tool_name: str, url: str | None) -> str:
    """Fetch real documentation."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=10) as http:
        if url:
            try:
                resp = await http.get(url)
                if resp.status_code == 200:
                    text = _extract_text(resp.text)
                    if len(text) > 100:
                        return text[:3000]
            except Exception:
                pass

        slug = tool_name.lower().replace(" ", "-")

        # GitHub README
        for owner in [slug, f"tiangolo/{slug}", f"pallets/{slug}", f"django/{slug}", f"expressjs/{slug}"]:
            for branch in ["main", "master"]:
                try:
                    resp = await http.get(f"https://raw.githubusercontent.com/{owner}/{branch}/README.md")
                    if resp.status_code == 200:
                        return resp.text[:3000]
                except Exception:
                    continue

        # PyPI
        try:
            resp = await http.get(f"https://pypi.org/pypi/{slug}/json")
            if resp.status_code == 200:
                data = resp.json()
                info = data.get("info", {})
                summary = info.get("summary", "")
                desc = info.get("description", "")
                return f"{tool_name}: {summary}\n\n{desc[:2500]}"
        except Exception:
            pass

        # npm
        try:
            resp = await http.get(f"https://registry.npmjs.org/{slug}")
            if resp.status_code == 200:
                data = resp.json()
                readme = data.get("readme", "")
                if readme:
                    return readme[:3000]
        except Exception:
            pass

    return f"Documentation for {tool_name}: Evaluate based on general knowledge. {tool_name} is a popular tool in its category."


async def _auto_fill(tool_name: str) -> dict:
    """Auto-generate description, task, and competitors from just a tool name."""
    msg = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": f"""For the tool/framework/service called "{tool_name}", generate:
1. A deliberately MEDIOCRE one-sentence description (generic, undersells the tool — like what a lazy developer would write)
2. A realistic task that a developer would use this tool for
3. 4 real competing alternatives

Return JSON only:
{{"description": "...", "task": "...", "competitors": ["...", "...", "...", "..."]}}
No markdown fencing."""}],
    )
    try:
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(raw)
    except Exception:
        return {"description": f"A tool called {tool_name}", "task": f"Build a project using {tool_name}"}


async def _optimize_description(tool_name: str, original_desc: str, task: str) -> str:
    msg = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": f"""Rewrite this tool description to maximize its chances of being selected by a coding agent for: "{task}"

Tool: {tool_name}
Original: {original_desc}

Write 2-3 compelling sentences highlighting key differentiators, performance, and ecosystem.
Return ONLY the description text."""}],
    )
    return msg.content[0].text.strip()


def _extract_text(html: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _lq(logs: list[LogEntry], queue: asyncio.Queue | None, actor: str, type: str, content: str, data: str | None = None):
    """Log with queue — convenience wrapper."""
    _log(logs, actor, type, content, data, queue)


def _log(logs: list[LogEntry], actor: str, type: str, content: str, data: str | None = None, queue: asyncio.Queue | None = None):
    entry = LogEntry(timestamp=time.time(), actor=actor, type=type, content=content, data=data)
    logs.append(entry)
    if queue:
        queue.put_nowait(entry)


async def run_agent_simulation_streaming(
    target_tool: str,
    target_url: str | None,
    target_description: str | None,
    optimized_description: str | None,
    task: str | None,
    competitors: list[str] | None = None,
    log_queue: asyncio.Queue | None = None,
) -> SimulationResult:
    """Same as run_agent_simulation but pushes logs to a queue for SSE streaming."""
    return await _run_simulation_impl(
        target_tool, target_url, target_description, optimized_description,
        task, competitors, log_queue,
    )
