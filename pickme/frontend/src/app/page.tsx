"use client";

import { useState } from "react";
import { ScanInput } from "@/components/scan-input";
import { ScorePanel } from "@/components/score-panel";
import { TrafficPanel } from "@/components/traffic-panel";
import { OptimizerPanel } from "@/components/optimizer-panel";
import { BenchmarkPanel } from "@/components/benchmark-panel";
import { apiPost, apiUpload } from "@/lib/api";

export default function Home() {
  const [reports, setReports] = useState<any[]>([]);
  const [traffic, setTraffic] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [lastUrl, setLastUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleScan(url: string) {
    setLoading(true);
    setLastUrl(url);
    try {
      const webReport = await apiPost("/api/scout/web", { url });
      const apiReport = await apiPost("/api/scout/api", { url }).catch(() => null);
      const results = [webReport, apiReport].filter(Boolean);
      setReports(results);
    } catch (err) {
      console.error("Scan failed:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleUploadLog(file: File) {
    setLoading(true);
    setError(null);
    try {
      const result = await apiUpload("/api/traffic/classify", file);
      setTraffic(result);
    } catch (err: any) {
      const msg = err?.message || String(err);
      setError(`Upload failed: ${msg}`);
      console.error("Upload failed:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-background p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Pick Me</h1>
          <p className="text-muted-foreground">Make AI agents choose you</p>
        </div>

        <ScanInput onScan={handleScan} onUploadLog={handleUploadLog} loading={loading} />

        {error && (
          <div className="bg-red-100 dark:bg-red-950 border border-red-500 text-red-700 dark:text-red-300 px-4 py-2 rounded">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ScorePanel reports={reports} loading={loading} />
          <TrafficPanel traffic={traffic} />
        </div>

        <OptimizerPanel reports={reports} onRescan={() => handleScan(lastUrl)} />

        <BenchmarkPanel beforeScore={reports.length > 0 ? Math.round(reports.reduce((s, r) => s + r.total_score, 0) / reports.reduce((s, r) => s + r.max_score, 0) * 100) : null} afterScore={null} />
      </div>
    </main>
  );
}
