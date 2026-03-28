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
