import { z } from "zod";

export const budgetSchema = z.enum(["low", "medium", "high"]);

export const preferencesSchema = z.object({
  location: z.string().min(1, "Please select a location"),
  budget: budgetSchema,
  cuisine: z.string().optional(),
  min_rating: z.number().min(0).max(5),
  additional: z.string().optional(),
  top_k: z.number().min(1).max(10).default(5),
});

export type PreferencesFormValues = z.infer<typeof preferencesSchema>;
export type BudgetTier = z.infer<typeof budgetSchema>;

export const BUDGET_OPTIONS: { value: BudgetTier; label: string; hint: string }[] = [
  { value: "low", label: "₹", hint: "≤₹500" },
  { value: "medium", label: "₹₹", hint: "₹501–1500" },
  { value: "high", label: "₹₹₹", hint: ">₹1500" },
];
