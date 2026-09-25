"use client";

import { useState } from "react";

import { ApiError, exportShareCard } from "@/lib/api";

// Task 135: single click -> fetch the rendered PNG -> trigger a browser
// download, via a temporary object-URL anchor (no server-side redirect or
// separate download page needed for a same-origin blob).
export default function ShareExportButton({ uploadId }: { uploadId: string }) {
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleExport() {
    setIsExporting(true);
    setError(null);
    try {
      const blob = await exportShareCard(uploadId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `qb-motion-atlas-${uploadId}.png`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not export the results card.");
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <div className="flex flex-col items-center gap-1">
      <button
        type="button"
        onClick={handleExport}
        disabled={isExporting}
        className="rounded border border-gray-300 px-4 py-2 text-sm font-medium disabled:opacity-50"
      >
        {isExporting ? "Preparing image..." : "Download shareable card"}
      </button>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
