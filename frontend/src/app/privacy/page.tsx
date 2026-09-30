import type { Metadata } from "next";

import { CONTACT_EMAIL, PROJECT_URL, RETENTION_DAYS } from "@/lib/contact";

export const metadata: Metadata = {
  title: "Privacy -- QB Motion Atlas",
};

export default function PrivacyPage() {
  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 px-6 py-16 text-sm leading-6 text-gray-800">
      <h1 className="text-2xl font-bold text-gray-900">Privacy</h1>
      <p>
        QB Motion Atlas is a personal portfolio project. This page describes exactly what happens to a video you
        upload. There are no accounts, no ads, and no tracking cookies.
      </p>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold text-gray-900">What is stored</h2>
        <ul className="list-disc space-y-1 pl-5">
          <li>The video file you upload or record.</li>
          <li>
            Data computed from it: body-position points for each frame, the phases of your throw, measurements such as
            joint angles and timing, your match result, and coaching notes.
          </li>
          <li>
            Your IP address is used only in server memory to limit how many uploads one address can make per hour. It
            is not written to the database or to logs.
          </li>
        </ul>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold text-gray-900">How long, and how to delete it</h2>
        <p>
          Everything tied to an upload -- the video and all data computed from it -- is deleted automatically{" "}
          {RETENTION_DAYS} days after upload. You can delete it sooner at any time with the &ldquo;Delete my video and
          results&rdquo; button at the bottom of your results page. Deletion is permanent.
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold text-gray-900">Who can see it</h2>
        <p>
          Your results page has a long random address. Anyone you share that link with can see your results and your
          video, so share it the way you would a private photo link. Nothing is listed publicly or used to train
          models.
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold text-gray-900">Services involved</h2>
        <ul className="list-disc space-y-1 pl-5">
          <li>Vercel hosts this website.</li>
          <li>Hugging Face hosts the analysis server that processes your video.</li>
          <li>Supabase stores the database and video files.</li>
          <li>
            Groq generates the written coaching notes. It receives only the numeric measurement differences (for
            example &ldquo;elbow angle 3.1&deg; lower&rdquo;) -- never your video or any image of you.
          </li>
        </ul>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold text-gray-900">Children</h2>
        <p>This site isn&apos;t directed at children under 13, and they shouldn&apos;t upload videos of themselves.</p>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold text-gray-900">Contact</h2>
        <p>
          Questions or a deletion request you can&apos;t do yourself:{" "}
          {CONTACT_EMAIL ? (
            <a href={`mailto:${CONTACT_EMAIL}`} className="underline">
              {CONTACT_EMAIL}
            </a>
          ) : (
            <a href={PROJECT_URL} className="underline">
              the project&apos;s repository
            </a>
          )}
          .
        </p>
      </section>
    </main>
  );
}
