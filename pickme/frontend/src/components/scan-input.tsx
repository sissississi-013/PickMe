"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface ScanInputProps {
  onScan: (url: string) => void;
  loading?: boolean;
}

export function ScanInput({ onScan, loading }: ScanInputProps) {
  const [url, setUrl] = useState("");

  return (
    <div className="flex gap-3">
      <Input
        placeholder="Enter a URL to analyze..."
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && url && onScan(url)}
        className="flex-1 h-11 text-base font-mono bg-card border-border placeholder:text-muted-foreground/40"
      />
      <Button
        onClick={() => url && onScan(url)}
        disabled={loading || !url}
        className="h-11 px-6 text-base bg-primary hover:bg-primary/90 text-primary-foreground"
      >
        {loading ? "Scanning..." : "Scan"}
      </Button>
    </div>
  );
}
