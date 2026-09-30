"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useUploadContext } from "@/context/UploadContext";
import { ApiError, deleteUpload } from "@/lib/api";

// Two-step so a stray tap can't destroy results: first click asks, second
// click deletes the video and everything derived from it on the server.
export default function DeleteUploadButton({ uploadId }: { uploadId: string }) {
  const router = useRouter();
  const { setResult, setStatus } = useUploadContext();
  const [isConfirming, setIsConfirming] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    setIsDeleting(true);
    setError(null);
    try {
      await deleteUpload(uploadId);
      setResult(null);
      setStatus(null);
      router.push("/?deleted=1");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not delete this upload.");
      setIsDeleting(false);
    }
  }

  return (
    <div className="flex flex-col items-center gap-2 border-t border-gray-200 pt-6 text-center">
      {!isConfirming ? (
        <button
          type="button"
          onClick={() => setIsConfirming(true)}
          className="text-sm text-gray-500 underline hover:text-gray-900"
        >
          Delete my video and results
        </button>
      ) : (
        <>
          <p className="text-sm text-gray-700">
            This permanently deletes your video and this results page. It can&apos;t be undone.
          </p>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleDelete}
              disabled={isDeleting}
              className="rounded bg-red-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {isDeleting ? "Deleting..." : "Yes, delete"}
            </button>
            <button
              type="button"
              onClick={() => setIsConfirming(false)}
              disabled={isDeleting}
              className="rounded border border-gray-300 px-4 py-2 text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
