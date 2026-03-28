"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

interface BotAccess {
  name: string;
  operator: string;
  category: string;
  allowed: boolean;
  market_share: number;
}

export interface DiscoveryReport {
  url: string;
  robots_txt_found: boolean;
  bot_access: BotAccess[];
  bots_allowed: number;
  bots_blocked: number;
  llms_txt_found: boolean;
  llms_txt_length: number;
  llms_txt_preview: string | null;
  sitemap_found: boolean;
  sitemap_url_count: number | null;
  is_ssr: boolean;
  structured_data_types: string[];
  ai_visibility_pct: number;
  page_title: string | null;
  word_count: number;
}

interface DiscoveryTabProps {
  discovery: DiscoveryReport | null;
  loading: boolean;
}

function scoreColor(pct: number): string {
  if (pct >= 70) return "#22c55e";
  if (pct >= 40) return "#eab308";
  return "#ef4444";
}

function scoreTextColor(pct: number): string {
  if (pct >= 70) return "text-green-500";
  if (pct >= 40) return "text-yellow-500";
  return "text-red-500";
}

export function DiscoveryTab({ discovery, loading }: DiscoveryTabProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <p className="text-muted-foreground font-mono animate-pulse text-sm">Scanning...</p>
      </div>
    );
  }

  if (!discovery) {
    return (
      <div className="flex items-center justify-center py-24">
        <p className="text-muted-foreground text-sm">Enter a URL above to discover your AI visibility</p>
      </div>
    );
  }

  const pct = Math.round(discovery.ai_visibility_pct);
  const donutData = [
    { value: pct },
    { value: 100 - pct },
  ];
  const color = scoreColor(pct);
  const textColor = scoreTextColor(pct);

  const totalBots = discovery.bots_allowed + discovery.bots_blocked;

  return (
    <div className="space-y-6">
      {/* Section 1: AI Visibility Score */}
      <div className="flex flex-col items-center gap-2 py-4">
        <div className="relative w-48 h-48">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={donutData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                startAngle={90}
                endAngle={-270}
                dataKey="value"
                strokeWidth={0}
              >
                <Cell fill={color} />
                <Cell fill="#e5e7eb" />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-4xl font-bold font-mono ${textColor}`}>{pct}</span>
            <span className="text-xs text-muted-foreground font-mono">/ 100</span>
          </div>
        </div>
        <p className="text-sm text-muted-foreground font-mono">
          {discovery.bots_allowed}/{totalBots} bots can discover your site
        </p>
      </div>

      <Separator />

      {/* Section 2: Bot Access Grid */}
      <div>
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">Bot Access</p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {discovery.bot_access.map((bot) => (
            <div
              key={bot.name}
              className="border rounded-md px-3 py-2 flex flex-col gap-0.5"
            >
              <div className="flex items-center gap-1.5">
                <span
                  className={`w-2 h-2 rounded-full flex-shrink-0 ${bot.allowed ? "bg-green-500" : "bg-red-500"}`}
                />
                <span className="text-xs font-mono font-medium truncate">{bot.name}</span>
              </div>
              <span className="text-[10px] text-muted-foreground pl-3.5 truncate">{bot.operator}</span>
              <span className={`text-[10px] pl-3.5 ${bot.allowed ? "text-green-600" : "text-red-500"}`}>
                {bot.allowed ? "Allowed" : "Blocked"}
              </span>
            </div>
          ))}
        </div>
      </div>

      <Separator />

      {/* Section 3: Discovery Signals */}
      <div>
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">Discovery Signals</p>
        <div className="grid grid-cols-3 gap-3">
          {/* robots.txt */}
          <div className="border rounded-md p-3 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-medium">robots.txt</span>
              <Badge variant={discovery.robots_txt_found ? "default" : "secondary"} className="text-[10px] h-4">
                {discovery.robots_txt_found ? "found" : "missing"}
              </Badge>
            </div>
            <p className="text-[10px] text-muted-foreground">
              {discovery.robots_txt_found
                ? "Crawl directives present"
                : "No crawl directives"}
            </p>
          </div>

          {/* llms.txt */}
          <div className="border rounded-md p-3 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-medium">llms.txt</span>
              <Badge variant={discovery.llms_txt_found ? "default" : "secondary"} className="text-[10px] h-4">
                {discovery.llms_txt_found ? "found" : "missing"}
              </Badge>
            </div>
            {discovery.llms_txt_found && discovery.llms_txt_preview ? (
              <p className="text-[10px] font-mono text-muted-foreground truncate">{discovery.llms_txt_preview}</p>
            ) : (
              <p className="text-[10px] text-muted-foreground">AI context file not found</p>
            )}
            {discovery.llms_txt_found && (
              <p className="text-[10px] text-muted-foreground font-mono">{discovery.llms_txt_length} chars</p>
            )}
          </div>

          {/* sitemap.xml */}
          <div className="border rounded-md p-3 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-medium">sitemap.xml</span>
              <Badge variant={discovery.sitemap_found ? "default" : "secondary"} className="text-[10px] h-4">
                {discovery.sitemap_found ? "found" : "missing"}
              </Badge>
            </div>
            {discovery.sitemap_found && discovery.sitemap_url_count !== null ? (
              <p className="text-[10px] font-mono text-muted-foreground">{discovery.sitemap_url_count} URLs indexed</p>
            ) : (
              <p className="text-[10px] text-muted-foreground">No sitemap detected</p>
            )}
          </div>
        </div>
      </div>

      <Separator />

      {/* Section 4: Page Snapshot */}
      <div>
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">Page Snapshot</p>
        <div className="bg-muted/50 rounded-md p-4 font-mono text-xs space-y-1.5 border">
          <div className="flex gap-2">
            <span className="text-muted-foreground w-32 flex-shrink-0">page_title</span>
            <span className="text-foreground">{discovery.page_title ?? "null"}</span>
          </div>
          <div className="flex gap-2">
            <span className="text-muted-foreground w-32 flex-shrink-0">word_count</span>
            <span className="text-foreground">{discovery.word_count}</span>
          </div>
          <div className="flex gap-2">
            <span className="text-muted-foreground w-32 flex-shrink-0">ssr</span>
            <span className={discovery.is_ssr ? "text-green-500" : "text-red-500"}>
              {discovery.is_ssr ? "true" : "false"}
            </span>
          </div>
          <div className="flex gap-2">
            <span className="text-muted-foreground w-32 flex-shrink-0">structured_data</span>
            <span className="text-foreground">
              {discovery.structured_data_types.length > 0
                ? discovery.structured_data_types.join(", ")
                : "none"}
            </span>
          </div>
          <div className="flex gap-2">
            <span className="text-muted-foreground w-32 flex-shrink-0">url</span>
            <span className="text-foreground truncate">{discovery.url}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
