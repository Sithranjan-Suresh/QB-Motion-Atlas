# Full Context — QB Motion Atlas ("NFL QB DNA")

## Vision

**One sentence:** A pose-based biomechanics system that decomposes a user's throwing motion into interpretable phases and matches them, phase by phase, against a curated database of NFL quarterback throwing mechanics — grounded in real metric-learning research, not a novelty filter.

**One paragraph:** Most "AI compares you to a pro athlete" tools collapse a complex motion into a single similarity score computed from a handful of static angles — shallow, uninterpretable, and impossible to defend under scrutiny. QB Motion Atlas instead treats a throw as a temporal sequence with distinct phases (load, stride, arm cock, acceleration, release, follow-through), extracts biomechanical features per phase, and computes similarity both through interpretable hand-engineered features and a learned embedding space trained with metric learning. The result is a system that can say not just "you throw like Josh Allen" but "your stride phase resembles Herbert, your release resembles Stafford" — and can back every claim with a number, a confidence level, and an honest statement of what it can't conclude. It's built as a long-term personal research/portfolio project, not a weekend hack, with the evaluation rigor to survive a technical interview.

## Problem

Existing throwing-motion analysis tools (dart-throw apps, generic swing analyzers) either give a shallow gimmick score with no interpretability, or require expensive proprietary motion-capture data (NFL Next Gen Stats) that's inaccessible to independent builders. There's no publicly available system that takes an ordinary phone video, extracts genuine phase-level biomechanics, and produces an interpretable, evaluated similarity comparison — while being explicit about the limits of what video-based pose estimation can actually measure.

## Target Users

- **Primary (consumer surface):** Football fans and players curious about their own throwing mechanics — want an engaging, shareable, personalized result.
- **Secondary (practical framing):** Youth football coaches who want fast, data-driven mechanics feedback for players without access to expensive biomechanics labs — today they rely purely on eyeballing form.
- **Tertiary (real target of the project):** AI/ML engineering internship reviewers — the project is designed to demonstrate genuine research ability with limited data, not just API integration skill.

## User Journey

1. User records or uploads a 5–15 second side-view video of themselves throwing a football.
2. System validates video quality (camera angle, full body visible, single throw detected) and rejects/re-prompts on failure rather than guessing.
3. Video is processed: pose extraction → phase segmentation → per-phase feature extraction → normalization.
4. System computes similarity against the reference QB database using both interpretable features (DTW/weighted distance) and a learned embedding space.
5. Results page renders: overall match + %, per-phase breakdown (which QB each phase resembles), skeleton overlay synced to the matched QB's reference clip, and specific coaching notes derived from measured deltas.
6. User can scrub frame-by-frame, export a shareable results card, or re-record if confidence was low.

## Core Features (at each maturity stage)

- Video/webcam capture and upload
- Pose extraction (MediaPipe → RTMPose as pipeline matures)
- Automatic throwing-phase segmentation (heuristic → learned temporal model)
- Per-phase biomechanical feature extraction (joint angles, timing, rotation velocity)
- Similarity engine: hand-engineered feature distance + DTW + learned metric-learning embedding
- Confidence-aware results (explicit low-confidence state, not forced answers)
- Data-derived coaching feedback (rule-based → LLM-phrased from structured deltas)
- Skeleton overlay + synced side-by-side comparison video
- Shareable results card export

## Key Differentiators

- Phase-decomposed comparison, not a single opaque score — each phase gets its own match and explanation.
- A learned embedding space trained via metric learning, not just hand-tuned distance metrics — real ML depth.
- An actual evaluation methodology (retrieval accuracy, self-consistency, discriminative validity) reported honestly, including where it's weak.
- Explicit, on-page epistemic honesty about what video-based similarity can and can't conclude.
- Built to generalize (the phase-segmentation + embedding framework extends to other positions/sports), not hardcoded to one comparison.

## Technical Overview

- **Stack:** Next.js frontend, FastAPI backend, PyTorch/MediaPipe pose + embedding pipeline, Postgres + pgvector (or FAISS) for similarity search, async job processing (Celery/Redis at scale).
- **Key technical bets:** (1) phase segmentation is the right unit of comparison, not the whole throw as one blob; (2) a learned embedding, layered on top of interpretable hand-engineered features, beats either approach alone; (3) camera-angle invariance (via 3D lifting) is the hardest and most differentiating problem to eventually tackle.
- **Data:** Small, curated, provenance-tracked dataset of publicly available NFL QB coaching-breakdown clips (8–20 QBs, 10–30 clips each depending on stage) — explicitly non-commercial/research-framed given licensing constraints.

## Demo Flow (portfolio demo, not a timed pitch)

Since this isn't a hackathon, there's no 90-second constraint — but the demo should still be designed to land in under two minutes for an interview or portfolio walkthrough:
1. Live webcam throw (not pre-recorded) — the "wow" moment: instant, in-person feedback.
2. Results page reveal: overall match, then scroll into the phase-by-phase breakdown.
3. One specific, data-backed coaching note read aloud — proves it's not templated.
4. Pull up the evaluation report (retrieval accuracy chart) — this is the moment that shifts the impression from "cool demo" to "this person did real ML work."

## Success Metrics

- **Technical:** documented top-1/top-3 known-identity retrieval accuracy on held-out clips; measurable discriminative validity (inter-QB distance > intra-QB distance); pose extraction PCK above a defined threshold.
- **Product:** a stranger can use the deployed app without explanation and get a sensible result or a clear, honest rejection.
- **Portfolio:** a written technical report (methodology + evaluation + honest limitations) that stands alone as a writing sample, independent of the live demo.

## Future Expansion

- Extend the same phase-segmentation + embedding framework to other positions (WR routes, DB backpedal, RB running style) to demonstrate the architecture generalizes.
- Monocular 2D-to-3D pose lifting to reduce camera-angle sensitivity.
- Cross-sport contrastive pretraining (baseball pitching, javelin) to improve embedding quality via transfer learning on a larger unlabeled pool before fine-tuning on the small NFL-specific set.
