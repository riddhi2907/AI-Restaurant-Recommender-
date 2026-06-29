import { motion } from "framer-motion";
import type { Recommendation } from "@/types/recommendation";
import { cn } from "@/lib/utils";

interface RecommendationCardProps {
  recommendation: Recommendation;
  index: number;
}

export function RecommendationCard({ recommendation, index }: RecommendationCardProps) {
  const isTopPick = recommendation.rank === 1;

  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.35 }}
      className={cn(
        "group overflow-hidden rounded-xl bg-surface-container-lowest transition-all hover:-translate-y-1",
        isTopPick
          ? "border-2 border-primary shadow-rank-glow"
          : "border border-outline-variant hover:border-primary/40 hover:shadow-soft",
      )}
    >
      <div className="p-md lg:p-lg">
        <div className="mb-md flex items-start justify-between gap-md">
          <div className="flex items-start gap-md">
            {isTopPick && (
              <span className="shrink-0 rounded-full bg-primary px-sm py-1 text-label-sm font-bold text-on-primary shadow-soft">
                #1 Choice
              </span>
            )}
            {!isTopPick && (
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface-container text-label-sm font-bold text-on-surface-variant">
                #{recommendation.rank}
              </span>
            )}
            <div>
              <h4 className={cn("text-on-surface", isTopPick ? "text-section-title" : "text-card-title")}>
                {recommendation.name}
              </h4>
              <p className="text-body-md text-on-surface-variant">{recommendation.cuisine}</p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-1 rounded-lg bg-secondary px-sm py-1 text-label-sm font-bold text-on-secondary">
            <span className="material-symbols-outlined text-[16px] material-symbols-filled">star</span>
            {recommendation.rating.toFixed(1)}
          </div>
        </div>

        <div className="mb-md flex items-center gap-xl text-label-sm font-bold text-on-surface-variant">
          <span className="flex items-center gap-1">
            <span className="material-symbols-outlined text-[18px]">payments</span>
            {recommendation.estimated_cost}
          </span>
        </div>

        <div
          className={cn(
            "rounded-lg p-sm",
            isTopPick
              ? "border-l-4 border-primary bg-surface-container"
              : "bg-surface-container/50",
          )}
        >
          <p className="text-body-md italic text-on-surface">&ldquo;{recommendation.explanation}&rdquo;</p>
        </div>
      </div>
    </motion.article>
  );
}
