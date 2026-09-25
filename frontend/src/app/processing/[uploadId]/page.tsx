"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useEffect } from "react";

import { useUploadStatus } from "@/hooks/useUploadStatus";
import { rejectionMessage } from "@/lib/rejectionMessages";

type PageProps = {
  params: Promise<{ uploadId: string }>;
};

// Task 81: processing indicator + explicit rejection-reason display.
export default function ProcessingPage({ params }: PageProps) {
  const { uploadId } = use(params);
  const router = useRouter();
  const { status, error, isPolling } = useUploadStatus(uploadId);

  useEffect(() => {
    if (status?.status === "passed") {
      router.push(`/results/${uploadId}`);
    }
  }, [status, router, uploadId]);

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
        </>
      )}

      {status?.status === "rejected" && (
        <div className="flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-red-700">We couldn&apos;t analyze this video</h2>
          <p className="text-sm text-gray-700">{rejectionMessage(status.rejection_reason)}</p>
          <Link href="/" className="text-sm font-medium underline">
            Try another video
          </Link>
        </div>
      )}

      {status?.status === "passed" && <p className="text-sm text-gray-600">Done -- redirecting to your results...</p>}
    </main>
  );
}
