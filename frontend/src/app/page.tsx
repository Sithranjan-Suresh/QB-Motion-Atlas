import Link from "next/link";

import UploadRecorder from "@/components/UploadRecorder";

export default async function Home({ searchParams }: PageProps<"/">) {
  const { deleted } = await searchParams;

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-8 px-6 py-16">
      {deleted === "1" && (
        <p role="status" className="rounded bg-gray-100 px-4 py-2 text-sm text-gray-700">
          Your video and results were deleted.
        </p>
      )}
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-3xl font-bold tracking-tight">QB Motion Atlas</h1>
        <p className="max-w-md text-sm text-gray-600">
          Upload a side-view video of your throw and see which NFL quarterback&apos;s mechanics it resembles, phase by
          phase.
        </p>
      </div>
      <p className="text-center text-xs text-gray-500">
        First time?{" "}
        <Link href="/how-to-film" className="font-medium underline">
          How to film your throw
        </Link>{" "}
        -- 30 seconds of setup avoids most rejected uploads.
      </p>
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
