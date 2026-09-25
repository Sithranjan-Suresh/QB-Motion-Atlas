"use client";

import { use, useEffect } from "react";

import CoachingNotesList from "@/components/CoachingNotesList";
import OverallMatchCard from "@/components/OverallMatchCard";
import { useUploadContext } from "@/context/UploadContext";
import { useResults } from "@/hooks/useResults";

type PageProps = {
  params: Promise<{ uploadId: string }>;
};

// Task 85.
export default function ResultsPage({ params }: PageProps) {
  const { uploadId } = use(params);
  const { result: contextResult, setResult } = useUploadContext();
  const { result: polledResult, error, isLoading } = useResults(uploadId, { skip: Boolean(contextResult) });

  const result = contextResult ?? polledResult;

  useEffect(() => {
    if (polledResult) setResult(polledResult);
  }, [polledResult, setResult]);

  if (error) {
    return (
      <main className="mx-auto flex min-h-screen max-w-xl flex-col items-center justify-center gap-4 px-6 py-16 text-center">
        <p className="text-sm text-red-600">{error}</p>
      </main>
    );
  }

  if (!result || isLoading) {
    return (
      <main className="mx-auto flex min-h-screen max-w-xl flex-col items-center justify-center gap-4 px-6 py-16 text-center">
        <div
          role="status"
          aria-label="Loading results"
          className="h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-gray-900"
        />
        <p className="text-sm text-gray-600">Loading your results...</p>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col items-center gap-8 px-6 py-16">
      <h1 className="text-2xl font-bold">Your Throw Analysis</h1>
      <OverallMatchCard
        matchedQbName={result.matched_qb_name}
        similarityScore={result.overall_similarity_score}
        confidenceLevel={result.confidence_level}
      />
      <CoachingNotesList notes={result.coaching_notes} />
    </main>
  );
}
