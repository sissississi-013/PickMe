# Discovery Benchmark: Research & Technical Documentation

## The Core Question

How do we benchmark whether an AI agent can discover, select, and use a tool?

This isn't SEO. This is a fundamentally new surface: **tool discovery in agent ecosystems**.

---

## How AI Agents Actually Discover Tools

### The Mechanism: Claude's Tool Search (BM25)

Source: [Claude Tool Search API Docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)

When Claude has too many tools (>10K tokens of definitions), it uses **tool search** instead of loading everything:

1. Tools are marked with `defer_loading: true` — NOT loaded into context
2. Claude gets a `tool_search_tool_bm25` tool instead
3. When Claude needs a tool, it searches using **natural language queries**
4. BM25 ranks tools by matching against: **tool names, descriptions, argument names, argument descriptions**
5. Returns 3-5 most relevant tools
6. Claude selects from those and invokes

**Key numbers:**
- At 30+ tools: selection accuracy degrades significantly
- At 100+ tools: basically random without tool search
- With BM25 tool search: Opus 4.5 went from 79.5% → 88.1% accuracy
- 85% reduction in token usage

### What Makes a Tool Discoverable

Source: [Getting Found by Agents: A Builder's Guide (2026)](https://blog.icme.io/getting-found-by-agents-a-builders-guide-to-tool-discovery-in-2026/)

1. **Naming**: `{service}_{action}_{resource}` pattern. Task-oriented, not REST mirrors.
   - Good: `github_create_issue`, `slack_send_message`
   - Bad: `create`, `post_data`, `GET /issues`

2. **Description**: Under 100 chars (registry hard limit). Must state:
   - Clear purpose
   - When to invoke ("Use when...")
   - What it returns
   - Discoverable keywords matching user intent

3. **Parameters**: Flat (no nesting), with enums, defaults, and descriptions

4. **Tool count**: 5-15 optimal. GitHub reduced from 40 → 13 tools and benchmarks went UP.

5. **Registry presence**: Be on all discovery surfaces — MCP Registry, Smithery, Glama, npm, awesome-mcp-servers

### The Research Papers

| Paper | Key Finding |
|-------|-------------|
| [arXiv 2602.14878](https://arxiv.org/html/2602.14878) - MCP Tool Descriptions Are Smelly | 97% of tool descriptions have quality issues. 56% fail to state purpose. |
| [MCP-Atlas](https://arxiv.org/html/2602.00933v1) | 36 real MCP servers, 220 tools, 1000 tasks. 5-10 distractors per task. |
| [MCP-Radar](https://arxiv.org/html/2505.16700v1) | 5-dimensional evaluation: accuracy, tool selection, compute efficiency, parameter accuracy, speed |
| [MCPAgentBench](https://arxiv.org/abs/2512.24565) | Real-world MCP benchmark with dynamic sandbox + distractor tool lists |
| [MCP-Bench](https://arxiv.org/pdf/2508.20453) | 28 MCP servers, 250 tools, 11 functional domains |

### Discovery Channels (Where Agents Find Tools)

Source: [Builder's Guide to Tool Discovery](https://blog.icme.io/getting-found-by-agents-a-builders-guide-to-tool-discovery-in-2026/)

1. **MCP Registries** — Official MCP Registry (via `mcp-publisher` CLI), Smithery (natural language search), Glama (largest indexed collection)
2. **Package managers** — npm for installation
3. **Skill directories** — ClawHub and curated capability sets
4. **Commerce layers** — x402 directories for pay-per-request
5. **Documentation** — Agents read `/llms.txt` and plaintext docs directly
6. **awesome-mcp-servers** — GitHub repo, heavily referenced

"You do not know which path the agent will take to find you. Be on all of them."

---

## Our Benchmark Approach

### Three Levels of Discoverability

| Level | Question | How We Test |
|-------|----------|-------------|
| **Discovery** | Can the agent FIND your tool? | Tool search with N distractors — did BM25 surface it? |
| **Selection** | Does the agent CHOOSE your tool? | Given search results, did it pick yours over alternatives? |
| **Invocation** | Can the agent USE your tool correctly? | Did it construct valid parameters? |

### Implementation: `POST /api/benchmark/discovery`

**Request:**
```json
{
  "tool": {
    "name": "your_tool_name",
    "description": "Your tool description",
    "inputSchema": { ... }
  },
  "task_prompt": "What the agent needs to accomplish",
  "num_distractors": 15
}
```

**What happens:**
1. Claude generates N distractor tools in the same category (realistic competitors)
2. All tools (target + distractors) are sent with `defer_loading: true`
3. `tool_search_tool_bm25_20251119` is the only non-deferred tool
4. Claude receives the task prompt and must discover, select, and invoke
5. We measure: discovered (bool), selected (bool), invoked_correctly (bool), discovery_rank
6. Claude auto-optimizes the tool description
7. Entire benchmark re-runs with optimized version
8. Before/after delta reported

**Response:**
```json
{
  "before": {
    "target_tool_name": "create",
    "discovered": false,
    "selected": false,
    "invoked_correctly": false,
    "discovery_rank": null,
    "competing_tools": ["jira_create_ticket", "linear_add_issue", ...]
  },
  "after": {
    "target_tool_name": "github_create_issue",
    "discovered": true,
    "selected": true,
    "invoked_correctly": true,
    "discovery_rank": 1,
    "competing_tools": ["github_create_issue", "jira_create_ticket", ...]
  },
  "optimized_description": "Create a new issue in a GitHub repository. Use when tracking bugs or feature requests. Returns issue URL.",
  "discovery_improvement": "Now discoverable (was hidden) | Now selected by agent | Now invoked correctly"
}
```

### Why This Is Different From Existing Tools

| Tool | What it does | Our advantage |
|------|-------------|---------------|
| MCP-Atlas benchmark | Academic evaluation of tool use | We benchmark YOUR specific tool in YOUR category |
| Known Agents | Bot traffic analytics | We measure agent selection, not just visits |
| Rate My OpenAPI | Scores API spec quality | We prove quality improvements with live agent proof |
| SEO tools | Search ranking | We measure agent tool discovery, not web search |

---

## Key Statistics for Pitch/Demo

- **51% of web traffic** is now AI bots (Cloudflare 2026)
- **69% of AI bot traffic** is OpenAI (GPTBot + ChatGPT-User)
- **97% of MCP tool descriptions** have quality issues (arXiv 2602.14878)
- **49% → 88%** tool selection accuracy with proper descriptions (Anthropic tool search)
- **+41% visibility** from adding quotations (GEO paper)
- **+33% visibility** from adding statistics (GEO paper)
- Agent accuracy **collapses past 30 tools** when descriptions overlap
- GitHub **reduced from 40 → 13 tools** and benchmarks improved
- Tool search reduces token usage by **85%** while maintaining accuracy
- **4,700% surge** in AI-driven traffic to US retail (Visa)

---

## APIs Used

### Anthropic API (Claude)
- **Model**: `claude-sonnet-4-6` for optimizer, benchmarks
- **Tool Search**: `tool_search_tool_bm25_20251119` for discovery benchmark
- **Features used**: `defer_loading: true`, tool use, tool search
- **Env var**: `ANTHROPIC_API_KEY`

### OpenAI API (GPT — optional)
- **Model**: `gpt-4o-mini` for cross-model benchmark comparison
- **Env var**: `OPENAI_API_KEY`
- Falls back gracefully if not configured

---

## File Reference

| File | Purpose |
|------|---------|
| `pickme/backend/discovery_benchmark.py` | Real discovery benchmark using tool_search_tool_bm25 |
| `pickme/backend/benchmark.py` | Legacy benchmark (pick rate + simple tool proof) |
| `pickme/backend/discovery.py` | URL discovery — robots.txt, llms.txt, bot access |
| `pickme/backend/optimizer.py` | LLM-powered fix generation |
| `pickme/backend/web_scout.py` | Website readiness scoring |
| `pickme/backend/api_scout.py` | API/OpenAPI readiness scoring |
| `pickme/backend/mcp_scout.py` | MCP tool description scoring |
| `pickme/frontend/src/components/simulation-tab.tsx` | Discovery benchmark UI |
| `pickme/frontend/src/components/discovery-tab.tsx` | Bot access grid + visibility |
| `pickme/frontend/src/components/metrics-tab.tsx` | Score breakdown |
