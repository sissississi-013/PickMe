import re
from models import ScoutReport, CategoryScore, CheckResult

NAMING_PATTERN = re.compile(r"^[a-z]+_[a-z]+_[a-z]+", re.IGNORECASE)
GENERIC_NAMES = {"create", "get", "update", "delete", "list", "read", "write", "set", "run", "execute"}
REST_PATTERNS = re.compile(r"^(GET|POST|PUT|PATCH|DELETE)\s", re.IGNORECASE)


def score_mcp_tools(tools: list[dict], server_name: str) -> ScoutReport:
    naming_checks = _check_naming(tools)
    desc_checks = _check_descriptions(tools)
    param_checks = _check_parameters(tools)
    server_checks = _check_server_design(tools)

    categories = [
        CategoryScore(name="Tool Naming", score=sum(c.points_earned for c in naming_checks), max_score=25, checks=naming_checks),
        CategoryScore(name="Description Quality", score=sum(c.points_earned for c in desc_checks), max_score=35, checks=desc_checks),
        CategoryScore(name="Parameter Design", score=sum(c.points_earned for c in param_checks), max_score=20, checks=param_checks),
        CategoryScore(name="Server Design", score=sum(c.points_earned for c in server_checks), max_score=20, checks=server_checks),
    ]

    total = sum(c.score for c in categories)
    return ScoutReport(target=server_name, scout_type="mcp", total_score=total, max_score=100, categories=categories)


def _check_naming(tools: list[dict]) -> list[CheckResult]:
    checks = []
    names = [t.get("name", "") for t in tools]

    matching = sum(1 for n in names if NAMING_PATTERN.match(n))
    ratio = matching / max(len(names), 1)
    score = round(10 * ratio)
    checks.append(CheckResult(
        name="Follows naming pattern", passed=ratio > 0.7, points_earned=score, points_possible=10,
        detail=f"{matching}/{len(names)} follow {{service}}_{{action}}_{{resource}}",
        research_basis="MCP best practices (philschmid.de)",
    ))

    rest_mirrors = sum(1 for n in names if REST_PATTERNS.search(n))
    ok = rest_mirrors == 0
    checks.append(CheckResult(
        name="Task-oriented names", passed=ok, points_earned=8 if ok else 0, points_possible=8,
        detail="Names are task-oriented" if ok else f"{rest_mirrors} names mirror REST endpoints",
        research_basis='Tool discovery guide: "name after the job"',
    ))

    generic_found = [n for n in names if n.lower() in GENERIC_NAMES]
    ok = len(generic_found) == 0
    checks.append(CheckResult(
        name="No generic names", passed=ok, points_earned=7 if ok else 0, points_possible=7,
        detail="All names are specific" if ok else f"Generic names: {', '.join(generic_found)}",
        research_basis="MCP best practices",
    ))

    return checks


def _check_descriptions(tools: list[dict]) -> list[CheckResult]:
    checks = []
    descs = [t.get("description", "") for t in tools]

    with_purpose = sum(1 for d in descs if len(d) > 20)
    ratio = with_purpose / max(len(descs), 1)
    score = round(10 * ratio)
    checks.append(CheckResult(
        name="States clear purpose", passed=ratio > 0.8, points_earned=score, points_possible=10,
        detail=f"{with_purpose}/{len(descs)} have clear descriptions",
        research_basis="arXiv 2602.14878: 56% fail to state purpose",
    ))

    trigger_pattern = re.compile(r"(use when|call this|use this|invoke when|for when)", re.IGNORECASE)
    with_trigger = sum(1 for d in descs if trigger_pattern.search(d))
    ratio = with_trigger / max(len(descs), 1)
    score = round(8 * ratio)
    checks.append(CheckResult(
        name="Specifies when to invoke", passed=ratio > 0.5, points_earned=score, points_possible=8,
        detail=f"{with_trigger}/{len(descs)} specify invocation context",
        research_basis="MCP best practices: docstrings must specify when",
    ))

    io_pattern = re.compile(r"(returns?|input|output|takes|accepts|produces)", re.IGNORECASE)
    with_io = sum(1 for d in descs if io_pattern.search(d))
    ratio = with_io / max(len(descs), 1)
    score = round(7 * ratio)
    checks.append(CheckResult(
        name="Specifies input/output", passed=ratio > 0.5, points_earned=score, points_possible=7,
        detail=f"{with_io}/{len(descs)} describe I/O",
        research_basis="MCP best practices",
    ))

    under_limit = sum(1 for d in descs if len(d) <= 100)
    ratio = under_limit / max(len(descs), 1)
    score = round(5 * ratio)
    checks.append(CheckResult(
        name="Under 100 characters", passed=ratio > 0.8, points_earned=score, points_possible=5,
        detail=f"{under_limit}/{len(descs)} under registry limit",
        research_basis="Tool discovery guide: registry hard limit",
    ))

    keyword_pattern = re.compile(r"(search|create|list|send|read|write|update|delete|fetch|get|find|generate)", re.IGNORECASE)
    with_keywords = sum(1 for d in descs if keyword_pattern.search(d))
    ratio = with_keywords / max(len(descs), 1)
    score = round(5 * ratio)
    checks.append(CheckResult(
        name="Contains discoverable keywords", passed=ratio > 0.5, points_earned=score, points_possible=5,
        detail=f"{with_keywords}/{len(descs)} have action keywords",
        research_basis="Tool Search: BM25 semantic matching",
    ))

    return checks


def _check_parameters(tools: list[dict]) -> list[CheckResult]:
    checks = []
    schemas = [t.get("inputSchema", {}) for t in tools]

    nested = 0
    for schema in schemas:
        for prop_name, prop in schema.get("properties", {}).items():
            if prop.get("type") == "object":
                nested += 1
    ok = nested == 0
    checks.append(CheckResult(
        name="Flat parameters", passed=ok, points_earned=8 if ok else 0, points_possible=8,
        detail="All parameters are flat" if ok else f"{nested} nested object parameters found",
        research_basis="MCP best practices: avoid complex nesting",
    ))

    total_props = sum(len(s.get("properties", {})) for s in schemas)
    with_enum = sum(
        1 for s in schemas
        for p in s.get("properties", {}).values()
        if p.get("enum") or p.get("const")
    )
    ratio = with_enum / max(total_props, 1)
    score = round(7 * min(ratio * 3, 1))
    checks.append(CheckResult(
        name="Constrained types (enum)", passed=with_enum > 0, points_earned=score, points_possible=7,
        detail=f"{with_enum}/{total_props} params use enum/const",
        research_basis="MCP best practices: Literal types",
    ))

    with_defaults = sum(
        1 for s in schemas
        for p in s.get("properties", {}).values()
        if "default" in p
    )
    ratio = with_defaults / max(total_props, 1)
    score = round(5 * min(ratio * 3, 1))
    checks.append(CheckResult(
        name="Sensible defaults", passed=with_defaults > 0, points_earned=score, points_possible=5,
        detail=f"{with_defaults}/{total_props} params have defaults",
        research_basis="MCP best practices",
    ))

    return checks


def _check_server_design(tools: list[dict]) -> list[CheckResult]:
    checks = []
    count = len(tools)

    optimal = 5 <= count <= 15
    if count < 5:
        score = round(8 * count / 5)
        detail = f"{count} tools — consider adding more for completeness"
    elif count <= 15:
        score = 8
        detail = f"{count} tools — optimal range (5-15)"
    elif count <= 30:
        score = 4
        detail = f"{count} tools — agents struggle above 15, accuracy degrades"
    else:
        score = 0
        detail = f"{count} tools — accuracy collapses at 30+, reduce to 5-15"
    checks.append(CheckResult(
        name="Tool count (5-15 optimal)", passed=optimal, points_earned=score, points_possible=8,
        detail=detail, research_basis="Discovery research: accuracy collapses at 30+",
    ))

    error_hints = sum(1 for t in tools if re.search(r"error|fail|invalid", t.get("description", ""), re.IGNORECASE))
    ok = error_hints > 0
    checks.append(CheckResult(
        name="Error handling mentioned", passed=ok, points_earned=6 if ok else 3, points_possible=6,
        detail="Error scenarios documented" if ok else "No error guidance in descriptions",
        research_basis="MCP best practices: return guidance",
    ))

    checks.append(CheckResult(
        name="Server Card (.well-known/mcp)", passed=False, points_earned=0, points_possible=6,
        detail="Server Card check requires remote server connection",
        research_basis="MCP roadmap: June 2026 spec",
    ))

    return checks
