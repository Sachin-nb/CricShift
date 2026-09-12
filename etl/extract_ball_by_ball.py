import pandas as pd
from typing import List, Dict

class BallByBallExtractor:
    @staticmethod
    def extract(deliveries_list: List[Dict[str, str]]) -> pd.DataFrame:
        df = pd.DataFrame(deliveries_list)
        
        cols = [
            'Match_ID', 'Season', 'Innings', 'Over', 'Ball',
            'Batting_Team', 'Bowling_Team', 'Batter', 'Bowler', 'Non_Striker',
            'Runs_Batter', 'Extras', 'Wide', 'NoBall', 'Bye', 'LegBye', 'Penalty',
            'Total_Runs', 'IsBoundary', 'IsSix', 'IsDotBall', 'Wicket',
            'Dismissal_Type', 'Player_Out', 'Fielder', 'Current_Score', 'Current_Wickets'
        ]
        
        for col in cols:
            if col not in df.columns:
                df[col] = ''
                
        return df[cols]
