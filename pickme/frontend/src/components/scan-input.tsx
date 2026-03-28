"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface ScanInputProps {
  onScan: (url: string) => void;
  onUploadLog: (file: File) => void;
  loading?: boolean;
}

export function ScanInput({ onScan, onUploadLog, loading }: ScanInputProps) {
  const [url, setUrl] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

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
      <input
        ref={fileRef}
        type="file"
        accept=".log,.txt,.csv,.json"
        style={{ display: "none" }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onUploadLog(file);
          if (fileRef.current) fileRef.current.value = "";
        }}
      />
      <button
        type="button"
        className="inline-flex shrink-0 items-center justify-center rounded-lg border border-border bg-background px-2.5 h-8 text-sm font-medium hover:bg-muted cursor-pointer"
        onClick={() => fileRef.current?.click()}
      >
        Upload Log
      </button>
    </div>
  );
}
