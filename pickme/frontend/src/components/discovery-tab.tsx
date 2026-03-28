"use client";

import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

interface BotAccess {
  name: string;
  operator: string;
  category: string;
  allowed: boolean;
  market_share: number;
}

interface SignalFinding {
  name: string;
  status: string;
  value: string;
  consequence: string;
  impact: string;
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
  markdown_preview: string | null;
  markdown_token_count: number;
  content_quality: SignalFinding[];
  signals: SignalFinding[];
}

interface DiscoveryTabProps {
  discovery: DiscoveryReport | null;
  loading: boolean;
}

const IMPACT_STYLES: Record<string, string> = {
  critical: "border-red-500/40 bg-red-500/5",
  high: "border-orange-400/40 bg-orange-400/5",
  medium: "border-yellow-400/40 bg-yellow-400/5",
  low: "border-green-500/40 bg-green-500/5",
};

const IMPACT_BADGE: Record<string, "destructive" | "default" | "secondary" | "outline"> = {
  critical: "destructive",
  high: "default",
  medium: "secondary",
  low: "outline",
};

const STATUS_DOT: Record<string, string> = {
  found: "bg-green-500",
  missing: "bg-red-500",
  partial: "bg-yellow-500",
};

export function DiscoveryTab({ discovery, loading }: DiscoveryTabProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <p className="text-muted-foreground animate-pulse">Scanning...</p>
      </div>
    );
  }

  if (!discovery) {
    return (
      <div className="flex items-center justify-center py-24">
        <p className="text-muted-foreground">Enter a URL above to discover your AI visibility</p>
      </div>
    );
  }

  const pct = Math.round(discovery.ai_visibility_pct);
  const donutData = [{ value: pct }, { value: 100 - pct }];
  const color = pct >= 70 ? "#3b82f6" : pct >= 40 ? "#eab308" : "#ef4444";
  const textColor = pct >= 70 ? "text-blue-400" : pct >= 40 ? "text-yellow-500" : "text-red-500";
  const totalBots = discovery.bots_allowed + discovery.bots_blocked;

  return (
    <div className="space-y-8 pt-4">

      {/* AI Visibility Score */}
      <div className="flex items-start gap-8">
        <div className="flex flex-col items-center gap-2">
          <div className="relative w-40 h-40">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={donutData} cx="50%" cy="50%" innerRadius={52} outerRadius={68} startAngle={90} endAngle={-270} dataKey="value" strokeWidth={0}>
                  <Cell fill={color} />
                  <Cell fill="rgba(255,255,255,0.06)" />
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={`text-3xl font-bold font-mono ${textColor}`}>{pct}</span>
              <span className="text-xs text-muted-foreground">/100</span>
            </div>
          </div>
          <p className="text-sm text-muted-foreground text-center">
            <span className="font-mono font-medium">{discovery.bots_allowed}/{totalBots}</span> bots can reach your site
          </p>
        </div>

        <div className="flex-1 space-y-1.5">
          <p className="text-xl font-semibold">{discovery.page_title || discovery.url}</p>
          <p className="text-sm text-muted-foreground font-mono">{discovery.url}</p>
          <div className="flex gap-4 mt-3 text-sm">
            <div>
              <span className="text-muted-foreground">Words: </span>
              <span className="font-mono">{discovery.word_count.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Tokens (markdown): </span>
              <span className="font-mono">{discovery.markdown_token_count.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-muted-foreground">SSR: </span>
              <span className={discovery.is_ssr ? "text-green-600" : "text-red-500"}>{discovery.is_ssr ? "Yes" : "No"}</span>
            </div>
          </div>
          {discovery.structured_data_types.length > 0 && (
            <div className="flex gap-1 mt-2 flex-wrap">
              {discovery.structured_data_types.map((t) => (
                <Badge key={t} variant="outline" className="text-xs font-mono">{t}</Badge>
              ))}
            </div>
          )}
        </div>
      </div>

      <Separator />

      {/* Discovery Signals with Consequences */}
      <div className="space-y-3">
        <p className="text-lg font-semibold text-foreground">
          <em>Discovery Signals</em>
        </p>
        <p className="text-sm text-muted-foreground">
          How AI crawlers find and navigate your site
        </p>
        <div className="space-y-2">
          {(discovery.signals || []).map((signal) => (
            <FindingCard key={signal.name} finding={signal} />
          ))}
        </div>
      </div>

      <Separator />

      {/* Content Quality */}
      <div className="space-y-3">
        <p className="text-lg font-semibold text-foreground">
          <em>Content Quality</em>
        </p>
        <p className="text-sm text-muted-foreground">
          How well AI agents can parse and cite your content
        </p>
        <div className="space-y-2">
          {(discovery.content_quality || []).map((finding) => (
            <FindingCard key={finding.name} finding={finding} />
          ))}
        </div>
      </div>

      <Separator />

      {/* Bot Access Grid */}
      <div className="space-y-3">
        <p className="text-lg font-semibold text-foreground">
          <em>Bot Access Map</em>
        </p>
        <p className="text-sm text-muted-foreground">
          Which AI bots can crawl your site based on robots.txt rules
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {discovery.bot_access.map((bot) => (
            <div key={bot.name} className="border rounded-md px-3 py-2 flex items-center gap-2 bg-card">
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${bot.allowed ? "bg-green-500" : "bg-red-500"}`} />
              <div className="min-w-0">
                <p className="text-sm font-mono truncate">{bot.name}</p>
                <p className="text-xs text-muted-foreground">{bot.operator}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <Separator />

      {/* Agent's View — Markdown Preview */}
      {discovery.markdown_preview && (
        <div className="space-y-3">
          <p className="text-lg font-semibold text-foreground">
            <em>Agent&apos;s View</em>
          </p>
          <p className="text-sm text-muted-foreground">
            This is what an AI agent sees after stripping navigation, scripts, and styling from your page.
            Raw HTML uses ~3x more tokens than this cleaned markdown.
          </p>
          <div className="bg-zinc-950 text-zinc-300 rounded-md p-4 font-mono text-xs max-h-80 overflow-y-auto whitespace-pre-wrap leading-relaxed">
            {discovery.markdown_preview}
          </div>
        </div>
      )}
    </div>
  );
}

function FindingCard({ finding }: { finding: SignalFinding }) {
  const borderStyle = IMPACT_STYLES[finding.impact] || IMPACT_STYLES.low;
  const dotColor = STATUS_DOT[finding.status] || STATUS_DOT.missing;

  return (
    <div className={`border rounded-md p-3 ${borderStyle}`}>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${dotColor}`} />
          <span className="text-sm font-medium">{finding.name}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-muted-foreground">{finding.value}</span>
          <Badge variant={IMPACT_BADGE[finding.impact] || "outline"} className="text-xs">
            {finding.impact}
          </Badge>
        </div>
      </div>
      <p className="text-sm text-muted-foreground pl-4">
        {finding.consequence}
      </p>
    </div>
  );
}
