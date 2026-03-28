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

class DiscoveryBenchmarkResult(BaseModel):
    target_tool_name: str
    task_prompt: str
    num_distractors: int
    discovered: bool
    selected: bool
    invoked_correctly: bool
    discovery_rank: int | None = None  # position in search results
    competing_tools: list[str] = []
    raw_response: list[str] = []

class DiscoveryBenchmarkReport(BaseModel):
    before: DiscoveryBenchmarkResult
    after: DiscoveryBenchmarkResult | None = None
    optimized_description: str | None = None
    discovery_improvement: str | None = None

class BotAccessEntry(BaseModel):
    name: str
    operator: str
    category: str
    allowed: bool
    market_share: float  # for weighting in visibility calc

class SignalFinding(BaseModel):
    name: str
    status: str  # "found" | "missing" | "partial"
    value: str
    consequence: str
    impact: str  # "critical" | "high" | "medium" | "low"

class DiscoveryReport(BaseModel):
    url: str
    robots_txt_found: bool
    robots_txt_raw: str | None = None
    bot_access: list[BotAccessEntry]
    bots_allowed: int
    bots_blocked: int
    llms_txt_found: bool
    llms_txt_length: int = 0
    llms_txt_preview: str | None = None
    sitemap_found: bool
    sitemap_url_count: int | None = None
    is_ssr: bool
    structured_data_types: list[str] = []
    ai_visibility_pct: int
    page_title: str | None = None
    word_count: int = 0
    # New: deeper analysis
    markdown_preview: str | None = None  # what agents actually see
    markdown_token_count: int = 0
    content_quality: list[SignalFinding] = []
    signals: list[SignalFinding] = []
