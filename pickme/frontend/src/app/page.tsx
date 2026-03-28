"use client";

import { useState, useEffect } from "react";
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
  const [dark, setDark] = useState(true);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

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
    <main className="min-h-screen bg-background text-foreground">
      <div className="max-w-5xl mx-auto px-8 py-10 space-y-8">

        {/* Header */}
        <div className="flex items-center justify-between pb-6 border-b border-border">
          <div className="flex items-center gap-4">
            <Image
              src={dark ? "/logo-light.png" : "/logo.png"}
              alt="PickMe"
              width={130}
              height={38}
              priority
            />
            <div className="border-l border-border pl-4">
              <p className="text-base text-muted-foreground">
                Make your brand get picked by AI agents
              </p>
            </div>
          </div>
          <button
            onClick={() => setDark(!dark)}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors px-3 py-1.5 rounded-md border border-border"
          >
            {dark ? "Light" : "Dark"}
          </button>
        </div>

        {/* Search */}
        <ScanInput onScan={handleScan} loading={loading} />

        {error && (
          <div className="text-sm text-destructive border border-destructive/30 rounded-md px-4 py-3">
            {error}
          </div>
        )}

        {/* Tabs */}
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
