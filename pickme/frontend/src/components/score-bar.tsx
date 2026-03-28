"use client";

interface ScoreBarProps {
  label: string;
  score: number;
  maxScore: number;
}

export function ScoreBar({ label, score, maxScore }: ScoreBarProps) {
  const pct = Math.round((score / maxScore) * 100);
  const color = pct >= 70 ? "bg-green-500" : pct >= 40 ? "bg-yellow-500" : "bg-red-500";

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm w-20 text-muted-foreground">{label}</span>
      <div className="flex-1 h-3 bg-muted rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-mono w-12 text-right">{score}/{maxScore}</span>
    </div>
  );
}
