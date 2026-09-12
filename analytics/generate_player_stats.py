import pandas as pd
import numpy as np

class PlayerStatsGenerator:
    @staticmethod
    def generate(matches_df: pd.DataFrame, bbb_df: pd.DataFrame) -> pd.DataFrame:
        numeric_cols = ['Runs_Batter', 'Extras', 'Wide', 'NoBall', 'Bye', 'LegBye', 'Penalty', 'Total_Runs', 'Wicket']
        for col in numeric_cols:
            bbb_df[col] = pd.to_numeric(bbb_df[col], errors='coerce').fillna(0)
            
        bbb_df['IsBoundary'] = bbb_df['Runs_Batter'].apply(lambda x: 1 if x == 4 else 0)
        bbb_df['IsSix'] = bbb_df['Runs_Batter'].apply(lambda x: 1 if x == 6 else 0)
        bbb_df['IsDotBall'] = np.where((bbb_df['Runs_Batter'] == 0) & (bbb_df['Extras'] == 0), 1, 0)

        balls_faced_df = bbb_df[bbb_df['Wide'] == 0]
        
        bat_agg = bbb_df.groupby('Batter').agg(
            Runs=('Runs_Batter', 'sum'),
            Fours=('IsBoundary', 'sum'),
            Sixes=('IsSix', 'sum'),
            Singles=('Runs_Batter', lambda x: (x == 1).sum()),
            Doubles=('Runs_Batter', lambda x: (x == 2).sum()),
            Triples=('Runs_Batter', lambda x: (x == 3).sum())
        ).reset_index()
        
        balls_faced_agg = balls_faced_df.groupby('Batter').agg(
            Balls_Faced=('Match_ID', 'count'),
            Dot_Balls=('IsDotBall', 'sum')
        ).reset_index()
        
        match_bat_agg = bbb_df.groupby(['Match_ID', 'Batter']).agg(
            Match_Runs=('Runs_Batter', 'sum')
        ).reset_index()
        
        dismissals_df = bbb_df[bbb_df['Player_Out'] != ''].copy()
        out_counts = dismissals_df.groupby('Player_Out').size().reset_index(name='Dismissals')
        out_counts.rename(columns={'Player_Out': 'Batter'}, inplace=True)
        
        hs_df = match_bat_agg.groupby('Batter').agg(
            Highest_Score=('Match_Runs', 'max'),
            Innings_Batted=('Match_ID', 'count')
        ).reset_index()
        
        match_bat_agg['Is_50'] = np.where((match_bat_agg['Match_Runs'] >= 50) & (match_bat_agg['Match_Runs'] < 100), 1, 0)
        match_bat_agg['Is_100'] = np.where(match_bat_agg['Match_Runs'] >= 100, 1, 0)
        match_bat_agg['Is_Duck'] = np.where(match_bat_agg['Match_Runs'] == 0, 1, 0)
        
        milestones = match_bat_agg.groupby('Batter').agg(
            Fifties=('Is_50', 'sum'),
            Hundreds=('Is_100', 'sum'),
            Ducks=('Is_Duck', 'sum')
        ).reset_index()
        
        batting = pd.merge(bat_agg, balls_faced_agg, on='Batter', how='outer').fillna(0)
        batting = pd.merge(batting, hs_df, on='Batter', how='outer').fillna(0)
        batting = pd.merge(batting, out_counts, on='Batter', how='outer').fillna(0)
        batting = pd.merge(batting, milestones, on='Batter', how='outer').fillna(0)
        
        batting.rename(columns={'Batter': 'Player_Name', 'Fifties': '50s', 'Hundreds': '100s'}, inplace=True)
        batting['Not_Outs'] = batting['Innings_Batted'] - batting['Dismissals']
        batting['Not_Outs'] = batting['Not_Outs'].clip(lower=0)
        
        batting['Average'] = np.where(batting['Dismissals'] > 0, batting['Runs'] / batting['Dismissals'], batting['Runs'])
        batting['Strike_Rate'] = np.where(batting['Balls_Faced'] > 0, (batting['Runs'] / batting['Balls_Faced']) * 100, 0)
        batting['Boundaries'] = batting['Fours'] + batting['Sixes']
        batting['Boundary_Percentage'] = np.where(batting['Runs'] > 0, ((batting['Fours']*4 + batting['Sixes']*6) / batting['Runs']) * 100, 0)
                                                 
        bbb_df['Runs_Conceded'] = bbb_df['Total_Runs'] - bbb_df['Bye'] - bbb_df['LegBye']
        bbb_df['Is_Legal_Ball'] = np.where((bbb_df['Wide'] == 0) & (bbb_df['NoBall'] == 0), 1, 0)
        
        excluded_dismissals = ['run out', 'retired hurt', 'retired out', 'obstructing the field', 'retired not out']
        bbb_df['Bowler_Wicket'] = np.where((bbb_df['Wicket'] == 1) & (~bbb_df['Dismissal_Type'].str.lower().isin(excluded_dismissals)), 1, 0)
        
        over_runs = bbb_df.groupby(['Match_ID', 'Innings', 'Over', 'Bowler']).agg(
            Runs_In_Over=('Runs_Conceded', 'sum'),
            Legal_Balls=('Is_Legal_Ball', 'sum')
        ).reset_index()
        over_runs['Is_Maiden'] = np.where((over_runs['Runs_In_Over'] == 0) & (over_runs['Legal_Balls'] >= 6), 1, 0)
        maidens_df = over_runs.groupby('Bowler').agg(Maidens=('Is_Maiden', 'sum')).reset_index()
        
        bowl_agg = bbb_df.groupby('Bowler').agg(
            Balls_Bowled=('Is_Legal_Ball', 'sum'),
            Runs_Conceded=('Runs_Conceded', 'sum'),
            Wickets=('Bowler_Wicket', 'sum'),
            Dot_Balls_Bowled=('IsDotBall', 'sum'),
            Fours_Conceded=('IsBoundary', 'sum'),
            Sixes_Conceded=('IsSix', 'sum')
        ).reset_index()
        
        bowling = pd.merge(bowl_agg, maidens_df, on='Bowler', how='outer').fillna(0)
        bowling.rename(columns={'Bowler': 'Player_Name'}, inplace=True)
        
        bowling['Overs_Bowled'] = bowling['Balls_Bowled'] / 6
        bowling['Economy'] = np.where(bowling['Overs_Bowled'] > 0, bowling['Runs_Conceded'] / bowling['Overs_Bowled'], 0)
        bowling['Bowling_Average'] = np.where(bowling['Wickets'] > 0, bowling['Runs_Conceded'] / bowling['Wickets'], 0)
        bowling['Bowling_Strike_Rate'] = np.where(bowling['Wickets'] > 0, bowling['Balls_Bowled'] / bowling['Wickets'], 0)

        fielding_df = bbb_df[bbb_df['Fielder'] != ''].copy()
        fielding_expanded = fielding_df.assign(Fielder=fielding_df['Fielder'].astype(str).str.split(',')).explode('Fielder')
        fielding_expanded['Fielder'] = fielding_expanded['Fielder'].str.strip()
        
        catches = fielding_expanded[fielding_expanded['Dismissal_Type'] == 'caught'].groupby('Fielder').size().reset_index(name='Caught')
        run_outs = fielding_expanded[fielding_expanded['Dismissal_Type'] == 'run out'].groupby('Fielder').size().reset_index(name='Run_Out')
        stumpings = fielding_expanded[fielding_expanded['Dismissal_Type'] == 'stumped'].groupby('Fielder').size().reset_index(name='Stumping')
        
        fielding = pd.merge(catches, run_outs, on='Fielder', how='outer').fillna(0)
        fielding = pd.merge(fielding, stumpings, on='Fielder', how='outer').fillna(0)
        fielding.rename(columns={'Fielder': 'Player_Name'}, inplace=True)
        
        pom_counts = matches_df['Player_of_Match'].value_counts().reset_index()
        pom_counts.columns = ['Player_Name', 'Player_of_the_Match_Count']
        
        all_participants = pd.concat([
            bbb_df[['Match_ID', 'Batter']].rename(columns={'Batter': 'Player_Name'}),
            bbb_df[['Match_ID', 'Non_Striker']].rename(columns={'Non_Striker': 'Player_Name'}),
            bbb_df[['Match_ID', 'Bowler']].rename(columns={'Bowler': 'Player_Name'})
        ]).drop_duplicates()
        matches_played = all_participants.groupby('Player_Name').size().reset_index(name='Matches_Played')

        players = set(batting['Player_Name']).union(set(bowling['Player_Name'])).union(set(fielding['Player_Name'])).union(set(matches_played['Player_Name']))
        players = {p for p in players if p and p != ''}
        
        final_df = pd.DataFrame({'Player_Name': list(players)})
        final_df = pd.merge(final_df, matches_played, on='Player_Name', how='left').fillna(0)
        final_df = pd.merge(final_df, batting, on='Player_Name', how='left').fillna(0)
        final_df = pd.merge(final_df, bowling, on='Player_Name', how='left').fillna(0)
        final_df = pd.merge(final_df, fielding, on='Player_Name', how='left').fillna(0)
        final_df = pd.merge(final_df, pom_counts, on='Player_Name', how='left').fillna(0)
        
        # ── Batting Position — compute median position across all innings ──────────
        # We find the first delivery each batter faced in each innings and
        # rank batters by the order they came in to bat.
        first_ball = bbb_df[bbb_df['Wide'] == 0].copy()
        first_ball = first_ball.groupby(['Match_ID', 'Innings', 'Batter']).first().reset_index()
        # Sort by Match_ID, Innings, then ball number (index order = batting order)
        first_ball = first_ball.sort_values(['Match_ID', 'Innings'])
        first_ball['Position'] = first_ball.groupby(['Match_ID', 'Innings']).cumcount() + 1
        pos_agg = first_ball.groupby('Batter')['Position'].median().reset_index()
        pos_agg.rename(columns={'Batter': 'Player_Name', 'Position': 'Batting_Position'}, inplace=True)
        pos_agg['Batting_Position'] = pos_agg['Batting_Position'].round(0).astype(int).clip(lower=1, upper=11)
        
        final_df = pd.merge(final_df, pos_agg, on='Player_Name', how='left')
        # Players who never batted (pure bowlers) default to position 11
        if 'Batting_Position_x' in final_df.columns:
            # merge created _x/_y because we already had a column — use the computed one
            final_df['Batting_Position'] = final_df['Batting_Position_y'].fillna(11).astype(int)
            final_df.drop(columns=['Batting_Position_x', 'Batting_Position_y'], inplace=True)
        else:
            final_df['Batting_Position'] = final_df['Batting_Position'].fillna(11).astype(int)
        final_df['Batting_Impact_Score'] = ((final_df['Runs'] * 1.5) + (final_df['Strike_Rate'] * 0.5)).clip(lower=0)
        final_df['Bowling_Impact_Score'] = ((final_df['Wickets'] * 20) + (final_df['Dot_Balls_Bowled'] * 2) - (final_df['Economy'] * 10)).clip(lower=0)
        final_df['Overall_Impact_Score'] = (final_df['Batting_Impact_Score'] + final_df['Bowling_Impact_Score'] + (final_df['Caught']*5)).clip(lower=0)
        
        cols_to_int = ['Matches_Played', 'Innings_Batted', 'Runs', 'Balls_Faced', 'Highest_Score', 'Fours', 'Sixes', 
                       'Dot_Balls', 'Singles', 'Doubles', 'Triples', 'Boundaries', 'Dismissals', 'Not_Outs', 
                       'Batting_Position', '50s', '100s', 'Ducks', 'Balls_Bowled', 'Runs_Conceded', 'Wickets', 
                       'Maidens', 'Dot_Balls_Bowled', 'Fours_Conceded', 'Sixes_Conceded', 'Caught', 'Run_Out', 
                       'Stumping', 'Player_of_the_Match_Count']
        
        for col in cols_to_int:
            if col in final_df.columns:
                final_df[col] = final_df[col].astype(int)
                
        float_cols = ['Average', 'Strike_Rate', 'Boundary_Percentage', 'Overs_Bowled', 'Economy', 'Bowling_Average', 
                      'Bowling_Strike_Rate', 'Batting_Impact_Score', 'Bowling_Impact_Score', 'Overall_Impact_Score']
        for col in float_cols:
            if col in final_df.columns:
                final_df[col] = final_df[col].round(2)
                
        return final_df
