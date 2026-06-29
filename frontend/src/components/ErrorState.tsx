import { AlertCircle, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  message: string;
  suggestions?: string[];
  onRetry?: () => void;
}

export function ErrorState({ message, suggestions = [], onRetry }: ErrorStateProps) {
  return (
    <div className="flex h-full min-h-[400px] flex-col items-center justify-center gap-lg p-md lg:p-xl">
      <div className="w-full max-w-lg rounded-xl border-l-4 border-error bg-error-container p-lg shadow-soft">
        <div className="flex flex-col items-center gap-md text-center md:flex-row md:text-left">
          <AlertCircle className="h-10 w-10 shrink-0 text-error" />
          <div className="flex-1">
            <h3 className="mb-xs text-card-title text-on-error-container">Something went wrong</h3>
            <p className="text-body-md text-on-error-container">{message}</p>
            {suggestions.length > 0 && (
              <p className="mt-sm text-label-sm text-on-error-container">
                Did you mean: {suggestions.slice(0, 3).join(", ")}?
              </p>
            )}
          </div>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="flex items-center gap-xs rounded-lg bg-error px-md py-2 text-label-sm font-bold text-on-primary transition-opacity hover:opacity-90"
            >
              <RefreshCw className="h-4 w-4" />
              Retry
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

interface NoResultsStateProps {
  onAdjust?: () => void;
}

export function NoResultsState({ onAdjust }: NoResultsStateProps) {
  return (
    <div className="flex h-full min-h-[400px] flex-col items-center justify-center gap-md p-md text-center lg:p-xl">
      <span className="material-symbols-outlined text-5xl text-outline">search_off</span>
      <h3 className="text-section-title text-on-surface">No matches found</h3>
      <p className="max-w-md text-body-md text-on-surface-variant">
        Try a different cuisine, relax your minimum rating, or choose another budget tier.
      </p>
      {onAdjust && (
        <button
          type="button"
          onClick={onAdjust}
          className="rounded-lg border border-outline-variant px-md py-2 text-label-sm font-bold text-on-surface-variant transition-colors hover:bg-surface-container-low"
        >
          Adjust preferences
        </button>
      )}
    </div>
  );
}
