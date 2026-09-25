"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { ApiError, createUpload } from "@/lib/api";

// Task 79: file upload only for V1 -- live webcam capture is a V2 feature
// (implementation_checklist.md's "Live Webcam Capture" section).
export default function UploadRecorder() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      setError("Choose a video file first.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const { upload_id } = await createUpload(file);
      router.push(`/processing/${upload_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Upload failed -- try again.");
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full max-w-md">
      <label htmlFor="video-file" className="text-sm font-medium">
        Upload a 5-15 second side-view video of your throw
      </label>
      <input
        id="video-file"
        ref={fileInputRef}
        type="file"
        accept="video/mp4,video/quicktime"
        disabled={isSubmitting}
        className="rounded border border-gray-300 p-2 text-sm file:mr-3 file:rounded file:border-0 file:bg-gray-900 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-white"
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {isSubmitting ? "Uploading..." : "Analyze my throw"}
      </button>
    </form>
  );
}
