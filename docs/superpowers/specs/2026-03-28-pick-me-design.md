# Pick Me — Design Specification

## Product Overview

**Pick Me** is a developer console that helps API providers, MCP server developers, framework maintainers, and SaaS products understand how AI agents see them — and get picked more.

It answers three questions:
1. **"How much of my traffic is from AI agents?"** — Classify existing server/API logs into human vs. AI crawler vs. AI agent vs. shopping agent
2. **"How discoverable am I?"** — Research-backed scoring across web, API, and MCP surfaces
3. **"How do I get picked more?"** — Agentic optimization with before/after proof via live agent benchmarks

### Core Differentiator

Known Agents tells you WHAT bots are doing. Pick Me tells you **WHY agents aren't picking you, fixes it, and proves the fix works with a live agent comparison.**

### Target Users

- API providers (Stripe, Twilio, etc.) — understand agent traffic, optimize docs
- MCP server developers — improve tool discoverability, score descriptions
- Framework/library vendors — break the Matthew Effect, increase recommendation rate
- SaaS products — become discoverable by AI agents recommending solutions
- E-commerce merchants — get chosen by shopping agents

---

## Architecture

### System Overview

```
User provides: server logs / API gateway logs / MCP server URL / website URL
                                    ↓
                        ┌───────────────────────┐
                        │     Pick Me Engine     │
                        ├───────────────────────┤
                        │                       │
                        │  ┌─────────────────┐  │
                        │  │  Traffic        │  │
                        │  │  Classifier     │  │
                        │  │  (Layers 1-3)   │  │
                        │  └─────────────────┘  │
                        │                       │
                        │  ┌─────────────────┐  │
                        │  │  Scout Agents   │  │
                        │  │  (Web/API/MCP)  │  │
                        │  └─────────────────┘  │
                        │                       │
                        │  ┌─────────────────┐  │
                        │  │  Optimizer      │  │
                        │  │  Agent          │  │
                        │  └─────────────────┘  │
                        │                       │
                        │  ┌─────────────────┐  │
                        │  │  Benchmark      │  │
                        │  │  Engine         │  │
                        │  └─────────────────┘  │
                        │                       │
                        └───────────────────────┘
                                    ↓
                        ┌───────────────────────┐
                        │   Developer Console   │
                        │   (Next.js Dashboard) │
                        └───────────────────────┘
```

### Tech Stack

- **Backend:** Python (FastAPI)
- **Frontend:** Next.js + Tailwind + shadcn/ui
- **Log parsing:** Python (regex + IP matching)
- **Web crawling:** `extruct` (structured data extraction) + `httpx` (async HTTP)
- **MCP inspection:** `mcp` Python SDK (connect, list_tools, score)
- **OpenAPI analysis:** Custom rules inspired by Spectral/Rate My OpenAPI
- **LLM APIs:** `anthropic` + `openai` SDKs (for benchmark engine)
- **Agent orchestration:** LLM-powered agents for optimization recommendations

---

## Panel 1: Agent Traffic Classifier

### What It Does

Takes existing server/API logs and classifies every request: **human, AI crawler, AI agent, shopping agent, unknown.**

### How It Works — Three Detection Layers

**Layer 1: User-Agent String Matching**

Match against a database of known AI bot user-agents:

| Bot | User-Agent Pattern | Operator | Category |
|-----|-------------------|----------|----------|
| GPTBot | `GPTBot/1.1` | OpenAI | AI Crawler |
| ChatGPT-User | `ChatGPT-User/1.0` | OpenAI | AI Agent |
| OAI-SearchBot | `OAI-SearchBot/1.0` | OpenAI | AI Crawler |
| ClaudeBot | `ClaudeBot` | Anthropic | AI Crawler |
| Claude-SearchBot | `Claude-SearchBot` | Anthropic | AI Crawler |
| Claude-User | `Claude/1.0` | Anthropic | AI Agent |
| PerplexityBot | `PerplexityBot` | Perplexity | AI Crawler |
| Meta-WebIndexer | `Meta-WebIndexer` | Meta | AI Crawler |
| Applebot-Extended | `Applebot-Extended` | Apple | AI Crawler |
| Bytespider | `Bytespider` | ByteDance | AI Crawler |
| CCBot | `CCBot` | Common Crawl | AI Crawler |
| DuckAssistBot | `DuckAssistBot` | DuckDuckGo | AI Crawler |

Source: Wislr 48-day server log analysis of 19 AI bots.

**Layer 2: IP Range Verification**

Validate claimed identity against published IP ranges:
- OpenAI publishes ranges at `openai.com` in JSON format (chatgpt-user.json, searchbot.json, gptbot.json)
- Reverse DNS lookup: request IP → hostname → verify domain matches claimed operator
- Forward DNS confirmation: hostname → IP → must match original request IP
- Flag mismatches as "spoofed bot"

Source: OpenAI published IP ranges (github.com/FabrizioCafolla/openai-crawlers-ip-ranges), Arcjet blog on agent identification.

**Layer 3: Behavioral Pattern Classification**

For requests not caught by Layers 1-2, classify by behavior:

| Pattern | Classification | Signals |
|---------|---------------|---------|
| Systematic bulk page crawling, no JS execution | AI Crawler | High request volume, sequential URL access, text-only |
| Single-page bursts triggered by queries | RAG Scraper | Short bursts, concentrated on specific content |
| Fast funnel navigation with JS execution | AI Agent | Unnaturally fast interactions, skips scrolling |
| Search → compare → select → transact path | Shopping Agent | Complete purchase funnel, structured data evaluation |
| Natural timing, varied patterns, normal mouse | Human | Organic session characteristics |

Source: HUMAN Security (5 signal categories), Quantum Metric (4 AI traffic types), Stytch (browser fingerprinting).

### Input Formats

- nginx access logs (standard combined format)
- Apache access logs
- API gateway exports (JSON/CSV)
- Cloudflare log exports
- Custom log formats (configurable parser)

### Output

- Traffic breakdown: pie chart showing human% / AI crawler% / AI agent% / shopping agent% / unknown%
- Per-bot timeline: when each bot visits, frequency, pages targeted
- Trend lines: agent traffic growth over time
- Page-level analysis: which pages attract the most agent traffic

### Hackathon Demo Approach

The classifier parses real nginx/apache log format — it is a working log parser, not simulated. For demo purposes, we use a sample log file containing real bot behavioral patterns (from published Wislr analysis data) or capture live traffic from our own deployed demo site. The classification engine processes each log line through all three layers and produces real-time results. In production, users upload their own logs, connect via one-line middleware SDK, or pipe CDN exports.

---

## Panel 2: Discoverability Score

### What It Does

Crawls a target (website URL, API endpoint, or MCP server) and produces a research-backed **Pick Me Score (0-100)** with category breakdowns.

### Three Scout Agents

#### WebScout — Web Readiness Score (100 points)

**Structured Data (30 points)**

| Check | Points | How to Detect | Research Basis |
|-------|--------|---------------|----------------|
| JSON-LD Schema.org markup present | 10 | Parse `<script type="application/ld+json">` via `extruct` | AAIO: structured data is #1 agent signal |
| Key schema types (Product, FAQPage, Article, WebAPI) | 8 | Validate @type values in extracted JSON-LD | AAIO: specific types agents parse |
| Pricing in structured HTML (not images/PDFs) | 6 | Check for `<table>` elements on pricing pages; flag `<img>` with pricing keywords | AAIO: agents can't extract from images/PDFs |
| HTML tables with consistent column headers | 3 | Parse `<table>` elements, validate `<th>` consistency | AAIO: agents parse table structures |
| SoftwareSourceCode schema for code examples | 3 | Check for SoftwareSourceCode @type in JSON-LD | API docs research |

**Discoverability (25 points)**

| Check | Points | How to Detect | Research Basis |
|-------|--------|---------------|----------------|
| llms.txt present and well-structured | 8 | HTTP GET `{domain}/llms.txt`, validate markdown structure | llmstxt.org specification |
| robots.txt allows AI bots | 8 | HTTP GET `{domain}/robots.txt`, check for GPTBot/ClaudeBot/PerplexityBot directives | AAIO: blocking = invisible |
| XML sitemap present and recent | 5 | HTTP GET `{domain}/sitemap.xml`, check lastmod dates | Server log research: bots request sitemaps |
| Server-side rendered (not JS-only) | 4 | Fetch with and without JS execution, compare content | AAIO: JS-only = invisible to agents |

**Content Quality (25 points)**

| Check | Points | How to Detect | Research Basis |
|-------|--------|---------------|----------------|
| First 200 words directly answer core question | 7 | Extract first 200 words, use LLM to evaluate "answer-first" structure | GEO: answer-first structure preferred |
| Statistics and data points present | 6 | Regex for numbers, percentages, data patterns in content | GEO paper: +33% visibility with statistics |
| Citations to authoritative sources | 6 | Count external links to authoritative domains | GEO paper: +30% visibility with citations |
| Content freshness (<12 months, Last-Updated visible) | 6 | Check Last-Modified header, meta tags, visible dates on page | AAIO: >12 months = deprioritized |

**Consistency & Authority (20 points)**

| Check | Points | How to Detect | Research Basis |
|-------|--------|---------------|----------------|
| Consistent entity naming across pages | 6 | Crawl multiple pages, compare entity references | AAIO: inconsistency = ambiguity |
| Cross-page pricing consistency | 6 | Extract pricing from multiple pages, compare | AAIO: pricing discrepancy = exclusion |
| Clear author attribution | 4 | Check for author schema, bylines | AAIO: authority signals |
| HTTPS with security headers | 4 | Check protocol + security headers (HSTS, CSP) | AAIO: domain trust signals |

#### APIScout — API Readiness Score (100 points)

**OpenAPI Spec Quality (35 points)**

| Check | Points | How to Detect | Research Basis |
|-------|--------|---------------|----------------|
| OpenAPI spec exists at predictable URL | 8 | Probe: `/openapi.json`, `/swagger.json`, `/docs`, `/api-docs`, `/.well-known/openapi` | Standard conventions |
| All endpoints have descriptions | 8 | Parse spec, count endpoints with/without description field | Rate My OpenAPI: documentation score |
| All parameters have descriptions + types | 7 | Parse spec, validate each parameter object | Rate My OpenAPI: completeness score |
| Response schemas defined for all endpoints | 6 | Check responses object for each path | Rate My OpenAPI: completeness |
| Examples with realistic data (not "test123") | 6 | Extract example values, flag placeholder patterns | API docs research |

**Agent-Friendly Documentation (35 points)**

| Check | Points | How to Detect | Research Basis |
|-------|--------|---------------|----------------|
| Problem-first page structure | 10 | Analyze H1/H2 headings: task-oriented vs endpoint-oriented | API docs: agents pick competitor if docs need 3 pages |
| Self-contained pages (no cross-page deps) | 8 | Check for "see also" / "refer to" patterns suggesting fragmented info | API docs research |
| Complete code examples with imports | 7 | Parse code blocks, check for import statements and initialization | API docs: agents prioritize runnable examples |
| Framework-specific guides | 5 | Check for framework names in headings/URLs (Next.js, Express, etc.) | API docs: platform-native patterns |
| Agent-helpful error messages | 5 | Analyze error response schemas for guidance text | MCP best practices: errors are context |

**Technical Infrastructure (30 points)**

| Check | Points | How to Detect | Research Basis |
|-------|--------|---------------|----------------|
| Clean URL hierarchy | 6 | Analyze URL structure for logical paths (/pricing, /docs/api) | AAIO: clean hierarchies |
| Rate limiting documented | 6 | Search spec and docs for rate limit info, check response headers | API agent-readiness |
| Auth requirements clearly documented | 6 | Check for security schemes in OpenAPI spec | API agent-readiness |
| Consistent HTTP semantics and error format | 6 | Validate response codes and error schema consistency across endpoints | API agent-readiness |
| WebAPI Schema.org markup on docs pages | 6 | Check docs pages for WebAPI/TechArticle JSON-LD | API docs research |

#### MCPScout — MCP Readiness Score (100 points)

**Tool Naming (25 points)**

| Check | Points | How to Detect | Research Basis |
|-------|--------|---------------|----------------|
| Follows {service}_{action}_{resource} pattern | 10 | Regex match tool names against pattern | MCP best practices (philschmid.de) |
| Task-oriented names (not endpoint mirrors) | 8 | Flag names matching REST patterns (POST, GET, create, update) | Tool discovery guide: "name after the job" |
| No generic names (create, get, update alone) | 7 | Flag single-word generic names | MCP best practices |

**Description Quality (35 points)**

| Check | Points | How to Detect | Research Basis |
|-------|--------|---------------|----------------|
| States clear purpose (not vague) | 10 | Use LLM to evaluate: "does this describe what the tool does?" | arXiv 2602.14878: 56% fail to state purpose |
| Specifies when to invoke | 8 | Check for trigger phrases ("Use when...", "Call this to...") | MCP best practices: docstrings must specify when |
| Specifies expected input/output | 7 | Check for I/O documentation in description | MCP best practices |
| Under 100 characters | 5 | Length check | Tool discovery guide: registry hard limit |
| Contains discoverable keywords | 5 | BM25 scoring against common query terms | Tool Search: BM25 semantic matching |

**Parameter Design (20 points)**

| Check | Points | How to Detect | Research Basis |
|-------|--------|---------------|----------------|
| Flat parameters (not nested objects) | 8 | Analyze inputSchema for nested object types | MCP best practices: avoid complex nesting |
| Literal/enum types for constrained choices | 7 | Check for enum/const in schema | MCP best practices: Literal types |
| Sensible defaults provided | 5 | Check for default values in schema | MCP best practices |

**Server Design (20 points)**

| Check | Points | How to Detect | Research Basis |
|-------|--------|---------------|----------------|
| 5-15 tools (not overloaded) | 8 | Count tools from list_tools() | Discovery research: accuracy collapses at 30+ |
| Helpful error strings (not exceptions) | 6 | Test tools with invalid input, check error format | MCP best practices: return guidance |
| Server Card at .well-known/mcp | 6 | HTTP GET `{server}/.well-known/mcp/server-card.json` | MCP roadmap: June 2026 spec |

### Implementation

- **WebScout:** `httpx` to fetch pages + `extruct` to extract structured data + custom checks
- **APIScout:** `httpx` to probe OpenAPI URLs + JSON/YAML parser + custom Spectral-like rules
- **MCPScout:** `mcp` Python SDK to connect, `list_tools()`, analyze each tool's metadata

---

## Panel 3: Optimizer Agent

### What It Does

An agentic system that analyzes the Scout results, generates specific fixes, and applies GEO/AAIO/MCP optimization strategies.

### How It Works

1. **Receive issues** from Scout agents (structured list of failed checks with severity)
2. **Prioritize** by predicted impact (points gained per fix)
3. **Generate fixes** using LLM agents:
   - Generate missing JSON-LD Schema.org markup
   - Write llms.txt from site content
   - Rewrite MCP tool names and descriptions following best practices
   - Restructure API documentation from endpoint-first to problem-first
   - Add statistics, citations, and authoritative tone to content (GEO strategies)
   - Fix robots.txt to unblock AI bots
   - Generate `.well-known/mcp/server-card.json`
4. **Present to user** with:
   - What's wrong (specific issue)
   - Why it matters (linked to research with citation)
   - The fix (generated code/content)
   - Predicted impact (+X points to score)
5. **User reviews** and applies or modifies fixes

### Optimization Strategies (Research-Backed)

| Strategy | Expected Impact | Source |
|----------|----------------|--------|
| Add quotations from authoritative sources | +41% visibility | GEO paper (KDD 2024) |
| Add statistics and data points | +33% visibility | GEO paper |
| Add citations to credible sources | +30% visibility | GEO paper |
| Improve fluency and readability | +26% visibility | GEO paper |
| Apply AutoGEO preference rules | +35-51% over baselines | AutoGEO (arXiv 2510.11438) |
| Optimize MCP tool descriptions | 49% → 88% selection accuracy | Anthropic Tool Search data |
| Follow {service}_{action}_{resource} naming | Measurably higher discovery rate | MCP best practices |
| Reduce tool count to 5-15 | Prevents accuracy collapse at 30+ | Tool discovery research |

---

## Panel 4: Before/After Proof (Benchmark Engine)

### What It Does

Proves that the optimizations actually work by running controlled agent benchmarks before and after.

### How It Works

**Step 1: Baseline Benchmark (Before)**
- Craft standardized prompts relevant to the target
  - For APIs: "What payment API should I use for a subscription product?"
  - For frameworks: "What Python web framework should I use for a new API?"
  - For MCP tools: Present tool descriptions to Claude's tool selection
- Send to Claude, GPT, and Gemini APIs
- Parse responses for mentions, recommendations, and code imports
- Calculate **Pick Rate** = times picked / total prompts, per LLM

**Step 2: Apply Optimizations**
- User applies fixes from Optimizer (or we apply to a test copy)

**Step 3: Post-Optimization Benchmark (After)**
- Re-run the exact same prompts
- Calculate new Pick Rate

**Step 4: Show the Delta**
- Side-by-side comparison: Before Score vs. After Score
- Per-LLM breakdown: "Claude: 41% → 68%, GPT: 52% → 71%, Gemini: 38% → 59%"
- Highlight which optimizations caused the biggest improvements

**Step 5: Live Agent Proof (the "mic drop")**
- For MCP tools: Present Claude with two tool descriptions (original vs. optimized) and the same task prompt. Show Claude picking the optimized one.
- For APIs/frameworks: Ask Claude "What should I use for X?" with original docs vs. optimized docs as context. Show the recommendation changing.
- This runs live during the demo — real API call, real response, real proof.

### Pick Rate Measurement

```
Pick Rate = (times_recommended + times_code_generated) / (2 × total_prompts)

Where:
- times_recommended = LLM mentions the tool in conversation response
- times_code_generated = LLM imports/uses the tool in generated code
- Factor of 2 accounts for the dual recommendation/generation gap
  (arXiv 2503.17181: 83% contradiction rate between the two modes)
```

### Prompt Design for Benchmarks

Each benchmark uses 5-10 prompt variations per topic to reduce noise:
- Direct recommendation: "What's the best X for Y?"
- Comparative: "Should I use A or B for Y?"
- Task-based: "Build me a Z that does W"
- Code generation: "Write code that implements X"
- Integration: "How do I add X to my existing Y project?"

---

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Pick Me — Developer Console                    [Scan URL]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐  ┌──────────────────────────────┐ │
│  │  PICK ME SCORE       │  │  AGENT TRAFFIC              │ │
│  │                      │  │                              │ │
│  │    ┌────┐            │  │  [Pie Chart]                │ │
│  │    │ 62 │ /100       │  │  Human: 49%                 │ │
│  │    └────┘            │  │  AI Crawlers: 32%           │ │
│  │                      │  │  AI Agents: 12%             │ │
│  │  Web:  78 ████████░░ │  │  Shopping Agents: 4%        │ │
│  │  API:  45 ████░░░░░░ │  │  Unknown: 3%               │ │
│  │  MCP:  71 ███████░░░ │  │                              │ │
│  │                      │  │  [Timeline: bot visits/day]  │ │
│  │  [View Details]      │  │  [Per-bot breakdown]        │ │
│  └─────────────────────┘  └──────────────────────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  OPTIMIZATION RECOMMENDATIONS                    [Fix]  ││
│  │                                                         ││
│  │  🔴 Critical: robots.txt blocks ClaudeBot        +8 pts ││
│  │     → Generated fix: Allow ClaudeBot in robots.txt      ││
│  │     Research: "blocking = invisible to ecosystem"       ││
│  │                                                         ││
│  │  🟡 High: 12 API endpoints missing descriptions  +12 pts││
│  │     → Generated: OpenAPI descriptions for each endpoint ││
│  │     Research: Rate My OpenAPI documentation scoring     ││
│  │                                                         ││
│  │  🟡 High: MCP tool "create" is generic name      +6 pts ││
│  │     → Rewrite: "stripe_create_payment_intent"           ││
│  │     Research: arXiv 2602.14878 — 97% have quality issues││
│  │                                                         ││
│  │  [Apply All Fixes] [Re-scan After]                      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  BEFORE / AFTER PROOF                                   ││
│  │                                                         ││
│  │  Pick Me Score:  62 ──────────→ 84  (+22)               ││
│  │                                                         ││
│  │  Pick Rate by LLM:                                      ││
│  │  Claude:  41% ──→ 68%  (+27%)                           ││
│  │  GPT:     52% ──→ 71%  (+19%)                           ││
│  │  Gemini:  38% ──→ 59%  (+21%)                           ││
│  │                                                         ││
│  │  [▶ Run Live Agent Proof]                               ││
│  │  "Watch Claude pick the optimized version in real-time" ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## Hackathon Demo Flow (5 minutes)

**0:00-0:30 — The Hook**
"51% of web traffic is now AI bots. Google Analytics can't see any of it. And when AI agents shop, code, and recommend on behalf of users — your business needs to be the one they pick. But right now, you're invisible."

**0:30-1:30 — Panel 1: Agent Traffic**
Show a real server log being classified. "Look — 32% of this API's traffic is AI crawlers. 12% is actual AI agents making decisions. They had no idea."

**1:30-2:30 — Panel 2: Discoverability Score**
Live scan a real website/API/MCP server. "Their Pick Me Score is 62. Their robots.txt blocks ClaudeBot. Their API docs use 'test123' as examples. Their MCP tool is named 'create' — agents can't find it."

**2:30-3:30 — Panel 3: Optimizer**
Show the agent generating fixes. "Our optimizer rewrites the MCP tool description, generates JSON-LD markup, fixes the robots.txt — all automatically."

**3:30-4:30 — Panel 4: Before/After Proof**
Re-scan. Score jumps to 84. Then: **the live agent proof.** "Watch this. Same prompt, same task. Before optimization, Claude picks the competitor. After optimization..." [live API call] "...Claude picks us."

**4:30-5:00 — The Close**
"Agentic commerce is $3-5 trillion by 2030. Six payment protocols are already live. Every business needs to be agent-discoverable. Pick Me is the Lighthouse score for AI readiness. We're the Google Analytics for the agentic economy — but we don't just show you the data. We fix it and prove it works."

---

## Research References

### Papers
- GEO: Generative Engine Optimization (KDD 2024, arXiv:2311.09735) — 9 optimization strategies, up to +41% visibility
- AutoGEO (Oct 2025, arXiv:2510.11438) — automated preference learning, +35-51% improvement
- MCP Tool Description Smells (Feb 2026, arXiv:2602.14878) — 97% of tools have quality issues
- LLM Framework Preferences (Mar 2025, arXiv:2503.17181) — 83% recommendation/generation contradiction
- Matthew Effect in AI Coding (Sep 2025, arXiv:2509.23261) — self-reinforcing popularity bias
- Cognitive Biases in LLM-Assisted Dev (Jan 2026, arXiv:2601.08045) — 56.4% biased actions

### Standards & Protocols
- RFC 9421: HTTP Message Signatures — cryptographic agent verification
- llms.txt specification (llmstxt.org) — AI-readable site index
- OpenTelemetry MCP Semantic Conventions (merged Jan 2026) — tool invocation tracing
- MCP Server Cards SEP-1649 — .well-known metadata discovery (June 2026 target)
- Cloudflare Web Bot Auth — agent registry and verification
- Visa Trusted Agent Protocol — agent identity for commerce

### Data Sources
- Wislr: 48 days of server logs, 19 AI bots analyzed
- Anthropic: agent autonomy dataset (millions of interactions)
- Cloudflare: AI bot traffic = 51% of web, will exceed human by 2027
- OpenAI: 69% of all AI bot traffic
- McKinsey: agentic commerce = $3-5T by 2030

### Existing Tools/Libraries to Build On
- `extruct` — structured data extraction from HTML (Python)
- `httpx` — async HTTP client (Python)
- `mcp` — MCP Python SDK for server inspection
- Rate My OpenAPI — OpenAPI spec scoring (open source, Spectral-based)
- AutoGEO — automated GEO optimization (github.com/cxcscmu/AutoGEO)
- Crawl4AI — LLM-friendly crawler (github.com/unclecode/crawl4ai)
- `pyauth/http-message-signatures` — RFC 9421 verification (Python)
- `cloudflare/web-bot-auth` — agent verification (JavaScript)
- OpenAI IP ranges — published bot IP verification
- Google Schemarama — Schema.org validation

### Competitive Landscape
- Known Agents (knownagents.com) — bot analytics + verification, NO optimization
- Agent Monitor — basic bot counting, NO optimization
- Matomo — added AI traffic reports, admits "can't measure zero-click"
- AWS WAF AI Dashboard — security focus, not analytics
- Rate My OpenAPI — API spec scoring only, not agent-readiness
- llms.txt generators — single-purpose file generation only
