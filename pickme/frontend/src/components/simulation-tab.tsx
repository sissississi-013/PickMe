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

interface AgentDecision {
  agent_label: string;
  picked_tool: string;
  reasoning: string;
  tools_evaluated: string[];
  confidence: string;
  raw_output: string;
}

interface LogEntry {
  timestamp: number;
  step: string;
  detail: string;
  data: string | null;
}

interface SimulationResult {
  task: string;
  target_tool: string;
  before: AgentDecision;
  after: AgentDecision;
  optimization_effective: boolean;
  summary: string;
  optimized_description: string;
  activity_log: LogEntry[];
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

export function SimulationTab({ reports, lastUrl, onRescan }: SimulationTabProps) {
  // Optimizer state
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [totalGain, setTotalGain] = useState(0);
  const [optimizerLoading, setOptimizerLoading] = useState(false);
  const [expandedRec, setExpandedRec] = useState<number | null>(null);

  // Agent simulation state
  const [toolName, setToolName] = useState("FastAPI");
  const [toolUrl, setToolUrl] = useState("");
  const [toolDesc, setToolDesc] = useState("A modern, fast web framework for building APIs with Python");
  const [simTask, setSimTask] = useState("Build a REST API backend for a task management app");
  const [competitors, setCompetitors] = useState("");
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [simLoading, setSimLoading] = useState(false);
  const [simError, setSimError] = useState<string | null>(null);

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

  async function runSimulation() {
    setSimLoading(true);
    setSimResult(null);
    setSimError(null);
    try {
      const compList = competitors.trim()
        ? competitors.split(",").map((c) => c.trim()).filter(Boolean)
        : null;

      const result = await apiPost<SimulationResult>("/api/simulate", {
        target_tool: toolName,
        target_url: toolUrl || null,
        target_description: toolDesc,
        task: simTask,
        competitors: compList,
      });
      setSimResult(result);
    } catch (err: any) {
      setSimError(err?.message || "Simulation failed");
    } finally {
      setSimLoading(false);
    }
  }

  return (
    <div className="space-y-8 pt-4">

      {/* Section 1: Optimization Recommendations */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">Optimization Recommendations</p>
            <p className="text-sm text-muted-foreground mt-0.5">
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

      {/* Section 2: Agent Simulation */}
      <div className="space-y-4">
        <div>
          <p className="font-medium">Agent Simulation</p>
          <p className="text-sm text-muted-foreground mt-0.5">
            Two parallel agents evaluate your tool against real competitors. One sees the original description, the other sees an optimized version.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <label className="text-sm text-muted-foreground">Tool / Framework / API name</label>
            <Input
              value={toolName}
              onChange={(e) => setToolName(e.target.value)}
              placeholder="e.g. FastAPI, Stripe, React"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm text-muted-foreground">Documentation URL (optional)</label>
            <Input
              value={toolUrl}
              onChange={(e) => setToolUrl(e.target.value)}
              placeholder="https://github.com/..."
              className="font-mono text-sm"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-sm text-muted-foreground">Current description of your tool</label>
          <textarea
            className="w-full h-20 text-sm border rounded-md p-3 bg-muted/30 resize-none focus:outline-none focus:ring-1 focus:ring-ring"
            value={toolDesc}
            onChange={(e) => setToolDesc(e.target.value)}
            placeholder="Describe what your tool does..."
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <label className="text-sm text-muted-foreground">Task for the agent</label>
            <Input
              value={simTask}
              onChange={(e) => setSimTask(e.target.value)}
              placeholder="Build a REST API backend..."
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm text-muted-foreground">Competitors (optional, comma-separated)</label>
            <Input
              value={competitors}
              onChange={(e) => setCompetitors(e.target.value)}
              placeholder="Express, Django, Flask, Spring Boot"
              className="font-mono text-sm"
            />
          </div>
        </div>

        <Button
          onClick={runSimulation}
          disabled={simLoading || !toolName.trim() || !simTask.trim()}
        >
          {simLoading ? "Running simulation (~30s)..." : "Run Agent Simulation"}
        </Button>

        {simError && (
          <div className="border border-destructive/30 rounded-md p-3">
            <p className="text-sm text-destructive">{simError}</p>
          </div>
        )}

        {simResult && (
          <div className="space-y-4">
            {/* Summary */}
            <div className={`border rounded-md p-4 ${
              simResult.optimization_effective
                ? "border-green-500 bg-green-50 dark:bg-green-950/30"
                : "border-border"
            }`}>
              <p className="text-sm font-medium">{simResult.summary}</p>
            </div>

            {/* Side by side agent decisions */}
            <div className="grid grid-cols-2 gap-4">
              <AgentCard decision={simResult.before} targetTool={simResult.target_tool} title="Agent A — Original" />
              <AgentCard decision={simResult.after} targetTool={simResult.target_tool} title="Agent B — Optimized" />
            </div>

            {/* Optimized description */}
            {simResult.optimized_description && (
              <div className="space-y-1.5">
                <p className="text-sm font-medium">Optimized Description</p>
                <pre className="text-sm font-mono bg-muted/40 p-3 rounded-md border whitespace-pre-wrap">
                  {simResult.optimized_description}
                </pre>
              </div>
            )}

            {/* Activity Log */}
            {simResult.activity_log.length > 0 && (
              <ActivityLog logs={simResult.activity_log} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function AgentCard({ decision, targetTool, title }: { decision: AgentDecision; targetTool: string; title: string }) {
  const pickedTarget = decision.picked_tool.toLowerCase().includes(targetTool.toLowerCase());

  return (
    <div className={`border rounded-md p-4 space-y-3 ${
      pickedTarget ? "border-green-500" : "border-red-500"
    }`}>
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">{title}</p>
        <Badge variant={pickedTarget ? "default" : "destructive"} className="text-xs">
          {pickedTarget ? "picked your tool" : "picked competitor"}
        </Badge>
      </div>

      <div>
        <p className="text-xs text-muted-foreground">Recommended:</p>
        <p className="text-base font-mono font-medium">{decision.picked_tool}</p>
      </div>

      <div>
        <p className="text-xs text-muted-foreground">Reasoning:</p>
        <p className="text-sm">{decision.reasoning}</p>
      </div>

      <div>
        <p className="text-xs text-muted-foreground">Tools evaluated:</p>
        <div className="flex flex-wrap gap-1 mt-1">
          {decision.tools_evaluated.map((t, i) => (
            <span
              key={i}
              className={`text-xs font-mono px-1.5 py-0.5 rounded ${
                t.toLowerCase().includes(targetTool.toLowerCase())
                  ? "bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              {t}
            </span>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <p className="text-xs text-muted-foreground">Confidence:</p>
        <Badge variant="outline" className="text-xs">{decision.confidence}</Badge>
      </div>

      {/* Show the actual prompt sent to Claude */}
      <details className="text-xs">
        <summary className="text-muted-foreground cursor-pointer">View agent prompt</summary>
        <div className="mt-2 space-y-2">
          <div>
            <p className="text-muted-foreground font-medium">System prompt:</p>
            <pre className="font-mono mt-1 p-2 bg-muted/40 rounded whitespace-pre-wrap overflow-x-auto text-xs">
              {decision.raw_output ? decision.raw_output : "N/A"}
            </pre>
          </div>
        </div>
      </details>
    </div>
  );
}

const STEP_COLORS: Record<string, string> = {
  init: "text-blue-500",
  fetch_docs: "text-cyan-500",
  competitors: "text-purple-500",
  optimize: "text-yellow-500",
  agent_a: "text-orange-500",
  agent_b: "text-green-500",
  result: "text-white font-medium",
};

function ActivityLog({ logs }: { logs: LogEntry[] }) {
  const startTime = logs.length > 0 ? logs[0].timestamp : 0;

  return (
    <div className="space-y-1.5">
      <p className="text-sm font-medium">Activity Log</p>
      <div className="bg-zinc-950 text-zinc-300 rounded-md p-4 font-mono text-xs max-h-96 overflow-y-auto space-y-0.5">
        {logs.map((log, i) => {
          const elapsed = ((log.timestamp - startTime) * 1000).toFixed(0);
          const color = STEP_COLORS[log.step] || "text-zinc-400";
          return (
            <div key={i}>
              <div className="flex gap-2">
                <span className="text-zinc-600 w-16 flex-shrink-0 text-right">{elapsed}ms</span>
                <span className={`w-24 flex-shrink-0 ${color}`}>[{log.step}]</span>
                <span className="text-zinc-300">{log.detail}</span>
              </div>
              {log.data && (
                <details className="ml-[10.5rem]">
                  <summary className="text-zinc-600 cursor-pointer hover:text-zinc-400">data</summary>
                  <pre className="text-zinc-500 whitespace-pre-wrap mt-0.5 pl-2 border-l border-zinc-800">
                    {log.data}
                  </pre>
                </details>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
