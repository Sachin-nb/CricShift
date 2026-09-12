import csv
import logging
from pathlib import Path
from typing import Dict, List, Tuple

class CricsheetParser:
    """Parses a Cricsheet CSV file into metadata and delivery records."""
    
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.metadata: Dict[str, str] = {}
        self.deliveries: List[Dict[str, str]] = []
        self.is_valid = False
        self.match_id = self.file_path.stem

    def parse(self) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row:
                        continue
                        
                    if row[0] == 'version':
                        self.is_valid = True
                        
                    elif row[0] == 'info':
                        self._parse_info(row)
                        
                    elif row[0] == 'ball':
                        self._parse_ball(row)
                        
            if self.is_valid:
                self.metadata['Match_ID'] = self.match_id
                self._enrich_deliveries()
                
        except Exception as e:
            logging.error(f"Error parsing {self.file_path}: {str(e)}")
            self.is_valid = False
            
        return self.metadata, self.deliveries

    def _parse_info(self, row: List[str]):
        if len(row) < 3:
            return
            
        key = row[1]
        val = row[2]
        
        if key == 'team':
            if 'team1' not in self.metadata:
                self.metadata['team1'] = val
            elif 'team2' not in self.metadata:
                self.metadata['team2'] = val
        elif key == 'umpire':
            if 'umpire1' not in self.metadata:
                self.metadata['umpire1'] = val
            elif 'umpire2' not in self.metadata:
                self.metadata['umpire2'] = val
        elif key in ['player_of_match', 'winner', 'venue', 'city', 'toss_winner', 'toss_decision', 'season', 'match_type', 'overs']:
            self.metadata[key] = val
        elif key == 'date':
            if 'date' not in self.metadata:
                self.metadata['date'] = val
        elif key == 'winner_runs':
            self.metadata['win_by_runs'] = val
        elif key == 'winner_wickets':
            self.metadata['win_by_wickets'] = val
        elif key == 'outcome':
            self.metadata['result'] = val
            if val == 'tie':
                self.metadata['winner'] = 'Tie'
            elif val == 'no result':
                self.metadata['winner'] = 'No Result'

    def _parse_ball(self, row: List[str]):
        # Cricsheet format: ball,innings,over.ball,batting_team,striker,non_striker,bowler,runs_off_bat,extras,wides,noballs,byes,legbyes,penalty,wicket_type,player_out,fielder
        row = row + [''] * (17 - len(row))
        
        deliv = {
            'Match_ID': self.match_id,
            'Innings': row[1],
            'Over_Ball': row[2],
            'Batting_Team': row[3],
            'Batter': row[4],
            'Non_Striker': row[5],
            'Bowler': row[6],
            'Runs_Batter': row[7],
            'Extras': row[8],
            'Wide': row[9],
            'NoBall': row[10],
            'Bye': row[11],
            'LegBye': row[12],
            'Penalty': row[13],
            'Dismissal_Type': row[14],
            'Player_Out': row[15],
            'Fielder': row[16]
        }
        self.deliveries.append(deliv)

    def _enrich_deliveries(self):
        curr_score = 0
        curr_wickets = 0
        curr_innings = None
        
        team1 = self.metadata.get('team1', '')
        team2 = self.metadata.get('team2', '')
        season = self.metadata.get('season', '')

        for d in self.deliveries:
            if d['Innings'] != curr_innings:
                curr_score = 0
                curr_wickets = 0
                curr_innings = d['Innings']
                
            runs = int(d['Runs_Batter']) if d['Runs_Batter'] else 0
            extras = int(d['Extras']) if d['Extras'] else 0
            
            curr_score += (runs + extras)
            
            dt = d['Dismissal_Type'].lower() if d['Dismissal_Type'] else ""
            if dt and "retired" not in dt:
                curr_wickets += 1
                
            d['Current_Score'] = curr_score
            d['Current_Wickets'] = curr_wickets
            d['Total_Runs'] = runs + extras
            d['IsBoundary'] = 1 if runs == 4 else 0
            d['IsSix'] = 1 if runs == 6 else 0
            d['IsDotBall'] = 1 if runs == 0 and extras == 0 else 0
            
            ob = d['Over_Ball'].split('.')
            d['Over'] = ob[0] if len(ob) > 0 else '0'
            d['Ball'] = ob[1] if len(ob) > 1 else '1'
            
            d['Wicket'] = 1 if dt and "retired" not in dt else 0
            d['Season'] = season
            
            if d['Batting_Team'] == team1:
                d['Bowling_Team'] = team2
            else:
                d['Bowling_Team'] = team1
