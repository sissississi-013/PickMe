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

const DEFAULT_TOOL = `{
  "name": "create",
  "description": "creates stuff",
  "inputSchema": {
    "type": "object",
    "properties": {
      "data": { "type": "object" }
    }
  }
}`;

const DEFAULT_TASK = "Create a new issue titled 'Login button not working' in the acme/webapp repository";

export function SimulationTab({ reports, lastUrl, onRescan }: SimulationTabProps) {
  // Optimizer state
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [totalGain, setTotalGain] = useState(0);
  const [optimizerLoading, setOptimizerLoading] = useState(false);
  const [expandedRec, setExpandedRec] = useState<number | null>(null);

  // Discovery benchmark state
  const [toolJson, setToolJson] = useState(DEFAULT_TOOL);
  const [taskPrompt, setTaskPrompt] = useState(DEFAULT_TASK);
  const [numDistractors, setNumDistractors] = useState(15);
  const [benchResult, setBenchResult] = useState<DiscoveryBenchmarkReport | null>(null);
  const [benchLoading, setBenchLoading] = useState(false);
  const [benchError, setBenchError] = useState<string | null>(null);

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
        setBenchError("Invalid JSON in tool definition");
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
      {/* Section 1: Discovery Benchmark — the hero feature */}
      <div className="space-y-4">
        <div>
          <p className="text-sm font-medium">Discovery Benchmark</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Test if AI agents can find your tool among {numDistractors} competitors using Claude&apos;s actual tool search mechanism
          </p>
        </div>

        <div className="space-y-3">
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground">Your Tool Definition (MCP/JSON)</label>
            <textarea
              className="w-full h-36 text-sm font-mono border rounded-md p-3 bg-muted/30 resize-none focus:outline-none focus:ring-1 focus:ring-ring"
              value={toolJson}
              onChange={(e) => setToolJson(e.target.value)}
              spellCheck={false}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs text-muted-foreground">Task Prompt (what the agent needs to do)</label>
              <Input
                value={taskPrompt}
                onChange={(e) => setTaskPrompt(e.target.value)}
                className="font-mono text-xs"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs text-muted-foreground">Distractor Count</label>
              <Input
                type="number"
                value={numDistractors}
                onChange={(e) => setNumDistractors(parseInt(e.target.value) || 15)}
                min={5}
                max={50}
                className="font-mono text-xs"
              />
            </div>
          </div>

          <Button
            onClick={runDiscoveryBenchmark}
            disabled={benchLoading}
            size="sm"
            className="text-xs"
          >
            {benchLoading ? "Running benchmark (this takes ~30s)..." : "Run Discovery Benchmark"}
          </Button>
        </div>

        {benchError && (
          <div className="border border-destructive/30 rounded-md p-3">
            <p className="text-xs text-destructive font-mono">{benchError}</p>
          </div>
        )}

        {benchResult && (
          <div className="space-y-4">
            {/* Before/After comparison */}
            <div className="grid grid-cols-2 gap-4">
              <BenchmarkResultCard title="Before Optimization" result={benchResult.before} />
              {benchResult.after && (
                <BenchmarkResultCard title="After Optimization" result={benchResult.after} />
              )}
            </div>

            {/* Improvement summary */}
            {benchResult.discovery_improvement && benchResult.discovery_improvement !== "No change" && (
              <div className="border border-green-500 bg-green-50 dark:bg-green-950/30 rounded-md p-3">
                <p className="text-xs font-medium text-green-700 dark:text-green-300">
                  {benchResult.discovery_improvement}
                </p>
              </div>
            )}

            {/* Optimized description */}
            {benchResult.optimized_description && (
              <div className="space-y-1.5">
                <p className="text-xs text-muted-foreground">Optimized Description</p>
                <pre className="text-sm font-mono bg-muted/40 p-3 rounded-md border whitespace-pre-wrap">
                  {benchResult.optimized_description}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>

      <Separator />

      {/* Section 2: Optimization Recommendations */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Optimization Recommendations</p>
            {totalGain > 0 && (
              <p className="text-xs text-green-600 font-mono mt-0.5">Predicted improvement: +{totalGain} pts</p>
            )}
          </div>
          <div className="flex gap-2">
            {recommendations.length > 0 && (
              <Button variant="outline" size="sm" onClick={onRescan} className="text-xs">Re-scan</Button>
            )}
            <Button
              size="sm"
              onClick={handleOptimize}
              disabled={optimizerLoading || reports.length === 0}
              className="text-xs"
            >
              {optimizerLoading ? "Analyzing..." : recommendations.length > 0 ? "Re-analyze" : "Generate Fixes"}
            </Button>
          </div>
        </div>

        {reports.length === 0 && (
          <p className="text-xs text-muted-foreground">Enter a URL and scan before generating fixes</p>
        )}

        {recommendations.length === 0 && !optimizerLoading && reports.length > 0 && (
          <p className="text-xs text-muted-foreground">Click &quot;Generate Fixes&quot; to get optimization recommendations</p>
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
                    <Badge variant={severityVariant[rec.severity] ?? "outline"} className="text-xs h-4">
                      {rec.severity}
                    </Badge>
                    <span className="text-xs font-medium">{rec.issue}</span>
                  </div>
                  <span className="text-xs text-green-600 font-mono">+{rec.predicted_impact} pts</span>
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
    </div>
  );
}

function BenchmarkResultCard({ title, result }: { title: string; result: DiscoveryResult }) {
  return (
    <div className="border rounded-md p-4 space-y-3">
      <p className="text-xs font-medium">{title}</p>

      <div className="grid grid-cols-3 gap-2">
        <StatusBadge label="Discovered" value={result.discovered} />
        <StatusBadge label="Selected" value={result.selected} />
        <StatusBadge label="Invoked" value={result.invoked_correctly} />
      </div>

      {result.discovery_rank !== null && (
        <p className="text-xs font-mono text-muted-foreground">
          Search rank: #{result.discovery_rank} of {result.competing_tools.length} results
        </p>
      )}

      {!result.discovered && (
        <p className="text-xs text-destructive">
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
          <pre className="font-mono mt-1 p-2 bg-muted/40 rounded whitespace-pre-wrap overflow-x-auto">
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
        className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
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
