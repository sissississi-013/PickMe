"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { apiPost } from "@/lib/api";

export interface ScoutReport {
  target: string;
  scout_type: string;
  total_score: number;
  max_score: number;
  categories: any[];
}

interface Recommendation {
  severity: string;
  issue: string;
  why_it_matters: string;
  fix: string;
  predicted_impact: number;
}

interface DiscoveryResult {
  target_tool_name: string;
  task_prompt: string;
  num_distractors: number;
  discovered: boolean;
  selected: boolean;
  invoked_correctly: boolean;
  discovery_rank: number | null;
  competing_tools: string[];
  raw_response: string[];
}

interface DiscoveryBenchmarkReport {
  before: DiscoveryResult;
  after: DiscoveryResult | null;
  optimized_description: string | null;
  discovery_improvement: string | null;
}

interface SimulationTabProps {
  reports: ScoutReport[];
  lastUrl: string;
  onRescan: () => void;
}

const severityVariant: Record<string, "destructive" | "default" | "secondary" | "outline"> = {
  critical: "destructive",
  high: "default",
  medium: "secondary",
  low: "outline",
};

const DEFAULT_TASK = "Create a new issue titled 'Login button not working' in the acme/webapp repository";

export function SimulationTab({ reports, lastUrl, onRescan }: SimulationTabProps) {
  // Input mode
  const [inputMode, setInputMode] = useState<"json" | "describe">("describe");
  const [toolDescription, setToolDescription] = useState("A tool that creates GitHub issues for bug tracking");
  const [toolJson, setToolJson] = useState("");
  const [generatingTool, setGeneratingTool] = useState(false);

  // Optimizer state
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [totalGain, setTotalGain] = useState(0);
  const [optimizerLoading, setOptimizerLoading] = useState(false);
  const [expandedRec, setExpandedRec] = useState<number | null>(null);

  // Benchmark state
  const [taskPrompt, setTaskPrompt] = useState(DEFAULT_TASK);
  const [numDistractors, setNumDistractors] = useState(15);
  const [benchResult, setBenchResult] = useState<DiscoveryBenchmarkReport | null>(null);
  const [benchLoading, setBenchLoading] = useState(false);
  const [benchError, setBenchError] = useState<string | null>(null);

  async function generateToolFromDescription() {
    setGeneratingTool(true);
    try {
      const result = await apiPost<any>("/api/tool/generate", { description: toolDescription });
      setToolJson(JSON.stringify(result, null, 2));
      setInputMode("json");
    } catch (err: any) {
      console.error("Failed to generate tool:", err);
    } finally {
      setGeneratingTool(false);
    }
  }

  async function handleOptimize() {
    if (reports.length === 0) return;
    setOptimizerLoading(true);
    setRecommendations([]);
    setTotalGain(0);
    try {
      for (const report of reports) {
        const result: any = await apiPost("/api/optimize", report);
        setRecommendations((prev) => [...prev, ...result.recommendations]);
        setTotalGain((prev) => prev + result.total_predicted_gain);
      }
    } catch (err) {
      console.error("Optimization failed:", err);
    } finally {
      setOptimizerLoading(false);
    }
  }

  async function runDiscoveryBenchmark() {
    setBenchLoading(true);
    setBenchResult(null);
    setBenchError(null);
    try {
      let parsedTool: unknown;
      try {
        parsedTool = JSON.parse(toolJson);
      } catch {
        setBenchError("Invalid JSON in tool definition. Use 'Describe' mode to generate one.");
        setBenchLoading(false);
        return;
      }
      const result = await apiPost<DiscoveryBenchmarkReport>("/api/benchmark/discovery", {
        tool: parsedTool,
        task_prompt: taskPrompt,
        num_distractors: numDistractors,
      });
      setBenchResult(result);
    } catch (err: any) {
      setBenchError(err?.message || "Benchmark failed");
    } finally {
      setBenchLoading(false);
    }
  }

  return (
    <div className="space-y-8 pt-4">

      {/* Section 1: Optimization Recommendations (from URL scan) */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">Optimization Recommendations</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Scan a URL first, then generate research-backed fixes
            </p>
            {totalGain > 0 && (
              <p className="text-sm text-green-600 font-mono mt-1">Predicted improvement: +{totalGain} pts</p>
            )}
          </div>
          <div className="flex gap-2">
            {recommendations.length > 0 && (
              <Button variant="outline" size="sm" onClick={onRescan}>Re-scan</Button>
            )}
            <Button
              size="sm"
              onClick={handleOptimize}
              disabled={optimizerLoading || reports.length === 0}
            >
              {optimizerLoading ? "Analyzing..." : recommendations.length > 0 ? "Re-analyze" : "Generate Fixes"}
            </Button>
          </div>
        </div>

        {reports.length === 0 && (
          <p className="text-sm text-muted-foreground">Scan a URL on the Discovery tab first</p>
        )}

        {recommendations.length > 0 && (
          <div className="space-y-2">
            {recommendations.map((rec, i) => (
              <div
                key={i}
                className="border rounded-md p-3 cursor-pointer hover:bg-muted/30 transition-colors"
                onClick={() => setExpandedRec(expandedRec === i ? null : i)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant={severityVariant[rec.severity] ?? "outline"} className="text-xs">
                      {rec.severity}
                    </Badge>
                    <span className="text-sm">{rec.issue}</span>
                  </div>
                  <span className="text-sm text-green-600 font-mono">+{rec.predicted_impact} pts</span>
                </div>
                {expandedRec === i && (
                  <div className="mt-3 pt-3 border-t space-y-2">
                    {rec.why_it_matters && (
                      <p className="text-xs text-muted-foreground">{rec.why_it_matters}</p>
                    )}
                    <pre className="text-xs font-mono bg-muted/60 p-3 rounded overflow-x-auto whitespace-pre-wrap border">
                      {rec.fix}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <Separator />

      {/* Section 2: Discovery Benchmark */}
      <div className="space-y-4">
        <div>
          <p className="font-medium">Discovery Benchmark</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Test if AI agents can find your tool among {numDistractors} real competitors using Claude&apos;s production tool search
          </p>
        </div>

        {/* Input mode toggle */}
        <div className="flex gap-2">
          <Button
            variant={inputMode === "describe" ? "default" : "outline"}
            size="sm"
            onClick={() => setInputMode("describe")}
          >
            Describe your tool
          </Button>
          <Button
            variant={inputMode === "json" ? "default" : "outline"}
            size="sm"
            onClick={() => setInputMode("json")}
          >
            Paste MCP JSON
          </Button>
        </div>

        {inputMode === "describe" ? (
          <div className="space-y-3">
            <div className="space-y-1.5">
              <label className="text-sm text-muted-foreground">Describe your tool, API, or service</label>
              <textarea
                className="w-full h-24 text-sm border rounded-md p-3 bg-muted/30 resize-none focus:outline-none focus:ring-1 focus:ring-ring"
                value={toolDescription}
                onChange={(e) => setToolDescription(e.target.value)}
                placeholder="e.g. A Stripe API endpoint for creating payment intents, or a GitHub MCP tool for managing issues..."
              />
            </div>
            <Button
              size="sm"
              onClick={generateToolFromDescription}
              disabled={generatingTool || !toolDescription.trim()}
            >
              {generatingTool ? "Generating..." : "Generate MCP Definition"}
            </Button>
          </div>
        ) : (
          <div className="space-y-1.5">
            <label className="text-sm text-muted-foreground">MCP Tool Definition (JSON)</label>
            <textarea
              className="w-full h-36 text-sm font-mono border rounded-md p-3 bg-muted/30 resize-none focus:outline-none focus:ring-1 focus:ring-ring"
              value={toolJson}
              onChange={(e) => setToolJson(e.target.value)}
              spellCheck={false}
              placeholder='{"name": "...", "description": "...", "inputSchema": {...}}'
            />
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <label className="text-sm text-muted-foreground">Task prompt for the agent</label>
            <Input
              value={taskPrompt}
              onChange={(e) => setTaskPrompt(e.target.value)}
              className="font-mono text-sm"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm text-muted-foreground">Competing tools</label>
            <Input
              type="number"
              value={numDistractors}
              onChange={(e) => setNumDistractors(parseInt(e.target.value) || 15)}
              min={5}
              max={50}
              className="font-mono text-sm"
            />
          </div>
        </div>

        <Button
          onClick={runDiscoveryBenchmark}
          disabled={benchLoading || !toolJson.trim()}
        >
          {benchLoading ? "Running benchmark (~30s)..." : "Run Discovery Benchmark"}
        </Button>

        {benchError && (
          <div className="border border-destructive/30 rounded-md p-3">
            <p className="text-sm text-destructive font-mono">{benchError}</p>
          </div>
        )}

        {benchResult && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <BenchmarkResultCard title="Before Optimization" result={benchResult.before} />
              {benchResult.after && (
                <BenchmarkResultCard title="After Optimization" result={benchResult.after} />
              )}
            </div>

            {benchResult.discovery_improvement && benchResult.discovery_improvement !== "No change" && (
              <div className="border border-green-500 bg-green-50 dark:bg-green-950/30 rounded-md p-3">
                <p className="text-sm text-green-700 dark:text-green-300">
                  {benchResult.discovery_improvement}
                </p>
              </div>
            )}

            {benchResult.optimized_description && (
              <div className="space-y-1.5">
                <p className="text-sm text-muted-foreground">Optimized Description</p>
                <pre className="text-sm font-mono bg-muted/40 p-3 rounded-md border whitespace-pre-wrap">
                  {benchResult.optimized_description}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function BenchmarkResultCard({ title, result }: { title: string; result: DiscoveryResult }) {
  return (
    <div className="border rounded-md p-4 space-y-3">
      <p className="text-sm font-medium">{title}</p>

      <div className="grid grid-cols-3 gap-2">
        <StatusBadge label="Discovered" value={result.discovered} />
        <StatusBadge label="Selected" value={result.selected} />
        <StatusBadge label="Invoked" value={result.invoked_correctly} />
      </div>

      {result.discovery_rank !== null && (
        <p className="text-sm font-mono text-muted-foreground">
          Search rank: #{result.discovery_rank} of {result.competing_tools.length} results
        </p>
      )}

      {!result.discovered && (
        <p className="text-sm text-destructive">
          Not found among {result.num_distractors} competing tools
        </p>
      )}

      {result.competing_tools.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Search results:</p>
          <div className="flex flex-wrap gap-1">
            {result.competing_tools.map((name, i) => (
              <span
                key={i}
                className={`text-xs font-mono px-1.5 py-0.5 rounded ${
                  name === result.target_tool_name
                    ? "bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {name}
              </span>
            ))}
          </div>
        </div>
      )}

      {result.raw_response.length > 0 && (
        <details className="text-xs">
          <summary className="text-muted-foreground cursor-pointer">Raw response</summary>
          <pre className="font-mono mt-1 p-2 bg-muted/40 rounded whitespace-pre-wrap overflow-x-auto text-xs">
            {result.raw_response.join("\n")}
          </pre>
        </details>
      )}
    </div>
  );
}

function StatusBadge({ label, value }: { label: string; value: boolean }) {
  return (
    <div className="text-center">
      <div
        className={`inline-flex items-center justify-center w-10 h-10 rounded-full text-base font-medium ${
          value
            ? "bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300"
            : "bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300"
        }`}
      >
        {value ? "Y" : "N"}
      </div>
      <p className="text-xs text-muted-foreground mt-1">{label}</p>
    </div>
  );
}
