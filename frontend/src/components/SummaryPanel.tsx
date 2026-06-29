interface SummaryPanelProps {
  summary: string;
}

export function SummaryPanel({ summary }: SummaryPanelProps) {
  return (
    <div className="relative mb-xl overflow-hidden rounded-xl border border-primary-container/20 bg-gradient-to-br from-primary-container/10 to-surface-container-high p-lg">
      <div className="relative z-10 flex items-start gap-md">
        <div className="animate-sparkle rounded-lg bg-primary p-xs">
          <span className="material-symbols-outlined text-on-primary material-symbols-filled">
            auto_awesome
          </span>
        </div>
        <div>
          <h3 className="mb-xs text-card-title text-on-surface">AI Recommendation Summary</h3>
          <p className="text-body-lg leading-relaxed text-on-surface-variant">{summary}</p>
        </div>
      </div>
    </div>
  );
}
