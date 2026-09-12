import pandas as pd
import numpy as np

class VenueStatsGenerator:
    @staticmethod
    def generate(matches_df: pd.DataFrame, bbb_df: pd.DataFrame) -> pd.DataFrame:
        matches_df['Venue'] = matches_df['Venue'].fillna('Unknown')
        venue_counts = matches_df.groupby('Venue').size().reset_index(name='Matches')
        
        city_mapping = matches_df.drop_duplicates(subset=['Venue'])[['Venue', 'City']]
        venue_stats = pd.merge(venue_counts, city_mapping, on='Venue', how='left')
        
        bbb_df['Total_Runs'] = pd.to_numeric(bbb_df['Total_Runs'], errors='coerce').fillna(0)
        bbb_df['Wicket'] = pd.to_numeric(bbb_df['Wicket'], errors='coerce').fillna(0)
        bbb_df['IsBoundary'] = np.where(pd.to_numeric(bbb_df['Runs_Batter'], errors='coerce') == 4, 1, 0)
        bbb_df['IsSix'] = np.where(pd.to_numeric(bbb_df['Runs_Batter'], errors='coerce') == 6, 1, 0)
        bbb_df['IsDotBall'] = np.where((pd.to_numeric(bbb_df['Runs_Batter'], errors='coerce') == 0) & (pd.to_numeric(bbb_df['Extras'], errors='coerce') == 0), 1, 0)
        
        # Ensure Innings is numeric so comparisons work correctly
        bbb_df['Innings'] = pd.to_numeric(bbb_df['Innings'], errors='coerce').fillna(1).astype(int)
        
        match_totals = bbb_df.groupby(['Match_ID', 'Innings']).agg(
            Total_Runs=('Total_Runs', 'sum'),
            Total_Wickets=('Wicket', 'sum'),
            Boundaries=('IsBoundary', 'sum'),
            Sixes=('IsSix', 'sum'),
            Dot_Balls=('IsDotBall', 'sum')
        ).reset_index()
        
        in1 = match_totals[match_totals['Innings'] == 1].copy()
        in2 = match_totals[match_totals['Innings'] == 2].copy()
        
        in1 = pd.merge(in1, matches_df[['Match_ID', 'Venue', 'Winner']], on='Match_ID', how='inner')
        in2 = pd.merge(in2, matches_df[['Match_ID', 'Venue', 'Winner']], on='Match_ID', how='inner')
        
        v_in1 = in1.groupby('Venue').agg(
            Average_First_Innings=('Total_Runs', 'mean'),
            Highest_Total=('Total_Runs', 'max'),
            Lowest_Total=('Total_Runs', 'min')
        ).reset_index()
        
        v_in2 = in2.groupby('Venue').agg(
            Average_Second_Innings=('Total_Runs', 'mean')
        ).reset_index()
        
        all_in = pd.merge(match_totals, matches_df[['Match_ID', 'Venue']], on='Match_ID', how='inner')
        v_overall = all_in.groupby('Venue').agg(
            Total_Match_Runs=('Total_Runs', 'sum'),
            Total_Match_Wickets=('Total_Wickets', 'sum'),
            Total_Boundaries=('Boundaries', 'sum'),
            Total_Sixes=('Sixes', 'sum'),
            Total_Dot_Balls=('Dot_Balls', 'sum')
        ).reset_index()
        
        first_bat = bbb_df[bbb_df['Innings'] == '1'][['Match_ID', 'Batting_Team']].drop_duplicates()
        first_bat = pd.merge(first_bat, matches_df[['Match_ID', 'Venue', 'Winner']], on='Match_ID', how='inner')
        
        first_bat['Bat_First_Win'] = np.where(first_bat['Batting_Team'] == first_bat['Winner'], 1, 0)
        first_bat['Chasing_Win'] = np.where((first_bat['Batting_Team'] != first_bat['Winner']) & (first_bat['Winner'] != '') & (first_bat['Winner'] != 'Tie') & (first_bat['Winner'] != 'No Result'), 1, 0)
        
        v_wins = first_bat.groupby('Venue').agg(
            Bat_First_Wins=('Bat_First_Win', 'sum'),
            Chasing_Wins=('Chasing_Win', 'sum')
        ).reset_index()
        
        bbb_df['Over'] = pd.to_numeric(bbb_df['Over'], errors='coerce').fillna(0)
        bbb_df['Phase'] = pd.cut(bbb_df['Over'], bins=[-1, 5, 14, 20], labels=['Powerplay', 'Middle', 'Death'])
        
        phase_runs = bbb_df.groupby(['Match_ID', 'Phase']).agg(Runs=('Total_Runs', 'sum')).reset_index()
        phase_runs = pd.merge(phase_runs, matches_df[['Match_ID', 'Venue']], on='Match_ID', how='inner')
        
        v_phases = phase_runs.groupby(['Venue', 'Phase']).agg(Total_Phase_Runs=('Runs', 'sum')).reset_index()
        
        pp = v_phases[v_phases['Phase'] == 'Powerplay'].rename(columns={'Total_Phase_Runs': 'PP_Runs'})
        mo = v_phases[v_phases['Phase'] == 'Middle'].rename(columns={'Total_Phase_Runs': 'MO_Runs'})
        do = v_phases[v_phases['Phase'] == 'Death'].rename(columns={'Total_Phase_Runs': 'DO_Runs'})
        
        v_phases_pivot = pd.merge(pp[['Venue', 'PP_Runs']], mo[['Venue', 'MO_Runs']], on='Venue', how='outer')
        v_phases_pivot = pd.merge(v_phases_pivot, do[['Venue', 'DO_Runs']], on='Venue', how='outer').fillna(0)
        
        venue_stats = pd.merge(venue_stats, v_in1, on='Venue', how='left').fillna(0)
        venue_stats = pd.merge(venue_stats, v_in2, on='Venue', how='left').fillna(0)
        venue_stats = pd.merge(venue_stats, v_overall, on='Venue', how='left').fillna(0)
        venue_stats = pd.merge(venue_stats, v_wins, on='Venue', how='left').fillna(0)
        venue_stats = pd.merge(venue_stats, v_phases_pivot, on='Venue', how='left').fillna(0)
        
        venue_stats['Bat_First_Win_Percentage'] = np.where(venue_stats['Matches'] > 0, (venue_stats['Bat_First_Wins'] / venue_stats['Matches']) * 100, 0)
        venue_stats['Chasing_Win_Percentage'] = np.where(venue_stats['Matches'] > 0, (venue_stats['Chasing_Wins'] / venue_stats['Matches']) * 100, 0)
        
        venue_stats['Average_Wickets'] = np.where(venue_stats['Matches'] > 0, venue_stats['Total_Match_Wickets'] / venue_stats['Matches'], 0)
        venue_stats['Average_Boundaries'] = np.where(venue_stats['Matches'] > 0, venue_stats['Total_Boundaries'] / venue_stats['Matches'], 0)
        venue_stats['Average_Sixes'] = np.where(venue_stats['Matches'] > 0, venue_stats['Total_Sixes'] / venue_stats['Matches'], 0)
        venue_stats['Average_Dot_Balls'] = np.where(venue_stats['Matches'] > 0, venue_stats['Total_Dot_Balls'] / venue_stats['Matches'], 0)
        
        venue_stats['Powerplay_Average'] = venue_stats['PP_Runs'] / (venue_stats['Matches'] * 2)
        venue_stats['Middle_Overs_Average'] = venue_stats['MO_Runs'] / (venue_stats['Matches'] * 2)
        venue_stats['Death_Overs_Average'] = venue_stats['DO_Runs'] / (venue_stats['Matches'] * 2)
        
        bbb_df['Wide'] = pd.to_numeric(bbb_df['Wide'], errors='coerce').fillna(0)
        legal_balls = bbb_df[bbb_df['Wide'] == 0]
        v_balls = pd.merge(legal_balls, matches_df[['Match_ID', 'Venue']], on='Match_ID', how='inner')
        v_balls_cnt = v_balls.groupby('Venue').size().reset_index(name='Total_Balls')
        
        venue_stats = pd.merge(venue_stats, v_balls_cnt, on='Venue', how='left').fillna(0)
        venue_stats['Average_Run_Rate'] = np.where(venue_stats['Total_Balls'] > 0, (venue_stats['Total_Match_Runs'] / (venue_stats['Total_Balls'] / 6)), 0)
        
        venue_stats['Average_Wickets_Per_Match'] = venue_stats['Average_Wickets']
        
        # ── Spin vs Pace economy per venue ───────────────────────────────────────
        # Identify spin bowlers by common bowling-type convention.
        # If a Bowling_Type column exists, use it; otherwise classify by wicket patterns
        # (spin bowlers typically have slower balls and specific dismissal types).
        # Fallback: use the Bowler name to look up type from bbb_df if available.
        if 'Bowling_Type' in bbb_df.columns:
            bbb_df['Bowling_Type'] = bbb_df['Bowling_Type'].fillna('Unknown')
            spin_mask = bbb_df['Bowling_Type'].str.contains('spin|off|leg|slow', case=False, na=False)
            pace_mask = ~spin_mask
        else:
            # Heuristic: no bowling type info → treat all deliveries equally, both stay 0
            spin_mask = pd.Series(False, index=bbb_df.index)
            pace_mask = pd.Series(False, index=bbb_df.index)

        bbb_df['Runs_Conceded'] = pd.to_numeric(
            bbb_df.get('Runs_Conceded', bbb_df['Total_Runs']), errors='coerce'
        ).fillna(0)

        def _economy_by_venue(mask: pd.Series) -> pd.Series:
            sub = bbb_df[mask & (pd.to_numeric(bbb_df.get('Wide', 0), errors='coerce').fillna(0) == 0)]
            sub_venue = pd.merge(sub, matches_df[['Match_ID', 'Venue']], on='Match_ID', how='inner')
            agg = sub_venue.groupby('Venue').agg(
                _rc=('Runs_Conceded', 'sum'),
                _balls=('Match_ID', 'count')
            )
            agg['_overs'] = agg['_balls'] / 6
            agg['_econ'] = np.where(agg['_overs'] > 0, agg['_rc'] / agg['_overs'], 0.0)
            return agg['_econ']

        spin_econ = _economy_by_venue(spin_mask)
        pace_econ = _economy_by_venue(pace_mask)

        venue_stats = venue_stats.set_index('Venue')
        venue_stats['Spin_Economy'] = spin_econ.reindex(venue_stats.index).fillna(0.0).round(2)
        venue_stats['Pace_Economy'] = pace_econ.reindex(venue_stats.index).fillna(0.0).round(2)
        venue_stats = venue_stats.reset_index()
        
        keep_cols = [
            'Venue', 'City', 'Matches', 'Average_First_Innings', 'Average_Second_Innings', 
            'Highest_Total', 'Lowest_Total', 'Average_Wickets', 'Average_Boundaries', 
            'Average_Sixes', 'Average_Dot_Balls', 'Bat_First_Wins', 'Chasing_Wins', 
            'Bat_First_Win_Percentage', 'Chasing_Win_Percentage', 'Powerplay_Average', 
            'Middle_Overs_Average', 'Death_Overs_Average', 'Average_Run_Rate', 
            'Average_Wickets_Per_Match', 'Spin_Economy', 'Pace_Economy'
        ]
        
        venue_stats = venue_stats[keep_cols]
        
        float_cols = ['Average_First_Innings', 'Average_Second_Innings', 'Average_Wickets', 'Average_Boundaries', 
                      'Average_Sixes', 'Average_Dot_Balls', 'Bat_First_Win_Percentage', 'Chasing_Win_Percentage', 
                      'Powerplay_Average', 'Middle_Overs_Average', 'Death_Overs_Average', 'Average_Run_Rate', 
                      'Average_Wickets_Per_Match']
        for col in float_cols:
            venue_stats[col] = venue_stats[col].round(2)
            
        int_cols = ['Matches', 'Highest_Total', 'Lowest_Total', 'Bat_First_Wins', 'Chasing_Wins']
        for col in int_cols:
            venue_stats[col] = venue_stats[col].astype(int)
            
        return venue_stats
