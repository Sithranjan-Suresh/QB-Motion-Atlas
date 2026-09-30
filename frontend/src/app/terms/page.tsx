import type { Metadata } from "next";
import Link from "next/link";

import { CONTACT_EMAIL, PROJECT_URL } from "@/lib/contact";

export const metadata: Metadata = {
  title: "Terms -- QB Motion Atlas",
};

export default function TermsPage() {
  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 px-6 py-16 text-sm leading-6 text-gray-800">
      <h1 className="text-2xl font-bold text-gray-900">Terms of use</h1>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold text-gray-900">What this is</h2>
        <p>
          QB Motion Atlas is a free personal portfolio project that compares a throwing motion against reference
          footage of NFL quarterbacks using computer-vision pose estimation. Results are automated estimates for
          entertainment and general interest -- not professional coaching, medical, or injury-prevention advice. The
          reference set is small, so treat a match as a rough resemblance, and pay attention to the confidence level
          shown with it.
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold text-gray-900">Your uploads</h2>
        <p>
          Only upload video you have the right to share: of yourself, or of someone who has agreed to it. Don&apos;t
          upload anything unlawful, or anything that isn&apos;t a throwing motion. You keep all rights to your video;
          you let the service store and process it only to produce your results, for the period described on the{" "}
          <Link href="/privacy" className="underline">
            privacy page
          </Link>
          .
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold text-gray-900">Reference footage</h2>
        <p>
          This project is not affiliated with, sponsored by, or endorsed by the NFL, any NFL team, or any player.
          Player names are used only to identify the reference footage. Reference clips come from publicly available
          videos, are trimmed to the few seconds of a single throw, and link to their original source. All rights
          remain with their owners.
        </p>
        <p>
          If you own footage shown here and want it removed, contact{" "}
          {CONTACT_EMAIL ? (
            <a href={`mailto:${CONTACT_EMAIL}`} className="underline">
              {CONTACT_EMAIL}
            </a>
          ) : (
            <a href={PROJECT_URL} className="underline">
              the project&apos;s repository
            </a>
          )}{" "}
          and it will be taken down promptly.
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold text-gray-900">No warranty</h2>
        <p>
          The service is provided as-is, may be unavailable or change at any time, and comes with no guarantee that
          results are accurate. Uploads may be limited to keep the free service running for everyone.
        </p>
      </section>
    </main>
  );
}
