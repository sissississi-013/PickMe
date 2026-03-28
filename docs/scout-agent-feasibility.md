# Pick Me — Scout Agent Technical Feasibility

## Surface 1: Website/Content Crawling

### How to crawl and extract structured data
- **Python `extruct`** library — extracts JSON-LD, Microdata, RDFa, OpenGraph from HTML in one call
- **Crawl4AI** — async crawler producing LLM-ready markdown with pluggable extraction strategies
- **Direct JSON-LD extraction**: `document.querySelectorAll('script[type="application/ld+json"]')` → parse JSON
- **llms.txt detection**: Simple HTTP GET to `{domain}/llms.txt`
- **robots.txt analysis**: HTTP GET to `{domain}/robots.txt`, parse for AI bot directives (GPTBot, ClaudeBot, etc.)

### What the Scout checks for a website
1. Schema.org JSON-LD presence and quality (Product, FAQPage, Article, WebAPI, etc.)
2. llms.txt existence and completeness
3. robots.txt AI bot configuration
4. Content freshness signals (Last-Modified headers, visible dates)
5. HTML structure (tables vs images for data, heading hierarchy)
6. Cross-page consistency (pricing, entity naming)
7. Meta tags quality (og:, description, canonical)
8. JavaScript rendering dependency (can agents see content without JS?)

### Tech: Python with extruct + httpx/aiohttp for async crawling. ~50 lines of core extraction logic.

---

## Surface 2: API/OpenAPI Spec Crawling

### How to discover OpenAPI specs
Common paths to probe:
- `/openapi.json`
- `/swagger.json`
- `/docs` (FastAPI default)
- `/redoc` (ReDoc default)
- `/api-docs`
- `/v1/openapi.json`, `/v2/openapi.json`
- `/.well-known/openapi`

### How to score an OpenAPI spec
Use **Rate My OpenAPI's approach** (Spectral-based linting):
- **Documentation score**: Are endpoints, parameters, schemas described?
- **Completeness score**: All paths documented? Request/response schemas present?
- **SDK generation readiness**: Proper operationIds, typed schemas?
- **Security score**: Auth schemes defined?
- **NEW: Agent-readiness score**:
  - Are descriptions problem-first or endpoint-first?
  - Do examples use realistic data (not "test123")?
  - Are error messages agent-helpful ("Try searching by email" vs. 500)?
  - Is the spec self-contained or requires reading 3 pages?

### Tech: Parse OpenAPI JSON/YAML → run Spectral rules + custom agent-readiness rules. Libraries exist (Rate My OpenAPI is open source).

---

## Surface 3: MCP Server Tool Inspection

### How to enumerate MCP tools programmatically
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def inspect_mcp_server(server_command, server_args):
    async with stdio_client(StdioServerParameters(
        command=server_command, args=server_args
    )) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"Name: {tool.name}")
                print(f"Description: {tool.description}")
                print(f"Schema: {tool.inputSchema}")
```

### For remote MCP servers (HTTP/SSE transport)
```python
from mcp.client.sse import sse_client

async def inspect_remote_mcp(url):
    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            return tools
```

### What the Scout checks for MCP tools
1. **Naming quality**: Does it follow `{service}_{action}_{resource}`? Or generic `create`, `get`?
2. **Description quality**: Does it specify when to invoke, argument formatting, expected returns?
3. **Parameter design**: Flat with explicit types and Literal constraints? Or nested dicts?
4. **Tool count**: 5-15 ideal. >15 = context pollution risk
5. **Error handling**: Do errors return helpful strings or raise exceptions?
6. **Discoverability keywords**: Would BM25 search find this tool for common queries?

### MCP Server Cards (coming June 2026)
- `.well-known/mcp/server-card.json` — structured metadata before connection
- We can already start scoring servers that implement this early

### Tech: MCP Python SDK (`pip install mcp`). Connect, list_tools(), score each tool. ~30 lines of core logic.

---

## Surface 4: Coding Agent Recommendation Measurement

### How to measure what AI agents recommend
This is the most novel surface. Approach:

1. **Prompt-based benchmarking**: Send standardized prompts to multiple LLMs:
   - "What Python web framework should I use for a new API project?"
   - "Write me a web server that handles user authentication"
   - "Set up a database connection for a new project"

2. **Parse responses**: Extract mentioned frameworks/libraries from both:
   - Recommendation text (conversation mode)
   - Generated code (code generation mode)

3. **Calculate "Pick Rate"**: How often is your tool picked vs. competitors?
   - Recommendation Pick Rate = mentions / total_prompts
   - Code Generation Pick Rate = code_imports / total_prompts
   - The GAP between these two (per arXiv 2503.17181) is the key metric

4. **Track over time**: Run benchmarks periodically, show trends

### Tech: LLM API calls (Claude, GPT, Gemini) + response parsing. Can be done with structured output / function calling for reliable extraction.

---

## Overall Architecture: Scout Agent

```
Scout Agent
├── WebScout
│   ├── Crawl URL (httpx + extruct)
│   ├── Extract JSON-LD, meta tags, structure
│   ├── Check llms.txt, robots.txt
│   └── Score agent-readiness (0-100)
├── APIScout
│   ├── Probe common OpenAPI paths
│   ├── Parse + lint OpenAPI spec (Spectral rules)
│   ├── Score documentation, completeness, agent-readiness
│   └── Check API docs structure (problem-first vs endpoint-first)
├── MCPScout
│   ├── Connect to MCP server (stdio or SSE)
│   ├── List tools, analyze names/descriptions/schemas
│   ├── Score naming, description quality, parameter design
│   └── Check Server Card if available
└── RecommendationScout
    ├── Send benchmark prompts to LLMs
    ├── Parse recommendation vs. code generation responses
    ├── Calculate Pick Rate and recommendation gap
    └── Compare against competitors
```

## Feasibility Assessment

| Surface | Difficulty | Time to MVP | Real Data? |
|---------|-----------|-------------|-----------|
| WebScout | Easy | 2-3 hours | Yes — live crawl any URL |
| APIScout | Medium | 2-3 hours | Yes — probe real API docs |
| MCPScout | Medium | 1-2 hours | Yes — connect to real MCP servers |
| RecommendationScout | Hard | 3-4 hours | Yes — real LLM API calls |
| **Combined MVP** | **Medium** | **4-6 hours** | **All real data** |

## Key Libraries
- `extruct` — structured data extraction from HTML
- `httpx` — async HTTP client
- `mcp` — MCP Python SDK (client)
- `spectral` — OpenAPI linting (or custom rules)
- `anthropic` / `openai` — LLM API calls for recommendation benchmarking
- `fastapi` — backend API for the scanner
- Next.js + shadcn — frontend dashboard
