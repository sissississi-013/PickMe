<p align="center">
  <img src="pickme/frontend/public/logo.png" alt="PickMe" width="280" />
</p>

<p align="center">
  <strong>Make your brand get picked by AI agents</strong>
</p>

<p align="center">
  AI coding agents are making more technical decisions every day. They pick frameworks, choose APIs, and select tools while building features. PickMe helps you measure, optimize, and validate whether your tool gets discovered and selected by these agents.
</p>

---

## What is PickMe?

PickMe is a developer console that answers one question: **Is your tool discoverable by AI agents?**

Traditional analytics miss AI agent traffic entirely. PickMe scans your site, API, or MCP tool definition, scores its discoverability with research-backed metrics, and runs live agent simulations to prove whether optimization actually works.

## How it Works

### 1. Discovery Scan

Enter any URL. PickMe checks:

- **robots.txt** against 16 known AI bots (GPTBot, ClaudeBot, ChatGPT-User, PerplexityBot, and more)
- **llms.txt** presence and quality
- **sitemap.xml** availability
- **Structured data** (JSON-LD Schema.org markup)
- **Server-side rendering** (agents cannot execute JavaScript)
- **Content quality** (statistics, citations, freshness)

Each finding includes a consequence explaining exactly why it matters, citing real research.

### 2. Optimization

PickMe generates specific, actionable fixes powered by Claude:

- JSON-LD blocks to add
- robots.txt rules to update
- Tool description rewrites for MCP servers
- llms.txt file generation

Every recommendation cites the research paper proving its impact (GEO paper: +33% visibility from statistics, +30% from citations).

### 3. Agent Simulation

Two real AI agents run in parallel with identical tasks:

- **Agent A** sees your original tool/description
- **Agent B** sees the optimized version
- Both search the web, read documentation, and evaluate competitors
- You see the full session log in real time
- Side-by-side comparison shows which tool each agent picked and why

This uses Claude's actual production tool search mechanism, not a toy demo.

## Key Research

| Finding | Source |
|---------|--------|
| 51% of web traffic is AI bots | Cloudflare 2026 |
| 97% of MCP tool descriptions have quality issues | arXiv 2602.14878 |
| +33% visibility from adding statistics | GEO paper |
| +30% visibility from adding citations | GEO paper |
| Tool selection: 49% to 88% with proper descriptions | Anthropic tool search |
| Agent accuracy collapses past 30 tools | MCP-Atlas benchmark |
| GPTBot and ClaudeBot started requesting sitemaps March 2026 | Wislr server log analysis |

## Tech Stack

**Backend:** Python, FastAPI, httpx, extruct, Anthropic SDK, OpenAI SDK

**Frontend:** Next.js 16, TypeScript, Tailwind CSS, shadcn/ui, Recharts

**APIs:** Claude Sonnet 4.6 (tool search BM25, optimization, simulation), OpenAI GPT-4o-mini (cross-model benchmarking)

**Features:** SSE streaming for real-time simulation logs, dark/light mode, responsive design

## Project Structure

```
pickme/
  backend/
    main.py                 # FastAPI app with all endpoints
    discovery.py            # URL scanning and bot access analysis
    web_scout.py            # Website readiness scoring (13 checks)
    api_scout.py            # OpenAPI spec scoring
    mcp_scout.py            # MCP tool description scoring
    optimizer.py            # Claude-powered fix generation
    agent_simulation.py     # Multi-turn agent simulation with tool use
    discovery_benchmark.py  # Tool search benchmarking with BM25
    bot_db.py               # 16 known AI bot database
    traffic_classifier.py   # Server log parser
    models.py               # Pydantic models
  frontend/
    src/app/page.tsx        # Main dashboard with 3 tabs
    src/components/
      discovery-tab.tsx     # AI visibility score, bot grid, signals, agent view
      metrics-tab.tsx       # Detailed score breakdown
      simulation-tab.tsx    # Agent simulation with streaming log
      scan-input.tsx        # URL input
  data/
    sample_access.log       # Demo server log with real bot patterns
  tests/
    test_bot_db.py          # Bot matching tests
    test_traffic_classifier.py
    test_web_scout.py
    test_api_scout.py
    test_mcp_scout.py
    test_integration.py     # End-to-end tests
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/discover` | POST | Scan URL for AI agent discoverability |
| `/api/scout/web` | POST | Score website readiness |
| `/api/scout/api` | POST | Score API/OpenAPI spec |
| `/api/scout/mcp` | POST | Score MCP tool definitions |
| `/api/optimize` | POST | Generate optimization recommendations |
| `/api/simulate` | POST | Run agent simulation (two parallel agents) |
| `/api/simulate/stream` | POST | Same as above with SSE streaming |
| `/api/benchmark/discovery` | POST | Tool search benchmark with distractors |
| `/api/tool/generate` | POST | Generate MCP definition from description |
| `/api/traffic/classify` | POST | Classify server log traffic |

## Running Locally

**Backend:**

```bash
cd pickme/backend
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
uvicorn main:app --port 8000
```

**Frontend:**

```bash
cd pickme/frontend
npm install
npm run dev
```

Open `http://localhost:3001` (or whatever port Next.js assigns).

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Powers optimization, simulation, and benchmarks |
| `OPENAI_API_KEY` | Optional | Cross-model benchmarking with GPT |
| `NEXT_PUBLIC_API_URL` | Optional | Backend URL (defaults to `http://localhost:8000`) |

## License

MIT
