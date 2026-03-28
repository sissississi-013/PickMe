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
