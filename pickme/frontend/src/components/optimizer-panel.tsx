"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiPost } from "@/lib/api";

interface Recommendation {
  severity: string;
  issue: string;
  why_it_matters: string;
  fix: string;
  predicted_impact: number;
}

interface OptimizerPanelProps {
  reports: any[];
  onRescan: () => void;
}

const severityColors: Record<string, string> = {
  critical: "destructive",
  high: "default",
  medium: "secondary",
  low: "outline",
};

export function OptimizerPanel({ reports, onRescan }: OptimizerPanelProps) {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [totalGain, setTotalGain] = useState(0);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);

  async function handleOptimize() {
    if (reports.length === 0) return;
    setLoading(true);
    try {
      for (const report of reports) {
        const result: any = await apiPost("/api/optimize", report);
        setRecommendations((prev) => [...prev, ...result.recommendations]);
        setTotalGain((prev) => prev + result.total_predicted_gain);
      }
    } catch (err) {
      console.error("Optimization failed:", err);
    } finally {
      setLoading(false);
    }
  }

  if (reports.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Optimization Recommendations
          <div className="flex gap-2">
            {recommendations.length > 0 && (
              <Button variant="outline" size="sm" onClick={onRescan}>Re-scan After</Button>
            )}
            <Button size="sm" onClick={handleOptimize} disabled={loading}>
              {loading ? "Analyzing..." : recommendations.length > 0 ? "Re-analyze" : "Generate Fixes"}
            </Button>
          </div>
        </CardTitle>
        {totalGain > 0 && (
          <p className="text-sm text-green-600">Predicted improvement: +{totalGain} points</p>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {recommendations.length === 0 && !loading && (
          <p className="text-muted-foreground text-sm">Click &quot;Generate Fixes&quot; to get optimization recommendations</p>
        )}
        {recommendations.map((rec, i) => (
          <div key={i} className="border rounded-lg p-3 space-y-2 cursor-pointer" onClick={() => setExpanded(expanded === i ? null : i)}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant={severityColors[rec.severity] as any}>{rec.severity}</Badge>
                <span className="text-sm font-medium">{rec.issue}</span>
              </div>
              <span className="text-sm text-green-600 font-mono">+{rec.predicted_impact} pts</span>
            </div>
            {expanded === i && (
              <div className="space-y-2 pt-2 border-t">
                <p className="text-xs text-muted-foreground">{rec.why_it_matters}</p>
                <pre className="text-xs bg-muted p-3 rounded overflow-x-auto whitespace-pre-wrap">{rec.fix}</pre>
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
