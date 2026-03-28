"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts";

interface TrafficSummary {
  total_requests: number;
  human: number;
  ai_crawler: number;
  ai_agent: number;
  shopping_agent: number;
  unknown: number;
  per_bot: Record<string, number>;
}

const COLORS = {
  Human: "#6366f1",
  "AI Crawlers": "#f59e0b",
  "AI Agents": "#ef4444",
  "Shopping Agents": "#10b981",
  Unknown: "#6b7280",
};

export function TrafficPanel({ traffic }: { traffic: TrafficSummary | null }) {
  if (!traffic) {
    return (
      <Card>
        <CardHeader><CardTitle>Agent Traffic</CardTitle></CardHeader>
        <CardContent><p className="text-muted-foreground">Upload a server log to classify traffic</p></CardContent>
      </Card>
    );
  }

  const pieData = [
    { name: "Human", value: traffic.human },
    { name: "AI Crawlers", value: traffic.ai_crawler },
    { name: "AI Agents", value: traffic.ai_agent },
    { name: "Shopping Agents", value: traffic.shopping_agent },
    { name: "Unknown", value: traffic.unknown },
  ].filter((d) => d.value > 0);

  const botData = Object.entries(traffic.per_bot)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  const agentPct = Math.round(((traffic.ai_crawler + traffic.ai_agent + traffic.shopping_agent) / traffic.total_requests) * 100);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Agent Traffic
          <span className="text-2xl font-bold text-red-500">{agentPct}% AI</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">{traffic.total_requests.toLocaleString()} total requests analyzed</p>
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}>
              {pieData.map((entry) => (
                <Cell key={entry.name} fill={COLORS[entry.name as keyof typeof COLORS] || "#999"} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>

        {botData.length > 0 && (
          <>
            <p className="text-sm font-medium">Per-Bot Breakdown</p>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={botData} layout="vertical" margin={{ left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="name" width={75} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </>
        )}
      </CardContent>
    </Card>
  );
}
