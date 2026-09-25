const CONFIDENCE_STYLES: Record<string, string> = {
  high: "bg-green-100 text-green-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-gray-100 text-gray-700",
};

type OverallMatchCardProps = {
  matchedQbName: string | null;
  similarityScore: number;
  confidenceLevel: string;
};

// Task 83.
export default function OverallMatchCard({ matchedQbName, similarityScore, confidenceLevel }: OverallMatchCardProps) {
  const confidenceStyle = CONFIDENCE_STYLES[confidenceLevel] ?? CONFIDENCE_STYLES.low;
  const percent = Math.round(similarityScore * 100);

  if (!matchedQbName) {
    return (
      <div className="w-full max-w-md rounded-lg border border-gray-200 p-6 text-center">
        <p className="text-sm text-gray-600">
          No reference throws are available to compare against yet -- check back once the reference database has
          been built out.
        </p>
      </div>
    );
  }

  return (
    <div className="flex w-full max-w-md flex-col items-center gap-2 rounded-lg border border-gray-200 p-6 text-center">
      <p className="text-sm text-gray-500">Your closest match</p>
      <p className="text-2xl font-bold capitalize">{matchedQbName.replace(/_/g, " ")}</p>
      <p className="text-3xl font-semibold">{percent}%</p>
      <span className={`rounded-full px-3 py-1 text-xs font-medium ${confidenceStyle}`}>
        {confidenceLevel} confidence
      </span>
    </div>
  );
}
