"use client";

import { useEffect, useState } from "react";

import ScrubBar from "@/components/ScrubBar";
import SkeletonOverlayPlayer from "@/components/SkeletonOverlayPlayer";
import { useFrameScrubber } from "@/hooks/useFrameScrubber";
import { getComparison, getReferenceClipVideoUrl, getUploadVideoUrl, type ComparisonResponse } from "@/lib/api";

// Builds a dense user-frame-index -> reference-frame-index lookup from the
// DTW alignment path (task 125), which only lists the frames actually on
// the warping path -- a user frame between two path points takes the
// nearest preceding one, so every index in range has a mapping.
function buildAlignmentLookup(alignment: [number, number][], userFrameCount: number): number[] {
  const lookup = new Array(userFrameCount).fill(0);
  let pathIdx = 0;
  for (let i = 0; i < userFrameCount; i++) {
    while (pathIdx < alignment.length - 1 && alignment[pathIdx][0] < i) {
      pathIdx++;
    }
    lookup[i] = alignment[pathIdx][1];
  }
  return lookup;
}

// Tasks 125-126: fetches the upload's comparison data and renders the
// user's own video+skeleton next to the matched QB's skeleton-only
// animation, both driven by one shared scrubber -- the reference side maps
// through the V1 DTW alignment (pipeline/similarity_dtw.py) so equivalent
// motion phases line up despite different clip lengths/tempos.
export default function SyncedComparisonView({
  uploadId,
  matchedClipId,
}: {
  uploadId: string;
  matchedClipId: string | null;
}) {
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getComparison(uploadId)
      .then((data) => {
        if (!cancelled) setComparison(data);
      })
      .catch(() => {
        if (!cancelled) setError("Could not load the synced comparison.");
      });
    return () => {
      cancelled = true;
    };
  }, [uploadId]);

  const userFrameCount = comparison?.user.frames.length ?? 0;
  const scrubber = useFrameScrubber(userFrameCount, comparison?.user.fps ?? 30);

  const alignment = comparison?.alignment;
  const alignmentLookup = alignment ? buildAlignmentLookup(alignment, userFrameCount) : null;

  if (error) {
    return <p className="text-sm text-red-600">{error}</p>;
  }
  if (!comparison) {
    return <p className="text-sm text-gray-500">Loading skeleton overlay...</p>;
  }

  const referenceFrameIndex = alignmentLookup ? alignmentLookup[scrubber.frameIndex] : undefined;

  return (
    <div className="flex w-full max-w-3xl flex-col gap-4">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">Skeleton Overlay</h2>
      <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
        <div className="flex flex-col items-center gap-1">
          <p className="text-xs font-medium text-gray-600">You</p>
          <SkeletonOverlayPlayer
            landmarks={comparison.user}
            videoUrl={getUploadVideoUrl(uploadId)}
            frameIndex={scrubber.frameIndex}
            hideOwnControls
          />
        </div>
        {comparison.reference && referenceFrameIndex !== undefined ? (
          <div className="flex flex-col items-center gap-1">
            <p className="text-xs font-medium capitalize text-gray-600">
              {comparison.reference_qb_name?.replace(/_/g, " ")}
            </p>
            <SkeletonOverlayPlayer
              landmarks={comparison.reference}
              videoUrl={
                matchedClipId && comparison.reference_video_eligible
                  ? getReferenceClipVideoUrl(matchedClipId)
                  : undefined
              }
              skeletonColor="#60a5fa"
              frameIndex={referenceFrameIndex}
              hideOwnControls
            />
            {comparison.reference_video_eligible && comparison.reference_clip_source_url ? (
              <a
                href={comparison.reference_clip_source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[10px] text-gray-400 hover:text-gray-600 hover:underline"
              >
                Footage source
              </a>
            ) : null}
          </div>
        ) : (
          <div className="flex w-full max-w-md items-center justify-center rounded border border-dashed border-gray-300 p-6 text-center text-sm text-gray-500">
            No synced comparison available yet for{" "}
            {comparison.reference_qb_name ? comparison.reference_qb_name.replace(/_/g, " ") : "this match"} --
            reference skeleton data hasn&apos;t been processed for this clip.
          </div>
        )}
      </div>
      <ScrubBar scrubber={scrubber} frameCount={userFrameCount} />
    </div>
  );
}
