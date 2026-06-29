import type { Recommendation, RecommendationResponse } from "@/types/recommendation";
import { RecommendationCard } from "./RecommendationCard";
import { SummaryPanel } from "./SummaryPanel";

interface ResultsSectionProps {
  response: RecommendationResponse;
}

export function ResultsSection({ response }: ResultsSectionProps) {
  const { summary, recommendations, metadata } = response;
  const shown = recommendations.length;
  const total = metadata.total_candidates;

  return (
    <section className="h-full bg-background p-md lg:p-margin-desktop">
      {summary && <SummaryPanel summary={summary} />}

      {!metadata.llm_used && recommendations.length > 0 && (
        <div className="mb-md inline-flex items-center gap-1 rounded-full border border-outline-variant bg-surface-container-low px-sm py-1 text-label-sm text-on-surface-variant">
          <span className="material-symbols-outlined text-[14px]">sort</span>
          Ranked by rating (AI unavailable)
        </div>
      )}

      <div className="space-y-lg">
        {recommendations.map((rec: Recommendation, index: number) => (
          <RecommendationCard key={`${rec.rank}-${rec.name}`} recommendation={rec} index={index} />
        ))}
      </div>

      {shown > 0 && (
        <div className="mt-xl border-t border-outline-variant pt-lg">
          <p className="text-body-md text-on-surface-variant">
            Showing {shown} of {total} candidate{total !== 1 ? "s" : ""}
            {metadata.llm_used ? " · AI-powered ranking" : " · Filter-based ranking"}
          </p>
        </div>
      )}
    </section>
  );
}
