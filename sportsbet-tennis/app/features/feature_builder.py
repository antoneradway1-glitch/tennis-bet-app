import argparse
import pandas as pd
from ..utils.db import get_conn
from .elo import Elo

def build_features():
    conn = get_conn()
    matches = conn.execute('SELECT * FROM matches ORDER BY date').fetchdf()
    if matches.empty:
        print("No matches found. Ingest data first.")
        return
    elo = Elo()
    rows = []
    # Basic rolling form: last 5 matches win rate
    history = {}
    def update_form(pid, won):
        wins, total = history.get(pid, (0,0))
        history[pid] = (wins + (1 if won else 0), total + 1)

    def form_rate(pid):
        wins, total = history.get(pid, (0,0))
        return (wins / total) if total > 0 else 0.5

    for _, m in matches.iterrows():
        p1 = m.p1_id; p2 = m.p2_id
        e1 = elo.get(p1); e2 = elo.get(p2)
        rows.append({
            "match_id": m.match_id,
            "p1_id": p1,
            "p2_id": p2,
            "surface": m.surface,
            "elo_diff": e1 - e2,
            "h2h_p1": 0.5,   # placeholder (can be replaced with true H2H computation)
            "form_p1": form_rate(p1),
            "form_p2": form_rate(p2),
            "label": 1 if m.winner_id == p1 else 0
        })
        # update elo + form
        elo.update(p1, p2, m.winner_id, surface=m.surface)
        update_form(p1, m.winner_id == p1)
        update_form(p2, m.winner_id == p2)

    feats = pd.DataFrame(rows)
    conn.execute("DELETE FROM features")
    conn.execute("INSERT INTO features SELECT * FROM feats", {"feats": feats})
    conn.close()
    print(f"Built {len(feats)} feature rows.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    if args.rebuild:
        build_features()
