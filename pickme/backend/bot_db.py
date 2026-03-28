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
