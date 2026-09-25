"use client";

import { createContext, useContext, useState, type ReactNode } from "react";

import type { AnalysisResultResponse, UploadStatusResponse } from "@/lib/api";

// Task 82: lightweight state carried across the processing -> results
// transition, so /results doesn't have to blindly re-poll from a cold
// start right after /processing already confirmed the upload passed --
// each page still fetches on its own if the context is empty (e.g. a
// direct link/refresh on /results), this just avoids a redundant round
// trip in the common navigation path.
type UploadContextValue = {
  status: UploadStatusResponse | null;
  setStatus: (status: UploadStatusResponse | null) => void;
  result: AnalysisResultResponse | null;
  setResult: (result: AnalysisResultResponse | null) => void;
};

const UploadContext = createContext<UploadContextValue | undefined>(undefined);

export function UploadProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<UploadStatusResponse | null>(null);
  const [result, setResult] = useState<AnalysisResultResponse | null>(null);

  return (
    <UploadContext.Provider value={{ status, setStatus, result, setResult }}>{children}</UploadContext.Provider>
  );
}

export function useUploadContext(): UploadContextValue {
  const ctx = useContext(UploadContext);
  if (!ctx) {
    throw new Error("useUploadContext must be used within an UploadProvider");
  }
  return ctx;
}
