"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  matchStateSchema,
  matchStateDefaults,
  type MatchStateFormData,
} from "@/lib/api/validation";
import { useTeams, useVenues, usePlayers } from "@/lib/api/hooks";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Loader2, ChevronDown, ChevronUp, Zap } from "lucide-react";
import { useState } from "react";

interface MatchStateFormProps {
  onSubmit: (data: MatchStateFormData) => void;
  isLoading?: boolean;
  submitLabel?: string;
}

export function MatchStateForm({
  onSubmit,
  isLoading,
  submitLabel = "Predict Match Intelligence",
}: MatchStateFormProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const { data: teamsData } = useTeams();
  const { data: venuesData } = useVenues();
  const { data: playersData } = usePlayers({ limit: 200 });

  const teamNames = (teamsData?.teams ?? [])
    .map((t) => String(t.Team ?? ""))
    .filter(Boolean)
    .sort();
  const venueNames = (venuesData?.venues ?? [])
    .map((v) => String(v.Venue ?? ""))
    .filter(Boolean)
    .sort();
  const playerNames = (playersData?.players ?? [])
    .map((p) => String(p.Player_Name ?? ""))
    .filter(Boolean)
    .sort();

  const form = useForm<MatchStateFormData>({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver(matchStateSchema) as any,
    defaultValues: matchStateDefaults,
  });

  const innings = form.watch("innings");

  // Watch required fields so we can disable the submit button until every
  // option is selected / filled. Results are only produced on a valid submit.
  const watched = form.watch();
  const isFilled = (v: unknown) =>
    v !== "" && v !== null && v !== undefined && !Number.isNaN(v as number);
  const allRequiredFilled =
    isFilled(watched.batting_team) &&
    isFilled(watched.bowling_team) &&
    isFilled(watched.venue) &&
    isFilled(watched.batter_name) &&
    isFilled(watched.bowler_name) &&
    isFilled(watched.season) &&
    isFilled(watched.current_over) &&
    isFilled(watched.current_ball) &&
    isFilled(watched.current_score) &&
    isFilled(watched.current_wickets) &&
    (Number(watched.innings) !== 2 || isFilled(watched.target));

  // Helper for numeric inputs: keep empty as "" (unfilled) instead of coercing
  // an empty string to 0, so the field stays required until a value is typed.
  const numberChange =
    (onChange: (v: number | string) => void) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const raw = e.target.value;
      onChange(raw === "" ? "" : Number(raw));
    };

  function handleFormSubmit(data: MatchStateFormData) {
    // Cross-field validation (moved from Zod .refine() for RHF compatibility)
    if (data.batting_team === data.bowling_team) {
      form.setError("bowling_team", {
        message: "Batting and bowling teams must be different",
      });
      return;
    }
    if (data.innings === 2 && data.target <= 0) {
      form.setError("target", {
        message: "Target must be > 0 for 2nd innings",
      });
      return;
    }
    onSubmit(data);
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleFormSubmit)} className="space-y-5">
        {/* Teams */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormField
            control={form.control}
            name="batting_team"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Batting Team</FormLabel>
                <Select onValueChange={field.onChange} value={field.value}>
                  <FormControl>
                    <SelectTrigger className="bg-white/5 border-white/10">
                      <SelectValue placeholder="Select team" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {teamNames.map((t) => (
                      <SelectItem key={t} value={t}>
                        {t}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="bowling_team"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Bowling Team</FormLabel>
                <Select onValueChange={field.onChange} value={field.value}>
                  <FormControl>
                    <SelectTrigger className="bg-white/5 border-white/10">
                      <SelectValue placeholder="Select team" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {teamNames.map((t) => (
                      <SelectItem key={t} value={t}>
                        {t}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        {/* Venue */}
        <FormField
          control={form.control}
          name="venue"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Venue</FormLabel>
              <Select onValueChange={field.onChange} value={field.value}>
                <FormControl>
                  <SelectTrigger className="bg-white/5 border-white/10">
                    <SelectValue placeholder="Select venue" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="Unknown">Unknown</SelectItem>
                  {venueNames.map((v) => (
                    <SelectItem key={v} value={v}>
                      {v}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Match state grid */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <FormField
            control={form.control}
            name="innings"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Innings</FormLabel>
                <Select
                  onValueChange={(v) => field.onChange(Number(v))}
                  value={String(field.value)}
                >
                  <FormControl>
                    <SelectTrigger className="bg-white/5 border-white/10">
                      <SelectValue />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="1">1st</SelectItem>
                    <SelectItem value="2">2nd</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="current_over"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Over</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    min={0}
                    max={20}
                    placeholder="0"
                    className="bg-white/5 border-white/10"
                    {...field}
                    value={field.value ?? ""}
                    onChange={numberChange(field.onChange)}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="current_ball"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Ball</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    min={0}
                    max={6}
                    placeholder="0"
                    className="bg-white/5 border-white/10"
                    {...field}
                    value={field.value ?? ""}
                    onChange={numberChange(field.onChange)}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="current_score"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Score</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    min={0}
                    placeholder="0"
                    className="bg-white/5 border-white/10"
                    {...field}
                    value={field.value ?? ""}
                    onChange={numberChange(field.onChange)}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <FormField
            control={form.control}
            name="current_wickets"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Wickets</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    min={0}
                    max={10}
                    placeholder="0"
                    className="bg-white/5 border-white/10"
                    {...field}
                    value={field.value ?? ""}
                    onChange={numberChange(field.onChange)}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          {innings === 2 && (
            <FormField
              control={form.control}
              name="target"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Target</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      min={1}
                      placeholder="Enter target"
                      className="bg-white/5 border-white/10"
                      {...field}
                      value={field.value ?? ""}
                      onChange={numberChange(field.onChange)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          )}
          <FormField
            control={form.control}
            name="season"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Season</FormLabel>
                <FormControl>
                  <Input className="bg-white/5 border-white/10" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        {/* Players */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormField
            control={form.control}
            name="batter_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Batter</FormLabel>
                <Select onValueChange={field.onChange} value={field.value}>
                  <FormControl>
                    <SelectTrigger className="bg-white/5 border-white/10">
                      <SelectValue placeholder="Select batter" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="Unknown">Unknown</SelectItem>
                    {playerNames.map((p) => (
                      <SelectItem key={`bat-${p}`} value={p}>
                        {p}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="bowler_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Bowler</FormLabel>
                <Select onValueChange={field.onChange} value={field.value}>
                  <FormControl>
                    <SelectTrigger className="bg-white/5 border-white/10">
                      <SelectValue placeholder="Select bowler" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="Unknown">Unknown</SelectItem>
                    {playerNames.map((p) => (
                      <SelectItem key={`bowl-${p}`} value={p}>
                        {p}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        {/* Advanced rolling stats toggle */}
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-white"
        >
          {showAdvanced ? (
            <ChevronUp className="h-3.5 w-3.5" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
          Advanced Rolling Stats
          <span className="text-[10px] text-muted-foreground/60">
            (optional — defaults to 0 if unavailable)
          </span>
        </button>

        {showAdvanced && (
          <div className="space-y-3 rounded-lg border border-white/5 bg-white/[0.02] p-4">
            <div className="text-[11px] text-muted-foreground mb-3">
              Enter recent ball-by-ball statistics if available from live match
              data. Leave as 0 if not tracked.
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {(
                [
                  ["runs_last_6_balls", "Runs (6b)"],
                  ["runs_last_12_balls", "Runs (12b)"],
                  ["runs_last_18_balls", "Runs (18b)"],
                  ["runs_last_30_balls", "Runs (30b)"],
                  ["wickets_last_6_balls", "Wkts (6b)"],
                  ["wickets_last_12_balls", "Wkts (12b)"],
                  ["boundaries_last_6_balls", "Bdry (6b)"],
                  ["boundaries_last_12_balls", "Bdry (12b)"],
                  ["dot_balls_last_6_balls", "Dots (6b)"],
                  ["dot_balls_last_12_balls", "Dots (12b)"],
                ] as [keyof MatchStateFormData, string][]
              ).map(([name, label]) => (
                <FormField
                  key={name}
                  control={form.control}
                  name={name}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-[11px]">{label}</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min={0}
                          className="h-8 text-xs bg-white/5 border-white/10"
                          {...field}
                          value={field.value as number}
                          onChange={(e) =>
                            field.onChange(Number(e.target.value))
                          }
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
              ))}
            </div>
          </div>
        )}

        {!allRequiredFilled && (
          <p className="text-center text-[11px] text-muted-foreground">
            Select and fill in all match details to generate predictions.
          </p>
        )}
        <Button
          type="submit"
          disabled={isLoading || !allRequiredFilled}
          className="w-full bg-gradient-to-r from-emerald-500 to-emerald-600 text-emerald-950 font-semibold shadow-[0_0_20px_rgba(0,200,83,0.4)] hover:shadow-[0_0_30px_rgba(0,200,83,0.6)] transition-all disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Analyzing…
            </>
          ) : (
            <>
              <Zap className="mr-2 h-4 w-4" />
              {submitLabel}
            </>
          )}
        </Button>
      </form>
    </Form>
  );
}
