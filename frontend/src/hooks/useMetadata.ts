import { useQuery } from "@tanstack/react-query";
import { getCuisines, getLocations, getReady } from "@/lib/api-client";

export function useLocations() {
  return useQuery({
    queryKey: ["locations"],
    queryFn: getLocations,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCuisines() {
  return useQuery({
    queryKey: ["cuisines"],
    queryFn: getCuisines,
    staleTime: 5 * 60 * 1000,
  });
}

export function useApiReady() {
  return useQuery({
    queryKey: ["ready"],
    queryFn: getReady,
    retry: 1,
    refetchInterval: 30_000,
  });
}
