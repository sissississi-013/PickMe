"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiPost } from "@/lib/api";

interface BenchmarkResult {
  llm_name: string;
  pick_rate_before: number;
  pick_rate_after: number | null;
}

interface BenchmarkPanelProps {
  beforeScore: number | null;
  afterScore: number | null;
}

export function BenchmarkPanel({ beforeScore, afterScore }: BenchmarkPanelProps) {
  const [taskPrompt, setTaskPrompt] = useState("Create a new issue to track this bug");
  const [toolBefore, setToolBefore] = useState('{"name": "create", "description": "creates stuff", "inputSchema": {"type": "object", "properties": {"data": {"type": "object"}}}}');
  const [toolAfter, setToolAfter] = useState('{"name": "github_create_issue", "description": "Create a new issue in a GitHub repository. Use when the user wants to report a bug or request a feature. Returns the issue URL and number.", "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string"}}}}');
  const [proofResult, setProofResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function runProof() {
    setLoading(true);
    try {
      const result = await apiPost("/api/benchmark/tool-proof", {
        task_prompt: taskPrompt,
        tool_before: JSON.parse(toolBefore),
        tool_after: JSON.parse(toolAfter),
      });
      setProofResult(result);
    } catch (err) {
      console.error("Proof failed:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Before / After Proof</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {beforeScore !== null && (
          <div className="flex items-center gap-4 text-lg">
            <span className="font-mono">{beforeScore}</span>
            <span className="text-muted-foreground">&rarr;</span>
            {afterScore !== null ? (
              <>
                <span className="font-mono font-bold text-green-600">{afterScore}</span>
                <span className="text-green-600 text-sm">(+{afterScore - beforeScore})</span>
              </>
            ) : (
              <span className="text-muted-foreground">re-scan to see improvement</span>
            )}
          </div>
        )}

        <div className="border-t pt-4 space-y-3">
          <p className="text-sm font-medium">Live Agent Tool Selection Proof</p>
          <p className="text-xs text-muted-foreground">Give Claude two tool descriptions (original vs. optimized) and watch which one it picks</p>

          <Input placeholder="Task prompt for the agent..." value={taskPrompt} onChange={(e) => setTaskPrompt(e.target.value)} />

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs text-muted-foreground">Original Tool (before)</label>
              <textarea className="w-full h-24 text-xs font-mono border rounded p-2 bg-muted" value={toolBefore} onChange={(e) => setToolBefore(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Optimized Tool (after)</label>
              <textarea className="w-full h-24 text-xs font-mono border rounded p-2 bg-muted" value={toolAfter} onChange={(e) => setToolAfter(e.target.value)} />
            </div>
          </div>

          <Button onClick={runProof} disabled={loading}>
            {loading ? "Running..." : "Run Live Agent Proof"}
          </Button>

          {proofResult && (
            <div className={`border rounded-lg p-4 ${proofResult.picked_optimized ? "border-green-500 bg-green-50 dark:bg-green-950" : "border-red-500 bg-red-50 dark:bg-red-950"}`}>
              <p className="font-medium">
                Claude picked: <span className="font-mono">{proofResult.picked}</span>
                {proofResult.picked_optimized ? " (optimized version!)" : " (original version)"}
              </p>
              <pre className="text-xs mt-2 whitespace-pre-wrap">{JSON.stringify(proofResult.response, null, 2)}</pre>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
