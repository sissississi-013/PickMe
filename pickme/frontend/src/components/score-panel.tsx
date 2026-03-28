"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScoreBar } from "./score-bar";

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

interface ScoutReport {
  target: string;
  scout_type: string;
  total_score: number;
  max_score: number;
  categories: CategoryScore[];
}

interface ScorePanelProps {
  reports: ScoutReport[];
  loading?: boolean;
}

export function ScorePanel({ reports, loading }: ScorePanelProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader><CardTitle>Pick Me Score</CardTitle></CardHeader>
        <CardContent><p className="text-muted-foreground animate-pulse">Scanning...</p></CardContent>
      </Card>
    );
  }

  if (reports.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Pick Me Score</CardTitle></CardHeader>
        <CardContent><p className="text-muted-foreground">Enter a URL above to scan</p></CardContent>
      </Card>
    );
  }

  const totalScore = reports.reduce((sum, r) => sum + r.total_score, 0);
  const totalMax = reports.reduce((sum, r) => sum + r.max_score, 0);
  const normalizedScore = Math.round((totalScore / totalMax) * 100);
  const scoreColor = normalizedScore >= 70 ? "text-green-500" : normalizedScore >= 40 ? "text-yellow-500" : "text-red-500";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Pick Me Score
          <span className={`text-4xl font-bold ${scoreColor}`}>{normalizedScore}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {reports.map((report) => (
          <div key={report.scout_type} className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="outline">{report.scout_type.toUpperCase()}</Badge>
              <span className="text-xs text-muted-foreground">{report.target}</span>
            </div>
            {report.categories.map((cat) => (
              <ScoreBar key={cat.name} label={cat.name} score={cat.score} maxScore={cat.max_score} />
            ))}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
