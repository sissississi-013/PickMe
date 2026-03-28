import re
import httpx
import extruct
from urllib.robotparser import RobotFileParser
from models import BotAccessEntry, DiscoveryReport, SignalFinding
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
    "Google": 0.0,
    "Microsoft": 0.0,
    "You.com": 0.005,
}


async def discover_url(url: str) -> DiscoveryReport:
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        main_resp = await client.get(url)
        html = main_resp.text
        base_url = str(main_resp.url).rstrip("/")

        robots_txt = await _fetch_text(client, f"{base_url}/robots.txt")
        llms_txt = await _fetch_text(client, f"{base_url}/llms.txt")
        sitemap_txt = await _fetch_text(client, f"{base_url}/sitemap.xml")

    # Bot access
    bot_access = _check_bot_access(robots_txt, base_url)

    # llms.txt
    llms_found = llms_txt is not None and len(llms_txt.strip()) > 10
    llms_preview = llms_txt[:500] if llms_found else None

    # Sitemap
    sitemap_found = sitemap_txt is not None and ("<urlset" in (sitemap_txt or "") or "<sitemapindex" in (sitemap_txt or ""))
    sitemap_count = None
    if sitemap_found and sitemap_txt:
        sitemap_count = len(re.findall(r"<loc>", sitemap_txt))

    # Content analysis
    text = _html_to_text(html)
    word_count = len(text.split())
    is_ssr = word_count > 100

    # Markdown preview (what agents actually see)
    markdown = _html_to_markdown(html)
    markdown_preview = markdown[:2000] if markdown else None
    markdown_tokens = len(markdown.split()) if markdown else 0

    # Title
    title_match = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
    page_title = title_match.group(1).strip() if title_match else None

    # Structured data
    sd_types = set()
    try:
        metadata = extruct.extract(html, base_url=base_url, errors="ignore")
        jsonld = metadata.get("json-ld", [])
        for item in jsonld:
            t = item.get("@type", "")
            if isinstance(t, list):
                sd_types.update(t)
            else:
                sd_types.add(t)
        sd_types.discard("")
    except Exception:
        pass

    # AI Visibility
    bots_allowed = sum(1 for b in bot_access if b.allowed)
    bots_blocked = sum(1 for b in bot_access if not b.allowed)

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

    # Build signal findings with consequences
    signals = _build_signals(robots_txt, bot_access, llms_found, llms_txt, sitemap_found, sitemap_count, is_ssr)

    # Build content quality findings
    content_quality = _build_content_quality(html, text, word_count, sd_types, main_resp.headers)

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
        markdown_preview=markdown_preview,
        markdown_token_count=markdown_tokens,
        content_quality=content_quality,
        signals=signals,
    )


def _build_signals(robots_txt, bot_access, llms_found, llms_txt, sitemap_found, sitemap_count, is_ssr) -> list[SignalFinding]:
    signals = []

    # robots.txt
    blocked = [b.name for b in bot_access if not b.allowed]
    blocked_share = sum(b.market_share for b in bot_access if not b.allowed)
    if not robots_txt:
        signals.append(SignalFinding(
            name="robots.txt", status="missing",
            value="Not found",
            consequence="All bots are allowed by default, but you have no control over crawl behavior. Consider adding one to manage crawl budget.",
            impact="low",
        ))
    elif blocked:
        signals.append(SignalFinding(
            name="robots.txt", status="partial",
            value=f"Blocking {len(blocked)} bots: {', '.join(blocked)}",
            consequence=f"You are invisible to {round(blocked_share * 100)}% of the AI ecosystem by traffic volume. These bots cannot index your content for AI-powered answers.",
            impact="critical" if blocked_share > 0.3 else "high",
        ))
    else:
        signals.append(SignalFinding(
            name="robots.txt", status="found",
            value="All AI bots allowed",
            consequence="Full AI ecosystem can crawl and index your content.",
            impact="low",
        ))

    # llms.txt
    if llms_found:
        signals.append(SignalFinding(
            name="llms.txt", status="found",
            value=f"{len(llms_txt)} characters",
            consequence="AI agents have a curated guide to your site. This is the equivalent of a README for bots — it tells them what your site offers and how to navigate it.",
            impact="low",
        ))
    else:
        signals.append(SignalFinding(
            name="llms.txt", status="missing",
            value="Not found",
            consequence="AI agents must guess your site structure. Without llms.txt, agents crawl blindly — missing key pages and misunderstanding your content hierarchy. Add one at /llms.txt per the llmstxt.org spec.",
            impact="high",
        ))

    # Sitemap
    if sitemap_found:
        signals.append(SignalFinding(
            name="sitemap.xml", status="found",
            value=f"{sitemap_count} URLs indexed" if sitemap_count else "Found",
            consequence="ClaudeBot and GPTBot now request sitemaps (as of March 2026). Your deep pages are discoverable.",
            impact="low",
        ))
    else:
        signals.append(SignalFinding(
            name="sitemap.xml", status="missing",
            value="Not found",
            consequence="ClaudeBot and GPTBot both started requesting sitemaps in March 2026. Without one, agents can only discover pages linked from your homepage — your deep content is invisible.",
            impact="high",
        ))

    # SSR
    if is_ssr:
        signals.append(SignalFinding(
            name="Server-side rendering", status="found",
            value=f"Content available without JavaScript",
            consequence="GPTBot, ClaudeBot, and ChatGPT-User can all read your content. ChatGPT-User fetches zero CSS/JS — only raw text.",
            impact="low",
        ))
    else:
        signals.append(SignalFinding(
            name="Server-side rendering", status="missing",
            value="Content requires JavaScript",
            consequence="Most AI crawlers cannot execute JavaScript. GPTBot, ClaudeBot, and ChatGPT-User will see a blank page. This makes your entire site invisible to the AI ecosystem.",
            impact="critical",
        ))

    return signals


def _build_content_quality(html: str, text: str, word_count: int, sd_types: set, headers) -> list[SignalFinding]:
    findings = []

    # Content depth
    if word_count >= 500:
        findings.append(SignalFinding(
            name="Content depth", status="found",
            value=f"{word_count} words",
            consequence="Technical implementation guides with 500+ words get 5x more AI citations than thin content (Wislr server log analysis).",
            impact="low",
        ))
    elif word_count >= 200:
        findings.append(SignalFinding(
            name="Content depth", status="partial",
            value=f"{word_count} words",
            consequence="Content is present but thin. Pages with 500+ words of technical depth get significantly more AI citations.",
            impact="medium",
        ))
    else:
        findings.append(SignalFinding(
            name="Content depth", status="missing",
            value=f"{word_count} words",
            consequence="Very thin content. AI agents prioritize pages with substantial, specific technical content. This page is unlikely to be cited.",
            impact="high",
        ))

    # Statistics / data points
    stat_pattern = r"\b\d+(?:\.\d+)?%|\b\d{1,3}(?:,\d{3})+\b|\$\d+"
    stats = re.findall(stat_pattern, text)
    if len(stats) >= 3:
        findings.append(SignalFinding(
            name="Statistics & data", status="found",
            value=f"{len(stats)} data points found",
            consequence="Pages with statistics get +33% visibility in AI-generated responses (GEO research paper).",
            impact="low",
        ))
    else:
        findings.append(SignalFinding(
            name="Statistics & data", status="missing",
            value=f"{len(stats)} data points found",
            consequence="Add concrete numbers, percentages, and benchmarks. The GEO paper shows +33% visibility improvement from adding statistics.",
            impact="medium",
        ))

    # Structured data
    if len(sd_types) > 0:
        findings.append(SignalFinding(
            name="Structured data (JSON-LD)", status="found",
            value=f"Types: {', '.join(sorted(sd_types))}",
            consequence="Agents extract structured data with 0.95 F1 accuracy vs 0.70 for raw HTML. Your content is machine-parseable.",
            impact="low",
        ))
    else:
        findings.append(SignalFinding(
            name="Structured data (JSON-LD)", status="missing",
            value="No Schema.org markup found",
            consequence="Without JSON-LD, agents parse raw HTML with ~0.70 accuracy — missing 30% of your content. Add Schema.org markup for Product, Article, FAQPage, or Organization types.",
            impact="high",
        ))

    # External citations
    ext_links = re.findall(r'href="https?://[^"]+', html)
    if len(ext_links) >= 3:
        findings.append(SignalFinding(
            name="Citations", status="found",
            value=f"{len(ext_links)} external links",
            consequence="Pages with citations to authoritative sources get +30% visibility in AI responses (GEO research).",
            impact="low",
        ))
    else:
        findings.append(SignalFinding(
            name="Citations", status="missing",
            value=f"{len(ext_links)} external links",
            consequence="Add citations to authoritative sources. The GEO paper shows +30% visibility improvement from external references.",
            impact="medium",
        ))

    # Freshness
    has_date = bool(re.search(r"202[5-9]|203\d", text))
    last_modified = headers.get("last-modified", "")
    if has_date or last_modified:
        findings.append(SignalFinding(
            name="Content freshness", status="found",
            value="Recent dates detected",
            consequence="Fresh content signals active maintenance. Pages older than 12 months get deprioritized by AI systems.",
            impact="low",
        ))
    else:
        findings.append(SignalFinding(
            name="Content freshness", status="missing",
            value="No recent dates found",
            consequence="Pages without freshness signals (dates, last-modified headers) get deprioritized. Content older than 12 months is significantly less likely to be cited.",
            impact="medium",
        ))

    return findings


def _html_to_text(html: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _html_to_markdown(html: str) -> str:
    """Convert HTML to clean markdown — what agents actually see."""
    md = html

    # Remove non-content elements entirely
    md = re.sub(r"<script[^>]*>.*?</script>", "", md, flags=re.DOTALL)
    md = re.sub(r"<style[^>]*>.*?</style>", "", md, flags=re.DOTALL)
    md = re.sub(r"<!--.*?-->", "", md, flags=re.DOTALL)
    md = re.sub(r"<svg[^>]*>.*?</svg>", "", md, flags=re.DOTALL)
    md = re.sub(r"<noscript[^>]*>.*?</noscript>", "", md, flags=re.DOTALL)
    md = re.sub(r"<img[^>]*/?>", "", md)  # images are invisible to text agents

    # Convert headings
    for i, tag in enumerate(["h1", "h2", "h3", "h4", "h5", "h6"], 1):
        prefix = "#" * i
        md = re.sub(rf"<{tag}[^>]*>(.*?)</{tag}>", rf"\n{prefix} \1\n", md, flags=re.DOTALL | re.IGNORECASE)

    # Convert code blocks before inline code
    md = re.sub(r"<pre[^>]*>(.*?)</pre>", r"\n```\n\1\n```\n", md, flags=re.DOTALL)
    md = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", md, flags=re.DOTALL)

    # Convert links — extract text and href, clean whitespace inside
    def _clean_link(m):
        href = m.group(1)
        text = re.sub(r"\s+", " ", m.group(2)).strip()
        # Strip remaining tags from link text
        text = re.sub(r"<[^>]+>", "", text).strip()
        if not text or text.lower() in ("", "sponsor"):
            return ""
        return f"[{text}]({href})"
    md = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', _clean_link, md, flags=re.DOTALL)

    # Convert emphasis
    md = re.sub(r"<(?:strong|b)[^>]*>(.*?)</(?:strong|b)>", r"**\1**", md, flags=re.DOTALL)
    md = re.sub(r"<em[^>]*>(.*?)</em>", r"*\1*", md, flags=re.DOTALL)

    # Convert lists
    md = re.sub(r"<li[^>]*>(.*?)</li>", r"\n- \1", md, flags=re.DOTALL)

    # Block elements → newlines
    md = re.sub(r"<br[^>]*/?>", "\n", md)
    md = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\1\n", md, flags=re.DOTALL)
    md = re.sub(r"<(?:div|section|article|main|aside|blockquote)[^>]*>", "\n", md)
    md = re.sub(r"</(?:div|section|article|main|aside|blockquote)>", "\n", md)

    # Strip ALL remaining HTML tags
    md = re.sub(r"<[^>]+>", "", md)

    # Decode entities
    md = md.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    md = md.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")

    # Critical cleanup: strip each line, remove empty lines, collapse whitespace
    lines = []
    for line in md.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Skip lines that are just whitespace artifacts or broken markdown
        if len(line) <= 2 and line.strip("*-#[] ") == "":
            continue
        lines.append(line)

    md = "\n".join(lines)

    # Collapse multiple blank-ish areas
    md = re.sub(r"\n{3,}", "\n\n", md)

    # If still too short, fall back to plain text
    if len(md) < 100:
        md = _html_to_text(html)

    return md


def _check_bot_access(robots_txt: str | None, base_url: str) -> list[BotAccessEntry]:
    entries = []
    for bot in KNOWN_BOTS:
        operator = bot.operator
        share = MARKET_SHARE.get(operator, 0.005)

        if robots_txt is None:
            entries.append(BotAccessEntry(
                name=bot.name, operator=operator, category=bot.category,
                allowed=True, market_share=share,
            ))
            continue

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
