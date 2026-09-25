import type { PhaseResult } from "@/lib/api";

const CONFIDENCE_STYLES: Record<string, string> = {
  high: "bg-green-100 text-green-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-gray-100 text-gray-700",
};

const PHASE_LABELS: Record<string, string> = {
  load: "Load",
  stride: "Stride",
  arm_cock: "Arm Cock",
  acceleration: "Acceleration",
  release: "Release",
  follow_through: "Follow-Through",
};

// Canonical throw order (pipeline/phase_segmentation.py), not object-key
// order, since phase_results is only populated for phases with reference
// data and can arrive in any order.
const PHASE_ORDER = ["load", "stride", "arm_cock", "acceleration", "release", "follow_through"];

// Tasks 116-118: one row per phase with enough reference data to compare
// against -- a phase absent from phaseResults just isn't rendered, the same
// honest-gap pattern OverallMatchCard uses for matched_qb_name being null.
export default function PhaseBreakdownPanel({ phaseResults }: { phaseResults: Record<string, PhaseResult> }) {
  const phases = PHASE_ORDER.filter((phase) => phase in phaseResults);

  if (phases.length === 0) {
    return (
      <div className="w-full max-w-md rounded-lg border border-gray-200 p-6 text-center">
        <p className="text-sm text-gray-600">
          No per-phase reference data is available yet -- check back once the reference database has more coverage.
        </p>
      </div>
    );
  }

  return (
    <div className="flex w-full max-w-md flex-col gap-3">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">Per-Phase Breakdown</h2>
      <ul className="flex flex-col gap-3">
        {phases.map((phase) => {
          const { matched_qb_name, score, confidence } = phaseResults[phase];
          const confidenceStyle = CONFIDENCE_STYLES[confidence] ?? CONFIDENCE_STYLES.low;
          return (
            <li key={phase} className="flex items-center justify-between rounded-lg border border-gray-200 p-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                  {PHASE_LABELS[phase] ?? phase}
                </p>
                <p className="mt-1 text-sm capitalize text-gray-800">{matched_qb_name.replace(/_/g, " ")}</p>
              </div>
              <div className="flex flex-col items-end gap-1">
                <p className="text-sm font-semibold">{Math.round(score * 100)}%</p>
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${confidenceStyle}`}>
                  {confidence}
                </span>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
