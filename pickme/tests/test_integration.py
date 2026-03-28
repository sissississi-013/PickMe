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
