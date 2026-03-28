"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { apiPost } from "@/lib/api";

interface CheckResult {
  name: string;
  passed: boolean;
  points_earned: number;
  points_possible: number;
  detail: string;
  research_basis: string;
}

interface CategoryScore {
  name: string;
  score: number;
  max_score: number;
  checks: CheckResult[];
}

export interface ScoutReport {
  target: string;
  scout_type: string;
  total_score: number;
  max_score: number;
  categories: CategoryScore[];
}

interface Recommendation {
  severity: string;
  issue: string;
  why_it_matters: string;
  fix: string;
  predicted_impact: number;
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

const DEFAULT_TOOL_BEFORE = `{"name": "create", "description": "creates stuff", "inputSchema": {"type": "object", "properties": {"data": {"type": "object"}}}}`;

const DEFAULT_TOOL_AFTER = `{"name": "github_create_issue", "description": "Create a new issue in a GitHub repository. Use when the user wants to report a bug or request a feature. Returns the issue URL and number.", "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string"}}}}`;

export function SimulationTab({ reports, lastUrl, onRescan }: SimulationTabProps) {
  // Optimizer state
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [totalGain, setTotalGain] = useState(0);
  const [optimizerLoading, setOptimizerLoading] = useState(false);
  const [expandedRec, setExpandedRec] = useState<number | null>(null);

  // Simulation state
  const [taskPrompt, setTaskPrompt] = useState("Create a new issue to track this bug");
  const [toolBefore, setToolBefore] = useState(DEFAULT_TOOL_BEFORE);
  const [toolAfter, setToolAfter] = useState(DEFAULT_TOOL_AFTER);
  const [simResult, setSimResult] = useState<any>(null);
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
      let parsedBefore: unknown;
      let parsedAfter: unknown;
      try {
        parsedBefore = JSON.parse(toolBefore);
        parsedAfter = JSON.parse(toolAfter);
      } catch {
        setSimError("Invalid JSON in tool definitions");
        setSimLoading(false);
        return;
      }
      const result = await apiPost("/api/benchmark/tool-proof", {
        task_prompt: taskPrompt,
        tool_before: parsedBefore,
        tool_after: parsedAfter,
      });
      setSimResult(result);
    } catch (err) {
      console.error("Simulation failed:", err);
      setSimError("Simulation request failed");
    } finally {
      setSimLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Section 1: Optimization Recommendations */}
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
              <Button variant="outline" size="sm" onClick={onRescan} className="text-xs">
                Re-scan
              </Button>
            )}
            <Button
              size="sm"
              onClick={handleOptimize}
              disabled={optimizerLoading || reports.length === 0}
              className="text-xs"
            >
              {optimizerLoading
                ? "Analyzing..."
                : recommendations.length > 0
                ? "Re-analyze"
                : "Generate Fixes"}
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
                    <Badge variant={severityVariant[rec.severity] ?? "outline"} className="text-[10px] h-4">
                      {rec.severity}
                    </Badge>
                    <span className="text-xs font-medium">{rec.issue}</span>
                  </div>
                  <span className="text-xs text-green-600 font-mono">+{rec.predicted_impact} pts</span>
                </div>

                {expandedRec === i && (
                  <div className="mt-3 pt-3 border-t space-y-2">
                    {rec.why_it_matters && (
                      <p className="text-[10px] text-muted-foreground">{rec.why_it_matters}</p>
                    )}
                    <pre className="text-[10px] font-mono bg-muted/60 p-3 rounded overflow-x-auto whitespace-pre-wrap border">
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
          <p className="text-sm font-medium">Live Agent Simulation</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Give Claude two tool definitions — original vs optimized — and see which one it selects
          </p>
        </div>

        <div className="space-y-2">
          <label className="text-xs text-muted-foreground">Task Prompt</label>
          <Input
            value={taskPrompt}
            onChange={(e) => setTaskPrompt(e.target.value)}
            placeholder="Describe the task for the agent..."
            className="font-mono text-xs"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground">Original Tool</label>
            <textarea
              className="w-full h-32 text-[10px] font-mono border rounded-md p-2.5 bg-muted/30 resize-none focus:outline-none focus:ring-1 focus:ring-ring"
              value={toolBefore}
              onChange={(e) => setToolBefore(e.target.value)}
              spellCheck={false}
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground">Optimized Tool</label>
            <textarea
              className="w-full h-32 text-[10px] font-mono border rounded-md p-2.5 bg-muted/30 resize-none focus:outline-none focus:ring-1 focus:ring-ring"
              value={toolAfter}
              onChange={(e) => setToolAfter(e.target.value)}
              spellCheck={false}
            />
          </div>
        </div>

        <Button
          onClick={runSimulation}
          disabled={simLoading}
          size="sm"
          className="text-xs"
        >
          {simLoading ? "Running..." : "Run Simulation"}
        </Button>

        {simError && (
          <div className="border border-red-300 bg-red-50 dark:bg-red-950/30 rounded-md p-3">
            <p className="text-xs text-red-600 font-mono">{simError}</p>
          </div>
        )}

        {simResult && (
          <div
            className={`border rounded-md p-4 space-y-2 ${
              simResult.picked_optimized
                ? "border-green-500 bg-green-50 dark:bg-green-950/30"
                : "border-red-500 bg-red-50 dark:bg-red-950/30"
            }`}
          >
            <div className="flex items-center gap-2">
              <Badge
                variant={simResult.picked_optimized ? "default" : "destructive"}
                className="text-[10px] h-4"
              >
                {simResult.picked_optimized ? "optimized selected" : "original selected"}
              </Badge>
              <span className="text-xs font-mono">{simResult.picked}</span>
            </div>
            {simResult.response && (
              <pre className="text-[10px] font-mono overflow-x-auto whitespace-pre-wrap text-muted-foreground">
                {JSON.stringify(simResult.response, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
