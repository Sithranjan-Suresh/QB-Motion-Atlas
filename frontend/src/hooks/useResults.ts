"use client";

import { useEffect, useRef, useState } from "react";

import { ApiError, getResults, type AnalysisResultResponse } from "@/lib/api";

const POLL_INTERVAL_MS = 2000;

export type UseResultsResult = {
  result: AnalysisResultResponse | null;
  error: string | null;
  isLoading: boolean;
};

// Polls GET /results/{id} until it stops 404ing (task 85's "not ready yet"
// case) -- covers a direct link/refresh on /results before the
// AnalysisResult row exists, since the normal navigation path (task 82's
// context) already has the result by the time it lands here. `skip` avoids
// a redundant fetch when the context already has it.
export function useResults(uploadId: string, options?: { skip?: boolean }): UseResultsResult {
  const skip = options?.skip ?? false;
  const [result, setResult] = useState<AnalysisResultResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(!skip);
  const isMounted = useRef(true);

  useEffect(() => {
    if (skip) return;

    isMounted.current = true;
    let timeoutId: ReturnType<typeof setTimeout> | undefined;

    async function poll() {
      try {
        const fetched = await getResults(uploadId);
        if (!isMounted.current) return;

        if (fetched) {
          setResult(fetched);
          setIsLoading(false);
        } else {
          timeoutId = setTimeout(poll, POLL_INTERVAL_MS);
        }
      } catch (err) {
        if (!isMounted.current) return;
        setError(err instanceof ApiError ? err.detail : "Could not load results.");
        setIsLoading(false);
      }
    }

    poll();

    return () => {
      isMounted.current = false;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [uploadId, skip]);

  return { result, error, isLoading };
}
