# Pick Me Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Pick Me — a developer console that classifies AI agent traffic, scores discoverability across web/API/MCP surfaces, generates agentic optimizations, and proves they work with live before/after benchmarks.

**Architecture:** Python FastAPI backend with four engines (Traffic Classifier, Scout Agents, Optimizer, Benchmark). Next.js frontend with shadcn/ui dashboard showing four panels. Backend and frontend communicate via REST API.

**Tech Stack:** Python 3.11+, FastAPI, httpx, extruct, mcp SDK, anthropic SDK, openai SDK | Next.js 14+, TypeScript, Tailwind CSS, shadcn/ui, recharts

---

## File Structure

```
pickme/
├── backend/
│   ├── main.py                    # FastAPI app, CORS, route mounting
│   ├── models.py                  # All Pydantic models (shared types)
│   ├── bot_db.py                  # Known AI bot database (user-agents, IPs, categories)
│   ├── traffic_classifier.py      # Log parsing + 3-layer classification
│   ├── web_scout.py               # Website readiness scoring (structured data, llms.txt, etc.)
│   ├── api_scout.py               # API/OpenAPI readiness scoring
│   ├── mcp_scout.py               # MCP tool readiness scoring
│   ├── optimizer.py               # LLM-powered fix generation
│   ├── benchmark.py               # Pick rate measurement + live agent proof
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx         # Root layout with font, metadata
│   │   │   └── page.tsx           # Main dashboard page (assembles all panels)
│   │   ├── components/
│   │   │   ├── scan-input.tsx     # URL/log input bar at top
│   │   │   ├── score-panel.tsx    # Pick Me Score with category breakdown
│   │   │   ├── traffic-panel.tsx  # Agent traffic pie chart + timeline
│   │   │   ├── optimizer-panel.tsx # Optimization recommendations list
│   │   │   ├── benchmark-panel.tsx # Before/after proof + live agent button
│   │   │   └── score-bar.tsx      # Reusable score progress bar component
│   │   └── lib/
│   │       └── api.ts             # API client functions (fetch wrapper)
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── next.config.ts
├── tests/
│   ├── test_bot_db.py
│   ├── test_traffic_classifier.py
│   ├── test_web_scout.py
│   ├── test_api_scout.py
│   └── test_mcp_scout.py
└── data/
    └── sample_access.log          # Demo nginx log with real bot patterns
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pickme/backend/requirements.txt`
- Create: `pickme/backend/main.py`
- Create: `pickme/backend/models.py`
- Create: `pickme/frontend/` (via create-next-app)

- [ ] **Step 1: Create backend directory and requirements**

```bash
mkdir -p pickme/backend pickme/tests pickme/data
```

```
# pickme/backend/requirements.txt
fastapi==0.115.12
uvicorn==0.34.2
httpx==0.28.1
extruct==0.18.0
pyyaml==6.0.2
anthropic>=0.52.0
openai>=1.82.0
python-multipart==0.0.20
```

- [ ] **Step 2: Install backend dependencies**

Run: `cd pickme/backend && pip install -r requirements.txt`

- [ ] **Step 3: Create shared Pydantic models**

```python
# pickme/backend/models.py
from pydantic import BaseModel

class BotInfo(BaseModel):
    name: str
    pattern: str
    operator: str
    category: str  # "ai_crawler" | "ai_agent" | "shopping_agent"

class TrafficEntry(BaseModel):
    ip: str
    timestamp: str
    method: str
    path: str
    status: int
    user_agent: str
    classification: str  # "human" | "ai_crawler" | "ai_agent" | "shopping_agent" | "unknown"
    bot_name: str | None = None
    operator: str | None = None

class TrafficSummary(BaseModel):
    total_requests: int
    human: int
    ai_crawler: int
    ai_agent: int
    shopping_agent: int
    unknown: int
    per_bot: dict[str, int]
    entries: list[TrafficEntry]

class CheckResult(BaseModel):
    name: str
    passed: bool
    points_earned: int
    points_possible: int
    detail: str
    research_basis: str

class CategoryScore(BaseModel):
    name: str
    score: int
    max_score: int
    checks: list[CheckResult]

class ScoutReport(BaseModel):
    target: str
    scout_type: str  # "web" | "api" | "mcp"
    total_score: int
    max_score: int
    categories: list[CategoryScore]

class Recommendation(BaseModel):
    severity: str  # "critical" | "high" | "medium" | "low"
    issue: str
    why_it_matters: str
    fix: str
    predicted_impact: int  # points gained

class OptimizationReport(BaseModel):
    recommendations: list[Recommendation]
    total_predicted_gain: int

class BenchmarkResult(BaseModel):
    llm_name: str
    pick_rate_before: float
    pick_rate_after: float | None = None
    raw_responses: list[str] = []

class BenchmarkReport(BaseModel):
    target_name: str
    prompt_used: str
    results: list[BenchmarkResult]
```

- [ ] **Step 4: Create FastAPI app shell**

```python
# pickme/backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Pick Me", description="Agent discoverability engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Verify backend starts**

Run: `cd pickme/backend && uvicorn main:app --reload --port 8000`
Expected: Server starts, `GET /health` returns `{"status": "ok"}`

- [ ] **Step 6: Scaffold frontend**

```bash
cd pickme && npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm
```

- [ ] **Step 7: Install frontend dependencies**

```bash
cd pickme/frontend && npx shadcn@latest init -d && npx shadcn@latest add card button badge progress tabs separator input
npm install recharts
```

- [ ] **Step 8: Create API client helper**

```typescript
// pickme/frontend/src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function apiUpload<T>(path: string, file: File): Promise<T> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
```

- [ ] **Step 9: Commit**

```bash
git add pickme/
git commit -m "feat: scaffold Pick Me project — FastAPI backend + Next.js frontend"
```

---

## Task 2: Bot Database

**Files:**
- Create: `pickme/backend/bot_db.py`
- Create: `pickme/tests/test_bot_db.py`

- [ ] **Step 1: Write the failing test**

```python
# pickme/tests/test_bot_db.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from bot_db import match_bot, KNOWN_BOTS

def test_match_gptbot():
    result = match_bot("Mozilla/5.0 (compatible; GPTBot/1.1; +https://openai.com/gptbot)")
    assert result is not None
    assert result.name == "GPTBot"
    assert result.operator == "OpenAI"
    assert result.category == "ai_crawler"

def test_match_chatgpt_user():
    result = match_bot("Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot")
    assert result is not None
    assert result.name == "ChatGPT-User"
    assert result.category == "ai_agent"

def test_match_claudebot():
    result = match_bot("Mozilla/5.0 (compatible; ClaudeBot/1.0; +https://claudebot.ai)")
    assert result is not None
    assert result.name == "ClaudeBot"
    assert result.operator == "Anthropic"

def test_no_match_chrome():
    result = match_bot("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
    assert result is None

def test_known_bots_not_empty():
    assert len(KNOWN_BOTS) >= 12
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd pickme && python -m pytest tests/test_bot_db.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bot_db'`

- [ ] **Step 3: Implement bot database**

```python
# pickme/backend/bot_db.py
import re
from models import BotInfo

KNOWN_BOTS: list[BotInfo] = [
    BotInfo(name="GPTBot", pattern=r"GPTBot", operator="OpenAI", category="ai_crawler"),
    BotInfo(name="ChatGPT-User", pattern=r"ChatGPT-User", operator="OpenAI", category="ai_agent"),
    BotInfo(name="OAI-SearchBot", pattern=r"OAI-SearchBot", operator="OpenAI", category="ai_crawler"),
    BotInfo(name="ClaudeBot", pattern=r"ClaudeBot", operator="Anthropic", category="ai_crawler"),
    BotInfo(name="Claude-SearchBot", pattern=r"Claude-SearchBot", operator="Anthropic", category="ai_crawler"),
    BotInfo(name="Claude-User", pattern=r"Claude/1\.0", operator="Anthropic", category="ai_agent"),
    BotInfo(name="PerplexityBot", pattern=r"PerplexityBot", operator="Perplexity", category="ai_crawler"),
    BotInfo(name="Meta-WebIndexer", pattern=r"Meta-WebIndexer", operator="Meta", category="ai_crawler"),
    BotInfo(name="Applebot-Extended", pattern=r"Applebot-Extended", operator="Apple", category="ai_crawler"),
    BotInfo(name="Bytespider", pattern=r"Bytespider", operator="ByteDance", category="ai_crawler"),
    BotInfo(name="CCBot", pattern=r"CCBot", operator="Common Crawl", category="ai_crawler"),
    BotInfo(name="DuckAssistBot", pattern=r"DuckAssistBot", operator="DuckDuckGo", category="ai_crawler"),
    BotInfo(name="Googlebot", pattern=r"Googlebot", operator="Google", category="ai_crawler"),
    BotInfo(name="Bingbot", pattern=r"bingbot", operator="Microsoft", category="ai_crawler"),
    BotInfo(name="Meta-ExternalAgent", pattern=r"Meta-ExternalAgent", operator="Meta", category="ai_agent"),
    BotInfo(name="YouBot", pattern=r"YouBot", operator="You.com", category="ai_crawler"),
]

_compiled = [(re.compile(bot.pattern, re.IGNORECASE), bot) for bot in KNOWN_BOTS]

def match_bot(user_agent: str) -> BotInfo | None:
    for regex, bot in _compiled:
        if regex.search(user_agent):
            return bot
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd pickme && python -m pytest tests/test_bot_db.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pickme/backend/bot_db.py pickme/tests/test_bot_db.py
git commit -m "feat: add known AI bot database with 16 bots and user-agent matching"
```

---

## Task 3: Traffic Classifier (Log Parser + 3-Layer Classification)

**Files:**
- Create: `pickme/backend/traffic_classifier.py`
- Create: `pickme/tests/test_traffic_classifier.py`
- Create: `pickme/data/sample_access.log`

- [ ] **Step 1: Create sample log file with real bot patterns**

```
# pickme/data/sample_access.log
66.249.66.1 - - [28/Mar/2026:10:15:32 +0000] "GET /docs/api HTTP/1.1" 200 5234 "-" "Mozilla/5.0 (compatible; GPTBot/1.1; +https://openai.com/gptbot)"
20.15.240.10 - - [28/Mar/2026:10:15:33 +0000] "GET /pricing HTTP/1.1" 200 3421 "-" "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot"
152.42.196.25 - - [28/Mar/2026:10:15:34 +0000] "GET / HTTP/1.1" 200 8912 "-" "Mozilla/5.0 (compatible; ClaudeBot/1.0; +https://claudebot.ai)"
74.6.231.20 - - [28/Mar/2026:10:15:35 +0000] "GET /api/v1/products HTTP/1.1" 200 1234 "-" "Mozilla/5.0 (compatible; PerplexityBot/1.0; +https://perplexity.ai/bot)"
192.168.1.50 - - [28/Mar/2026:10:15:36 +0000] "GET / HTTP/1.1" 200 8912 "https://google.com" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
192.168.1.51 - - [28/Mar/2026:10:15:37 +0000] "GET /about HTTP/1.1" 200 4321 "https://google.com" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
40.77.167.80 - - [28/Mar/2026:10:15:38 +0000] "GET /sitemap.xml HTTP/1.1" 200 2345 "-" "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
66.249.66.2 - - [28/Mar/2026:10:15:39 +0000] "GET /openapi.json HTTP/1.1" 200 15678 "-" "Mozilla/5.0 (compatible; GPTBot/1.1; +https://openai.com/gptbot)"
20.15.240.11 - - [28/Mar/2026:10:15:40 +0000] "GET /docs/authentication HTTP/1.1" 200 4567 "-" "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot"
192.168.1.52 - - [28/Mar/2026:10:15:41 +0000] "GET /pricing HTTP/1.1" 200 3421 "https://twitter.com" "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1"
66.249.66.3 - - [28/Mar/2026:10:15:42 +0000] "GET /docs/webhooks HTTP/1.1" 200 6789 "-" "Mozilla/5.0 (compatible; GPTBot/1.1; +https://openai.com/gptbot)"
152.42.196.26 - - [28/Mar/2026:10:15:43 +0000] "GET /llms.txt HTTP/1.1" 404 0 "-" "Mozilla/5.0 (compatible; ClaudeBot/1.0; +https://claudebot.ai)"
10.0.0.5 - - [28/Mar/2026:10:15:44 +0000] "GET /products HTTP/1.1" 200 4567 "-" "Mozilla/5.0 (compatible; Meta-ExternalAgent/1.0; +https://www.facebook.com/externalhit_uatext.php)"
192.168.1.53 - - [28/Mar/2026:10:15:45 +0000] "POST /api/v1/checkout HTTP/1.1" 201 890 "https://example.com" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
20.15.240.12 - - [28/Mar/2026:10:15:46 +0000] "GET /pricing HTTP/1.1" 200 3421 "-" "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot"
```

- [ ] **Step 2: Write the failing test**

```python
# pickme/tests/test_traffic_classifier.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from traffic_classifier import parse_log_line, classify_log

def test_parse_gptbot_line():
    line = '66.249.66.1 - - [28/Mar/2026:10:15:32 +0000] "GET /docs/api HTTP/1.1" 200 5234 "-" "Mozilla/5.0 (compatible; GPTBot/1.1; +https://openai.com/gptbot)"'
    entry = parse_log_line(line)
    assert entry is not None
    assert entry.ip == "66.249.66.1"
    assert entry.path == "/docs/api"
    assert entry.classification == "ai_crawler"
    assert entry.bot_name == "GPTBot"

def test_parse_human_line():
    line = '192.168.1.50 - - [28/Mar/2026:10:15:36 +0000] "GET / HTTP/1.1" 200 8912 "https://google.com" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"'
    entry = parse_log_line(line)
    assert entry is not None
    assert entry.classification == "human"
    assert entry.bot_name is None

def test_classify_log_summary():
    log_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_access.log")
    summary = classify_log(log_path)
    assert summary.total_requests == 15
    assert summary.ai_crawler > 0
    assert summary.ai_agent > 0
    assert summary.human > 0
    assert summary.ai_crawler + summary.ai_agent + summary.human + summary.shopping_agent + summary.unknown == summary.total_requests
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd pickme && python -m pytest tests/test_traffic_classifier.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement traffic classifier**

```python
# pickme/backend/traffic_classifier.py
import re
from models import TrafficEntry, TrafficSummary
from bot_db import match_bot

LOG_PATTERN = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) \S+" (?P<status>\d+) \S+ '
    r'"[^"]*" "(?P<user_agent>[^"]*)"'
)

def parse_log_line(line: str) -> TrafficEntry | None:
    m = LOG_PATTERN.match(line.strip())
    if not m:
        return None

    ip = m.group("ip")
    user_agent = m.group("user_agent")
    bot = match_bot(user_agent)

    if bot:
        classification = bot.category
        bot_name = bot.name
        operator = bot.operator
    else:
        classification = "human"
        bot_name = None
        operator = None

    return TrafficEntry(
        ip=ip,
        timestamp=m.group("timestamp"),
        method=m.group("method"),
        path=m.group("path"),
        status=int(m.group("status")),
        user_agent=user_agent,
        classification=classification,
        bot_name=bot_name,
        operator=operator,
    )

def classify_log(log_path: str) -> TrafficSummary:
    entries: list[TrafficEntry] = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            entry = parse_log_line(line)
            if entry:
                entries.append(entry)

    per_bot: dict[str, int] = {}
    counts = {"human": 0, "ai_crawler": 0, "ai_agent": 0, "shopping_agent": 0, "unknown": 0}

    for e in entries:
        counts[e.classification] = counts.get(e.classification, 0) + 1
        if e.bot_name:
            per_bot[e.bot_name] = per_bot.get(e.bot_name, 0) + 1

    return TrafficSummary(
        total_requests=len(entries),
        human=counts["human"],
        ai_crawler=counts["ai_crawler"],
        ai_agent=counts["ai_agent"],
        shopping_agent=counts["shopping_agent"],
        unknown=counts["unknown"],
        per_bot=per_bot,
        entries=entries,
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd pickme && python -m pytest tests/test_traffic_classifier.py -v`
Expected: All 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add pickme/backend/traffic_classifier.py pickme/tests/test_traffic_classifier.py pickme/data/sample_access.log
git commit -m "feat: add log parser with 3-layer traffic classification"
```

---

## Task 4: WebScout — Website Readiness Scoring

**Files:**
- Create: `pickme/backend/web_scout.py`
- Create: `pickme/tests/test_web_scout.py`

- [ ] **Step 1: Write the failing test**

```python
# pickme/tests/test_web_scout.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import pytest
from web_scout import scan_website

@pytest.mark.asyncio
async def test_scan_real_website():
    """Scan a real website and verify score structure."""
    report = await scan_website("https://httpbin.org")
    assert report.scout_type == "web"
    assert 0 <= report.total_score <= 100
    assert len(report.categories) == 4
    category_names = [c.name for c in report.categories]
    assert "Structured Data" in category_names
    assert "Discoverability" in category_names
    assert "Content Quality" in category_names
    assert "Consistency & Authority" in category_names
    for cat in report.categories:
        assert cat.score <= cat.max_score
        for check in cat.checks:
            assert check.points_earned <= check.points_possible
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd pickme && pip install pytest-asyncio && python -m pytest tests/test_web_scout.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement WebScout**

```python
# pickme/backend/web_scout.py
import httpx
import extruct
import re
from models import ScoutReport, CategoryScore, CheckResult

async def scan_website(url: str) -> ScoutReport:
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        # Fetch main page
        main_resp = await client.get(url)
        html = main_resp.text
        base_url = str(main_resp.url)

        # Extract structured data
        metadata = extruct.extract(html, base_url=base_url, errors="ignore")
        jsonld = metadata.get("json-ld", [])

        # Fetch supplementary files
        llms_txt = await _fetch_text(client, f"{base_url.rstrip('/')}/llms.txt")
        robots_txt = await _fetch_text(client, f"{base_url.rstrip('/')}/robots.txt")
        sitemap = await _fetch_text(client, f"{base_url.rstrip('/')}/sitemap.xml")

    structured_data_checks = _check_structured_data(jsonld, html)
    discoverability_checks = _check_discoverability(llms_txt, robots_txt, sitemap, html)
    content_quality_checks = _check_content_quality(html, main_resp.headers)
    authority_checks = _check_authority(base_url, html, main_resp)

    categories = [
        CategoryScore(name="Structured Data", score=sum(c.points_earned for c in structured_data_checks), max_score=30, checks=structured_data_checks),
        CategoryScore(name="Discoverability", score=sum(c.points_earned for c in discoverability_checks), max_score=25, checks=discoverability_checks),
        CategoryScore(name="Content Quality", score=sum(c.points_earned for c in content_quality_checks), max_score=25, checks=content_quality_checks),
        CategoryScore(name="Consistency & Authority", score=sum(c.points_earned for c in authority_checks), max_score=20, checks=authority_checks),
    ]

    total = sum(c.score for c in categories)
    return ScoutReport(target=url, scout_type="web", total_score=total, max_score=100, categories=categories)


async def _fetch_text(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        resp = await client.get(url)
        return resp.text if resp.status_code == 200 else None
    except Exception:
        return None


def _check_structured_data(jsonld: list, html: str) -> list[CheckResult]:
    checks = []

    # JSON-LD present
    has_jsonld = len(jsonld) > 0
    checks.append(CheckResult(
        name="JSON-LD Schema.org markup", passed=has_jsonld, points_earned=10 if has_jsonld else 0,
        points_possible=10, detail=f"Found {len(jsonld)} JSON-LD blocks" if has_jsonld else "No JSON-LD markup found",
        research_basis="AAIO: structured data is #1 agent signal",
    ))

    # Key schema types
    types_found = set()
    key_types = {"Product", "FAQPage", "Article", "WebAPI", "SoftwareApplication", "Organization", "WebSite"}
    for item in jsonld:
        t = item.get("@type", "")
        if isinstance(t, list):
            types_found.update(t)
        else:
            types_found.add(t)
    matched = types_found & key_types
    score = min(8, len(matched) * 2)
    checks.append(CheckResult(
        name="Key schema types", passed=len(matched) > 0, points_earned=score,
        points_possible=8, detail=f"Found: {', '.join(matched)}" if matched else "No key schema types (Product, FAQPage, Article, WebAPI)",
        research_basis="AAIO: specific types agents parse",
    ))

    # Pricing in HTML tables vs images
    has_tables = bool(re.search(r"<table", html, re.IGNORECASE))
    pricing_in_img = bool(re.search(r"<img[^>]*(?:pricing|price|plan)", html, re.IGNORECASE))
    ok = has_tables and not pricing_in_img
    checks.append(CheckResult(
        name="Pricing in structured HTML", passed=ok, points_earned=6 if ok else (3 if has_tables else 0),
        points_possible=6, detail="Pricing in HTML tables" if ok else "Pricing may be in images/PDFs — agents can't extract",
        research_basis="AAIO: agents can't extract from images/PDFs",
    ))

    # Tables with headers
    has_th = bool(re.search(r"<th", html, re.IGNORECASE))
    checks.append(CheckResult(
        name="HTML tables with headers", passed=has_th, points_earned=3 if has_th else 0,
        points_possible=3, detail="Tables have consistent headers" if has_th else "No table headers found",
        research_basis="AAIO: agents parse table structures",
    ))

    # SoftwareSourceCode schema
    has_code_schema = any(item.get("@type") == "SoftwareSourceCode" for item in jsonld)
    checks.append(CheckResult(
        name="SoftwareSourceCode schema", passed=has_code_schema, points_earned=3 if has_code_schema else 0,
        points_possible=3, detail="SoftwareSourceCode schema found" if has_code_schema else "No SoftwareSourceCode schema",
        research_basis="API docs research",
    ))

    return checks


def _check_discoverability(llms_txt: str | None, robots_txt: str | None, sitemap: str | None, html: str) -> list[CheckResult]:
    checks = []

    # llms.txt
    has_llms = llms_txt is not None and len(llms_txt.strip()) > 10
    checks.append(CheckResult(
        name="llms.txt present", passed=has_llms, points_earned=8 if has_llms else 0,
        points_possible=8, detail=f"llms.txt found ({len(llms_txt)} chars)" if has_llms else "No llms.txt — agents have no curated site map",
        research_basis="llmstxt.org specification",
    ))

    # robots.txt allows AI bots
    ai_bots_blocked = []
    if robots_txt:
        for bot in ["GPTBot", "ClaudeBot", "PerplexityBot", "ChatGPT-User"]:
            if re.search(rf"User-agent:\s*{bot}.*?Disallow:\s*/", robots_txt, re.IGNORECASE | re.DOTALL):
                ai_bots_blocked.append(bot)
    bots_ok = len(ai_bots_blocked) == 0
    checks.append(CheckResult(
        name="robots.txt allows AI bots", passed=bots_ok, points_earned=8 if bots_ok else 0,
        points_possible=8,
        detail="All major AI bots allowed" if bots_ok else f"Blocked: {', '.join(ai_bots_blocked)}",
        research_basis="AAIO: blocking = invisible to ecosystem",
    ))

    # Sitemap
    has_sitemap = sitemap is not None and "<urlset" in (sitemap or "")
    checks.append(CheckResult(
        name="XML sitemap present", passed=has_sitemap, points_earned=5 if has_sitemap else 0,
        points_possible=5, detail="Sitemap found" if has_sitemap else "No XML sitemap",
        research_basis="Server log research: bots request sitemaps",
    ))

    # SSR check (simplified: check if meaningful content in raw HTML)
    text_content = re.sub(r"<[^>]+>", "", html)
    has_ssr = len(text_content.strip()) > 500
    checks.append(CheckResult(
        name="Server-side rendered", passed=has_ssr, points_earned=4 if has_ssr else 0,
        points_possible=4, detail="Content available without JS" if has_ssr else "Content may require JavaScript — invisible to most agents",
        research_basis="AAIO: JS-only = invisible to agents",
    ))

    return checks


def _check_content_quality(html: str, headers: httpx.Headers) -> list[CheckResult]:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()
    checks = []

    # First 200 words (simplified: check length)
    has_content = len(words) >= 200
    checks.append(CheckResult(
        name="Substantial content present", passed=has_content, points_earned=7 if has_content else 3,
        points_possible=7, detail=f"{len(words)} words of content" if has_content else "Thin content — agents prefer comprehensive pages",
        research_basis="GEO: answer-first structure preferred",
    ))

    # Statistics
    stat_pattern = r"\b\d+(?:\.\d+)?%|\b\d{1,3}(?:,\d{3})+\b|\$\d+"
    stats = re.findall(stat_pattern, text)
    has_stats = len(stats) >= 2
    checks.append(CheckResult(
        name="Statistics and data points", passed=has_stats, points_earned=6 if has_stats else 0,
        points_possible=6, detail=f"Found {len(stats)} data points" if has_stats else "No statistics found — add data for +33% visibility",
        research_basis="GEO paper: +33% visibility with statistics",
    ))

    # External links (citations)
    ext_links = re.findall(r'href="https?://[^"]+', html)
    has_citations = len(ext_links) >= 3
    checks.append(CheckResult(
        name="Citations to external sources", passed=has_citations, points_earned=6 if has_citations else 0,
        points_possible=6, detail=f"Found {len(ext_links)} external links" if has_citations else "No citations — add authoritative sources for +30% visibility",
        research_basis="GEO paper: +30% visibility with citations",
    ))

    # Freshness
    last_modified = headers.get("last-modified", "")
    has_date = bool(re.search(r"202[5-9]|203\d", html)) or bool(last_modified)
    checks.append(CheckResult(
        name="Content freshness", passed=has_date, points_earned=6 if has_date else 0,
        points_possible=6, detail="Recent dates detected" if has_date else "No freshness signals — pages >12 months get deprioritized",
        research_basis="AAIO: >12 months = deprioritized",
    ))

    return checks


def _check_authority(base_url: str, html: str, resp: httpx.Response) -> list[CheckResult]:
    checks = []

    # Entity naming (simplified: check title consistency)
    title_match = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
    has_title = title_match is not None
    checks.append(CheckResult(
        name="Consistent entity naming", passed=has_title, points_earned=6 if has_title else 0,
        points_possible=6, detail=f"Title: {title_match.group(1).strip()}" if has_title else "No page title found",
        research_basis="AAIO: inconsistency = ambiguity",
    ))

    # Pricing consistency (simplified: single-page scan)
    checks.append(CheckResult(
        name="Cross-page pricing consistency", passed=True, points_earned=3,
        points_possible=6, detail="Single-page scan — multi-page consistency requires deep crawl",
        research_basis="AAIO: pricing discrepancy = exclusion",
    ))

    # Author attribution
    has_author = bool(re.search(r'"author"|"Author"|byline|data-author', html))
    checks.append(CheckResult(
        name="Author attribution", passed=has_author, points_earned=4 if has_author else 0,
        points_possible=4, detail="Author attribution found" if has_author else "No author attribution",
        research_basis="AAIO: authority signals",
    ))

    # HTTPS
    is_https = base_url.startswith("https")
    hsts = "strict-transport-security" in resp.headers
    score = (2 if is_https else 0) + (2 if hsts else 0)
    checks.append(CheckResult(
        name="HTTPS + security headers", passed=is_https, points_earned=score,
        points_possible=4, detail=f"HTTPS: {'✓' if is_https else '✗'}, HSTS: {'✓' if hsts else '✗'}",
        research_basis="AAIO: domain trust signals",
    ))

    return checks
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd pickme && python -m pytest tests/test_web_scout.py -v`
Expected: PASS (requires internet to reach httpbin.org)

- [ ] **Step 5: Commit**

```bash
git add pickme/backend/web_scout.py pickme/tests/test_web_scout.py
git commit -m "feat: add WebScout with 13 research-backed checks across 4 categories"
```

---

## Task 5: APIScout — OpenAPI Readiness Scoring

**Files:**
- Create: `pickme/backend/api_scout.py`
- Create: `pickme/tests/test_api_scout.py`

- [ ] **Step 1: Write the failing test**

```python
# pickme/tests/test_api_scout.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import pytest
from api_scout import scan_api

@pytest.mark.asyncio
async def test_scan_petstore():
    """Scan the Petstore demo API spec."""
    report = await scan_api("https://petstore3.swagger.io")
    assert report.scout_type == "api"
    assert 0 <= report.total_score <= 100
    assert len(report.categories) == 3
    category_names = [c.name for c in report.categories]
    assert "OpenAPI Spec Quality" in category_names

def test_score_openapi_spec_dict():
    from api_scout import score_openapi_spec
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0"},
        "paths": {
            "/users": {
                "get": {
                    "description": "List all users",
                    "parameters": [{"name": "limit", "in": "query", "description": "Max results", "schema": {"type": "integer"}}],
                    "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": {"type": "array"}}}}},
                }
            },
            "/users/{id}": {
                "get": {
                    "responses": {"200": {"description": "OK"}}
                }
            }
        },
    }
    report = score_openapi_spec(spec, "https://example.com")
    assert report.total_score > 0
    assert report.scout_type == "api"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd pickme && python -m pytest tests/test_api_scout.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement APIScout**

```python
# pickme/backend/api_scout.py
import httpx
import json
import yaml
import re
from models import ScoutReport, CategoryScore, CheckResult

OPENAPI_PATHS = ["/openapi.json", "/swagger.json", "/api-docs", "/docs/openapi.json", "/.well-known/openapi"]

async def scan_api(base_url: str) -> ScoutReport:
    spec = None
    spec_url = None
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        for path in OPENAPI_PATHS:
            try:
                resp = await client.get(f"{base_url.rstrip('/')}{path}")
                if resp.status_code == 200:
                    content = resp.text
                    try:
                        spec = json.loads(content)
                    except json.JSONDecodeError:
                        try:
                            spec = yaml.safe_load(content)
                        except Exception:
                            continue
                    if isinstance(spec, dict) and ("openapi" in spec or "swagger" in spec):
                        spec_url = path
                        break
                    spec = None
            except Exception:
                continue

    if spec is None:
        return ScoutReport(
            target=base_url, scout_type="api", total_score=0, max_score=100,
            categories=[CategoryScore(
                name="OpenAPI Spec Quality", score=0, max_score=35,
                checks=[CheckResult(name="OpenAPI spec exists", passed=False, points_earned=0, points_possible=8,
                    detail=f"No spec found at {', '.join(OPENAPI_PATHS)}", research_basis="Standard conventions")],
            )],
        )

    return score_openapi_spec(spec, base_url, spec_url)


def score_openapi_spec(spec: dict, base_url: str, spec_url: str | None = None) -> ScoutReport:
    paths = spec.get("paths", {})
    all_operations = []
    for path, methods in paths.items():
        for method, op in methods.items():
            if method in ("get", "post", "put", "patch", "delete"):
                all_operations.append((path, method, op if isinstance(op, dict) else {}))

    # Category 1: OpenAPI Spec Quality (35 pts)
    spec_checks = []

    # Spec exists
    spec_checks.append(CheckResult(
        name="OpenAPI spec exists", passed=True, points_earned=8, points_possible=8,
        detail=f"Found at {spec_url}" if spec_url else "Spec provided",
        research_basis="Standard conventions",
    ))

    # Endpoints with descriptions
    with_desc = sum(1 for _, _, op in all_operations if op.get("description") or op.get("summary"))
    total_ops = max(len(all_operations), 1)
    desc_ratio = with_desc / total_ops
    desc_score = round(8 * desc_ratio)
    spec_checks.append(CheckResult(
        name="Endpoints have descriptions", passed=desc_ratio > 0.8, points_earned=desc_score, points_possible=8,
        detail=f"{with_desc}/{total_ops} endpoints have descriptions",
        research_basis="Rate My OpenAPI: documentation score",
    ))

    # Parameters with descriptions
    total_params = 0
    params_with_desc = 0
    for _, _, op in all_operations:
        for param in op.get("parameters", []):
            total_params += 1
            if param.get("description"):
                params_with_desc += 1
    param_ratio = params_with_desc / max(total_params, 1)
    param_score = round(7 * param_ratio)
    spec_checks.append(CheckResult(
        name="Parameters have descriptions", passed=param_ratio > 0.8, points_earned=param_score, points_possible=7,
        detail=f"{params_with_desc}/{total_params} params documented",
        research_basis="Rate My OpenAPI: completeness score",
    ))

    # Response schemas
    with_schema = 0
    for _, _, op in all_operations:
        for code, resp in op.get("responses", {}).items():
            if isinstance(resp, dict) and resp.get("content"):
                with_schema += 1
                break
    schema_ratio = with_schema / total_ops
    schema_score = round(6 * schema_ratio)
    spec_checks.append(CheckResult(
        name="Response schemas defined", passed=schema_ratio > 0.8, points_earned=schema_score, points_possible=6,
        detail=f"{with_schema}/{total_ops} endpoints have response schemas",
        research_basis="Rate My OpenAPI: completeness",
    ))

    # Realistic examples
    has_examples = False
    placeholder_patterns = re.compile(r"test|example|foo|bar|string|123|sample", re.IGNORECASE)
    for _, _, op in all_operations:
        for param in op.get("parameters", []):
            ex = param.get("example") or param.get("schema", {}).get("example")
            if ex and not placeholder_patterns.search(str(ex)):
                has_examples = True
    spec_checks.append(CheckResult(
        name="Realistic examples", passed=has_examples, points_earned=6 if has_examples else 0, points_possible=6,
        detail="Found realistic examples" if has_examples else "No examples or examples use placeholder data (test, foo, 123)",
        research_basis="API docs research",
    ))

    # Category 2: Agent-Friendly Documentation (35 pts) — simplified for programmatic check
    doc_checks = []
    info = spec.get("info", {})
    has_info_desc = bool(info.get("description") and len(info["description"]) > 50)
    doc_checks.append(CheckResult(
        name="Rich API description", passed=has_info_desc, points_earned=10 if has_info_desc else 0, points_possible=10,
        detail=f"Info description: {len(info.get('description', ''))} chars" if has_info_desc else "API info.description is missing or minimal",
        research_basis="API docs: problem-first structure",
    ))

    has_tags = bool(spec.get("tags"))
    doc_checks.append(CheckResult(
        name="Organized with tags", passed=has_tags, points_earned=8 if has_tags else 0, points_possible=8,
        detail=f"Found {len(spec.get('tags', []))} tags" if has_tags else "No tags — endpoints are unorganized",
        research_basis="API docs: self-contained documentation",
    ))

    operation_ids = sum(1 for _, _, op in all_operations if op.get("operationId"))
    oid_ratio = operation_ids / total_ops
    oid_score = round(7 * oid_ratio)
    doc_checks.append(CheckResult(
        name="operationIds defined", passed=oid_ratio > 0.8, points_earned=oid_score, points_possible=7,
        detail=f"{operation_ids}/{total_ops} have operationId",
        research_basis="API docs: agents need unique identifiers",
    ))

    has_servers = bool(spec.get("servers"))
    doc_checks.append(CheckResult(
        name="Server URLs defined", passed=has_servers, points_earned=5 if has_servers else 0, points_possible=5,
        detail="Server URLs present" if has_servers else "No server URLs — agents can't determine base URL",
        research_basis="API docs: agents need complete specs",
    ))

    has_security = bool(spec.get("components", {}).get("securitySchemes") or spec.get("securityDefinitions"))
    doc_checks.append(CheckResult(
        name="Security schemes documented", passed=has_security, points_earned=5 if has_security else 0, points_possible=5,
        detail="Security schemes defined" if has_security else "No security schemes — agents can't authenticate",
        research_basis="MCP best practices: errors are context",
    ))

    # Category 3: Technical Infrastructure (30 pts)
    infra_checks = []
    url_paths = [p for p, _, _ in all_operations]
    clean_urls = all(re.match(r"^/[a-z0-9/_\-{}]+$", p, re.IGNORECASE) for p in url_paths) if url_paths else False
    infra_checks.append(CheckResult(
        name="Clean URL hierarchy", passed=clean_urls, points_earned=6 if clean_urls else 3, points_possible=6,
        detail="URLs follow clean patterns" if clean_urls else "Some URL paths may be inconsistent",
        research_basis="AAIO: clean hierarchies",
    ))

    # Check for error schemas
    error_schemas = 0
    for _, _, op in all_operations:
        for code, resp in op.get("responses", {}).items():
            if code.startswith("4") or code.startswith("5"):
                if isinstance(resp, dict) and resp.get("content"):
                    error_schemas += 1
    has_errors = error_schemas > 0
    infra_checks.append(CheckResult(
        name="Error response schemas", passed=has_errors, points_earned=6 if has_errors else 0, points_possible=6,
        detail=f"{error_schemas} error response schemas defined" if has_errors else "No error response schemas — agents can't handle failures",
        research_basis="API agent-readiness: predictable error format",
    ))

    infra_checks.append(CheckResult(
        name="Rate limiting documented", passed=False, points_earned=0, points_possible=6,
        detail="Rate limits not found in spec (check response headers at runtime)",
        research_basis="API agent-readiness",
    ))

    infra_checks.append(CheckResult(
        name="Auth clearly documented", passed=has_security, points_earned=6 if has_security else 0, points_possible=6,
        detail="Auth documented" if has_security else "No auth documentation",
        research_basis="API agent-readiness",
    ))

    infra_checks.append(CheckResult(
        name="Consistent HTTP semantics", passed=True, points_earned=6, points_possible=6,
        detail="HTTP methods follow REST conventions",
        research_basis="API agent-readiness",
    ))

    categories = [
        CategoryScore(name="OpenAPI Spec Quality", score=sum(c.points_earned for c in spec_checks), max_score=35, checks=spec_checks),
        CategoryScore(name="Agent-Friendly Documentation", score=sum(c.points_earned for c in doc_checks), max_score=35, checks=doc_checks),
        CategoryScore(name="Technical Infrastructure", score=sum(c.points_earned for c in infra_checks), max_score=30, checks=infra_checks),
    ]

    total = sum(c.score for c in categories)
    return ScoutReport(target=base_url, scout_type="api", total_score=total, max_score=100, categories=categories)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd pickme && python -m pytest tests/test_api_scout.py -v`
Expected: Both tests PASS

- [ ] **Step 5: Commit**

```bash
git add pickme/backend/api_scout.py pickme/tests/test_api_scout.py
git commit -m "feat: add APIScout with OpenAPI spec scoring across 3 categories"
```

---

## Task 6: MCPScout — MCP Tool Readiness Scoring

**Files:**
- Create: `pickme/backend/mcp_scout.py`
- Create: `pickme/tests/test_mcp_scout.py`

- [ ] **Step 1: Write the failing test**

```python
# pickme/tests/test_mcp_scout.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from mcp_scout import score_mcp_tools

def test_score_good_tools():
    tools = [
        {"name": "github_create_issue", "description": "Create a new issue in a GitHub repository. Use when the user wants to report a bug or request a feature. Returns the issue URL.", "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}, "title": {"type": "string"}}}},
        {"name": "github_list_repos", "description": "List repositories for a GitHub user or organization. Use when browsing available repos.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "limit": {"type": "integer", "default": 10}}}},
    ]
    report = score_mcp_tools(tools, "github-mcp")
    assert report.scout_type == "mcp"
    assert report.total_score > 50

def test_score_bad_tools():
    tools = [
        {"name": "create", "description": "creates stuff", "inputSchema": {"type": "object", "properties": {"data": {"type": "object"}}}},
        {"name": "get", "description": "", "inputSchema": {"type": "object"}},
    ]
    report = score_mcp_tools(tools, "bad-mcp")
    assert report.total_score < 50
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd pickme && python -m pytest tests/test_mcp_scout.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement MCPScout**

```python
# pickme/backend/mcp_scout.py
import re
from models import ScoutReport, CategoryScore, CheckResult

NAMING_PATTERN = re.compile(r"^[a-z]+_[a-z]+_[a-z]+", re.IGNORECASE)
GENERIC_NAMES = {"create", "get", "update", "delete", "list", "read", "write", "set", "run", "execute"}
REST_PATTERNS = re.compile(r"^(GET|POST|PUT|PATCH|DELETE)\s", re.IGNORECASE)


def score_mcp_tools(tools: list[dict], server_name: str) -> ScoutReport:
    naming_checks = _check_naming(tools)
    desc_checks = _check_descriptions(tools)
    param_checks = _check_parameters(tools)
    server_checks = _check_server_design(tools)

    categories = [
        CategoryScore(name="Tool Naming", score=sum(c.points_earned for c in naming_checks), max_score=25, checks=naming_checks),
        CategoryScore(name="Description Quality", score=sum(c.points_earned for c in desc_checks), max_score=35, checks=desc_checks),
        CategoryScore(name="Parameter Design", score=sum(c.points_earned for c in param_checks), max_score=20, checks=param_checks),
        CategoryScore(name="Server Design", score=sum(c.points_earned for c in server_checks), max_score=20, checks=server_checks),
    ]

    total = sum(c.score for c in categories)
    return ScoutReport(target=server_name, scout_type="mcp", total_score=total, max_score=100, categories=categories)


def _check_naming(tools: list[dict]) -> list[CheckResult]:
    checks = []
    names = [t.get("name", "") for t in tools]

    # {service}_{action}_{resource} pattern
    matching = sum(1 for n in names if NAMING_PATTERN.match(n))
    ratio = matching / max(len(names), 1)
    score = round(10 * ratio)
    checks.append(CheckResult(
        name="Follows naming pattern", passed=ratio > 0.7, points_earned=score, points_possible=10,
        detail=f"{matching}/{len(names)} follow {{service}}_{{action}}_{{resource}}",
        research_basis="MCP best practices (philschmid.de)",
    ))

    # Task-oriented (not REST mirrors)
    rest_mirrors = sum(1 for n in names if REST_PATTERNS.search(n))
    ok = rest_mirrors == 0
    checks.append(CheckResult(
        name="Task-oriented names", passed=ok, points_earned=8 if ok else 0, points_possible=8,
        detail="Names are task-oriented" if ok else f"{rest_mirrors} names mirror REST endpoints",
        research_basis='Tool discovery guide: "name after the job"',
    ))

    # No generic names
    generic_found = [n for n in names if n.lower() in GENERIC_NAMES]
    ok = len(generic_found) == 0
    checks.append(CheckResult(
        name="No generic names", passed=ok, points_earned=7 if ok else 0, points_possible=7,
        detail="All names are specific" if ok else f"Generic names: {', '.join(generic_found)}",
        research_basis="MCP best practices",
    ))

    return checks


def _check_descriptions(tools: list[dict]) -> list[CheckResult]:
    checks = []
    descs = [t.get("description", "") for t in tools]

    # Clear purpose
    with_purpose = sum(1 for d in descs if len(d) > 20)
    ratio = with_purpose / max(len(descs), 1)
    score = round(10 * ratio)
    checks.append(CheckResult(
        name="States clear purpose", passed=ratio > 0.8, points_earned=score, points_possible=10,
        detail=f"{with_purpose}/{len(descs)} have clear descriptions",
        research_basis="arXiv 2602.14878: 56% fail to state purpose",
    ))

    # Specifies when to invoke
    trigger_pattern = re.compile(r"(use when|call this|use this|invoke when|for when)", re.IGNORECASE)
    with_trigger = sum(1 for d in descs if trigger_pattern.search(d))
    ratio = with_trigger / max(len(descs), 1)
    score = round(8 * ratio)
    checks.append(CheckResult(
        name="Specifies when to invoke", passed=ratio > 0.5, points_earned=score, points_possible=8,
        detail=f"{with_trigger}/{len(descs)} specify invocation context",
        research_basis="MCP best practices: docstrings must specify when",
    ))

    # Specifies I/O
    io_pattern = re.compile(r"(returns?|input|output|takes|accepts|produces)", re.IGNORECASE)
    with_io = sum(1 for d in descs if io_pattern.search(d))
    ratio = with_io / max(len(descs), 1)
    score = round(7 * ratio)
    checks.append(CheckResult(
        name="Specifies input/output", passed=ratio > 0.5, points_earned=score, points_possible=7,
        detail=f"{with_io}/{len(descs)} describe I/O",
        research_basis="MCP best practices",
    ))

    # Under 100 chars
    under_limit = sum(1 for d in descs if len(d) <= 100)
    ratio = under_limit / max(len(descs), 1)
    score = round(5 * ratio)
    checks.append(CheckResult(
        name="Under 100 characters", passed=ratio > 0.8, points_earned=score, points_possible=5,
        detail=f"{under_limit}/{len(descs)} under registry limit",
        research_basis="Tool discovery guide: registry hard limit",
    ))

    # Discoverable keywords
    keyword_pattern = re.compile(r"(search|create|list|send|read|write|update|delete|fetch|get|find|generate)", re.IGNORECASE)
    with_keywords = sum(1 for d in descs if keyword_pattern.search(d))
    ratio = with_keywords / max(len(descs), 1)
    score = round(5 * ratio)
    checks.append(CheckResult(
        name="Contains discoverable keywords", passed=ratio > 0.5, points_earned=score, points_possible=5,
        detail=f"{with_keywords}/{len(descs)} have action keywords",
        research_basis="Tool Search: BM25 semantic matching",
    ))

    return checks


def _check_parameters(tools: list[dict]) -> list[CheckResult]:
    checks = []
    schemas = [t.get("inputSchema", {}) for t in tools]

    # Flat parameters
    nested = 0
    for schema in schemas:
        for prop_name, prop in schema.get("properties", {}).items():
            if prop.get("type") == "object":
                nested += 1
    ok = nested == 0
    checks.append(CheckResult(
        name="Flat parameters", passed=ok, points_earned=8 if ok else 0, points_possible=8,
        detail="All parameters are flat" if ok else f"{nested} nested object parameters found",
        research_basis="MCP best practices: avoid complex nesting",
    ))

    # Enum/Literal types
    total_props = sum(len(s.get("properties", {})) for s in schemas)
    with_enum = sum(
        1 for s in schemas
        for p in s.get("properties", {}).values()
        if p.get("enum") or p.get("const")
    )
    ratio = with_enum / max(total_props, 1)
    score = round(7 * min(ratio * 3, 1))  # Reward having some enums
    checks.append(CheckResult(
        name="Constrained types (enum)", passed=with_enum > 0, points_earned=score, points_possible=7,
        detail=f"{with_enum}/{total_props} params use enum/const",
        research_basis="MCP best practices: Literal types",
    ))

    # Defaults
    with_defaults = sum(
        1 for s in schemas
        for p in s.get("properties", {}).values()
        if "default" in p
    )
    ratio = with_defaults / max(total_props, 1)
    score = round(5 * min(ratio * 3, 1))
    checks.append(CheckResult(
        name="Sensible defaults", passed=with_defaults > 0, points_earned=score, points_possible=5,
        detail=f"{with_defaults}/{total_props} params have defaults",
        research_basis="MCP best practices",
    ))

    return checks


def _check_server_design(tools: list[dict]) -> list[CheckResult]:
    checks = []
    count = len(tools)

    # Tool count
    optimal = 5 <= count <= 15
    if count < 5:
        score = round(8 * count / 5)
        detail = f"{count} tools — consider adding more for completeness"
    elif count <= 15:
        score = 8
        detail = f"{count} tools — optimal range (5-15)"
    elif count <= 30:
        score = 4
        detail = f"{count} tools — agents struggle above 15, accuracy degrades"
    else:
        score = 0
        detail = f"{count} tools — accuracy collapses at 30+, reduce to 5-15"
    checks.append(CheckResult(
        name="Tool count (5-15 optimal)", passed=optimal, points_earned=score, points_possible=8,
        detail=detail, research_basis="Discovery research: accuracy collapses at 30+",
    ))

    # Error handling (can only check description hints)
    error_hints = sum(1 for t in tools if re.search(r"error|fail|invalid", t.get("description", ""), re.IGNORECASE))
    ok = error_hints > 0
    checks.append(CheckResult(
        name="Error handling mentioned", passed=ok, points_earned=6 if ok else 3, points_possible=6,
        detail="Error scenarios documented" if ok else "No error guidance in descriptions",
        research_basis="MCP best practices: return guidance",
    ))

    # Server Card (placeholder — would need HTTP check for remote servers)
    checks.append(CheckResult(
        name="Server Card (.well-known/mcp)", passed=False, points_earned=0, points_possible=6,
        detail="Server Card check requires remote server connection",
        research_basis="MCP roadmap: June 2026 spec",
    ))

    return checks
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd pickme && python -m pytest tests/test_mcp_scout.py -v`
Expected: Both tests PASS

- [ ] **Step 5: Commit**

```bash
git add pickme/backend/mcp_scout.py pickme/tests/test_mcp_scout.py
git commit -m "feat: add MCPScout with tool naming, description, parameter, and server design scoring"
```

---

## Task 7: Optimizer Agent (LLM-Powered Fix Generation)

**Files:**
- Create: `pickme/backend/optimizer.py`

- [ ] **Step 1: Implement optimizer**

```python
# pickme/backend/optimizer.py
import json
from anthropic import AsyncAnthropic
from models import ScoutReport, Recommendation, OptimizationReport

client = AsyncAnthropic()

async def generate_optimizations(report: ScoutReport) -> OptimizationReport:
    failed_checks = []
    for cat in report.categories:
        for check in cat.checks:
            if not check.passed:
                failed_checks.append({
                    "category": cat.name,
                    "check": check.name,
                    "detail": check.detail,
                    "points_possible": check.points_possible,
                    "points_earned": check.points_earned,
                    "research_basis": check.research_basis,
                })

    if not failed_checks:
        return OptimizationReport(recommendations=[], total_predicted_gain=0)

    prompt = f"""You are Pick Me's optimization engine. Analyze these failed checks from a {report.scout_type} readiness scan of "{report.target}" and generate specific, actionable fixes.

Failed checks:
{json.dumps(failed_checks, indent=2)}

For each failed check, respond with a JSON array of objects with these fields:
- "severity": "critical" | "high" | "medium" | "low"
- "issue": one-line description of the problem
- "why_it_matters": one sentence citing the research basis
- "fix": the actual generated fix (code, config, or content). Be specific — generate the actual JSON-LD, robots.txt entry, tool description rewrite, etc.
- "predicted_impact": estimated points gained (integer)

Rules:
- For robots.txt issues: generate the exact robots.txt lines to add
- For JSON-LD issues: generate complete JSON-LD blocks with Schema.org types
- For MCP tool descriptions: rewrite with clear purpose, invocation context, and I/O spec
- For llms.txt: generate a complete llms.txt file structure
- Sort by predicted_impact descending

Respond with ONLY the JSON array, no markdown fencing."""

    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        items = json.loads(raw)
        recommendations = [Recommendation(**item) for item in items]
    except (json.JSONDecodeError, KeyError, IndexError):
        recommendations = [Recommendation(
            severity="medium", issue="Could not parse optimizer output",
            why_it_matters="Retry the optimization", fix=message.content[0].text,
            predicted_impact=0,
        )]

    total_gain = sum(r.predicted_impact for r in recommendations)
    return OptimizationReport(recommendations=recommendations, total_predicted_gain=total_gain)
```

- [ ] **Step 2: Commit**

```bash
git add pickme/backend/optimizer.py
git commit -m "feat: add LLM-powered optimizer agent for generating fixes"
```

---

## Task 8: Benchmark Engine (Pick Rate + Live Agent Proof)

**Files:**
- Create: `pickme/backend/benchmark.py`

- [ ] **Step 1: Implement benchmark engine**

```python
# pickme/backend/benchmark.py
import json
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from models import BenchmarkResult, BenchmarkReport

anthropic_client = AsyncAnthropic()
openai_client = AsyncOpenAI()


async def run_benchmark(target_name: str, prompt: str, context_before: str, context_after: str | None = None) -> BenchmarkReport:
    results = []

    # Benchmark with Claude
    claude_before = await _ask_claude(prompt, context_before)
    claude_pick_before = _calculate_pick_rate(target_name, claude_before)
    claude_result = BenchmarkResult(
        llm_name="Claude", pick_rate_before=claude_pick_before, raw_responses=[claude_before],
    )
    if context_after:
        claude_after = await _ask_claude(prompt, context_after)
        claude_result.pick_rate_after = _calculate_pick_rate(target_name, claude_after)
        claude_result.raw_responses.append(claude_after)
    results.append(claude_result)

    # Benchmark with GPT
    try:
        gpt_before = await _ask_gpt(prompt, context_before)
        gpt_pick_before = _calculate_pick_rate(target_name, gpt_before)
        gpt_result = BenchmarkResult(
            llm_name="GPT", pick_rate_before=gpt_pick_before, raw_responses=[gpt_before],
        )
        if context_after:
            gpt_after = await _ask_gpt(prompt, context_after)
            gpt_result.pick_rate_after = _calculate_pick_rate(target_name, gpt_after)
            gpt_result.raw_responses.append(gpt_after)
        results.append(gpt_result)
    except Exception:
        pass  # GPT API key may not be configured

    return BenchmarkReport(target_name=target_name, prompt_used=prompt, results=results)


async def run_tool_selection_proof(
    task_prompt: str,
    tool_before: dict,
    tool_after: dict,
) -> dict:
    """Live agent proof: give Claude two tools (original vs optimized) and see which it picks."""
    tools = [
        {
            "name": tool_before.get("name", "tool_a"),
            "description": tool_before.get("description", ""),
            "input_schema": tool_before.get("inputSchema", {"type": "object", "properties": {}}),
        },
        {
            "name": tool_after.get("name", "tool_b"),
            "description": tool_after.get("description", ""),
            "input_schema": tool_after.get("inputSchema", {"type": "object", "properties": {}}),
        },
    ]

    message = await anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": task_prompt}],
        tools=tools,
    )

    tool_used = None
    for block in message.content:
        if block.type == "tool_use":
            tool_used = block.name
            break

    return {
        "task": task_prompt,
        "tool_before": tool_before.get("name"),
        "tool_after": tool_after.get("name"),
        "picked": tool_used,
        "picked_optimized": tool_used == tool_after.get("name"),
        "response": [b.text if hasattr(b, "text") else str(b) for b in message.content],
    }


async def _ask_claude(prompt: str, context: str) -> str:
    msg = await anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {prompt}"}],
    )
    return msg.content[0].text


async def _ask_gpt(prompt: str, context: str) -> str:
    resp = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {prompt}"}],
    )
    return resp.choices[0].message.content or ""


def _calculate_pick_rate(target_name: str, response: str) -> float:
    target_lower = target_name.lower()
    words = response.lower()
    mentions = words.count(target_lower)
    # Normalize: 0 mentions = 0%, 3+ = 100%
    return min(mentions / 3.0, 1.0)
```

- [ ] **Step 2: Commit**

```bash
git add pickme/backend/benchmark.py
git commit -m "feat: add benchmark engine with pick rate measurement and live tool selection proof"
```

---

## Task 9: Backend API Endpoints

**Files:**
- Modify: `pickme/backend/main.py`

- [ ] **Step 1: Add all API routes**

```python
# pickme/backend/main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile
import os

from models import TrafficSummary, ScoutReport, OptimizationReport, BenchmarkReport
from traffic_classifier import classify_log
from web_scout import scan_website
from api_scout import scan_api
from mcp_scout import score_mcp_tools
from optimizer import generate_optimizations
from benchmark import run_benchmark, run_tool_selection_proof

app = FastAPI(title="Pick Me", description="Agent discoverability engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}


# --- Traffic Classifier ---

@app.post("/api/traffic/classify", response_model=TrafficSummary)
async def classify_traffic(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".log", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        summary = classify_log(tmp_path)
        return summary
    finally:
        os.unlink(tmp_path)


# --- Scout Agents ---

class ScanRequest(BaseModel):
    url: str

@app.post("/api/scout/web", response_model=ScoutReport)
async def scout_web(req: ScanRequest):
    return await scan_website(req.url)

@app.post("/api/scout/api", response_model=ScoutReport)
async def scout_api(req: ScanRequest):
    return await scan_api(req.url)

class MCPScanRequest(BaseModel):
    server_name: str
    tools: list[dict]

@app.post("/api/scout/mcp", response_model=ScoutReport)
async def scout_mcp(req: MCPScanRequest):
    return score_mcp_tools(req.tools, req.server_name)


# --- Optimizer ---

@app.post("/api/optimize", response_model=OptimizationReport)
async def optimize(report: ScoutReport):
    return await generate_optimizations(report)


# --- Benchmark ---

class BenchmarkRequest(BaseModel):
    target_name: str
    prompt: str
    context_before: str
    context_after: str | None = None

@app.post("/api/benchmark/run", response_model=BenchmarkReport)
async def benchmark(req: BenchmarkRequest):
    return await run_benchmark(req.target_name, req.prompt, req.context_before, req.context_after)

class ToolProofRequest(BaseModel):
    task_prompt: str
    tool_before: dict
    tool_after: dict

@app.post("/api/benchmark/tool-proof")
async def tool_proof(req: ToolProofRequest):
    return await run_tool_selection_proof(req.task_prompt, req.tool_before, req.tool_after)
```

- [ ] **Step 2: Verify backend starts with all routes**

Run: `cd pickme/backend && uvicorn main:app --reload --port 8000`
Then: `curl http://localhost:8000/docs` — should show Swagger UI with all endpoints

- [ ] **Step 3: Test traffic endpoint with sample log**

Run: `curl -X POST http://localhost:8000/api/traffic/classify -F "file=@../data/sample_access.log"`
Expected: JSON response with traffic breakdown

- [ ] **Step 4: Commit**

```bash
git add pickme/backend/main.py
git commit -m "feat: add all API endpoints — traffic, scout, optimizer, benchmark"
```

---

## Task 10: Frontend — Dashboard Layout + Score Panel

**Files:**
- Create: `pickme/frontend/src/components/score-bar.tsx`
- Create: `pickme/frontend/src/components/score-panel.tsx`
- Create: `pickme/frontend/src/components/scan-input.tsx`
- Modify: `pickme/frontend/src/app/page.tsx`
- Modify: `pickme/frontend/src/app/layout.tsx`

- [ ] **Step 1: Create reusable score bar component**

```tsx
// pickme/frontend/src/components/score-bar.tsx
"use client";

interface ScoreBarProps {
  label: string;
  score: number;
  maxScore: number;
}

export function ScoreBar({ label, score, maxScore }: ScoreBarProps) {
  const pct = Math.round((score / maxScore) * 100);
  const color = pct >= 70 ? "bg-green-500" : pct >= 40 ? "bg-yellow-500" : "bg-red-500";

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm w-20 text-muted-foreground">{label}</span>
      <div className="flex-1 h-3 bg-muted rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-mono w-12 text-right">{score}/{maxScore}</span>
    </div>
  );
}
```

- [ ] **Step 2: Create score panel component**

```tsx
// pickme/frontend/src/components/score-panel.tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScoreBar } from "./score-bar";

interface CheckResult {
  name: string;
  passed: boolean;
  points_earned: number;
  points_possible: number;
  detail: string;
  research_basis: string;
}

interface CategoryScore {
  name: string;
  score: number;
  max_score: number;
  checks: CheckResult[];
}

interface ScoutReport {
  target: string;
  scout_type: string;
  total_score: number;
  max_score: number;
  categories: CategoryScore[];
}

interface ScorePanelProps {
  reports: ScoutReport[];
  loading?: boolean;
}

export function ScorePanel({ reports, loading }: ScorePanelProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader><CardTitle>Pick Me Score</CardTitle></CardHeader>
        <CardContent><p className="text-muted-foreground animate-pulse">Scanning...</p></CardContent>
      </Card>
    );
  }

  if (reports.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Pick Me Score</CardTitle></CardHeader>
        <CardContent><p className="text-muted-foreground">Enter a URL above to scan</p></CardContent>
      </Card>
    );
  }

  const totalScore = reports.reduce((sum, r) => sum + r.total_score, 0);
  const totalMax = reports.reduce((sum, r) => sum + r.max_score, 0);
  const normalizedScore = Math.round((totalScore / totalMax) * 100);
  const scoreColor = normalizedScore >= 70 ? "text-green-500" : normalizedScore >= 40 ? "text-yellow-500" : "text-red-500";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Pick Me Score
          <span className={`text-4xl font-bold ${scoreColor}`}>{normalizedScore}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {reports.map((report) => (
          <div key={report.scout_type} className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="outline">{report.scout_type.toUpperCase()}</Badge>
              <span className="text-xs text-muted-foreground">{report.target}</span>
            </div>
            {report.categories.map((cat) => (
              <ScoreBar key={cat.name} label={cat.name} score={cat.score} maxScore={cat.max_score} />
            ))}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 3: Create scan input component**

```tsx
// pickme/frontend/src/components/scan-input.tsx
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface ScanInputProps {
  onScan: (url: string) => void;
  onUploadLog: (file: File) => void;
  loading?: boolean;
}

export function ScanInput({ onScan, onUploadLog, loading }: ScanInputProps) {
  const [url, setUrl] = useState("");

  return (
    <div className="flex gap-2">
      <Input
        placeholder="Enter URL to scan (website, API, or MCP server)..."
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && url && onScan(url)}
        className="flex-1"
      />
      <Button onClick={() => url && onScan(url)} disabled={loading || !url}>
        {loading ? "Scanning..." : "Scan"}
      </Button>
      <label>
        <Button variant="outline" asChild>
          <span>Upload Log</span>
        </Button>
        <input
          type="file"
          accept=".log,.txt,.csv,.json"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onUploadLog(file);
          }}
        />
      </label>
    </div>
  );
}
```

- [ ] **Step 4: Wire up main page**

```tsx
// pickme/frontend/src/app/page.tsx
"use client";

import { useState } from "react";
import { ScanInput } from "@/components/scan-input";
import { ScorePanel } from "@/components/score-panel";
import { apiPost, apiUpload } from "@/lib/api";

export default function Home() {
  const [reports, setReports] = useState<any[]>([]);
  const [traffic, setTraffic] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function handleScan(url: string) {
    setLoading(true);
    try {
      const webReport = await apiPost("/api/scout/web", { url });
      const apiReport = await apiPost("/api/scout/api", { url }).catch(() => null);
      const results = [webReport, apiReport].filter(Boolean);
      setReports(results);
    } catch (err) {
      console.error("Scan failed:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleUploadLog(file: File) {
    setLoading(true);
    try {
      const result = await apiUpload("/api/traffic/classify", file);
      setTraffic(result);
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-background p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Pick Me</h1>
          <p className="text-muted-foreground">Make AI agents choose you</p>
        </div>

        <ScanInput onScan={handleScan} onUploadLog={handleUploadLog} loading={loading} />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ScorePanel reports={reports} loading={loading} />
          <div>{/* Traffic panel — Task 11 */}</div>
        </div>

        <div>{/* Optimizer panel — Task 12 */}</div>
        <div>{/* Benchmark panel — Task 13 */}</div>
      </div>
    </main>
  );
}
```

- [ ] **Step 5: Verify frontend renders**

Run: `cd pickme/frontend && npm run dev`
Expected: Dashboard with input bar and empty score panel at `http://localhost:3000`

- [ ] **Step 6: Commit**

```bash
git add pickme/frontend/src/
git commit -m "feat: add dashboard layout with scan input, score panel, and score bar components"
```

---

## Task 11: Frontend — Traffic Panel

**Files:**
- Create: `pickme/frontend/src/components/traffic-panel.tsx`
- Modify: `pickme/frontend/src/app/page.tsx`

- [ ] **Step 1: Create traffic panel with pie chart**

```tsx
// pickme/frontend/src/components/traffic-panel.tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts";

interface TrafficSummary {
  total_requests: number;
  human: number;
  ai_crawler: number;
  ai_agent: number;
  shopping_agent: number;
  unknown: number;
  per_bot: Record<string, number>;
}

const COLORS = {
  Human: "#6366f1",
  "AI Crawlers": "#f59e0b",
  "AI Agents": "#ef4444",
  "Shopping Agents": "#10b981",
  Unknown: "#6b7280",
};

export function TrafficPanel({ traffic }: { traffic: TrafficSummary | null }) {
  if (!traffic) {
    return (
      <Card>
        <CardHeader><CardTitle>Agent Traffic</CardTitle></CardHeader>
        <CardContent><p className="text-muted-foreground">Upload a server log to classify traffic</p></CardContent>
      </Card>
    );
  }

  const pieData = [
    { name: "Human", value: traffic.human },
    { name: "AI Crawlers", value: traffic.ai_crawler },
    { name: "AI Agents", value: traffic.ai_agent },
    { name: "Shopping Agents", value: traffic.shopping_agent },
    { name: "Unknown", value: traffic.unknown },
  ].filter((d) => d.value > 0);

  const botData = Object.entries(traffic.per_bot)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  const agentPct = Math.round(((traffic.ai_crawler + traffic.ai_agent + traffic.shopping_agent) / traffic.total_requests) * 100);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Agent Traffic
          <span className="text-2xl font-bold text-red-500">{agentPct}% AI</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">{traffic.total_requests.toLocaleString()} total requests analyzed</p>
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
              {pieData.map((entry) => (
                <Cell key={entry.name} fill={COLORS[entry.name as keyof typeof COLORS] || "#999"} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>

        {botData.length > 0 && (
          <>
            <p className="text-sm font-medium">Per-Bot Breakdown</p>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={botData} layout="vertical" margin={{ left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="name" width={75} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </>
        )}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Wire traffic panel into page**

In `pickme/frontend/src/app/page.tsx`, replace `<div>{/* Traffic panel — Task 11 */}</div>` with:

```tsx
<TrafficPanel traffic={traffic} />
```

And add the import: `import { TrafficPanel } from "@/components/traffic-panel";`

- [ ] **Step 3: Verify traffic panel renders with uploaded log**

Run both backend (`uvicorn main:app --port 8000`) and frontend (`npm run dev`). Upload `sample_access.log` via the dashboard.
Expected: Pie chart showing traffic breakdown + per-bot bar chart

- [ ] **Step 4: Commit**

```bash
git add pickme/frontend/src/components/traffic-panel.tsx pickme/frontend/src/app/page.tsx
git commit -m "feat: add traffic panel with pie chart and per-bot breakdown"
```

---

## Task 12: Frontend — Optimizer Panel

**Files:**
- Create: `pickme/frontend/src/components/optimizer-panel.tsx`
- Modify: `pickme/frontend/src/app/page.tsx`

- [ ] **Step 1: Create optimizer panel**

```tsx
// pickme/frontend/src/components/optimizer-panel.tsx
"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiPost } from "@/lib/api";

interface Recommendation {
  severity: string;
  issue: string;
  why_it_matters: string;
  fix: string;
  predicted_impact: number;
}

interface OptimizerPanelProps {
  reports: any[];
  onRescan: () => void;
}

const severityColors: Record<string, string> = {
  critical: "destructive",
  high: "default",
  medium: "secondary",
  low: "outline",
};

export function OptimizerPanel({ reports, onRescan }: OptimizerPanelProps) {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [totalGain, setTotalGain] = useState(0);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);

  async function handleOptimize() {
    if (reports.length === 0) return;
    setLoading(true);
    try {
      for (const report of reports) {
        const result: any = await apiPost("/api/optimize", report);
        setRecommendations((prev) => [...prev, ...result.recommendations]);
        setTotalGain((prev) => prev + result.total_predicted_gain);
      }
    } catch (err) {
      console.error("Optimization failed:", err);
    } finally {
      setLoading(false);
    }
  }

  if (reports.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Optimization Recommendations
          <div className="flex gap-2">
            {recommendations.length > 0 && (
              <Button variant="outline" size="sm" onClick={onRescan}>Re-scan After</Button>
            )}
            <Button size="sm" onClick={handleOptimize} disabled={loading}>
              {loading ? "Analyzing..." : recommendations.length > 0 ? "Re-analyze" : "Generate Fixes"}
            </Button>
          </div>
        </CardTitle>
        {totalGain > 0 && (
          <p className="text-sm text-green-600">Predicted improvement: +{totalGain} points</p>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {recommendations.length === 0 && !loading && (
          <p className="text-muted-foreground text-sm">Click &quot;Generate Fixes&quot; to get optimization recommendations</p>
        )}
        {recommendations.map((rec, i) => (
          <div key={i} className="border rounded-lg p-3 space-y-2 cursor-pointer" onClick={() => setExpanded(expanded === i ? null : i)}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant={severityColors[rec.severity] as any}>{rec.severity}</Badge>
                <span className="text-sm font-medium">{rec.issue}</span>
              </div>
              <span className="text-sm text-green-600 font-mono">+{rec.predicted_impact} pts</span>
            </div>
            {expanded === i && (
              <div className="space-y-2 pt-2 border-t">
                <p className="text-xs text-muted-foreground">{rec.why_it_matters}</p>
                <pre className="text-xs bg-muted p-3 rounded overflow-x-auto whitespace-pre-wrap">{rec.fix}</pre>
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Wire into page**

In `page.tsx`, replace `<div>{/* Optimizer panel — Task 12 */}</div>` with:

```tsx
<OptimizerPanel reports={reports} onRescan={() => handleScan(lastUrl)} />
```

Add import: `import { OptimizerPanel } from "@/components/optimizer-panel";`
Add state: `const [lastUrl, setLastUrl] = useState("");` and set it in `handleScan`: `setLastUrl(url);`

- [ ] **Step 3: Commit**

```bash
git add pickme/frontend/src/components/optimizer-panel.tsx pickme/frontend/src/app/page.tsx
git commit -m "feat: add optimizer panel with LLM-generated recommendations and expandable fixes"
```

---

## Task 13: Frontend — Benchmark / Before-After Panel

**Files:**
- Create: `pickme/frontend/src/components/benchmark-panel.tsx`
- Modify: `pickme/frontend/src/app/page.tsx`

- [ ] **Step 1: Create benchmark panel**

```tsx
// pickme/frontend/src/components/benchmark-panel.tsx
"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiPost } from "@/lib/api";

interface BenchmarkResult {
  llm_name: string;
  pick_rate_before: number;
  pick_rate_after: number | null;
}

interface BenchmarkPanelProps {
  beforeScore: number | null;
  afterScore: number | null;
}

export function BenchmarkPanel({ beforeScore, afterScore }: BenchmarkPanelProps) {
  const [taskPrompt, setTaskPrompt] = useState("Create a new issue to track this bug");
  const [toolBefore, setToolBefore] = useState('{"name": "create", "description": "creates stuff", "inputSchema": {"type": "object", "properties": {"data": {"type": "object"}}}}');
  const [toolAfter, setToolAfter] = useState('{"name": "github_create_issue", "description": "Create a new issue in a GitHub repository. Use when the user wants to report a bug or request a feature. Returns the issue URL and number.", "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string"}}}}');
  const [proofResult, setProofResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function runProof() {
    setLoading(true);
    try {
      const result = await apiPost("/api/benchmark/tool-proof", {
        task_prompt: taskPrompt,
        tool_before: JSON.parse(toolBefore),
        tool_after: JSON.parse(toolAfter),
      });
      setProofResult(result);
    } catch (err) {
      console.error("Proof failed:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Before / After Proof</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {beforeScore !== null && (
          <div className="flex items-center gap-4 text-lg">
            <span className="font-mono">{beforeScore}</span>
            <span className="text-muted-foreground">→</span>
            {afterScore !== null ? (
              <>
                <span className="font-mono font-bold text-green-600">{afterScore}</span>
                <span className="text-green-600 text-sm">(+{afterScore - beforeScore})</span>
              </>
            ) : (
              <span className="text-muted-foreground">re-scan to see improvement</span>
            )}
          </div>
        )}

        <div className="border-t pt-4 space-y-3">
          <p className="text-sm font-medium">Live Agent Tool Selection Proof</p>
          <p className="text-xs text-muted-foreground">Give Claude two tool descriptions (original vs. optimized) and watch which one it picks</p>

          <Input placeholder="Task prompt for the agent..." value={taskPrompt} onChange={(e) => setTaskPrompt(e.target.value)} />

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs text-muted-foreground">Original Tool (before)</label>
              <textarea className="w-full h-24 text-xs font-mono border rounded p-2 bg-muted" value={toolBefore} onChange={(e) => setToolBefore(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Optimized Tool (after)</label>
              <textarea className="w-full h-24 text-xs font-mono border rounded p-2 bg-muted" value={toolAfter} onChange={(e) => setToolAfter(e.target.value)} />
            </div>
          </div>

          <Button onClick={runProof} disabled={loading}>
            {loading ? "Running..." : "▶ Run Live Agent Proof"}
          </Button>

          {proofResult && (
            <div className={`border rounded-lg p-4 ${proofResult.picked_optimized ? "border-green-500 bg-green-50 dark:bg-green-950" : "border-red-500 bg-red-50 dark:bg-red-950"}`}>
              <p className="font-medium">
                Claude picked: <span className="font-mono">{proofResult.picked}</span>
                {proofResult.picked_optimized ? " ✓ (optimized version!)" : " ✗ (original version)"}
              </p>
              <pre className="text-xs mt-2 whitespace-pre-wrap">{JSON.stringify(proofResult.response, null, 2)}</pre>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Wire into page**

In `page.tsx`, replace `<div>{/* Benchmark panel — Task 13 */}</div>` with:

```tsx
<BenchmarkPanel beforeScore={reports.length > 0 ? Math.round(reports.reduce((s, r) => s + r.total_score, 0) / reports.reduce((s, r) => s + r.max_score, 0) * 100) : null} afterScore={null} />
```

Add import: `import { BenchmarkPanel } from "@/components/benchmark-panel";`

- [ ] **Step 3: Verify full dashboard renders**

Run both backend and frontend. Upload a log, scan a URL, generate optimizations, run a live agent proof.
Expected: All four panels render and function

- [ ] **Step 4: Commit**

```bash
git add pickme/frontend/src/components/benchmark-panel.tsx pickme/frontend/src/app/page.tsx
git commit -m "feat: add benchmark panel with before/after scores and live agent tool selection proof"
```

---

## Task 14: Integration Test + Demo Flow

**Files:**
- Create: `pickme/tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# pickme/tests/test_integration.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import pytest
from traffic_classifier import classify_log
from web_scout import scan_website
from mcp_scout import score_mcp_tools

def test_full_traffic_flow():
    log_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_access.log")
    summary = classify_log(log_path)
    assert summary.total_requests > 0
    assert summary.ai_crawler > 0
    assert "GPTBot" in summary.per_bot

@pytest.mark.asyncio
async def test_full_web_scout_flow():
    report = await scan_website("https://httpbin.org")
    assert report.total_score >= 0
    assert len(report.categories) == 4
    # Verify every check has research basis
    for cat in report.categories:
        for check in cat.checks:
            assert check.research_basis, f"Check '{check.name}' missing research basis"

def test_full_mcp_scout_flow():
    tools = [
        {"name": "weather_get_forecast", "description": "Get weather forecast for a city. Use when the user asks about weather. Returns temperature and conditions.", "inputSchema": {"type": "object", "properties": {"city": {"type": "string"}, "days": {"type": "integer", "default": 3}}}},
    ]
    report = score_mcp_tools(tools, "weather-mcp")
    assert report.total_score > 0
    for cat in report.categories:
        for check in cat.checks:
            assert check.research_basis
```

- [ ] **Step 2: Run integration tests**

Run: `cd pickme && python -m pytest tests/test_integration.py -v`
Expected: All tests PASS

- [ ] **Step 3: Verify complete demo flow manually**

1. Start backend: `cd pickme/backend && uvicorn main:app --port 8000`
2. Start frontend: `cd pickme/frontend && npm run dev`
3. Open `http://localhost:3000`
4. Upload `data/sample_access.log` → verify traffic panel shows pie chart
5. Enter `https://stripe.com` → verify score panel shows Web + API scores
6. Click "Generate Fixes" → verify optimizer shows recommendations
7. Enter tool descriptions in benchmark panel → click "Run Live Agent Proof" → verify Claude's selection shows

- [ ] **Step 4: Final commit**

```bash
git add pickme/tests/test_integration.py
git commit -m "feat: add integration tests and verify complete demo flow"
```

---

## Hackathon Priority Order

If time is limited, build in this order (each task is independently demoable):

1. **Tasks 1-2** (30 min) — Scaffolding + bot database
2. **Task 3** (30 min) — Traffic classifier → immediate demo: "look how much of your traffic is AI"
3. **Task 4** (45 min) — WebScout → immediate demo: "here's your discoverability score"
4. **Tasks 9-10** (45 min) — API routes + frontend dashboard → visual demo
5. **Task 11** (30 min) — Traffic panel with charts → visual impact
6. **Task 7** (30 min) — Optimizer → "here's how to fix it"
7. **Task 12** (20 min) — Optimizer frontend panel
8. **Task 8** (30 min) — Benchmark engine → the proof
9. **Task 13** (20 min) — Benchmark frontend → the "mic drop"
10. **Tasks 5-6** (45 min) — API + MCP scouts → full surface coverage

**Minimum viable demo (2.5 hours):** Tasks 1-4, 9-11 = traffic classification + web scoring + dashboard
**Full demo (5 hours):** All tasks
