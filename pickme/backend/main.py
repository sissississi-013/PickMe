from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile
import os

from models import TrafficSummary, ScoutReport, OptimizationReport, BenchmarkReport
from discovery import discover_url
from models import DiscoveryReport
from traffic_classifier import classify_log
from web_scout import scan_website
from api_scout import scan_api
from mcp_scout import score_mcp_tools
from optimizer import generate_optimizations
from benchmark import run_benchmark, run_tool_selection_proof
from discovery_benchmark import run_discovery_benchmark
from models import DiscoveryBenchmarkReport

app = FastAPI(title="Pick Me", description="Agent discoverability engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}


# --- Traffic Classifier ---

@app.post("/api/traffic/classify", response_model=TrafficSummary)
async def classify_traffic(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".log", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        summary = classify_log(tmp_path)
        return summary
    finally:
        os.unlink(tmp_path)


# --- Scout Agents ---

class ScanRequest(BaseModel):
    url: str

@app.post("/api/scout/web", response_model=ScoutReport)
async def scout_web(req: ScanRequest):
    return await scan_website(req.url)

@app.post("/api/scout/api", response_model=ScoutReport)
async def scout_api(req: ScanRequest):
    return await scan_api(req.url)

class MCPScanRequest(BaseModel):
    server_name: str
    tools: list[dict]

@app.post("/api/scout/mcp", response_model=ScoutReport)
async def scout_mcp(req: MCPScanRequest):
    return score_mcp_tools(req.tools, req.server_name)


# --- Discovery ---

@app.post("/api/discover", response_model=DiscoveryReport)
async def discover(req: ScanRequest):
    return await discover_url(req.url)


# --- Optimizer ---

@app.post("/api/optimize", response_model=OptimizationReport)
async def optimize(report: ScoutReport):
    return await generate_optimizations(report)


# --- Benchmark ---

class BenchmarkRequest(BaseModel):
    target_name: str
    prompt: str
    context_before: str
    context_after: str | None = None

@app.post("/api/benchmark/run", response_model=BenchmarkReport)
async def benchmark(req: BenchmarkRequest):
    return await run_benchmark(req.target_name, req.prompt, req.context_before, req.context_after)

class ToolProofRequest(BaseModel):
    task_prompt: str
    tool_before: dict
    tool_after: dict

@app.post("/api/benchmark/tool-proof")
async def tool_proof(req: ToolProofRequest):
    return await run_tool_selection_proof(req.task_prompt, req.tool_before, req.tool_after)


# --- Discovery Benchmark ---

class DiscoveryBenchmarkRequest(BaseModel):
    tool: dict
    task_prompt: str
    num_distractors: int = 15

@app.post("/api/benchmark/discovery", response_model=DiscoveryBenchmarkReport)
async def discovery_benchmark(req: DiscoveryBenchmarkRequest):
    return await run_discovery_benchmark(req.tool, req.task_prompt, req.num_distractors)
