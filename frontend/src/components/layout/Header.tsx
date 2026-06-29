export function Header() {
  return (
    <header className="fixed top-0 z-50 flex h-16 w-full items-center justify-between border-b border-outline-variant bg-surface px-md lg:px-margin-desktop">
      <div className="flex items-center gap-xs">
        <span className="material-symbols-outlined text-3xl text-primary material-symbols-filled">
          restaurant
        </span>
        <span className="text-card-title font-black text-primary">AI Restaurant Recommender</span>
      </div>
      <span className="hidden text-label-sm font-bold uppercase tracking-wider text-on-surface-variant sm:block">
        Powered by AI
      </span>
    </header>
  );
}
