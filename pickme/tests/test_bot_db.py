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
