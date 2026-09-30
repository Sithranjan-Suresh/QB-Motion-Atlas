import Link from "next/link";

export default function SiteFooter() {
  return (
    <footer className="border-t border-gray-200 px-6 py-6 text-center text-xs text-gray-500">
      <nav className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2" aria-label="Footer">
        <Link href="/how-to-film" className="underline hover:text-gray-900">
          How to film
        </Link>
        <Link href="/qbs" className="underline hover:text-gray-900">
          Reference database
        </Link>
        <Link href="/privacy" className="underline hover:text-gray-900">
          Privacy
        </Link>
        <Link href="/terms" className="underline hover:text-gray-900">
          Terms
        </Link>
      </nav>
      <p className="mt-3">
        Not affiliated with or endorsed by the NFL, any NFL team, or any player.
      </p>
    </footer>
  );
}
