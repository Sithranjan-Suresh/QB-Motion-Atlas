// Where takedown and privacy requests go. Set NEXT_PUBLIC_CONTACT_EMAIL in
// the deployment; without it the pages point at the project's repository.
export const CONTACT_EMAIL = process.env.NEXT_PUBLIC_CONTACT_EMAIL ?? "";
export const PROJECT_URL = process.env.NEXT_PUBLIC_PROJECT_URL ?? "https://github.com/Sithranjan-Suresh/QB-Motion-Atlas";
export const RETENTION_DAYS = Number(process.env.NEXT_PUBLIC_UPLOAD_RETENTION_DAYS ?? "7");
