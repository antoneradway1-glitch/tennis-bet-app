import argparse
import pandas as pd
from pathlib import Path
from ..utils.db import get_conn
from ..utils.paths import DB_PATH

DATA_DIR = Path(__file__).parent.parent / "data"

def load_sample():
    conn = get_conn()
    players = pd.read_csv(DATA_DIR / "players.csv")
    matches = pd.read_csv(DATA_DIR / "sample_matches.csv", parse_dates=["date"])
    conn.execute("DELETE FROM players")
    conn.execute("DELETE FROM matches")
    conn.execute("DELETE FROM features")
    conn.execute("DELETE FROM signals")
    conn.execute("DELETE FROM artifacts")
    conn.execute("INSERT INTO players SELECT * FROM players_df", {"players_df": players})
    conn.execute("INSERT INTO matches SELECT * FROM matches_df", {"matches_df": matches})
    conn.close()
    print(f"Loaded {len(players)} players and {len(matches)} matches into {DB_PATH}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--load-sample", action="store_true")
    args = parser.parse_args()
    if args.load_sample:
        load_sample()
