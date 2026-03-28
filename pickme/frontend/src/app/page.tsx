"use client";

import { useState } from "react";
import { ScanInput } from "@/components/scan-input";
import { DiscoveryTab } from "@/components/discovery-tab";
import { MetricsTab } from "@/components/metrics-tab";
import { SimulationTab } from "@/components/simulation-tab";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { apiPost } from "@/lib/api";
import Image from "next/image";

export default function Home() {
  const [discovery, setDiscovery] = useState<any>(null);
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUrl, setLastUrl] = useState("");

  async function handleScan(url: string) {
    setLoading(true);
    setError(null);
    setLastUrl(url);
    try {
      const [discoverResult, webReport, apiReport] = await Promise.all([
        apiPost("/api/discover", { url }),
        apiPost("/api/scout/web", { url }),
        apiPost("/api/scout/api", { url }).catch(() => null),
      ]);
      setDiscovery(discoverResult);
      setReports([webReport, apiReport].filter(Boolean));
    } catch (err: any) {
      setError(err?.message || "Scan failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-background">
      <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
        <div className="flex items-center gap-3 -ml-1 pb-4 border-b border-border">
          <Image src="/logo-light.png" alt="PickMe" width={120} height={36} priority />
          <p className="text-sm text-muted-foreground border-l pl-3">AI Agent Discoverability Engine</p>
        </div>

        <ScanInput onScan={handleScan} loading={loading} />

        {error && (
          <div className="text-sm text-destructive border border-destructive/30 rounded-md px-3 py-2">
            {error}
          </div>
        )}

        <Tabs defaultValue={0}>
          <TabsList variant="line">
            <TabsTrigger value={0}>Discovery</TabsTrigger>
            <TabsTrigger value={1}>Metrics</TabsTrigger>
            <TabsTrigger value={2}>Simulation</TabsTrigger>
          </TabsList>
          <TabsContent value={0}>
            <DiscoveryTab discovery={discovery} loading={loading} />
          </TabsContent>
          <TabsContent value={1}>
            <MetricsTab reports={reports} loading={loading} />
          </TabsContent>
          <TabsContent value={2}>
            <SimulationTab reports={reports} lastUrl={lastUrl} onRescan={() => handleScan(lastUrl)} />
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}
