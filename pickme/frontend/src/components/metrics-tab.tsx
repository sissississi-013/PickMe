"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";

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

interface MetricsTabProps {
  reports: ScoutReport[];
  loading: boolean;
}

function scoreTextColor(pct: number): string {
  if (pct >= 70) return "text-green-500";
  if (pct >= 40) return "text-yellow-500";
  return "text-red-500";
}

export function MetricsTab({ reports, loading }: MetricsTabProps) {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());

  function toggleCategory(key: string) {
    setExpandedKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <p className="text-muted-foreground font-mono animate-pulse text-sm">Analyzing...</p>
      </div>
    );
  }

  if (reports.length === 0) {
    return (
      <div className="flex items-center justify-center py-24">
        <p className="text-muted-foreground text-sm">Enter a URL above to see your metrics</p>
      </div>
    );
  }

  const totalScore = reports.reduce((sum, r) => sum + r.total_score, 0);
  const totalMax = reports.reduce((sum, r) => sum + r.max_score, 0);
  const normalizedPct = totalMax > 0 ? Math.round((totalScore / totalMax) * 100) : 0;
  const textColor = scoreTextColor(normalizedPct);

  return (
    <div className="space-y-6">
      {/* Section 1: Overall Score */}
      <div className="flex items-center gap-4 pb-2">
        <span className={`text-5xl font-bold font-mono ${textColor}`}>{normalizedPct}</span>
        <div className="flex flex-col gap-0.5">
          <span className="text-sm text-muted-foreground font-mono">{totalScore} / {totalMax} pts</span>
          <span className="text-xs text-muted-foreground">overall AI-readiness score</span>
        </div>
      </div>

      <Separator />

      {/* Section 2: Per-report sections */}
      {reports.map((report) => {
        const reportPct = report.max_score > 0
          ? Math.round((report.total_score / report.max_score) * 100)
          : 0;

        return (
          <div key={report.scout_type} className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="font-mono text-xs uppercase">
                  {report.scout_type}
                </Badge>
                <span className="text-xs text-muted-foreground font-mono">{report.target}</span>
              </div>
              <span className={`font-mono text-sm font-semibold ${scoreTextColor(reportPct)}`}>
                {report.total_score}/{report.max_score}
              </span>
            </div>

            <div className="space-y-2.5">
              {report.categories.map((cat) => {
                const catPct = cat.max_score > 0 ? Math.round((cat.score / cat.max_score) * 100) : 0;
                const key = `${report.scout_type}-${cat.name}`;
                const isExpanded = expandedKeys.has(key);

                return (
                  <div key={cat.name} className="space-y-1.5">
                    <button
                      className="w-full text-left group"
                      onClick={() => toggleCategory(key)}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium group-hover:text-foreground text-muted-foreground transition-colors">
                          {cat.name}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono text-muted-foreground">
                            {cat.score}/{cat.max_score}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {isExpanded ? "▲" : "▼"}
                          </span>
                        </div>
                      </div>
                      <Progress value={catPct} className="h-1.5" />
                    </button>

                    {isExpanded && (
                      <div className="pl-2 border-l border-border ml-1 space-y-2 pt-1 pb-2">
                        {cat.checks.map((check, i) => (
                          <div key={i} className="space-y-0.5">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <Badge
                                  variant={check.passed ? "default" : "destructive"}
                                  className="text-[9px] h-4 px-1.5"
                                >
                                  {check.passed ? "pass" : "fail"}
                                </Badge>
                                <span className="text-xs font-mono">{check.name}</span>
                              </div>
                              <span className="text-xs font-mono text-muted-foreground">
                                {check.points_earned}/{check.points_possible} pts
                              </span>
                            </div>
                            {check.detail && (
                              <p className="text-xs text-muted-foreground pl-10">{check.detail}</p>
                            )}
                            {check.research_basis && (
                              <p className="text-xs text-muted-foreground/60 pl-10 italic">{check.research_basis}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
