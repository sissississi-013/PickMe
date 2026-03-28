# Pick Me — Scoring Criteria (Research-Backed)

## Agent Traffic: Technical Viability Assessment

### How to get real agent traffic data

**Option 1: Middleware integration (like Known Agents)**
- User installs a middleware (Node.js, Python, etc.) or platform connector
- Middleware inspects every incoming request's User-Agent header
- Logs bot visits server-side and sends to our dashboard
- Known Agents does this with one-line SDK integration
- We could build a similar lightweight middleware for the hackathon

**Option 2: Log file upload**
- User uploads nginx/apache access logs
- We parse for AI bot user-agents (GPTBot, ClaudeBot, etc.)
- Show traffic patterns, page targeting, burst patterns
- This is the EASIEST path for the hackathon demo

**Option 3: CDN integration**
- Cloudflare provides AI Crawl Control analytics via GraphQL API
- AWS WAF has AI activity dashboard
- Microsoft Clarity now has bot activity dashboard
- These require the user to use those CDNs

**For the hackathon: Option 2 (log upload) is most feasible.**
- We can use publicly available server log patterns from the Wislr analysis
- Or generate realistic test data based on real behavioral patterns
- The dashboard visualizes real patterns (GPTBot bursts, ClaudeBot steady growth, etc.)

**For production: Option 1 (middleware) is the right path.**
- One-line SDK integration like Known Agents
- Works with any backend (Node.js, Python, Next.js middleware)

### Viability verdict: VIABLE but needs scoping for hackathon
- Log upload for demo ✓
- Middleware SDK for production ✓
- Cannot access someone else's server traffic without their cooperation ✗

---

## Web Readiness Score (research-backed criteria)

### Structured Data (30 points)
| Check | Points | Research Basis |
|-------|--------|---------------|
| JSON-LD Schema.org markup present | 10 | AAIO framework: "first-party structured data" is #1 priority |
| Key schema types present (Product, FAQPage, Article, WebAPI) | 8 | AAIO: specific schema types agents parse |
| Pricing in structured HTML (not images/PDFs) | 6 | AAIO: "if data exists only in paragraph form, agents cannot reliably extract" |
| HTML tables with consistent column headers | 3 | AAIO: agents parse table structures |
| SoftwareSourceCode schema for code examples | 3 | API docs optimization research |

### Discoverability (25 points)
| Check | Points | Research Basis |
|-------|--------|---------------|
| llms.txt present and well-structured | 8 | llms.txt spec: proposed standard for LLM inference |
| robots.txt allows AI bots (GPTBot, ClaudeBot, PerplexityBot) | 8 | AAIO: blocking = invisible to ecosystem |
| XML sitemap present and recent | 5 | Server log research: bots request sitemaps |
| Server-side rendered (not JS-only) | 4 | AAIO: "login walls or JavaScript-only rendering block agent access" |

### Content Quality (25 points)
| Check | Points | Research Basis |
|-------|--------|---------------|
| First 200 words directly answer the core question | 7 | GEO research: "answer first" structure |
| Statistics and data points present | 6 | GEO paper: +33% visibility with statistics |
| Citations to authoritative sources | 6 | GEO paper: +30% visibility with citations |
| Content freshness (Last-Updated metadata, <12 months) | 6 | AAIO: "pages older than 12 months deprioritized" |

### Consistency & Authority (20 points)
| Check | Points | Research Basis |
|-------|--------|---------------|
| Consistent entity naming across pages | 6 | AAIO: "inconsistent entity naming creates ambiguity" |
| Cross-page pricing consistency | 6 | AAIO: "pricing discrepancies trigger exclusion" |
| Clear author attribution | 4 | AAIO: authority signals |
| HTTPS with security headers | 4 | AAIO: domain-level trust signals |

**Total: 100 points**

---

## API Readiness Score (research-backed criteria)

### OpenAPI Spec Quality (35 points)
| Check | Points | Research Basis |
|-------|--------|---------------|
| OpenAPI spec exists at predictable URL | 8 | API docs research: agents look at /openapi.json |
| All endpoints have descriptions | 8 | Rate My OpenAPI: documentation category |
| All parameters have descriptions + types | 7 | API agent-readiness: "detailed definition of every parameter" |
| Response schemas defined for all endpoints | 6 | Rate My OpenAPI: completeness category |
| Examples with realistic data (not "test123") | 6 | API docs research: agents prioritize realistic examples |

### Agent-Friendly Documentation (35 points)
| Check | Points | Research Basis |
|-------|--------|---------------|
| Problem-first structure ("Authenticate Your App" not "Auth Endpoint") | 10 | API docs research: "recommend competitor whose auth is documented in one section" |
| Self-contained pages (no cross-page dependencies) | 8 | API docs research: if auth requires 3 pages, agent picks competitor |
| Complete code examples with imports | 7 | API docs research: agents prioritize complete, runnable examples |
| Framework-specific guides (Next.js, Express, etc.) | 5 | API docs research: use platform-native patterns |
| Error messages are agent-helpful ("Try searching by email") | 5 | MCP best practices: "error messages are context too" |

### Technical Infrastructure (30 points)
| Check | Points | Research Basis |
|-------|--------|---------------|
| Clean URL hierarchy (/pricing, /docs/api) | 6 | AAIO: clean URL hierarchies |
| Rate limiting documented | 6 | API agent-readiness: "rate limiting and quota information" |
| Auth requirements clearly documented | 6 | API agent-readiness: "authentication requirements clearly documented" |
| Consistent HTTP semantics and error format | 6 | API agent-readiness: "predictable outputs with clearly defined schemas" |
| WebAPI Schema.org markup on docs pages | 6 | API docs research: WebAPI + TechArticle schemas |

**Total: 100 points**

---

## MCP Readiness Score (research-backed criteria)

### Tool Naming (25 points)
| Check | Points | Research Basis |
|-------|--------|---------------|
| Follows {service}_{action}_{resource} pattern | 10 | MCP best practices: philschmid.de |
| Task-oriented names (not endpoint mirrors) | 8 | Tool discovery guide: "name tools after the job" |
| No generic names (create, get, update) | 7 | MCP best practices: generic names cause confusion |

### Description Quality (35 points)
| Check | Points | Research Basis |
|-------|--------|---------------|
| States clear purpose (not vague) | 10 | arXiv 2602.14878: "56% fail to state purpose clearly" |
| Specifies when to invoke | 8 | MCP best practices: docstrings must specify when |
| Specifies expected input/output | 7 | MCP best practices: argument formatting rules |
| Under 100 characters (registry limit) | 5 | Tool discovery guide: hard limit |
| Contains discoverable keywords | 5 | Tool Search: BM25 semantic matching |

### Parameter Design (20 points)
| Check | Points | Research Basis |
|-------|--------|---------------|
| Flat parameters (not nested dicts) | 8 | MCP best practices: avoid complex nested structures |
| Literal/enum types for constrained choices | 7 | MCP best practices: Literal types reduce decision complexity |
| Sensible defaults provided | 5 | MCP best practices: reduces agent errors |

### Server Design (20 points)
| Check | Points | Research Basis |
|-------|--------|---------------|
| 5-15 tools per server (not overloaded) | 8 | Tool discovery: accuracy collapses at 30+ tools |
| Helpful error strings (not exceptions) | 6 | MCP best practices: return guidance agents can follow |
| Server Card at .well-known/mcp (if applicable) | 6 | MCP roadmap: coming June 2026 spec |

**Total: 100 points**

---

## Pick Rate Benchmark (the live agent proof)

### How to measure
1. Craft standardized prompts relevant to the target (e.g., "What payment API should I use?")
2. Send to Claude, GPT, Gemini APIs
3. Parse responses for:
   - **Recommendation mentions** (conversation mode)
   - **Code imports** (code generation mode)
4. Calculate Pick Rate = mentions / total_prompts per LLM
5. Run BEFORE and AFTER optimization
6. Show the delta: "Pick Rate went from 41% → 68% after optimization"

### Research basis
- arXiv 2503.17181: 83% gap between recommendation and code generation
- GEO paper: up to +41% visibility boost with quotation optimization
- AutoGEO: 35-51% improvement over baselines
- MCP Tool Search: 49% → 88% accuracy with better descriptions
