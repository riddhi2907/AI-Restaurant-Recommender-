import { useCallback, useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { ApiClientError, postRecommendations } from "@/lib/api-client";
import type { PreferencesFormValues } from "@/types/preferences";
import type { RecommendationResponse } from "@/types/recommendation";
import { useApiReady } from "@/hooks/useMetadata";
import { PreferenceForm } from "@/components/PreferenceForm";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { ErrorState, NoResultsState } from "@/components/ErrorState";
import { ResultsSection } from "@/components/ResultsSection";
import { cn } from "@/lib/utils";

type ViewState = "idle" | "loading" | "success" | "empty" | "error";

export default function HomePage() {
  const resultsRef = useRef<HTMLElement>(null);
  const [viewState, setViewState] = useState<ViewState>("idle");
  const [lastResponse, setLastResponse] = useState<RecommendationResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [errorSuggestions, setErrorSuggestions] = useState<string[]>([]);
  const [loadingPhrase, setLoadingPhrase] = useState(0);
  const [lastPreferences, setLastPreferences] = useState<PreferencesFormValues | null>(null);

  const { data: ready, isError: readyError } = useApiReady();

  const mutation = useMutation({
    mutationFn: postRecommendations,
    onMutate: () => {
      setViewState("loading");
      setErrorMessage("");
      setErrorSuggestions([]);
    },
    onSuccess: (data) => {
      setLastResponse(data);
      if (data.recommendations.length === 0) {
        setViewState("empty");
      } else {
        setViewState("success");
      }
    },
    onError: (error: Error) => {
      setViewState("error");
      if (error instanceof ApiClientError) {
        setErrorMessage(error.message);
        setErrorSuggestions(error.suggestions);
      } else {
        setErrorMessage("Unable to reach the recommendation service. Is the API running?");
      }
    },
  });

  const handleSubmit = useCallback(
    (values: PreferencesFormValues) => {
      setLastPreferences(values);
      mutation.mutate(values);
    },
    [mutation],
  );

  const handleRetry = useCallback(() => {
    if (lastPreferences) {
      mutation.mutate(lastPreferences);
    }
  }, [lastPreferences, mutation]);

  useEffect(() => {
    if (viewState !== "loading") return;
    const id = setInterval(() => setLoadingPhrase((p) => p + 1), 3000);
    return () => clearInterval(id);
  }, [viewState]);

  useEffect(() => {
    if (viewState === "success" && resultsRef.current) {
      resultsRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [viewState]);

  const apiBanner =
    readyError || (ready && !ready.dataset_loaded) ? (
      <div className="border-b border-error/30 bg-error-container px-md py-sm text-center text-body-md text-on-error-container">
        Restaurant dataset is not available. Start the backend API first.
      </div>
    ) : ready && !ready.groq_configured ? (
      <div className="border-b border-amber-200 bg-amber-50 px-md py-sm text-center text-body-md text-amber-900">
        GROQ_API_KEY not configured — results will use rating-based fallback.
      </div>
    ) : null;

  return (
    <>
      {apiBanner}
      <div className="mx-auto grid min-h-[calc(100vh-64px)] max-w-[1200px] grid-cols-1 md:grid-cols-[400px_1fr]">
        <aside
          className={cn(
            "border-outline-variant bg-surface-container-lowest p-md lg:p-lg md:border-r",
            viewState === "loading" && "relative",
          )}
        >
          {viewState === "loading" && (
            <div className="pointer-events-none absolute inset-0 z-10 bg-white/20" />
          )}
          <div className={cn(viewState === "loading" && "sticky top-24 opacity-60")}>
            <PreferenceForm
              onSubmit={handleSubmit}
              isLoading={mutation.isPending}
              disabled={viewState === "loading"}
              defaultValues={lastPreferences ?? undefined}
            />
          </div>
        </aside>

        <section ref={resultsRef} className="min-h-[480px]">
          {viewState === "idle" && <EmptyState />}
          {viewState === "loading" && <LoadingState phraseIndex={loadingPhrase} />}
          {viewState === "success" && lastResponse && (
            <ResultsSection response={lastResponse} />
          )}
          {viewState === "empty" && (
            <NoResultsState onAdjust={() => setViewState("idle")} />
          )}
          {viewState === "error" && (
            <ErrorState
              message={errorMessage}
              suggestions={errorSuggestions}
              onRetry={lastPreferences ? handleRetry : undefined}
            />
          )}
        </section>
      </div>
    </>
  );
}
