import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "How to film your throw -- QB Motion Atlas",
};

const STEPS: { title: string; body: string }[] = [
  {
    title: "Film from your throwing-arm side",
    body: "Put the camera level with you, off your throwing shoulder, roughly at a right angle to the direction you throw. Head-on or from behind hides the arm path and will be rejected.",
  },
  {
    title: "Keep your whole body in frame",
    body: "Head to feet, for the entire throw -- including the stride forward and the follow-through. Step back until there's space around you; landscape orientation helps.",
  },
  {
    title: "One throw per video",
    body: "Start recording a moment before you begin the drop or set, stop after the follow-through. 5-15 seconds is ideal. Multiple reps in one clip will be rejected.",
  },
  {
    title: "Only you in the shot",
    body: "Other people moving near you can confuse the pose tracking. A plain background and decent light (outdoors, or a bright gym) give the cleanest result.",
  },
  {
    title: "Hold the camera still",
    body: "A tripod, a fence, or a friend standing still. Panning or zooming during the throw makes the motion look different from what your body actually did.",
  },
  {
    title: "Normal speed",
    body: "Upload real-time footage, not slow motion -- the analysis measures timing, and slowed video throws those numbers off.",
  },
];

export default function HowToFilmPage() {
  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-8 px-6 py-16">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold">How to film your throw</h1>
        <p className="text-sm text-gray-600">
          The analysis tracks 33 body points frame by frame, so it can only compare what the camera can clearly see.
          These six things avoid almost every rejected upload.
        </p>
      </div>
      <ol className="flex flex-col gap-5">
        {STEPS.map((step, i) => (
          <li key={step.title} className="flex gap-4">
            <span
              aria-hidden
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gray-900 text-sm font-semibold text-white"
            >
              {i + 1}
            </span>
            <div className="flex flex-col gap-1">
              <h2 className="font-semibold">{step.title}</h2>
              <p className="text-sm text-gray-700">{step.body}</p>
            </div>
          </li>
        ))}
      </ol>
      <p className="text-sm text-gray-600">
        Supported formats: MP4, MOV (iPhone) and WebM, up to 100 MB and 15 seconds.
      </p>
      <Link href="/" className="self-start rounded bg-gray-900 px-4 py-2 text-sm font-medium text-white">
        Upload a throw
      </Link>
    </main>
  );
}
