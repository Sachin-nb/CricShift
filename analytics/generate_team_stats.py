import pandas as pd
import numpy as np

class TeamStatsGenerator:
    @staticmethod
    def generate(matches_df: pd.DataFrame, bbb_df: pd.DataFrame) -> pd.DataFrame:
        teams = set(matches_df['Team1'].dropna().unique()).union(set(matches_df['Team2'].dropna().unique()))
        teams = {t for t in teams if t}
        
        team_stats_list = []
        
        bbb_df['Total_Runs'] = pd.to_numeric(bbb_df['Total_Runs'], errors='coerce').fillna(0)
        bbb_df['Wicket'] = pd.to_numeric(bbb_df['Wicket'], errors='coerce').fillna(0)
        bbb_df['Runs_Batter'] = pd.to_numeric(bbb_df['Runs_Batter'], errors='coerce').fillna(0)
        bbb_df['Extras'] = pd.to_numeric(bbb_df['Extras'], errors='coerce').fillna(0)
        bbb_df['Wide'] = pd.to_numeric(bbb_df['Wide'], errors='coerce').fillna(0)
        bbb_df['NoBall'] = pd.to_numeric(bbb_df['NoBall'], errors='coerce').fillna(0)
        
        bbb_df['IsBoundary'] = np.where((bbb_df['Runs_Batter'] == 4) | (bbb_df['Runs_Batter'] == 6), 1, 0)
        bbb_df['IsDotBall'] = np.where((bbb_df['Runs_Batter'] == 0) & (bbb_df['Extras'] == 0), 1, 0)
        
        bbb_df['Is_Legal_Ball'] = np.where((bbb_df['Wide'] == 0) & (bbb_df['NoBall'] == 0), 1, 0)
        bbb_df['Over'] = pd.to_numeric(bbb_df['Over'], errors='coerce').fillna(0)
        # Ensure Innings is numeric so comparisons like == 1 work correctly
        bbb_df['Innings'] = pd.to_numeric(bbb_df['Innings'], errors='coerce').fillna(1).astype(int)
        bbb_df['Phase'] = pd.cut(bbb_df['Over'], bins=[-1, 5, 14, 20], labels=['Powerplay', 'Middle', 'Death'])
        
        for team in teams:
            team_matches = matches_df[(matches_df['Team1'] == team) | (matches_df['Team2'] == team)]
            matches_played = len(team_matches)
            
            wins = len(team_matches[team_matches['Winner'] == team])
            losses = len(team_matches[(team_matches['Winner'] != team) & (team_matches['Winner'] != '') & (team_matches['Winner'] != 'Tie') & (team_matches['Winner'] != 'No Result')])
            win_pct = (wins / matches_played) * 100 if matches_played > 0 else 0
            
            team_batting = bbb_df[bbb_df['Batting_Team'] == team]
            total_innings = len(team_batting['Match_ID'].unique())
            
            in1 = team_batting[team_batting['Innings'] == 1]
            in2 = team_batting[team_batting['Innings'] == 2]
            
            in1_totals = in1.groupby('Match_ID')['Total_Runs'].sum()
            in2_totals = in2.groupby('Match_ID')['Total_Runs'].sum()
            all_totals = team_batting.groupby(['Match_ID', 'Innings'])['Total_Runs'].sum()
            
            avg_first = in1_totals.mean() if not in1_totals.empty else 0
            avg_chase = in2_totals.mean() if not in2_totals.empty else 0
            avg_total = all_totals.mean() if not all_totals.empty else 0
            
            high_total = all_totals.max() if not all_totals.empty else 0
            low_total = all_totals.min() if not all_totals.empty else 0
            
            total_legal_balls = team_batting['Is_Legal_Ball'].sum()
            avg_rr = (team_batting['Total_Runs'].sum() / (total_legal_balls / 6)) if total_legal_balls > 0 else 0
            
            avg_wkts_lost = team_batting['Wicket'].sum() / total_innings if total_innings > 0 else 0
            
            pp_runs = team_batting[team_batting['Phase'] == 'Powerplay']['Total_Runs'].sum()
            mo_runs = team_batting[team_batting['Phase'] == 'Middle']['Total_Runs'].sum()
            do_runs = team_batting[team_batting['Phase'] == 'Death']['Total_Runs'].sum()
            
            pp_legal_balls = team_batting[(team_batting['Phase'] == 'Powerplay') & (team_batting['Is_Legal_Ball'] == 1)].shape[0]
            do_legal_balls = team_batting[(team_batting['Phase'] == 'Death') & (team_batting['Is_Legal_Ball'] == 1)].shape[0]
            
            pp_rr = (pp_runs / (pp_legal_balls / 6)) if pp_legal_balls > 0 else 0
            do_rr = (do_runs / (do_legal_balls / 6)) if do_legal_balls > 0 else 0
            
            total_runs = team_batting['Total_Runs'].sum()
            total_balls = len(team_batting)
            boundary_runs = team_batting[team_batting['IsBoundary'] == 1]['Runs_Batter'].sum()
            boundary_pct = (boundary_runs / total_runs) * 100 if total_runs > 0 else 0
            
            dot_balls = team_batting['IsDotBall'].sum()
            dot_pct = (dot_balls / total_balls) * 100 if total_balls > 0 else 0
            
            bat_first_matches = pd.merge(in1[['Match_ID']].drop_duplicates(), matches_df, on='Match_ID', how='inner')
            bat_first_wins = len(bat_first_matches[bat_first_matches['Winner'] == team])
            bf_pct = (bat_first_wins / len(bat_first_matches)) * 100 if len(bat_first_matches) > 0 else 0
            
            chase_matches = pd.merge(in2[['Match_ID']].drop_duplicates(), matches_df, on='Match_ID', how='inner')
            chase_wins = len(chase_matches[chase_matches['Winner'] == team])
            ch_pct = (chase_wins / len(chase_matches)) * 100 if len(chase_matches) > 0 else 0
            
            team_stats_list.append({
                'Team': team,
                'Matches': matches_played,
                'Wins': wins,
                'Losses': losses,
                'Win_Percentage': win_pct,
                'Average_First_Innings': avg_first,
                'Average_Chase': avg_chase,
                'Average_Total': avg_total,
                'Highest_Total': high_total,
                'Lowest_Total': low_total,
                'Average_Run_Rate': avg_rr,
                'Average_Wickets_Lost': avg_wkts_lost,
                'Powerplay_Runs': pp_runs / total_innings if total_innings > 0 else 0,
                'Middle_Overs_Runs': mo_runs / total_innings if total_innings > 0 else 0,
                'Death_Overs_Runs': do_runs / total_innings if total_innings > 0 else 0,
                'Powerplay_Run_Rate': pp_rr,
                'Death_Run_Rate': do_rr,
                'Boundary_Percentage': boundary_pct,
                'Dot_Ball_Percentage': dot_pct,
                'Bat_First_Win_Percentage': bf_pct,
                'Chasing_Win_Percentage': ch_pct
            })
            
        df = pd.DataFrame(team_stats_list)
        
        float_cols = ['Win_Percentage', 'Average_First_Innings', 'Average_Chase', 'Average_Total',
                      'Average_Run_Rate', 'Average_Wickets_Lost', 'Powerplay_Runs', 'Middle_Overs_Runs',
                      'Death_Overs_Runs', 'Powerplay_Run_Rate', 'Death_Run_Rate', 'Boundary_Percentage',
                      'Dot_Ball_Percentage', 'Bat_First_Win_Percentage', 'Chasing_Win_Percentage']
                      
        for col in float_cols:
            df[col] = df[col].round(2)
            
        int_cols = ['Matches', 'Wins', 'Losses', 'Highest_Total', 'Lowest_Total']
        for col in int_cols:
            df[col] = df[col].fillna(0).astype(int)
            
        return df
