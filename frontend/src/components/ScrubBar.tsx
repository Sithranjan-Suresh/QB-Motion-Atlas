import type { FrameScrubber } from "@/hooks/useFrameScrubber";

// Task 126: play/pause + a frame-indexed range slider, shared by
// SkeletonOverlayPlayer's standalone mode and SyncedComparisonView.
export default function ScrubBar({ scrubber, frameCount }: { scrubber: FrameScrubber; frameCount: number }) {
  return (
    <div className="flex w-full items-center gap-3">
      <button
        type="button"
        onClick={scrubber.isPlaying ? scrubber.pause : scrubber.play}
        disabled={frameCount <= 1}
        className="rounded bg-gray-900 px-3 py-1 text-xs font-medium text-white disabled:opacity-50"
      >
        {scrubber.isPlaying ? "Pause" : "Play"}
      </button>
      <input
        type="range"
        min={0}
        max={Math.max(0, frameCount - 1)}
        value={scrubber.frameIndex}
        onChange={(e) => scrubber.seek(Number(e.target.value))}
        className="flex-1"
      />
      <span className="w-16 shrink-0 text-right text-xs text-gray-500">
        {scrubber.frameIndex + 1} / {frameCount}
      </span>
    </div>
  );
}
