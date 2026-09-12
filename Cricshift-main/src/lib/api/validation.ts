/**
 * Zod Validation Schemas — Phase 5
 * Mirrors backend Pydantic validators for client-side validation.
 */

import { z } from "zod";

/**
 * Base object schema — used by zodResolver for proper type inference.
 * Cross-field validation (same-team, target for innings 2) is handled
 * in the form submit handler to avoid Zod v4 / RHF type conflicts.
 *
 * Coerce a possibly-empty input into a required number.
 * Empty string / null / undefined -> validation error (field must be filled),
 * so results are only produced after the user explicitly enters every value.
 */
const requiredNumber = (opts?: { min?: number; max?: number; msg?: string }) =>
  z
    .preprocess(
      (v) => (v === "" || v === null || v === undefined ? undefined : v),
      z.coerce.number({ error: opts?.msg ?? "Required" }).int(),
    )
    .refine((n) => (opts?.min === undefined ? true : n >= opts.min), {
      message: opts?.msg ?? `Must be ≥ ${opts?.min}`,
    })
    .refine((n) => (opts?.max === undefined ? true : n <= opts.max), {
      message: opts?.msg ?? `Must be ≤ ${opts?.max}`,
    });

export const matchStateSchema = z.object({
  batting_team: z.string().min(1, "Select a batting team"),
  bowling_team: z.string().min(1, "Select a bowling team"),
  venue: z.string().min(1, "Select a venue"),
  innings: z.coerce.number().int().min(1).max(2).default(1),
  current_over: requiredNumber({ min: 0, max: 20, msg: "Enter the over" }),
  current_ball: requiredNumber({ min: 0, max: 6, msg: "Enter the ball" }),
  current_score: requiredNumber({ min: 0, msg: "Enter the score" }),
  current_wickets: requiredNumber({ min: 0, max: 10, msg: "Enter wickets" }),
  target: z.coerce.number().int().min(0).default(0),
  batter_name: z.string().min(1, "Select a batter"),
  bowler_name: z.string().min(1, "Select a bowler"),
  season: z.string().min(1, "Enter the season"),
  /* Rolling window stats — 0 is a valid default meaning "start of innings"
     or "data not available from live feed". The backend also defaults to 0. */
  runs_last_6_balls: z.coerce.number().int().min(0).default(0),
  runs_last_12_balls: z.coerce.number().int().min(0).default(0),
  runs_last_18_balls: z.coerce.number().int().min(0).default(0),
  runs_last_30_balls: z.coerce.number().int().min(0).default(0),
  wickets_last_6_balls: z.coerce.number().int().min(0).max(10).default(0),
  wickets_last_12_balls: z.coerce.number().int().min(0).max(10).default(0),
  boundaries_last_6_balls: z.coerce.number().int().min(0).default(0),
  boundaries_last_12_balls: z.coerce.number().int().min(0).default(0),
  dot_balls_last_6_balls: z.coerce.number().int().min(0).max(6).default(0),
  dot_balls_last_12_balls: z.coerce.number().int().min(0).max(12).default(0),
});

export type MatchStateFormData = z.infer<typeof matchStateSchema>;

/**
 * Form defaults. Required fields start EMPTY so the user must explicitly select
 * or enter every option before results are produced. Numeric required fields
 * use "" (empty input) which fails validation until a value is typed.
 */
export const matchStateDefaults: MatchStateFormData = {
  batting_team: "",
  bowling_team: "",
  venue: "",
  innings: 1,
  // Empty until the user types a value (cast because the resolved type is number).
  current_over: "" as unknown as number,
  current_ball: "" as unknown as number,
  current_score: "" as unknown as number,
  current_wickets: "" as unknown as number,
  target: 0,
  batter_name: "",
  bowler_name: "",
  season: "2024",
  runs_last_6_balls: 0,
  runs_last_12_balls: 0,
  runs_last_18_balls: 0,
  runs_last_30_balls: 0,
  wickets_last_6_balls: 0,
  wickets_last_12_balls: 0,
  boundaries_last_6_balls: 0,
  boundaries_last_12_balls: 0,
  dot_balls_last_6_balls: 0,
  dot_balls_last_12_balls: 0,
};
