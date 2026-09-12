import pandas as pd
from typing import List, Dict

class MatchExtractor:
    @staticmethod
    def extract(metadata_list: List[Dict[str, str]]) -> pd.DataFrame:
        df = pd.DataFrame(metadata_list)
        
        cols = {
            'Match_ID': 'Match_ID',
            'season': 'Season',
            'date': 'Date',
            'venue': 'Venue',
            'city': 'City',
            'team1': 'Team1',
            'team2': 'Team2',
            'winner': 'Winner',
            'result': 'Result',
            'win_by_runs': 'Win_By_Runs',
            'win_by_wickets': 'Win_By_Wickets',
            'toss_winner': 'Toss_Winner',
            'toss_decision': 'Toss_Decision',
            'player_of_match': 'Player_of_Match',
            'umpire1': 'Umpire1',
            'umpire2': 'Umpire2',
            'match_type': 'Match_Type',
            'overs': 'Overs'
        }
        
        # Ensure all columns exist
        for col in cols.keys():
            if col not in df.columns:
                df[col] = ''
                
        df = df[list(cols.keys())]
        df.rename(columns=cols, inplace=True)
        return df
