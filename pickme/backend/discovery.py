import re
import httpx
import extruct
from urllib.robotparser import RobotFileParser
from io import StringIO
from models import BotAccessEntry, DiscoveryReport
from bot_db import KNOWN_BOTS

# Market share weights (based on research: OpenAI 69%, Meta 16%, Anthropic 11%)
MARKET_SHARE = {
    "OpenAI": 0.69,
    "Meta": 0.16,
    "Anthropic": 0.11,
    "Perplexity": 0.02,
    "Apple": 0.01,
    "ByteDance": 0.005,
    "Common Crawl": 0.005,
    "DuckDuckGo": 0.005,
    "Google": 0.0,  # Googlebot is search, not AI agent ecosystem
    "Microsoft": 0.0,  # Bingbot is search
    "You.com": 0.005,
}


async def discover_url(url: str) -> DiscoveryReport:
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        # Fetch all resources in parallel-ish
        main_resp = await client.get(url)
        html = main_resp.text
        base_url = str(main_resp.url).rstrip("/")

        robots_txt = await _fetch_text(client, f"{base_url}/robots.txt")
        llms_txt = await _fetch_text(client, f"{base_url}/llms.txt")
        sitemap_txt = await _fetch_text(client, f"{base_url}/sitemap.xml")

    # Parse robots.txt for each known bot
    bot_access = _check_bot_access(robots_txt, base_url)

    # llms.txt
    llms_found = llms_txt is not None and len(llms_txt.strip()) > 10
    llms_preview = llms_txt[:500] if llms_found else None

    # Sitemap
    sitemap_found = sitemap_txt is not None and "<urlset" in (sitemap_txt or "")
    sitemap_count = None
    if sitemap_found and sitemap_txt:
        sitemap_count = len(re.findall(r"<loc>", sitemap_txt))

    # Page content analysis
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    word_count = len(text.split())
    is_ssr = word_count > 100

    # Title
    title_match = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
    page_title = title_match.group(1).strip() if title_match else None

    # Structured data
    try:
        metadata = extruct.extract(html, base_url=base_url, errors="ignore")
        jsonld = metadata.get("json-ld", [])
        sd_types = set()
        for item in jsonld:
            t = item.get("@type", "")
            if isinstance(t, list):
                sd_types.update(t)
            else:
                sd_types.add(t)
        sd_types.discard("")
    except Exception:
        sd_types = set()

    # AI Visibility percentage
    bots_allowed = sum(1 for b in bot_access if b.allowed)
    bots_blocked = sum(1 for b in bot_access if not b.allowed)

    # Weighted visibility: bot access (40%), llms.txt (20%), sitemap (15%), SSR (15%), structured data (10%)
    weighted_bot_access = sum(b.market_share for b in bot_access if b.allowed)
    total_market = sum(b.market_share for b in bot_access)
    bot_score = (weighted_bot_access / total_market * 100) if total_market > 0 else 50

    visibility = (
        bot_score * 0.40
        + (100 if llms_found else 0) * 0.20
        + (100 if sitemap_found else 0) * 0.15
        + (100 if is_ssr else 0) * 0.15
        + (min(len(sd_types) * 25, 100)) * 0.10
    )

    return DiscoveryReport(
        url=url,
        robots_txt_found=robots_txt is not None,
        robots_txt_raw=robots_txt[:2000] if robots_txt else None,
        bot_access=bot_access,
        bots_allowed=bots_allowed,
        bots_blocked=bots_blocked,
        llms_txt_found=llms_found,
        llms_txt_length=len(llms_txt) if llms_txt else 0,
        llms_txt_preview=llms_preview,
        sitemap_found=sitemap_found,
        sitemap_url_count=sitemap_count,
        is_ssr=is_ssr,
        structured_data_types=sorted(sd_types),
        ai_visibility_pct=round(visibility),
        page_title=page_title,
        word_count=word_count,
    )


def _check_bot_access(robots_txt: str | None, base_url: str) -> list[BotAccessEntry]:
    entries = []
    for bot in KNOWN_BOTS:
        operator = bot.operator
        share = MARKET_SHARE.get(operator, 0.005)

        if robots_txt is None:
            # No robots.txt = all allowed
            entries.append(BotAccessEntry(
                name=bot.name, operator=operator, category=bot.category,
                allowed=True, market_share=share,
            ))
            continue

        # Use RobotFileParser for proper parsing
        rp = RobotFileParser()
        rp.parse(robots_txt.splitlines())
        allowed = rp.can_fetch(bot.name, base_url + "/")

        entries.append(BotAccessEntry(
            name=bot.name, operator=operator, category=bot.category,
            allowed=allowed, market_share=share,
        ))

    return entries


async def _fetch_text(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        resp = await client.get(url)
        return resp.text if resp.status_code == 200 else None
    except Exception:
        return None
