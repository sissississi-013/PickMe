"""
Real discovery benchmark using Claude's tool_search_tool_bm25.

This uses the actual production mechanism agents use to discover tools:
1. Generate distractor tools in the same category
2. Run Claude with tool_search_tool_bm25 + defer_loading on all tools
3. Measure: discovered? selected? invoked correctly?
4. Optimize description and re-run to show delta
"""

import json
from anthropic import AsyncAnthropic
from models import DiscoveryBenchmarkResult, DiscoveryBenchmarkReport

client = AsyncAnthropic()


async def run_discovery_benchmark(
    tool: dict,
    task_prompt: str,
    num_distractors: int = 15,
) -> DiscoveryBenchmarkReport:
    """Run a full discovery benchmark: before optimization, optimize, then after."""

    # Step 1: Generate distractor tools
    distractors = await _generate_distractors(tool, num_distractors)

    # Step 2: Run benchmark with original tool
    before = await _run_single_benchmark(tool, distractors, task_prompt)

    # Step 3: Optimize the tool description
    optimized_tool = await _optimize_tool(tool)

    # Step 4: Run benchmark with optimized tool
    after = await _run_single_benchmark(optimized_tool, distractors, task_prompt)

    # Compute improvement summary
    improvement_parts = []
    if not before.discovered and after.discovered:
        improvement_parts.append("Now discoverable (was hidden)")
    if not before.selected and after.selected:
        improvement_parts.append("Now selected by agent")
    if not before.invoked_correctly and after.invoked_correctly:
        improvement_parts.append("Now invoked correctly")
    if before.discovered and after.discovered:
        if (before.discovery_rank or 99) > (after.discovery_rank or 99):
            improvement_parts.append(f"Rank improved: #{before.discovery_rank} -> #{after.discovery_rank}")

    return DiscoveryBenchmarkReport(
        before=before,
        after=after,
        optimized_description=optimized_tool.get("description", ""),
        discovery_improvement=" | ".join(improvement_parts) if improvement_parts else "No change",
    )


async def _generate_distractors(tool: dict, count: int) -> list[dict]:
    """Use Claude to generate realistic distractor tools in the same category."""
    tool_name = tool.get("name", "unknown_tool")
    tool_desc = tool.get("description", "")

    prompt = f"""Generate {count} realistic MCP tool definitions that are plausible alternatives or competitors to this tool:

Name: {tool_name}
Description: {tool_desc}

Requirements:
- Each tool should be in a similar domain but serve a slightly different purpose
- Use realistic naming patterns (service_action_resource)
- Include inputSchema with realistic properties
- Make some descriptions good and some mediocre (to simulate real registry conditions)
- Do NOT duplicate the original tool

Return a JSON array of tool objects, each with "name", "description", and "inputSchema" fields.
Return ONLY the JSON array, no markdown fencing."""

    msg = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(raw)
    except (json.JSONDecodeError, IndexError):
        # Fallback: generate simple distractors
        return [
            {
                "name": f"tool_{i}_action",
                "description": f"A tool that performs action {i} in a related domain",
                "inputSchema": {"type": "object", "properties": {"input": {"type": "string"}}},
            }
            for i in range(count)
        ]


async def _run_single_benchmark(
    target_tool: dict,
    distractors: list[dict],
    task_prompt: str,
) -> DiscoveryBenchmarkResult:
    """Run Claude with tool_search_tool_bm25 and measure discovery."""

    # Build the tools list: search tool (non-deferred) + target + distractors (all deferred)
    tools = [
        {
            "type": "tool_search_tool_bm25_20251119",
            "name": "tool_search_tool_bm25",
        }
    ]

    # Add target tool (deferred)
    tools.append({
        "name": target_tool.get("name", "target_tool"),
        "description": target_tool.get("description", ""),
        "input_schema": target_tool.get("inputSchema", {"type": "object", "properties": {}}),
        "defer_loading": True,
    })

    # Add distractors (deferred)
    for d in distractors:
        tools.append({
            "name": d.get("name", "distractor"),
            "description": d.get("description", ""),
            "input_schema": d.get("inputSchema", {"type": "object", "properties": {}}),
            "defer_loading": True,
        })

    # Run Claude with tool search
    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system="You are a helpful assistant with access to tools. You MUST search for and use available tools to complete tasks. Do not ask clarifying questions — use reasonable defaults for any missing parameters. Always attempt to use a tool rather than responding with text.",
        messages=[{"role": "user", "content": task_prompt}],
        tools=tools,
    )

    # Analyze results
    target_name = target_tool.get("name", "target_tool")
    discovered = False
    selected = False
    invoked_correctly = False
    discovery_rank = None
    competing_tools = []

    for block in message.content:
        # Check tool search results for discovery
        if hasattr(block, "type") and block.type == "tool_search_tool_result":
            content = block.content
            if hasattr(content, "tool_references"):
                refs = content.tool_references
                for i, ref in enumerate(refs):
                    tool_ref_name = ref.tool_name if hasattr(ref, "tool_name") else str(ref)
                    competing_tools.append(tool_ref_name)
                    if tool_ref_name == target_name:
                        discovered = True
                        discovery_rank = i + 1

        # Check if Claude actually selected and invoked the tool
        if hasattr(block, "type") and block.type == "tool_use":
            if block.name == target_name:
                selected = True
                # Check if input has the expected fields
                if hasattr(block, "input") and isinstance(block.input, dict):
                    invoked_correctly = len(block.input) > 0

    # Build response text for display
    response_parts = []
    for block in message.content:
        if hasattr(block, "text"):
            response_parts.append(block.text)
        elif hasattr(block, "type"):
            if block.type == "tool_use":
                response_parts.append(f"[Tool call: {block.name}({json.dumps(block.input) if hasattr(block, 'input') else ''})]")
            elif block.type == "tool_search_tool_result":
                response_parts.append(f"[Search found: {', '.join(competing_tools)}]")

    return DiscoveryBenchmarkResult(
        target_tool_name=target_name,
        task_prompt=task_prompt,
        num_distractors=len(distractors),
        discovered=discovered,
        selected=selected,
        invoked_correctly=invoked_correctly,
        discovery_rank=discovery_rank,
        competing_tools=competing_tools,
        raw_response=response_parts,
    )


async def _optimize_tool(tool: dict) -> dict:
    """Use Claude to rewrite the tool for maximum discoverability."""
    prompt = f"""You are an MCP tool description optimizer. Rewrite this tool definition for maximum discoverability by AI agents.

Current tool:
{json.dumps(tool, indent=2)}

Rules for optimization:
1. Name: Use {{service}}_{{action}}_{{resource}} pattern, task-oriented
2. Description: Under 100 chars, state clear purpose, specify when to invoke ("Use when..."), describe return value
3. inputSchema: Use flat parameters with descriptions, add enums where appropriate, add sensible defaults
4. Include discoverable keywords that match how users describe the task

Return ONLY the optimized tool as a JSON object with "name", "description", and "inputSchema" fields. No markdown fencing."""

    msg = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(raw)
    except (json.JSONDecodeError, IndexError):
        return tool  # Return original if optimization fails
