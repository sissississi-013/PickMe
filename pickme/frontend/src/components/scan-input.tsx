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
    <div className="flex gap-2">
      <Input
        placeholder="Enter URL to scan..."
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && url && onScan(url)}
        className="flex-1 font-mono text-sm bg-card border-border placeholder:text-muted-foreground/50"
      />
      <Button
        onClick={() => url && onScan(url)}
        disabled={loading || !url}
        className="bg-primary hover:bg-primary/90 text-primary-foreground"
      >
        {loading ? "Scanning..." : "Scan"}
      </Button>
    </div>
  );
}
