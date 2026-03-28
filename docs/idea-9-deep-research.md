# Idea 9 Deep Research: AAIO Platform (Analytics + Optimization for Agent Traffic)

## Competitive Landscape

### Known Agents (formerly Dark Visitors) — darkvisitors.com → knownagents.com
**The closest competitor. "Google Analytics for Bots."**
- Real-time agent traffic analytics (visits, sessions, pages, duration)
- LLM referral tracking (which AI platforms recommend your site → conversion attribution)
- Agent identity verification API (cryptographic validation, spoofing detection)
- Automatic robots.txt management (WordPress plugin, category-based blocking)
- MCP & Shopping Observability (early access — monitoring MCP endpoint traffic)
- Integrations: WordPress, Cloudflare, AWS, Fastly, Shopify, Node.js
- **What they DON'T do:** Content optimization, agent-readiness scoring, recommendations, content rewriting

### Agent Monitor (agentmonitor.io)
- Server-side bot counting (analyzed 94M+ visits, 249 websites)
- Found 65% bot traffic, 24% AI bots
- Basic bot profile identification
- Launched Feb 17, 2026 on Product Hunt (5-person team from SEO agency)
- **Very basic — just counting, no optimization**

### Matomo AI Reports
- Added AI traffic reports (chatbot + agent reports)
- Behavioral metrics, referral detection
- Admits "can't measure visits that never occur" (zero-click)
- **Feature on existing platform, not purpose-built**

### AWS WAF AI Activity Dashboard
- Security-focused, not analytics-focused
- Covers 650+ unique bots/agents
- **Enterprise security tool, not marketing/developer tool**

### Rate My OpenAPI (Zuplo) / Score My OpenAPI (APIMatic)
- OpenAPI spec quality scoring (completeness, documentation, security)
- 100-point scoring with breakdown
- **API-spec only — doesn't cover full agent-readiness**

### llms.txt Generators (Apify, Firecrawl, WordLift, etc.)
- Auto-generate llms.txt files from website content
- **Single-purpose tools — no analytics, no scoring, no optimization**

---

## Key Research Papers

### GEO: Generative Engine Optimization (KDD 2024, arxiv:2311.09735)
**9 optimization strategies tested:**
1. Quotation Addition → **+41% visibility**
2. Statistics Addition → **+33% visibility**
3. Cite Sources → **+30% visibility**
4. Fluency Optimization → **+26% visibility**
5. Authoritative tone → moderate improvement
6. Technical Terms → moderate improvement
7. Easy-to-Understand → moderate improvement
8. Unique Words → minor improvement
9. Keyword Stuffing → **little to no improvement** (traditional SEO doesn't work for agents)

**Key insight:** Agents care about data quality, citations, and structured information — NOT keyword density.

### AutoGEO (October 2025, arxiv:2510.11438)
**Automated system for learning generative engine preferences:**
- AutoGEO_API: 35.99% improvement over baselines, up to 50.99% over strongest baseline
- AutoGEO_Mini: 20.99% improvement at 0.0071x cost
- **78-84% overlap** in preferences across different LLM engines (Gemini, GPT, Claude)
- Only **34-40% overlap** with commercial queries → domain-specific optimization needed
- Code: https://github.com/cxcscmu/AutoGEO

**Preference rules engines favor:**
- Comprehensiveness (cover all aspects)
- Source attribution (credible citations)
- Factual accuracy (verifiable, current)
- Logical structure (headings, lists, hierarchy)
- Clear language (avoid jargon)
- Neutral tone (no promotional bias)

### AAIO Framework (April 2025, Luciano Floridi et al.)
**Agent evaluation hierarchy:**
1. First-party structured data (Schema.org, OpenAPI specs)
2. Verified third-party references
3. Cross-source consistency
4. Content freshness (>12 months = deprioritized)
5. Depth & specificity
6. Authority signals

**Rejection triggers:** No machine-readable format, pricing inconsistencies, login walls, JS-only rendering, inconsistent entity naming.

**Citation tripling effect:** Agents prefer sources they've previously validated → compounding advantage for early optimizers.

---

## Technical Details: How Agent Discovery Actually Works

### Web Content Discovery
- Agents use standard HTTP crawling with specific user agents
- **GPTBot**: burst patterns (152 requests in 3 minutes), never checks robots.txt
- **ClaudeBot**: steady growth (+54% MoM), recently started requesting sitemaps
- **ChatGPT-User**: text-only ("Zero images, zero CSS, zero JS")
- **OAI-SearchBot**: checks robots.txt 3-6x/day (most compliant)
- **Meta-WebIndexer**: 79.8% of crawl budget on language variants
- **Google Analytics is blind** — bots don't execute JavaScript

### MCP Tool Discovery
- Claude uses Tool Search Tool (regex or BM25 semantic matching)
- Tool names + descriptions = the "SEO title" of the agent world
- Pattern: `{service}_{action}_{resource}` (e.g., `slack_send_message`)
- Anti-pattern: generic names like `create_issue`
- Accuracy went from 49% → 88% with Tool Search enabled
- **Limit servers to 5-15 tools** — descriptions compete for context window
- MCP Server Cards (`.well-known/mcp/server-card.json`) coming in June 2026 spec

### API Documentation
- Agents need: complete OpenAPI specs at `/openapi.json`
- Self-contained pages (if auth requires reading 3 pages, agent picks competitor)
- Problem-first documentation ("Authenticate Your Node.js App" > "Authentication")
- Complete code examples with realistic data (not "test123")
- Error messages as agent instructions ("User not found. Try searching by email instead")
- `llms.txt` at site root (markdown map of key resources for LLMs)

### Structured Data
- Essential Schema.org types: Product, Offer, FAQPage, Article, SoftwareApplication, AggregateRating
- HTML comparison tables with consistent column headers
- Pricing in structured HTML (NOT images or PDFs)
- JSON-LD structured data for all key entities
- WebAPI schema for API documentation pages
- TechArticle schema for docs
- SoftwareSourceCode schema for code examples

---

## The Product Architecture: Analytics + Optimization

### Side A: Analytics (understand agent traffic)
**Server-side tracking:**
- Parse access logs for AI bot user agents (19+ known bots)
- IP verification against published ranges (prevent spoofing)
- Behavioral pattern analysis (burst vs. steady, content targeting)
- Page-level agent engagement metrics
- Sitemap/robots.txt request tracking

**Citation & recommendation tracking:**
- Monitor when AI platforms cite your content
- Track LLM referral traffic and conversions
- Measure "agent share of voice" vs. competitors

**MCP endpoint monitoring:**
- Track tool invocation patterns
- Monitor which tools agents select and which they skip
- Tool description effectiveness scoring

### Side B: Optimization (make agents choose you)
**Agent-Readiness Scanner:**
- Crawl any URL and produce an Agent Readiness Score (0-100)
- Check: Schema.org JSON-LD, llms.txt, robots.txt AI bot config, OpenAPI specs, content freshness, cross-page consistency, structured data quality, HTML tables vs. images/PDFs
- Benchmark against competitors

**Content Optimizer:**
- Apply GEO/AutoGEO research: add citations, statistics, authoritative tone
- Generate/fix Schema.org markup
- Generate llms.txt from site content
- Rewrite API documentation for agent-readiness
- Optimize MCP tool names and descriptions

**Automated Fixes:**
- Generate JSON-LD structured data
- Generate llms.txt and llms-full.txt
- Rewrite tool descriptions following {service}_{action}_{resource} pattern
- Convert image/PDF content to structured HTML
- Add freshness metadata (Last-Updated dates)

---

## Existing Tools & Libraries to Build On

### For Crawling & Extraction
- **Crawl4AI** (github.com/unclecode/crawl4ai) — LLM-friendly web crawler, produces clean markdown
- **Google Schemarama** (github.com/google/schemarama) — Schema.org validation
- **crwlr/schema-org** — Extract JSON-LD from HTML
- **Apify llms.txt Generator** — Auto-generate llms.txt files

### For OpenAPI Analysis
- **Rate My OpenAPI** (Zuplo) — Open source API spec scoring
- **42Crunch API Audit** — 300+ checks for API spec security/quality

### For Content Optimization
- **AutoGEO** (github.com/cxcscmu/AutoGEO) — Automated GEO optimization
- GEO preference rules as scoring/rewriting basis

### For Bot Detection
- User-agent string matching + IP verification
- Nginx/Apache log parsing
- Known Agents' verification API as reference

---

## Agentic Commerce Context

**Market size:** $3-5 trillion by 2030 (McKinsey)
**Protocols:** ACP (OpenAI/Stripe), UCP (Google/Shopify), AP2, MCP, A2A, Visa TAP
**Key gap:** "Every protocol requires merchants to opt in — millions of long-tail merchants remain invisible to agents"
**Checkout bottleneck:** Only 5 pure-play checkout execution companies exist
**Layer 6 (Merchant Enablement & Discovery)** is where our product fits — helping merchants become agent-discoverable

---

## Key Differentiation from Competitors

| Capability | Known Agents | Agent Monitor | Our Product |
|---|---|---|---|
| Bot traffic counting | Yes | Yes | Yes |
| Bot behavior analysis | Yes | Basic | Deep |
| LLM referral tracking | Yes | No | Yes |
| Agent-readiness scoring | No | No | **Yes** |
| Content optimization | No | No | **Yes** |
| Schema/structured data audit | No | No | **Yes** |
| llms.txt generation | No | No | **Yes** |
| OpenAPI doc optimization | No | No | **Yes** |
| MCP tool description scoring | No | No | **Yes** |
| Auto-fix/rewrite | No | No | **Yes** |
| Competitor benchmarking | No | No | **Yes** |

**Our unique value:** Known Agents tells you WHAT bots are doing. We tell you WHY agents aren't choosing you AND fix it.
