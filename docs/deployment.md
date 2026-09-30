# Deployment

Free-tier stack, chosen 2026-09-30:

| Piece | Service | Why |
|---|---|---|
| Frontend | Vercel | Next.js host; CLI already connected on the Windows machine |
| Backend API + worker | Hugging Face Space (Docker) | Free 2 vCPU / 16 GB. The analysis peaks at ~411 MiB per job, measured in the production image on a 15s 1080p clip. Render's free tier (512 MB, 0.1 CPU) would sit at its memory limit and take minutes per upload. |
| Database | Supabase Postgres (pgvector) | Migrations run automatically on every backend boot |
| Video storage | Supabase Storage via its S3 API | The Space's disk is wiped on restart, so uploads can't live there |
| Coaching notes | Groq (`openai/gpt-oss-20b`) | Free; only numeric deltas are sent, never video |

Everything below is one-time setup. After it, backend deploys are `python scripts/deploy_hf_space.py --space <name>` (or the `Deploy backend` GitHub Action) and frontend deploys are `vercel --prod`.

## 0. Rotate the keys that were pasted into chat
- Groq: https://console.groq.com/keys, delete the old key, create a new one.
- Supabase: Project Settings -> Database -> Reset database password. Pick one without `@`, `:` or `/` to avoid URL-encoding it.

## 1. Supabase: connection string and storage keys
1. **Database URL:** click **Connect** at the top of the project, then copy **Session pooler** (not "Direct connection": that host is IPv6-only, and neither Hugging Face nor most networks can reach it). It looks like
   `postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres`.
   Paste it exactly as given: the `postgresql://` prefix is converted to the right driver automatically, and a URL-encoded password (`%40`) works.
2. **Bucket:** Storage -> New bucket -> name `qb-motion-atlas`, **private**.
3. **S3 keys:** Project Settings -> Storage -> S3 Connection. Note the **Endpoint** (`https://<project-ref>.storage.supabase.co/storage/v1/s3`) and **Region**, then **New access key** and save the key ID and secret.

## 2. Put production settings in `.env` (Windows repo root)
Pull this branch first. `.env` is gitignored.
```
DATABASE_URL=<session pooler URL from step 1.1>
S3_BUCKET=qb-motion-atlas
S3_ENDPOINT_URL=https://<project-ref>.storage.supabase.co/storage/v1/s3
S3_REGION=<region from step 1.3>
S3_ACCESS_KEY_ID=<from step 1.3>
S3_SECRET_ACCESS_KEY=<from step 1.3>
GROQ_API_KEY=<new Groq key>
CORS_ALLOWED_ORIGINS=http://localhost:3000
HF_TOKEN=<from step 3>
```
Your local dev database setting moves into this file too, so keep a copy of the old `.env` (e.g. `.env.local-dev`) and swap back afterwards.

## 3. Hugging Face: token, then deploy the backend
1. Create an account at https://huggingface.co, then Settings -> Access Tokens -> **Create new token** with **Write** access. Put it in `.env` as `HF_TOKEN`.
2. From the repo root:
   ```
   pip install huggingface_hub
   python scripts/deploy_hf_space.py --space <your-hf-username>/qb-motion-atlas-api --secrets-from-env
   ```
   This creates the Space, copies the secrets and variables from `.env` into its settings, and uploads the code. The first build takes ~5 minutes; watch it under the Space's **Logs** tab.
3. Check `https://<your-hf-username>-qb-motion-atlas-api.hf.space/health/ready`. It should report `"database": "ok"` and `"storage": "S3Storage"`.

## 4. Load the reference data (Windows, needs `data/`)
```
python scripts/publish_reference_data.py
```
This seeds the production database from `provenance.csv` and the `data/*_raw` folders, then uploads each reference clip (trimmed to the throw) to the bucket. It lists any clip it skipped and why. Re-run it any time clips are added; it only uploads new ones (`--force` re-uploads all of them).

## 5. Frontend on Vercel
```
cd frontend
vercel env add NEXT_PUBLIC_API_BASE_URL production     # https://<your-hf-username>-qb-motion-atlas-api.hf.space
vercel env add NEXT_PUBLIC_CONTACT_EMAIL production    # optional: shown on /privacy and /terms for takedowns
vercel --prod
```
Vercel prints the site URL (e.g. `https://qb-motion-atlas.vercel.app`).

## 6. Allow the site to call the API
In the Space: Settings -> Variables and secrets, set `CORS_ALLOWED_ORIGINS` to the Vercel URL from step 5 (comma-separate several). The Space restarts on its own.

## 7. Smoke test
On your phone, open the Vercel URL, upload a real side-view throw, and confirm you reach either a result or a specific rejection reason. On the result page, check that the skeleton overlay plays and that "Delete my video and results" works.

If the reference video doesn't play but everything else works, set the Space variable `S3_SERVE_MODE=proxy`. That streams video through the API instead of redirecting to a signed storage URL.

## Things to know about the free tiers
- **Hugging Face** Spaces sleep after 48 hours without traffic; the first visit after that takes a minute to wake. Jobs are stored in Postgres, so an upload made during a restart still gets processed when it's back.
- **Supabase** pauses free projects after a week of inactivity; unpause from the dashboard.
- **Groq** has per-minute rate limits; if one is hit, that upload quietly gets the rule-based coaching notes instead.
- Rate limits and retention can be tuned without code changes through the Space variables listed in `.env.example`.

## Continuous deployment (optional)
`.github/workflows/deploy-backend.yml` redeploys the Space on pushes to `main` that touch backend code. Enable it by adding the repository **variable** `HF_SPACE` (`<your-hf-username>/qb-motion-atlas-api`) and the repository **secret** `HF_TOKEN` in GitHub -> Settings -> Secrets and variables -> Actions. Vercel's GitHub integration can do the same for the frontend (import the repo with root directory `frontend/`).

## Operations
- **Logs:** Space -> Logs. One JSON object per line; `"upload matched"` lines include the per-layer similarity scores.
- **Health:** `/health` (process up) and `/health/ready` (database reachable, queue depth). Point a free uptime monitor such as UptimeRobot at `/health/ready`; it also stops the Space from going to sleep.
- **Errors:** set `SENTRY_DSN` as a Space secret to report exceptions to Sentry.
- **Takedown:** set `REFERENCE_VIDEO_OVERLAY_ENABLED=false` to switch every reference clip to skeleton-only immediately, or `REFERENCE_VIDEO_ALLOW_OFFICIAL=false` for only league/team broadcast clips.
- **Stuck uploads** are retried automatically (`JOB_TIMEOUT_SEC`, `JOB_MAX_ATTEMPTS`) and then marked failed with a "try again" message. `uploads.last_error` in the database holds the reason.
