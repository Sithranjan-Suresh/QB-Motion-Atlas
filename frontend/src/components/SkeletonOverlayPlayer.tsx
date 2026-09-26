"use client";

import { useEffect, useRef } from "react";

import ScrubBar from "@/components/ScrubBar";
import { useFrameScrubber, type FrameScrubber } from "@/hooks/useFrameScrubber";
import type { LandmarkSequenceResponse } from "@/lib/api";
import { POSE_CONNECTIONS } from "@/lib/poseConnections";

const CANVAS_WIDTH = 480;
const CANVAS_HEIGHT = 360; // 4:3, matching MediaPipe's normalized [0,1] coordinate space regardless of source aspect ratio

function drawSkeleton(ctx: CanvasRenderingContext2D, landmarks: [number, number][], color: string) {
  ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 3;

  for (const [a, b] of POSE_CONNECTIONS) {
    const [ax, ay] = landmarks[a];
    const [bx, by] = landmarks[b];
    ctx.beginPath();
    ctx.moveTo(ax * CANVAS_WIDTH, ay * CANVAS_HEIGHT);
    ctx.lineTo(bx * CANVAS_WIDTH, by * CANVAS_HEIGHT);
    ctx.stroke();
  }
  for (const [x, y] of landmarks) {
    ctx.beginPath();
    ctx.arc(x * CANVAS_WIDTH, y * CANVAS_HEIGHT, 3, 0, 2 * Math.PI);
    ctx.fill();
  }
}

type SkeletonOverlayPlayerProps = {
  landmarks: LandmarkSequenceResponse;
  // The video to overlay the skeleton on top of: the user's own upload
  // (task 124), or, for the matched reference clip (task A1), its real
  // footage when pipeline/video_licensing.py.is_video_overlay_eligible()
  // allows it. Omitted renders skeleton-only on a plain background --
  // always true for the user's side pre-recording, and for a reference
  // clip sourced from an official broadcast channel (see research_log.md).
  videoUrl?: string;
  skeletonColor?: string;
  // Controlled mode: a parent (SyncedComparisonView) drives frameIndex and
  // owns the shared scrubber. Uncontrolled: this component manages its own
  // scrub bar via useFrameScrubber.
  frameIndex?: number;
  hideOwnControls?: boolean;
};

export default function SkeletonOverlayPlayer({
  landmarks,
  videoUrl,
  skeletonColor = "#22c55e",
  frameIndex: controlledFrameIndex,
  hideOwnControls = false,
}: SkeletonOverlayPlayerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const ownScrubber = useFrameScrubber(landmarks.frames.length, landmarks.fps);
  const frameIndex = controlledFrameIndex ?? ownScrubber.frameIndex;
  const frame = landmarks.frames[Math.min(frameIndex, landmarks.frames.length - 1)];

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!ctx || !frame) return;
    drawSkeleton(ctx, frame.landmarks as [number, number][], skeletonColor);
  }, [frame, skeletonColor]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !frame) return;
    const targetSeconds = frame.timestamp_ms / 1000;
    if (Math.abs(video.currentTime - targetSeconds) > 1 / landmarks.fps) {
      video.currentTime = targetSeconds;
    }
  }, [frame, landmarks.fps]);

  return (
    <div className="flex w-80 shrink-0 flex-col gap-2">
      {/* w-80 (fixed), not w-full/max-w-md -- the video/canvas inside are
          position:absolute and don't contribute intrinsic size, so in a
          shrink-to-fit flex column (SyncedComparisonView's side-by-side
          layout) a percentage width here would resolve against whatever
          sibling content (e.g. the QB name label) happens to be widest,
          producing mismatched box sizes between the two sides -- found via
          real browser testing, not something a unit test would catch. */}
      <div className="relative overflow-hidden rounded bg-black" style={{ aspectRatio: `${CANVAS_WIDTH}/${CANVAS_HEIGHT}` }}>
        {videoUrl && (
          <video ref={videoRef} src={videoUrl} muted playsInline className="absolute inset-0 h-full w-full object-contain" />
        )}
        <canvas ref={canvasRef} width={CANVAS_WIDTH} height={CANVAS_HEIGHT} className="absolute inset-0 h-full w-full" />
      </div>
      {!hideOwnControls && controlledFrameIndex === undefined && (
        <ScrubBar scrubber={ownScrubber} frameCount={landmarks.frames.length} />
      )}
    </div>
  );
}

export type { FrameScrubber };
