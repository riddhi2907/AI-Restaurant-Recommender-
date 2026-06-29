import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Loader2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { useCuisines, useLocations } from "@/hooks/useMetadata";
import { cn } from "@/lib/utils";
import {
  BUDGET_OPTIONS,
  preferencesSchema,
  type PreferencesFormValues,
} from "@/types/preferences";

interface PreferenceFormProps {
  onSubmit: (values: PreferencesFormValues) => void;
  isLoading: boolean;
  disabled?: boolean;
  defaultValues?: Partial<PreferencesFormValues>;
}

export function PreferenceForm({
  onSubmit,
  isLoading,
  disabled = false,
  defaultValues,
}: PreferenceFormProps) {
  const { data: locations = [], isLoading: locationsLoading } = useLocations();
  const { data: cuisines = [] } = useCuisines();
  const [cuisineQuery, setCuisineQuery] = useState("");
  const [showCuisineSuggestions, setShowCuisineSuggestions] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<PreferencesFormValues>({
    resolver: zodResolver(preferencesSchema),
    defaultValues: {
      location: "",
      budget: "medium",
      cuisine: "",
      min_rating: 0,
      additional: "",
      top_k: 5,
      ...defaultValues,
    },
  });

  const budget = watch("budget");
  const minRating = watch("min_rating");
  const location = watch("location");

  useEffect(() => {
    if (!location && locations.length === 1) {
      setValue("location", locations[0]);
    }
  }, [location, locations, setValue]);

  const filteredCuisines = useMemo(() => {
    if (!cuisineQuery.trim()) return cuisines.slice(0, 8);
    const q = cuisineQuery.toLowerCase();
    return cuisines.filter((c) => c.toLowerCase().includes(q)).slice(0, 8);
  }, [cuisines, cuisineQuery]);

  const formDisabled = disabled || isLoading;

  const cuisineRegister = register("cuisine");

  return (
    <div className={cn("max-w-md w-full mx-auto", formDisabled && !isLoading && "opacity-60")}>
      <div className="mb-xl">
        <div className="mb-xs flex items-center gap-xs">
          <span className="material-symbols-outlined text-primary material-symbols-filled">
            auto_awesome
          </span>
          <span className="text-label-sm font-bold uppercase tracking-wider text-primary">
            Smart Filters
          </span>
        </div>
        <h1 className="mb-xs text-page-title text-on-surface">Find your next favorite meal.</h1>
        <p className="text-body-md text-on-surface-variant">
          Tell us what you&apos;re craving, and our AI will scout the best spots in town for you.
        </p>
      </div>

      <form
        onSubmit={handleSubmit(onSubmit)}
        className={cn("space-y-lg", formDisabled && "pointer-events-none")}
      >
        {/* Location dropdown */}
        <div className="space-y-xs">
          <label htmlFor="location" className="flex items-center gap-xs text-body-lg text-on-surface">
            <span className="material-symbols-outlined text-outline">location_on</span>
            Where are you? <span className="text-primary">*</span>
          </label>
          <div className="relative">
            <select
              id="location"
              {...register("location")}
              disabled={locationsLoading || formDisabled}
              className={cn(
                "h-12 w-full appearance-none rounded-lg border bg-surface px-md pr-10 text-body-md outline-none transition-all",
                errors.location
                  ? "border-error focus:border-error focus:ring-2 focus:ring-error/20"
                  : "border-outline-variant focus:border-primary focus:ring-2 focus:ring-primary/20",
              )}
            >
              <option value="">
                {locationsLoading ? "Loading locations…" : "Select an area"}
              </option>
              {locations.map((loc) => (
                <option key={loc} value={loc}>
                  {loc}
                </option>
              ))}
            </select>
            <span className="material-symbols-outlined pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-outline">
              expand_more
            </span>
          </div>
          {errors.location && (
            <p className="text-label-sm text-error">{errors.location.message}</p>
          )}
        </div>

        {/* Cuisine with autocomplete */}
        <div className="relative space-y-xs">
          <label htmlFor="cuisine" className="flex items-center gap-xs text-body-lg text-on-surface">
            <span className="material-symbols-outlined text-outline">restaurant_menu</span>
            Cuisine preference
          </label>
          <input
            id="cuisine"
            type="text"
            autoComplete="off"
            placeholder="e.g. Italian, North Indian"
            disabled={formDisabled}
            {...cuisineRegister}
            onChange={(e) => {
              cuisineRegister.onChange(e);
              setCuisineQuery(e.target.value);
              setShowCuisineSuggestions(true);
            }}
            onFocus={() => setShowCuisineSuggestions(true)}
            onBlur={() => setTimeout(() => setShowCuisineSuggestions(false), 150)}
            className="h-12 w-full rounded-lg border border-outline-variant bg-surface px-md text-body-md outline-none transition-all focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
          {showCuisineSuggestions && filteredCuisines.length > 0 && (
            <ul className="absolute z-20 mt-1 max-h-48 w-full overflow-auto rounded-lg border border-outline-variant bg-surface-container-lowest shadow-soft">
              {filteredCuisines.map((c) => (
                <li key={c}>
                  <button
                    type="button"
                    className="w-full px-md py-2 text-left text-body-md hover:bg-surface-container-low"
                    onMouseDown={() => {
                      setValue("cuisine", c);
                      setCuisineQuery(c);
                      setShowCuisineSuggestions(false);
                    }}
                  >
                    {c}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Budget segmented control */}
        <div className="space-y-xs">
          <label className="text-body-lg text-on-surface">Budget Range</label>
          <div className="flex gap-1 rounded-lg bg-surface-container p-1">
            {BUDGET_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                disabled={formDisabled}
                title={opt.hint}
                onClick={() => setValue("budget", opt.value)}
                className={cn(
                  "flex-1 rounded-md py-2 text-center text-body-md transition-all",
                  budget === opt.value
                    ? "bg-primary text-on-primary shadow-soft"
                    : "text-on-surface-variant hover:bg-surface-bright",
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <p className="text-label-sm text-on-surface-variant">
            {BUDGET_OPTIONS.find((o) => o.value === budget)?.hint} for two
          </p>
        </div>

        {/* Min rating slider */}
        <div className="space-y-xs">
          <div className="flex items-center justify-between">
            <label htmlFor="min_rating" className="text-body-lg text-on-surface">
              Minimum Rating
            </label>
            <span className="text-label-sm font-bold text-primary">
              {minRating.toFixed(1)}
              {minRating > 0 ? "+" : ""}
            </span>
          </div>
          <input
            id="min_rating"
            type="range"
            min={0}
            max={5}
            step={0.1}
            disabled={formDisabled}
            {...register("min_rating", { valueAsNumber: true })}
            className="slider-thumb"
          />
          <div className="flex justify-between text-label-sm text-on-surface-variant">
            <span>0.0</span>
            <span>5.0</span>
          </div>
        </div>

        {/* Extras */}
        <div className="space-y-xs">
          <label htmlFor="additional" className="text-label-sm font-bold uppercase text-on-surface-variant">
            Extras
          </label>
          <textarea
            id="additional"
            rows={2}
            placeholder="family-friendly, quick service, outdoor seating"
            disabled={formDisabled}
            {...register("additional")}
            className="w-full resize-none rounded-lg border border-outline-variant bg-surface px-md py-3 text-body-md outline-none transition-all focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </div>

        <button
          type="submit"
          disabled={formDisabled}
          className="group flex h-14 w-full items-center justify-center gap-xs rounded-lg bg-primary text-body-lg font-medium text-on-primary shadow-soft transition-all hover:bg-primary-container active:scale-[0.98] disabled:opacity-70"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              Finding matches…
            </>
          ) : (
            <>
              Get Recommendations
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
            </>
          )}
        </button>
      </form>
    </div>
  );
}
