import type { MetadataRoute } from "next";

// Task A6: belt-and-suspenders alongside the per-page `robots` metadata in
// layout.tsx -- disallow crawling entirely rather than relying on the meta
// tag alone (some crawlers fetch robots.txt before rendering pages).
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      disallow: "/",
    },
  };
}
