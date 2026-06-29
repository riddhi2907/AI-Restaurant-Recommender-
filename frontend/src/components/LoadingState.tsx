const LOADING_PHRASES = [
  "AI is ranking your matches…",
  "Cross-referencing reviews…",
  "Finding the best value options…",
  "Matching your cuisine preferences…",
];

interface LoadingStateProps {
  phraseIndex?: number;
}

export function LoadingState({ phraseIndex = 0 }: LoadingStateProps) {
  const phrase = LOADING_PHRASES[phraseIndex % LOADING_PHRASES.length];

  return (
    <div className="flex h-full min-h-[480px] flex-col gap-lg bg-surface-container-low p-md lg:p-xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-sm">
          <span className="material-symbols-outlined animate-pulse text-primary material-symbols-filled">
            auto_awesome
          </span>
          <h3 className="text-card-title text-on-surface">{phrase}</h3>
        </div>
        <div className="h-4 w-32 shimmer rounded" />
      </div>

      <div className="flex flex-col gap-md">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="overflow-hidden rounded-xl bg-surface shadow-soft"
          >
            <div className="p-md">
              <div className="mb-sm flex items-start justify-between">
                <div className="h-6 w-2/3 shimmer rounded" />
                <div className="h-6 w-14 shimmer rounded-lg" />
              </div>
              <div className="mb-md h-4 w-1/3 shimmer rounded" />
              <div className="h-16 w-full shimmer rounded-lg" />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-lg flex items-center gap-md rounded-xl border border-primary-container/20 bg-primary-container/10 p-lg">
        <span className="material-symbols-outlined text-3xl text-primary-container">lightbulb</span>
        <div>
          <p className="mb-1 text-label-sm font-bold uppercase text-primary-container">Pro tip</p>
          <p className="text-body-md italic text-on-surface-variant">
            We analyze ratings and preferences to find the best spots for you.
          </p>
        </div>
      </div>
    </div>
  );
}
