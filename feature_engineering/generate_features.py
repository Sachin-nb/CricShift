import pandas as pd
import numpy as np
import logging
from feature_utils import calculate_rolling_features, calculate_momentum_scores, calculate_partnership_features

class FeatureGenerator:
    def __init__(self, matches_df, bbb_df, player_stats, team_stats, venue_stats):
        self.matches_df = matches_df
        self.bbb_df = bbb_df
        self.player_stats = player_stats
        self.team_stats = team_stats
        self.venue_stats = venue_stats
        
    def generate(self) -> pd.DataFrame:
        logging.info("Starting feature generation...")
        
        # 1. Base DataFrame
        df = self.bbb_df.copy()
        
        # Merge basic match info
        match_info = self.matches_df[['Match_ID', 'Venue', 'Winner']].copy()
        df = pd.merge(df, match_info, on='Match_ID', how='left')
        
        # Numeric conversions
        df['Over'] = pd.to_numeric(df['Over'], errors='coerce').fillna(0)
        df['Ball'] = pd.to_numeric(df['Ball'], errors='coerce').fillna(0)
        df['Current_Score'] = pd.to_numeric(df['Current_Score'], errors='coerce').fillna(0)
        df['Current_Wickets'] = pd.to_numeric(df['Current_Wickets'], errors='coerce').fillna(0)
        df['Total_Runs'] = pd.to_numeric(df['Total_Runs'], errors='coerce').fillna(0)
        df['Wicket'] = pd.to_numeric(df['Wicket'], errors='coerce').fillna(0)
        df['IsBoundary'] = pd.to_numeric(df['IsBoundary'], errors='coerce').fillna(0)
        df['IsDotBall'] = pd.to_numeric(df['IsDotBall'], errors='coerce').fillna(0)
        
        # Match Context Features
        df['Current_Over'] = df['Over']
        df['Current_Ball'] = df['Ball']
        
        # Max overs is usually 20, unless specified. We assume 20.
        df['Balls_Bowled'] = (df['Current_Over'] * 6) + df['Current_Ball']
        df['Balls_Remaining'] = np.maximum(0, 120 - df['Balls_Bowled'])
        df['Overs_Remaining'] = df['Balls_Remaining'] / 6
        
        df['Current_Run_Rate'] = np.where(df['Balls_Bowled'] > 0, (df['Current_Score'] / df['Balls_Bowled']) * 6, 0)
        
        # Target & Required Run Rate (only for Innings 2)
        in1_totals = df[df['Innings'] == '1'].groupby('Match_ID')['Current_Score'].max().reset_index(name='Innings1_Total')
        df = pd.merge(df, in1_totals, on='Match_ID', how='left')
        
        df['Target'] = np.where(df['Innings'] == '2', df['Innings1_Total'] + 1, 0)
        df['Runs_Remaining'] = np.where(df['Innings'] == '2', np.maximum(0, df['Target'] - df['Current_Score']), 0)
        
        df['Required_Run_Rate'] = np.where((df['Innings'] == '2') & (df['Balls_Remaining'] > 0), 
                                           (df['Runs_Remaining'] / df['Balls_Remaining']) * 6, 0)
                                           
        df['Required_Run_Rate_Gap'] = np.where(df['Innings'] == '2', df['Required_Run_Rate'] - df['Current_Run_Rate'], 0)
        
        # 2. Match Phase Features
        df['Powerplay_Flag'] = np.where(df['Current_Over'] < 6, 1, 0)
        df['Middle_Overs_Flag'] = np.where((df['Current_Over'] >= 6) & (df['Current_Over'] < 15), 1, 0)
        df['Death_Overs_Flag'] = np.where(df['Current_Over'] >= 15, 1, 0)
        df['Pressure_Overs_Flag'] = np.where(df['Overs_Remaining'] <= 3, 1, 0)
        
        # 3. Rolling & Momentum Features
        df = calculate_rolling_features(df)
        df = calculate_momentum_scores(df)
        df = calculate_partnership_features(df)
        
        # Pressure Index (now that RRR is calculated)
        df['Pressure_Index'] = df['Required_Run_Rate'] + (df['Wickets_Last_6_Balls'] * 2) + (df['Dot_Ball_Pressure'] / 10)
        df['Pressure_Index'] = df['Pressure_Index'].fillna(0)
        
        # 4. Batter Features
        batter_cols = {
            'Player_Name': 'Batter',
            'Average': 'Batter_Career_Average',
            'Strike_Rate': 'Batter_Career_Strike_Rate',
            'Boundary_Percentage': 'Batter_Boundary_Percentage',
            'Batting_Impact_Score': 'Batting_Impact_Score'
        }
        bat_df = self.player_stats[['Player_Name', 'Average', 'Strike_Rate', 'Boundary_Percentage', 'Batting_Impact_Score']].rename(columns=batter_cols)
        df = pd.merge(df, bat_df, on='Batter', how='left').fillna(0)
        df['Batter_Name'] = df['Batter']
        df['Batter_Recent_Form'] = df['Batter_Career_Average']  # Proxy for recent form
        
        # 5. Bowler Features
        bowler_cols = {
            'Player_Name': 'Bowler',
            'Economy': 'Bowler_Economy',
            'Bowling_Strike_Rate': 'Bowler_Strike_Rate',
            'Dot_Balls_Bowled': 'Bowler_Dot_Balls',
            'Balls_Bowled': 'Career_Balls_Bowled',
            'Bowling_Impact_Score': 'Bowling_Impact_Score'
        }
        bowl_df = self.player_stats[['Player_Name', 'Economy', 'Bowling_Strike_Rate', 'Dot_Balls_Bowled', 'Balls_Bowled', 'Bowling_Impact_Score']].rename(columns=bowler_cols)
        df = pd.merge(df, bowl_df, on='Bowler', how='left').fillna(0)
        df['Bowler_Name'] = df['Bowler']
        df['Bowler_Wicket_Rate'] = np.where(df['Bowler_Strike_Rate'] > 0, 1 / df['Bowler_Strike_Rate'], 0)
        df['Bowler_Dot_Ball_Percentage'] = np.where(df['Career_Balls_Bowled'] > 0, (df['Bowler_Dot_Balls'] / df['Career_Balls_Bowled']) * 100, 0)
        df['Bowler_Recent_Form'] = df['Bowler_Economy']  # Proxy
        
        # 6. Team Features
        team_cols = {
            'Team': 'Batting_Team',
            'Win_Percentage': 'Team_Win_Percentage',
            'Bat_First_Win_Percentage': 'Bat_First_Strength',
            'Chasing_Win_Percentage': 'Chase_Strength'
        }
        t_df = self.team_stats[['Team', 'Win_Percentage', 'Bat_First_Win_Percentage', 'Chasing_Win_Percentage']].rename(columns=team_cols)
        df = pd.merge(df, t_df, on='Batting_Team', how='left').fillna(0)
        df['Team_Form_Last_5_Matches'] = df['Team_Win_Percentage']  # Proxy
        
        # 7. Venue Features
        venue_cols = {
            'Venue': 'Venue',
            'Average_Run_Rate': 'Venue_Run_Rate',
            'Average_First_Innings': 'Venue_Average_Score',
            'Chasing_Win_Percentage': 'Venue_Chasing_Success'
        }
        v_df = self.venue_stats[['Venue', 'Average_Run_Rate', 'Average_First_Innings', 'Chasing_Win_Percentage']].rename(columns=venue_cols)
        df = pd.merge(df, v_df, on='Venue', how='left').fillna(0)
        # Difficulty Index: 10 - Run Rate (simplistic)
        df['Venue_Difficulty_Index'] = np.maximum(0, 10 - df['Venue_Run_Rate'])
        
        # 8. Target Labels
        # Momentum Shift Label: 1 if momentum changed drastically (simple heuristic: score > 15 & wicket = 0, or wickets > 2 in 12 balls)
        df['Momentum_Shift_Label'] = np.where((df['Runs_Last_12_Balls'] > 20) | (df['Wickets_Last_12_Balls'] >= 2), 1, 0)
        
        # Match Winner Label: 1 if Batting Team wins, 0 otherwise
        df['Match_Winner_Label'] = np.where(df['Winner'] == df['Batting_Team'], 1, 0)
        
        # Win Probability Label: For training regressors, can just use Match_Winner_Label as 1.0 or 0.0
        df['Win_Probability_Label'] = df['Match_Winner_Label'].astype(float)
        
        # Select final columns
        final_cols = [
            'Match_ID', 'Season', 'Venue', 'Batting_Team', 'Bowling_Team', 'Innings', 
            'Current_Over', 'Current_Ball', 'Current_Score', 'Current_Wickets', 
            'Balls_Remaining', 'Overs_Remaining', 'Runs_Remaining', 'Target', 
            'Current_Run_Rate', 'Required_Run_Rate', 'Required_Run_Rate_Gap',
            'Runs_Last_6_Balls', 'Runs_Last_12_Balls', 'Runs_Last_18_Balls', 'Runs_Last_30_Balls',
            'Wickets_Last_6_Balls', 'Wickets_Last_12_Balls', 'Boundaries_Last_6_Balls', 
            'Boundaries_Last_12_Balls', 'Dot_Balls_Last_6_Balls', 'Dot_Balls_Last_12_Balls',
            'Momentum_Score', 'Boundary_Momentum', 'Dot_Ball_Pressure', 'Pressure_Index',
            'Current_Partnership_Runs', 'Current_Partnership_Balls', 'Current_Partnership_Run_Rate',
            'Batter_Name', 'Batter_Career_Average', 'Batter_Career_Strike_Rate', 'Batter_Recent_Form', 
            'Batter_Boundary_Percentage', 'Batting_Impact_Score',
            'Bowler_Name', 'Bowler_Economy', 'Bowler_Strike_Rate', 'Bowler_Wicket_Rate', 
            'Bowler_Recent_Form', 'Bowler_Dot_Ball_Percentage', 'Bowling_Impact_Score',
            'Team_Win_Percentage', 'Bat_First_Strength', 'Chase_Strength', 'Team_Form_Last_5_Matches',
            'Venue_Run_Rate', 'Venue_Average_Score', 'Venue_Chasing_Success', 'Venue_Difficulty_Index',
            'Powerplay_Flag', 'Middle_Overs_Flag', 'Death_Overs_Flag', 'Pressure_Overs_Flag',
            'Momentum_Shift_Label', 'Match_Winner_Label', 'Win_Probability_Label'
        ]
        
        df = df[final_cols]
        
        # Fix NaNs resulting from divisions
        df.replace([np.inf, -np.inf], 0, inplace=True)
        df.fillna(0, inplace=True)
        
        logging.info(f"Feature generation complete. Dataset shape: {df.shape}")
        return df
