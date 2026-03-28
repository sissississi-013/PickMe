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
