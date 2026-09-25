"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type FrameScrubber = {
  frameIndex: number;
  isPlaying: boolean;
  play: () => void;
  pause: () => void;
  seek: (index: number) => void;
};

// Task 126: shared play/pause/scrub state, driven by frame index rather than
// native <video> playback -- used both by SkeletonOverlayPlayer's standalone
// scrub bar and SyncedComparisonView, which need the exact same frame index
// concept to drive a video element and a skeleton-only canvas in lockstep.
export function useFrameScrubber(frameCount: number, fps: number): FrameScrubber {
  const [frameIndex, setFrameIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const pause = useCallback(() => {
    setIsPlaying(false);
    if (intervalRef.current) clearInterval(intervalRef.current);
  }, []);

  const play = useCallback(() => {
    if (frameCount <= 1) return;
    setIsPlaying(true);
  }, [frameCount]);

  const seek = useCallback(
    (index: number) => {
      pause();
      setFrameIndex(Math.max(0, Math.min(frameCount - 1, index)));
    },
    [frameCount, pause]
  );

  useEffect(() => {
    if (!isPlaying) return;

    intervalRef.current = setInterval(() => {
      setFrameIndex((prev) => {
        if (prev >= frameCount - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 1000 / fps);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isPlaying, frameCount, fps]);

  return { frameIndex, isPlaying, play, pause, seek };
}
