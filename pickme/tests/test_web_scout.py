import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import pytest
from web_scout import scan_website

@pytest.mark.asyncio
async def test_scan_real_website():
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
