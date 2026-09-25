import Link from "next/link";

import UploadRecorder from "@/components/UploadRecorder";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-8 px-6 py-16">
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-3xl font-bold tracking-tight">QB Motion Atlas</h1>
        <p className="max-w-md text-sm text-gray-600">
          Upload a side-view video of your throw and see which NFL quarterback&apos;s mechanics it resembles, phase by
          phase.
        </p>
      </div>
      <UploadRecorder />
      <Link
        href="/qbs"
        className="rounded text-sm font-medium text-gray-600 underline focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-900"
      >
        Browse the reference database
      </Link>
    </main>
  );
}
