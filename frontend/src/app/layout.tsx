import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

import { UploadProvider } from "@/context/UploadContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "QB Motion Atlas",
  description: "Compare your throwing motion to NFL quarterbacks, phase by phase.",
  // Task A6: this is a portfolio demo, not a public product, and some
  // matched results embed real (non-broadcast) reference clip video
  // (pipeline/video_licensing.py) -- keep it out of search results rather
  // than relying on obscurity alone.
  robots: {
    index: false,
    follow: false,
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <UploadProvider>{children}</UploadProvider>
      </body>
    </html>
  );
}
