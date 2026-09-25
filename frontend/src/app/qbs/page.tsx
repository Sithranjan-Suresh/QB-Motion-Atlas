"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApiError, listQbs, type QBSummary } from "@/lib/api";

// Task 140: optional reference-database browser page via GET /qbs.
export default function QbsPage() {
  const [qbs, setQbs] = useState<QBSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listQbs()
      .then((data) => {
        if (!cancelled) setQbs(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Could not load the reference database.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col items-center gap-8 px-6 py-16">
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold">Reference Database</h1>
        <p className="max-w-md text-sm text-gray-600">
          The NFL quarterbacks currently in QB Motion Atlas&apos;s reference set, and how many clips each has.
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {!error && !qbs && (
        <div
          role="status"
          aria-label="Loading reference database"
          className="h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-gray-900"
        />
      )}

      {qbs && qbs.length === 0 && <p className="text-sm text-gray-500">No reference clips yet.</p>}

      {qbs && qbs.length > 0 && (
        <ul className="flex w-full flex-col gap-2">
          {qbs.map((qb) => (
            <li
              key={qb.qb_name}
              className="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3"
            >
              <span className="text-sm font-medium capitalize">{qb.qb_name.replace(/_/g, " ")}</span>
              <span className="text-xs text-gray-500">
                {qb.clip_count} clip{qb.clip_count === 1 ? "" : "s"}
              </span>
            </li>
          ))}
        </ul>
      )}

      <Link href="/" className="text-sm font-medium underline focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-900 rounded">
        Back to upload
      </Link>
    </main>
  );
}
