import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import pytest
from api_scout import scan_api, score_openapi_spec

@pytest.mark.asyncio
async def test_scan_petstore():
    report = await scan_api("https://petstore3.swagger.io")
    assert report.scout_type == "api"
    assert 0 <= report.total_score <= 100
    assert len(report.categories) >= 1
    category_names = [c.name for c in report.categories]
    assert "OpenAPI Spec Quality" in category_names

def test_score_openapi_spec_dict():
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
