# Overnight report: 2026-09-30

Branch: `main-hd9r2q-mtd6kt`, 14 commits, all pushed. No pull request opened.

## Summary
The app is deployable. The backend runs as one Docker image (API + background worker) with every piece a public URL needs. It is built, tested, and checked end to end here, including the real production image running against S3-compatible storage. What's left is **your accounts** (about 30 minutes, `docs/deployment.md`) and **the data work on your Windows machine** (which decides whether the matches mean anything).

Tests: 192 pass locally. GitHub CI now runs backend tests, frontend lint and build, and a Docker build on every push. See "CI status" at the end.

## Your morning checklist
1. **Rotate** the Groq key and the Supabase database password; both were pasted into chat.
2. **Supabase:** copy the *Session pooler* connection string. The direct `db.<ref>.supabase.co` address you sent is IPv6-only and can't be reached from Hugging Face or from here, which is why I couldn't connect last night. Then create a private bucket `qb-motion-atlas` and an S3 access key. Clicks are in `docs/deployment.md` step 1.
3. **Hugging Face:** create an account and a *Write* token.
4. **Then either:**
   - **Paste me** the pooler string, the S3 endpoint, region, key ID and secret, and the HF token. I can deploy the backend from here (I checked that Hugging Face is reachable from this container), run the smoke test, and tell you the API URL. OR
   - **Do it yourself:** put them in `.env` and run `python scripts/deploy_hf_space.py --space <you>/qb-motion-atlas-api --secrets-from-env` (`docs/deployment.md` steps 2-3).
5. **On Windows** (only you can do this, since `data/` lives there): `python scripts/publish_reference_data.py` loads the reference clips into Supabase and uploads the trimmed videos.
6. **Frontend:** `cd frontend`, `vercel env add NEXT_PUBLIC_API_BASE_URL production` (the Space URL), then `vercel --prod`.
7. Set the Space's `CORS_ALLOWED_ORIGINS` to the Vercel URL, then run `python scripts/smoke_test_deploy.py --api <space-url> --frontend <vercel-url>`.

## What was built (by commit)
| Area | What changed |
|---|---|
| Train/test split | `split_clips()` groups clips by source session. New `source_session` column in `provenance.csv`; only the Mariota pro-day pair is filled in, so check the rest when you promote clips. |
| Coaching notes | Groq via plain httpx (`pipeline/llm_client.py`), default model `openai/gpt-oss-20b`; falls back to the rule-based notes on any error. Verified against the live API. |
| Job queue | `api/worker.py`: the `uploads` table *is* the queue. Rows are claimed with `SKIP LOCKED`; abandoned jobs are retried; jobs run in a child process with a hard 5-minute timeout; after 3 attempts the user sees "something went wrong, try again" instead of an endless spinner. No Redis needed. |
| Storage | `api/storage.py`: local disk for dev, any S3-compatible bucket for production. Videos play through short-lived signed URLs (or a proxy mode that supports seeking). |
| Upload safety | Uploads stream to disk in 1 MB chunks (the old code loaded all 100 MB into memory), oversized bodies are refused early (413), files must actually be mp4/mov/webm, 10 uploads per hour per IP (429), and new uploads are refused while 20 jobs are queued (503). |
| Privacy | Uploads are deleted automatically after 7 days; `DELETE /uploads/{id}` plus a "Delete my video and results" button. |
| Matching | `pipeline/matching.py`: live uploads now use feature distance **plus DTW plus the embedding** (when a model exists). Before tonight only the first layer was used. Failed-QC clips are no longer matchable. |
| Reference video | Broadcast clips are now shown, per your decision. `REFERENCE_VIDEO_ALLOW_OFFICIAL=false` or `REFERENCE_VIDEO_OVERLAY_ENABLED=false` turns them off without a deploy if a takedown notice arrives. |
| Deployment | `Dockerfile`, `requirements-prod.txt` (no torch), `scripts/deploy_hf_space.py`, `scripts/publish_reference_data.py`, `scripts/smoke_test_deploy.py`, CI and deploy workflows, and `.env.example` documenting every setting. |
| Ops | JSON logs, `/health/ready`, optional Sentry (`SENTRY_DSN`). |
| Frontend | `/how-to-film`, `/privacy`, `/terms`, a footer with a not-affiliated-with-the-NFL notice, delete button, "failed" and "taking longer than usual" states. Checked in a real browser at phone width. |

## Bugs found and fixed along the way
These were in existing code; each would have broken production:
1. **Every per-phase breakdown would have been empty.** The seed script never created per-phase reference rows, and embedding backfill depended on them too.
2. **A new database engine per request.** On Supabase that means a new TLS connection each time until the pooler runs out of connections.
3. **Migrations would crash** on a URL-encoded password (your `@` becomes `%40`, and Alembic's config parser treats `%` specially).
4. **The embedding model imported torch**, which the production image doesn't install.
5. **Both Windows-only test failures:** the candidates doc was read as cp1252 instead of UTF-8 (so the parser found 0 candidates), and the share card used a Linux-only font path (fonts are now bundled).
6. **CI never seeded the reference clips**, so one API test could only pass on a hand-seeded machine.

## Measurements
- Production image: **565 MB** compressed.
- A 15s 1080p upload in the production container: **411 MiB peak**, **121 MiB** once the job finishes. That's why I chose Hugging Face Spaces (16 GB free) over Render's free tier (512 MB, and 0.1 CPU would take minutes per upload).
- Groq: valid output on the first call. In one note the model got the direction of an elbow-angle difference backwards; logged in `docs/coaching_prompt.md`.

## Not done, and why
- **Actually deploying:** needs your Hugging Face token and the Supabase pooler string and storage keys (see the checklist above).
- **Validating matching accuracy:** needs your machine's `data/` folder: promote the round-4 clips, retrim the 8 zero-follow-through clips, gold-label, then re-run `python -m eval.run_evaluation`. Until that shows same-QB retrieval clearly above chance, a "72% Josh Allen" result is not yet backed by evidence. This is still the biggest gap between "deployed" and "works".
- **Round 5 sourcing** (Brissett, Rodgers, Hurts, Bryce Young): local machine only.
- **A trained embedding model:** 35 clips is too few to train one that means anything, so the embedding layer stays switched off (it turns on automatically when `EMBEDDING_CHECKPOINTS_DIR` points at checkpoints).
- **Search indexing:** the site still sets `noindex`, as before. Remove `robots` in `frontend/src/app/layout.tsx` when you want it findable.
- **The privacy and terms pages** are written to match what the code actually does, but they aren't legal advice.
- **claude-office hooks** are still in your `~/.claude/settings.json` on Windows (`bash hooks/uninstall.sh` in the claude-office folder).

## CI status
See the Actions tab for branch `main-hd9r2q-mtd6kt`. The only real failure during the night was the missing seed step (fixed); later runs were cancelled by newer pushes, which is the intended behavior. The status of the latest run is also in my chat reply.
