import os
import sys

# Add the project root to sys.path so we can import backend modules
sys.path.append(r"C:\Users\sachi\OneDrive\Documents\Project Phase\cricket-analytics")

from backend.live.api_client import LiveAPIClient

client = LiveAPIClient()
raw_matches = client.get_live_matches()

if isinstance(raw_matches, dict) and "data" in raw_matches:
    matches = raw_matches["data"]
elif isinstance(raw_matches, list):
    matches = raw_matches
elif isinstance(raw_matches, dict):
    matches = list(raw_matches.values())
else:
    matches = []

print(f"Total matches returned by API: {len(matches)}")
print("\nFirst 10 matches statuses:")
for m in matches[:10]:
    if isinstance(m, dict):
        print(f"ID: {m.get('match_id')} | Status: {m.get('match_status')} | Title: {m.get('matchs')} | Team A: {m.get('team_a')} vs Team B: {m.get('team_b')}")
