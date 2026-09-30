"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useEffect, useState } from "react";

import { useUploadContext } from "@/context/UploadContext";
import { useUploadStatus } from "@/hooks/useUploadStatus";
import { rejectionMessage } from "@/lib/rejectionMessages";

type PageProps = {
  params: Promise<{ uploadId: string }>;
};

// Analysis normally takes well under a minute; past this, say so rather than
// leaving a silent spinner (a busy queue or a cold-starting server).
const SLOW_NOTICE_AFTER_MS = 45_000;

// Task 81: processing indicator + explicit rejection-reason display.
export default function ProcessingPage({ params }: PageProps) {
  const { uploadId } = use(params);
  const router = useRouter();
  const { status, error, isPolling } = useUploadStatus(uploadId);
  const { setStatus } = useUploadContext();
  const [isSlow, setIsSlow] = useState(false);

  useEffect(() => {
    const timeoutId = setTimeout(() => setIsSlow(true), SLOW_NOTICE_AFTER_MS);
    return () => clearTimeout(timeoutId);
  }, []);

  useEffect(() => {
    setStatus(status);
    if (status?.status === "passed") {
      router.push(`/results/${uploadId}`);
    }
  }, [status, router, uploadId, setStatus]);

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col items-center justify-center gap-6 px-6 py-16 text-center">
      {error && <p className="text-sm text-red-600">{error}</p>}

      {!error && isPolling && (
        <>
          <div
            role="status"
            aria-label="Processing"
            className="h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-gray-900"
          />
          <p className="text-sm text-gray-600">
            Analyzing your throw{status?.status === "processing" ? "..." : ""}
          </p>
          {isSlow && (
            <p className="max-w-sm text-xs text-gray-500">
              This is taking longer than usual -- the server may be waking up or working through other uploads. You can
              keep this page open; it will update on its own.
            </p>
          )}
        </>
      )}

      {status?.status === "rejected" && (
        <div className="flex flex-col gap-4 animate-fade-in">
          <h2 className="text-lg font-semibold text-red-700">We couldn&apos;t analyze this video</h2>
          <p className="text-sm text-gray-700">{rejectionMessage(status.rejection_reason)}</p>
          <Link href="/" className="text-sm font-medium underline">
            Try another video
          </Link>
        </div>
      )}

      {status?.status === "failed" && (
        <div className="flex flex-col gap-4 animate-fade-in">
          <h2 className="text-lg font-semibold text-red-700">Something went wrong</h2>
          <p className="text-sm text-gray-700">{rejectionMessage(status.rejection_reason)}</p>
          <Link href="/" className="text-sm font-medium underline">
            Upload again
          </Link>
        </div>
      )}

      {status?.status === "passed" && <p className="text-sm text-gray-600">Done -- redirecting to your results...</p>}
    </main>
  );
}
