import type { CoachingNote } from "@/lib/api";

const PHASE_LABELS: Record<string, string> = {
  load: "Load",
  stride: "Stride",
  arm_cock: "Arm Cock",
  acceleration: "Acceleration",
  release: "Release",
  follow_through: "Follow-Through",
};

// Task 84.
export default function CoachingNotesList({ notes }: { notes: CoachingNote[] }) {
  if (notes.length === 0) {
    return <p className="text-sm text-gray-500">No coaching notes available for this throw yet.</p>;
  }

  return (
    <ul className="flex w-full max-w-md flex-col gap-3">
      {notes.map((note) => (
        <li key={note.phase} className="rounded-lg border border-gray-200 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
            {PHASE_LABELS[note.phase] ?? note.phase}
          </p>
          <p className="mt-1 text-sm text-gray-800">{note.note}</p>
        </li>
      ))}
    </ul>
  );
}
