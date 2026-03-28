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
