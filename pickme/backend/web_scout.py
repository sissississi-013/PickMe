import httpx
import extruct
import re
from models import ScoutReport, CategoryScore, CheckResult

async def scan_website(url: str) -> ScoutReport:
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        main_resp = await client.get(url)
        html = main_resp.text
        base_url = str(main_resp.url)
        metadata = extruct.extract(html, base_url=base_url, errors="ignore")
        jsonld = metadata.get("json-ld", [])
        llms_txt = await _fetch_text(client, f"{base_url.rstrip('/')}/llms.txt")
        robots_txt = await _fetch_text(client, f"{base_url.rstrip('/')}/robots.txt")
        sitemap = await _fetch_text(client, f"{base_url.rstrip('/')}/sitemap.xml")

    structured_data_checks = _check_structured_data(jsonld, html)
    discoverability_checks = _check_discoverability(llms_txt, robots_txt, sitemap, html)
    content_quality_checks = _check_content_quality(html, main_resp.headers)
    authority_checks = _check_authority(base_url, html, main_resp)

    categories = [
        CategoryScore(name="Structured Data", score=sum(c.points_earned for c in structured_data_checks), max_score=30, checks=structured_data_checks),
        CategoryScore(name="Discoverability", score=sum(c.points_earned for c in discoverability_checks), max_score=25, checks=discoverability_checks),
        CategoryScore(name="Content Quality", score=sum(c.points_earned for c in content_quality_checks), max_score=25, checks=content_quality_checks),
        CategoryScore(name="Consistency & Authority", score=sum(c.points_earned for c in authority_checks), max_score=20, checks=authority_checks),
    ]

    total = sum(c.score for c in categories)
    return ScoutReport(target=url, scout_type="web", total_score=total, max_score=100, categories=categories)


async def _fetch_text(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        resp = await client.get(url)
        return resp.text if resp.status_code == 200 else None
    except Exception:
        return None


def _check_structured_data(jsonld: list, html: str) -> list[CheckResult]:
    checks = []
    has_jsonld = len(jsonld) > 0
    checks.append(CheckResult(
        name="JSON-LD Schema.org markup", passed=has_jsonld, points_earned=10 if has_jsonld else 0,
        points_possible=10, detail=f"Found {len(jsonld)} JSON-LD blocks" if has_jsonld else "No JSON-LD markup found",
        research_basis="AAIO: structured data is #1 agent signal",
    ))
    types_found = set()
    key_types = {"Product", "FAQPage", "Article", "WebAPI", "SoftwareApplication", "Organization", "WebSite"}
    for item in jsonld:
        t = item.get("@type", "")
        if isinstance(t, list):
            types_found.update(t)
        else:
            types_found.add(t)
    matched = types_found & key_types
    score = min(8, len(matched) * 2)
    checks.append(CheckResult(
        name="Key schema types", passed=len(matched) > 0, points_earned=score,
        points_possible=8, detail=f"Found: {', '.join(matched)}" if matched else "No key schema types (Product, FAQPage, Article, WebAPI)",
        research_basis="AAIO: specific types agents parse",
    ))
    has_tables = bool(re.search(r"<table", html, re.IGNORECASE))
    pricing_in_img = bool(re.search(r"<img[^>]*(?:pricing|price|plan)", html, re.IGNORECASE))
    ok = has_tables and not pricing_in_img
    checks.append(CheckResult(
        name="Pricing in structured HTML", passed=ok, points_earned=6 if ok else (3 if has_tables else 0),
        points_possible=6, detail="Pricing in HTML tables" if ok else "Pricing may be in images/PDFs — agents can't extract",
        research_basis="AAIO: agents can't extract from images/PDFs",
    ))
    has_th = bool(re.search(r"<th", html, re.IGNORECASE))
    checks.append(CheckResult(
        name="HTML tables with headers", passed=has_th, points_earned=3 if has_th else 0,
        points_possible=3, detail="Tables have consistent headers" if has_th else "No table headers found",
        research_basis="AAIO: agents parse table structures",
    ))
    has_code_schema = any(item.get("@type") == "SoftwareSourceCode" for item in jsonld)
    checks.append(CheckResult(
        name="SoftwareSourceCode schema", passed=has_code_schema, points_earned=3 if has_code_schema else 0,
        points_possible=3, detail="SoftwareSourceCode schema found" if has_code_schema else "No SoftwareSourceCode schema",
        research_basis="API docs research",
    ))
    return checks


def _check_discoverability(llms_txt: str | None, robots_txt: str | None, sitemap: str | None, html: str) -> list[CheckResult]:
    checks = []
    has_llms = llms_txt is not None and len(llms_txt.strip()) > 10
    checks.append(CheckResult(
        name="llms.txt present", passed=has_llms, points_earned=8 if has_llms else 0,
        points_possible=8, detail=f"llms.txt found ({len(llms_txt)} chars)" if has_llms else "No llms.txt — agents have no curated site map",
        research_basis="llmstxt.org specification",
    ))
    ai_bots_blocked = []
    if robots_txt:
        for bot in ["GPTBot", "ClaudeBot", "PerplexityBot", "ChatGPT-User"]:
            if re.search(rf"User-agent:\s*{bot}.*?Disallow:\s*/", robots_txt, re.IGNORECASE | re.DOTALL):
                ai_bots_blocked.append(bot)
    bots_ok = len(ai_bots_blocked) == 0
    checks.append(CheckResult(
        name="robots.txt allows AI bots", passed=bots_ok, points_earned=8 if bots_ok else 0,
        points_possible=8,
        detail="All major AI bots allowed" if bots_ok else f"Blocked: {', '.join(ai_bots_blocked)}",
        research_basis="AAIO: blocking = invisible to ecosystem",
    ))
    has_sitemap = sitemap is not None and "<urlset" in (sitemap or "")
    checks.append(CheckResult(
        name="XML sitemap present", passed=has_sitemap, points_earned=5 if has_sitemap else 0,
        points_possible=5, detail="Sitemap found" if has_sitemap else "No XML sitemap",
        research_basis="Server log research: bots request sitemaps",
    ))
    text_content = re.sub(r"<[^>]+>", "", html)
    has_ssr = len(text_content.strip()) > 500
    checks.append(CheckResult(
        name="Server-side rendered", passed=has_ssr, points_earned=4 if has_ssr else 0,
        points_possible=4, detail="Content available without JS" if has_ssr else "Content may require JavaScript — invisible to most agents",
        research_basis="AAIO: JS-only = invisible to agents",
    ))
    return checks


def _check_content_quality(html: str, headers: httpx.Headers) -> list[CheckResult]:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()
    checks = []
    has_content = len(words) >= 200
    checks.append(CheckResult(
        name="Substantial content present", passed=has_content, points_earned=7 if has_content else 3,
        points_possible=7, detail=f"{len(words)} words of content" if has_content else "Thin content — agents prefer comprehensive pages",
        research_basis="GEO: answer-first structure preferred",
    ))
    stat_pattern = r"\b\d+(?:\.\d+)?%|\b\d{1,3}(?:,\d{3})+\b|\$\d+"
    stats = re.findall(stat_pattern, text)
    has_stats = len(stats) >= 2
    checks.append(CheckResult(
        name="Statistics and data points", passed=has_stats, points_earned=6 if has_stats else 0,
        points_possible=6, detail=f"Found {len(stats)} data points" if has_stats else "No statistics found — add data for +33% visibility",
        research_basis="GEO paper: +33% visibility with statistics",
    ))
    ext_links = re.findall(r'href="https?://[^"]+', html)
    has_citations = len(ext_links) >= 3
    checks.append(CheckResult(
        name="Citations to external sources", passed=has_citations, points_earned=6 if has_citations else 0,
        points_possible=6, detail=f"Found {len(ext_links)} external links" if has_citations else "No citations — add authoritative sources for +30% visibility",
        research_basis="GEO paper: +30% visibility with citations",
    ))
    last_modified = headers.get("last-modified", "")
    has_date = bool(re.search(r"202[5-9]|203\d", html)) or bool(last_modified)
    checks.append(CheckResult(
        name="Content freshness", passed=has_date, points_earned=6 if has_date else 0,
        points_possible=6, detail="Recent dates detected" if has_date else "No freshness signals — pages >12 months get deprioritized",
        research_basis="AAIO: >12 months = deprioritized",
    ))
    return checks


def _check_authority(base_url: str, html: str, resp: httpx.Response) -> list[CheckResult]:
    checks = []
    title_match = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
    has_title = title_match is not None
    checks.append(CheckResult(
        name="Consistent entity naming", passed=has_title, points_earned=6 if has_title else 0,
        points_possible=6, detail=f"Title: {title_match.group(1).strip()}" if has_title else "No page title found",
        research_basis="AAIO: inconsistency = ambiguity",
    ))
    checks.append(CheckResult(
        name="Cross-page pricing consistency", passed=True, points_earned=3,
        points_possible=6, detail="Single-page scan — multi-page consistency requires deep crawl",
        research_basis="AAIO: pricing discrepancy = exclusion",
    ))
    has_author = bool(re.search(r'"author"|"Author"|byline|data-author', html))
    checks.append(CheckResult(
        name="Author attribution", passed=has_author, points_earned=4 if has_author else 0,
        points_possible=4, detail="Author attribution found" if has_author else "No author attribution",
        research_basis="AAIO: authority signals",
    ))
    is_https = base_url.startswith("https")
    hsts = "strict-transport-security" in resp.headers
    score = (2 if is_https else 0) + (2 if hsts else 0)
    checks.append(CheckResult(
        name="HTTPS + security headers", passed=is_https, points_earned=score,
        points_possible=4, detail=f"HTTPS: {'Y' if is_https else 'N'}, HSTS: {'Y' if hsts else 'N'}",
        research_basis="AAIO: domain trust signals",
    ))
    return checks
