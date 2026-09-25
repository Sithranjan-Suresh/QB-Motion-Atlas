"use client";

import { useEffect, useRef, useState } from "react";

import { ApiError, getUploadStatus, type UploadStatusResponse } from "@/lib/api";

const POLL_INTERVAL_MS = 2000;

export type UseUploadStatusResult = {
  status: UploadStatusResponse | null;
  error: string | null;
  isPolling: boolean;
};

// Polls GET /uploads/{id}/status every POLL_INTERVAL_MS until the upload
// leaves "processing" (task 80). Stops polling on "passed"/"rejected" or on
// a request error -- never polls forever once there's a definitive answer.
export function useUploadStatus(uploadId: string): UseUploadStatusResult {
  const [status, setStatus] = useState<UploadStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    let timeoutId: ReturnType<typeof setTimeout> | undefined;

    async function poll() {
      try {
        const result = await getUploadStatus(uploadId);
        if (!isMounted.current) return;
        setStatus(result);

        if (result.status === "processing") {
          timeoutId = setTimeout(poll, POLL_INTERVAL_MS);
        } else {
          setIsPolling(false);
        }
      } catch (err) {
        if (!isMounted.current) return;
        setError(err instanceof ApiError ? err.detail : "Could not check upload status.");
        setIsPolling(false);
      }
    }

    poll();

    return () => {
      isMounted.current = false;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [uploadId]);

  return { status, error, isPolling };
}
