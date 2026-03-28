import httpx
import json
import yaml
import re
from models import ScoutReport, CategoryScore, CheckResult

OPENAPI_PATHS = ["/openapi.json", "/swagger.json", "/api-docs", "/docs/openapi.json", "/.well-known/openapi"]

async def scan_api(base_url: str) -> ScoutReport:
    spec = None
    spec_url = None
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        for path in OPENAPI_PATHS:
            try:
                resp = await client.get(f"{base_url.rstrip('/')}{path}")
                if resp.status_code == 200:
                    content = resp.text
                    try:
                        spec = json.loads(content)
                    except json.JSONDecodeError:
                        try:
                            spec = yaml.safe_load(content)
                        except Exception:
                            continue
                    if isinstance(spec, dict) and ("openapi" in spec or "swagger" in spec):
                        spec_url = path
                        break
                    spec = None
            except Exception:
                continue

    if spec is None:
        return ScoutReport(
            target=base_url, scout_type="api", total_score=0, max_score=100,
            categories=[CategoryScore(
                name="OpenAPI Spec Quality", score=0, max_score=35,
                checks=[CheckResult(name="OpenAPI spec exists", passed=False, points_earned=0, points_possible=8,
                    detail=f"No spec found at {', '.join(OPENAPI_PATHS)}", research_basis="Standard conventions")],
            )],
        )

    return score_openapi_spec(spec, base_url, spec_url)


def score_openapi_spec(spec: dict, base_url: str, spec_url: str | None = None) -> ScoutReport:
    paths = spec.get("paths", {})
    all_operations = []
    for path, methods in paths.items():
        for method, op in methods.items():
            if method in ("get", "post", "put", "patch", "delete"):
                all_operations.append((path, method, op if isinstance(op, dict) else {}))

    spec_checks = []
    spec_checks.append(CheckResult(
        name="OpenAPI spec exists", passed=True, points_earned=8, points_possible=8,
        detail=f"Found at {spec_url}" if spec_url else "Spec provided",
        research_basis="Standard conventions",
    ))

    total_ops = max(len(all_operations), 1)
    with_desc = sum(1 for _, _, op in all_operations if op.get("description") or op.get("summary"))
    desc_ratio = with_desc / total_ops
    desc_score = round(8 * desc_ratio)
    spec_checks.append(CheckResult(
        name="Endpoints have descriptions", passed=desc_ratio > 0.8, points_earned=desc_score, points_possible=8,
        detail=f"{with_desc}/{total_ops} endpoints have descriptions",
        research_basis="Rate My OpenAPI: documentation score",
    ))

    total_params = 0
    params_with_desc = 0
    for _, _, op in all_operations:
        for param in op.get("parameters", []):
            total_params += 1
            if param.get("description"):
                params_with_desc += 1
    param_ratio = params_with_desc / max(total_params, 1)
    param_score = round(7 * param_ratio)
    spec_checks.append(CheckResult(
        name="Parameters have descriptions", passed=param_ratio > 0.8, points_earned=param_score, points_possible=7,
        detail=f"{params_with_desc}/{total_params} params documented",
        research_basis="Rate My OpenAPI: completeness score",
    ))

    with_schema = 0
    for _, _, op in all_operations:
        for code, resp in op.get("responses", {}).items():
            if isinstance(resp, dict) and resp.get("content"):
                with_schema += 1
                break
    schema_ratio = with_schema / total_ops
    schema_score = round(6 * schema_ratio)
    spec_checks.append(CheckResult(
        name="Response schemas defined", passed=schema_ratio > 0.8, points_earned=schema_score, points_possible=6,
        detail=f"{with_schema}/{total_ops} endpoints have response schemas",
        research_basis="Rate My OpenAPI: completeness",
    ))

    has_examples = False
    placeholder_patterns = re.compile(r"test|example|foo|bar|string|123|sample", re.IGNORECASE)
    for _, _, op in all_operations:
        for param in op.get("parameters", []):
            ex = param.get("example") or param.get("schema", {}).get("example")
            if ex and not placeholder_patterns.search(str(ex)):
                has_examples = True
    spec_checks.append(CheckResult(
        name="Realistic examples", passed=has_examples, points_earned=6 if has_examples else 0, points_possible=6,
        detail="Found realistic examples" if has_examples else "No examples or examples use placeholder data (test, foo, 123)",
        research_basis="API docs research",
    ))

    doc_checks = []
    info = spec.get("info", {})
    has_info_desc = bool(info.get("description") and len(info["description"]) > 50)
    doc_checks.append(CheckResult(
        name="Rich API description", passed=has_info_desc, points_earned=10 if has_info_desc else 0, points_possible=10,
        detail=f"Info description: {len(info.get('description', ''))} chars" if has_info_desc else "API info.description is missing or minimal",
        research_basis="API docs: problem-first structure",
    ))

    has_tags = bool(spec.get("tags"))
    doc_checks.append(CheckResult(
        name="Organized with tags", passed=has_tags, points_earned=8 if has_tags else 0, points_possible=8,
        detail=f"Found {len(spec.get('tags', []))} tags" if has_tags else "No tags — endpoints are unorganized",
        research_basis="API docs: self-contained documentation",
    ))

    operation_ids = sum(1 for _, _, op in all_operations if op.get("operationId"))
    oid_ratio = operation_ids / total_ops
    oid_score = round(7 * oid_ratio)
    doc_checks.append(CheckResult(
        name="operationIds defined", passed=oid_ratio > 0.8, points_earned=oid_score, points_possible=7,
        detail=f"{operation_ids}/{total_ops} have operationId",
        research_basis="API docs: agents need unique identifiers",
    ))

    has_servers = bool(spec.get("servers"))
    doc_checks.append(CheckResult(
        name="Server URLs defined", passed=has_servers, points_earned=5 if has_servers else 0, points_possible=5,
        detail="Server URLs present" if has_servers else "No server URLs — agents can't determine base URL",
        research_basis="API docs: agents need complete specs",
    ))

    has_security = bool(spec.get("components", {}).get("securitySchemes") or spec.get("securityDefinitions"))
    doc_checks.append(CheckResult(
        name="Security schemes documented", passed=has_security, points_earned=5 if has_security else 0, points_possible=5,
        detail="Security schemes defined" if has_security else "No security schemes — agents can't authenticate",
        research_basis="MCP best practices: errors are context",
    ))

    infra_checks = []
    url_paths = [p for p, _, _ in all_operations]
    clean_urls = all(re.match(r"^/[a-z0-9/_\-{}]+$", p, re.IGNORECASE) for p in url_paths) if url_paths else False
    infra_checks.append(CheckResult(
        name="Clean URL hierarchy", passed=clean_urls, points_earned=6 if clean_urls else 3, points_possible=6,
        detail="URLs follow clean patterns" if clean_urls else "Some URL paths may be inconsistent",
        research_basis="AAIO: clean hierarchies",
    ))

    error_schemas = 0
    for _, _, op in all_operations:
        for code, resp in op.get("responses", {}).items():
            if code.startswith("4") or code.startswith("5"):
                if isinstance(resp, dict) and resp.get("content"):
                    error_schemas += 1
    has_errors = error_schemas > 0
    infra_checks.append(CheckResult(
        name="Error response schemas", passed=has_errors, points_earned=6 if has_errors else 0, points_possible=6,
        detail=f"{error_schemas} error response schemas defined" if has_errors else "No error response schemas — agents can't handle failures",
        research_basis="API agent-readiness: predictable error format",
    ))

    infra_checks.append(CheckResult(
        name="Rate limiting documented", passed=False, points_earned=0, points_possible=6,
        detail="Rate limits not found in spec (check response headers at runtime)",
        research_basis="API agent-readiness",
    ))

    infra_checks.append(CheckResult(
        name="Auth clearly documented", passed=has_security, points_earned=6 if has_security else 0, points_possible=6,
        detail="Auth documented" if has_security else "No auth documentation",
        research_basis="API agent-readiness",
    ))

    infra_checks.append(CheckResult(
        name="Consistent HTTP semantics", passed=True, points_earned=6, points_possible=6,
        detail="HTTP methods follow REST conventions",
        research_basis="API agent-readiness",
    ))

    categories = [
        CategoryScore(name="OpenAPI Spec Quality", score=sum(c.points_earned for c in spec_checks), max_score=35, checks=spec_checks),
        CategoryScore(name="Agent-Friendly Documentation", score=sum(c.points_earned for c in doc_checks), max_score=35, checks=doc_checks),
        CategoryScore(name="Technical Infrastructure", score=sum(c.points_earned for c in infra_checks), max_score=30, checks=infra_checks),
    ]

    total = sum(c.score for c in categories)
    return ScoutReport(target=base_url, scout_type="api", total_score=total, max_score=100, categories=categories)
