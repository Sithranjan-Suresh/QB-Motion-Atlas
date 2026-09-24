# Notebooks

Sandbox for exploratory pose-extraction and pipeline experiments. Anything proven out here that becomes a real pipeline step gets promoted into `pipeline/` as a proper module — notebooks are for exploration, not production code.

Convention:
- Name notebooks `NN_short_description.ipynb` (e.g. `01_pose_extraction_sanity_check.ipynb`), numbered in the rough order they were created, so the exploration history stays readable.
- Clear cell outputs before committing large-output notebooks (video frames, big arrays) to keep diffs reviewable.
- One notebook = one question or experiment. Don't let a single notebook grow into a general-purpose scratchpad.
