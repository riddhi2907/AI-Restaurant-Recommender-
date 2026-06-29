export function Footer() {
  return (
    <footer className="flex w-full flex-col items-center justify-between gap-md border-t border-outline-variant bg-surface-container-lowest px-md py-xl md:flex-row lg:px-margin-desktop">
      <div className="flex flex-col items-center gap-xs md:items-start">
        <span className="text-label-sm font-bold text-on-surface">AI Restaurant Recommender</span>
        <p className="max-w-xs text-center text-body-md text-on-surface-variant md:text-left">
          Data from Zomato dataset | Recommendations powered by AI
        </p>
      </div>
      <p className="text-label-sm text-on-surface-variant">© 2026 AI Restaurant Recommender</p>
    </footer>
  );
}
