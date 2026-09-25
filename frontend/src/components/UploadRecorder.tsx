"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { ApiError, createUpload } from "@/lib/api";

const RECORDING_CAP_SEC = 15;

// Picks the first mimeType the browser's MediaRecorder actually supports,
// preferring vp9 for smaller files -- Safari only supports plain
// "video/webm" (or nothing at all, handled by the caller).
function pickSupportedMimeType(): string | null {
  const candidates = ["video/webm;codecs=vp9", "video/webm;codecs=vp8", "video/webm"];
  for (const candidate of candidates) {
    if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(candidate)) {
      return candidate;
    }
  }
  return null;
}

// Task 120: hints correct side-on framing before recording starts -- a
// dashed silhouette guide plus instructional text, not an enforced check
// (pipeline/validation.py's real camera-angle check still runs server-side).
function FramingGuideOverlay() {
  return (
    <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-between p-3">
      <p className="rounded bg-black/60 px-2 py-1 text-xs text-white">Stand side-on, full body in frame</p>
      <svg viewBox="0 0 100 100" className="h-full w-auto opacity-40" preserveAspectRatio="xMidYMid meet">
        <line x1="50" y1="8" x2="50" y2="92" stroke="white" strokeWidth="0.5" strokeDasharray="2,2" />
        <ellipse cx="50" cy="16" rx="7" ry="8" stroke="white" strokeWidth="1" fill="none" />
        <line x1="50" y1="24" x2="50" y2="60" stroke="white" strokeWidth="1" />
        <line x1="50" y1="30" x2="68" y2="42" stroke="white" strokeWidth="1" />
        <line x1="50" y1="60" x2="40" y2="90" stroke="white" strokeWidth="1" />
        <line x1="50" y1="60" x2="58" y2="90" stroke="white" strokeWidth="1" />
      </svg>
    </div>
  );
}

type WebcamState = "idle" | "live" | "recording" | "preview";

// Tasks 119-121: MediaRecorder-based webcam capture alongside the existing
// file-upload flow (task 79), capped at RECORDING_CAP_SEC with a visible
// timer, framing guide during live preview, and the recorded blob wrapped
// into a File so it flows through the exact same createUpload() call as a
// picked file -- api/main.py's ALLOWED_CONTENT_TYPES now also accepts
// video/webm (MediaRecorder's actual output format; browsers don't record
// directly to mp4/quicktime).
export default function UploadRecorder() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [mode, setMode] = useState<"file" | "webcam">("file");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [webcamState, setWebcamState] = useState<WebcamState>("idle");
  const [secondsLeft, setSecondsLeft] = useState(RECORDING_CAP_SEC);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  function stopStream() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }

  useEffect(() => {
    return () => {
      stopStream();
      if (timerRef.current) clearInterval(timerRef.current);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function startCamera() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setWebcamState("live");
    } catch {
      setError("Could not access the camera -- check your browser's camera permission for this site.");
    }
  }

  function startRecording() {
    const stream = streamRef.current;
    if (!stream) return;
    const mimeType = pickSupportedMimeType();
    if (!mimeType) {
      setError("This browser can't record video. Try uploading a file instead.");
      return;
    }

    chunksRef.current = [];
    const recorder = new MediaRecorder(stream, { mimeType });
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: mimeType });
      setRecordedBlob(blob);
      setPreviewUrl(URL.createObjectURL(blob));
      setWebcamState("preview");
      stopStream();
    };
    recorderRef.current = recorder;
    recorder.start();
    setWebcamState("recording");
    setSecondsLeft(RECORDING_CAP_SEC);

    timerRef.current = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          if (timerRef.current) clearInterval(timerRef.current);
          recorderRef.current?.stop();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }

  function stopRecording() {
    if (timerRef.current) clearInterval(timerRef.current);
    recorderRef.current?.stop();
  }

  function retake() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setRecordedBlob(null);
    setWebcamState("idle");
  }

  async function submitFile(file: File) {
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

  async function handleFileSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      setError("Choose a video file first.");
      return;
    }
    await submitFile(file);
  }

  async function useRecording() {
    if (!recordedBlob) return;
    const extension = recordedBlob.type.includes("webm") ? "webm" : "mp4";
    const file = new File([recordedBlob], `webcam-throw.${extension}`, { type: recordedBlob.type });
    await submitFile(file);
  }

  function switchMode(next: "file" | "webcam") {
    stopStream();
    if (timerRef.current) clearInterval(timerRef.current);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setRecordedBlob(null);
    setWebcamState("idle");
    setError(null);
    setMode(next);
  }

  return (
    <div className="flex w-full min-w-0 max-w-md flex-col gap-4">
      <div className="flex gap-2 text-sm">
        <button
          type="button"
          onClick={() => switchMode("file")}
          className={`rounded px-3 py-1.5 font-medium ${mode === "file" ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-700"}`}
        >
          Upload a file
        </button>
        <button
          type="button"
          onClick={() => switchMode("webcam")}
          className={`rounded px-3 py-1.5 font-medium ${mode === "webcam" ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-700"}`}
        >
          Record with webcam
        </button>
      </div>

      {mode === "file" && (
        <form onSubmit={handleFileSubmit} className="flex w-full min-w-0 flex-col gap-4">
          <label htmlFor="video-file" className="text-sm font-medium">
            Upload a 5-15 second side-view video of your throw
          </label>
          <input
            id="video-file"
            ref={fileInputRef}
            type="file"
            accept="video/mp4,video/quicktime"
            disabled={isSubmitting}
            className="w-full min-w-0 rounded border border-gray-300 p-2 text-sm file:mr-3 file:rounded file:border-0 file:bg-gray-900 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-white"
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
      )}

      {mode === "webcam" && (
        <div className="flex w-full flex-col gap-4">
          <p className="text-sm font-medium">Record up to {RECORDING_CAP_SEC}s of your throw, side-on to the camera</p>

          <div className="relative aspect-video w-full overflow-hidden rounded bg-black">
            <video
              ref={videoRef}
              muted
              playsInline
              className="h-full w-full object-cover"
              style={{ display: webcamState === "preview" ? "none" : "block" }}
            />
            {(webcamState === "live" || webcamState === "recording") && <FramingGuideOverlay />}
            {webcamState === "recording" && (
              <div className="absolute right-3 top-3 rounded bg-red-600 px-2 py-1 text-xs font-semibold text-white">
                REC {secondsLeft}s
              </div>
            )}
            {webcamState === "preview" && previewUrl && (
              <video src={previewUrl} controls className="h-full w-full object-cover" />
            )}
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          {webcamState === "idle" && (
            <button
              type="button"
              onClick={startCamera}
              className="rounded bg-gray-900 px-4 py-2 text-sm font-medium text-white"
            >
              Start camera
            </button>
          )}
          {webcamState === "live" && (
            <button
              type="button"
              onClick={startRecording}
              className="rounded bg-gray-900 px-4 py-2 text-sm font-medium text-white"
            >
              Start recording
            </button>
          )}
          {webcamState === "recording" && (
            <button
              type="button"
              onClick={stopRecording}
              className="rounded bg-red-600 px-4 py-2 text-sm font-medium text-white"
            >
              Stop recording
            </button>
          )}
          {webcamState === "preview" && (
            <div className="flex gap-2">
              <button
                type="button"
                onClick={retake}
                disabled={isSubmitting}
                className="flex-1 rounded border border-gray-300 px-4 py-2 text-sm font-medium disabled:opacity-50"
              >
                Retake
              </button>
              <button
                type="button"
                onClick={useRecording}
                disabled={isSubmitting}
                className="flex-1 rounded bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
              >
                {isSubmitting ? "Uploading..." : "Use this recording"}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
