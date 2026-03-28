"use client";

import { useState } from "react";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface ScanInputProps {
  onScan: (url: string) => void;
  onUploadLog: (file: File) => void;
  loading?: boolean;
}

export function ScanInput({ onScan, onUploadLog, loading }: ScanInputProps) {
  const [url, setUrl] = useState("");

  return (
    <div className="flex gap-2">
      <Input
        placeholder="Enter URL to scan (website, API, or MCP server)..."
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && url && onScan(url)}
        className="flex-1"
      />
      <Button onClick={() => url && onScan(url)} disabled={loading || !url}>
        {loading ? "Scanning..." : "Scan"}
      </Button>
      <label className={cn(buttonVariants({ variant: "outline" }), "cursor-pointer")}>
        Upload Log
        <input
          type="file"
          accept=".log,.txt,.csv,.json"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onUploadLog(file);
          }}
        />
      </label>
    </div>
  );
}
