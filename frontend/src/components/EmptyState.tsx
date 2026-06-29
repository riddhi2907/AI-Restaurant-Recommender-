import { Sparkles, UtensilsCrossed } from "lucide-react";

export function EmptyState() {
  return (
    <div className="relative flex h-full min-h-[480px] flex-col items-center justify-center overflow-hidden bg-background px-md">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: "radial-gradient(#b7122a 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />
      <div className="relative z-10 max-w-lg text-center">
        <div className="relative mb-lg inline-flex h-24 w-24 items-center justify-center rounded-full bg-surface-container-high">
          <UtensilsCrossed className="h-12 w-12 text-outline-variant" strokeWidth={1.5} />
          <div className="absolute -right-1 -top-1 rounded-full bg-primary p-1.5 shadow-soft">
            <Sparkles className="h-4 w-4 text-on-primary" />
          </div>
        </div>
        <h2 className="mb-sm text-section-title text-on-surface">Awaiting your taste preferences</h2>
        <p className="mb-xl text-body-md leading-relaxed text-on-surface-variant">
          Our AI is ready to scour thousands of restaurants. Fill out the form to see your
          personalized picks appear here.
        </p>
        <div className="grid select-none grid-cols-2 gap-md opacity-30">
          {[1, 2].map((i) => (
            <div
              key={i}
              className="rounded-xl border border-outline-variant/30 bg-white p-sm text-left shadow-soft"
            >
              <div className="mb-xs h-16 w-full rounded-lg bg-surface-container" />
              <div className="mb-xs h-4 w-3/4 rounded bg-surface-container" />
              <div className="h-3 w-1/2 rounded bg-surface-container" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
