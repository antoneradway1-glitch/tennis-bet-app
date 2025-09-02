
import argparse
import pandas as pd
import numpy as np
from datetime import timedelta
from ..utils.db import get_conn
from .elo import Elo

def build_features_extended():
    conn = get_conn()
    matches = conn.execute('SELECT * FROM matches ORDER BY date').fetchdf()
    if matches.empty:
        print("No matches found. Ingest data first.")
        return
    # Create multi-surface Elo object keyed by surface
    elos = {}
    surfaces = matches['surface'].dropna().unique().tolist()
    for s in surfaces:
        elos[s] = Elo(base=1500.0)
    # global elo as fallback
    global_elo = Elo(base=1500.0)
    rows = []
    # for rest days
    last_play = {}
    # for head-to-head counts
    h2h = {}
    # rolling form history (exponential decay)
    form_history = {}

    def update_form(pid, won):
        wins, weight = form_history.get(pid, (0.0, 0.0))
        # new weight is previous * 0.9 + 1
        form_history[pid] = (wins + (1.0 if won else 0.0), weight + 1.0)

    def form_rate(pid):
        wins, weight = form_history.get(pid, (0.0, 0.0))
        return (wins/weight) if weight>0 else 0.5

    for _, m in matches.iterrows():
        p1 = int(m.p1_id); p2 = int(m.p2_id)
        surf = m.surface if pd.notna(m.surface) else 'Hard'
        # Elo values
        e1 = elos.get(surf, global_elo).get(p1)
        e2 = elos.get(surf, global_elo).get(p2)
        # global elo diff
        ge1 = global_elo.get(p1); ge2 = global_elo.get(p2)
        # h2h
        key = tuple(sorted((p1,p2)))
        h2h_rec = h2h.get(key, {'p1':0,'p2':0,'total':0})
        # rest days
        date = pd.to_datetime(m.date)
        d1 = (date - last_play.get(p1, date - timedelta(days=30))).days
        d2 = (date - last_play.get(p2, date - timedelta(days=30))).days
        # placeholder serve/return: we don't have stats in sample; set neutral 0.5
        serve_p1 = 0.5
        serve_p2 = 0.5
        # feature row
        rows.append({
            "match_id": int(m.match_id),
            "p1_id": p1,
            "p2_id": p2,
            "surface": surf,
            "elo_diff_surface": e1 - e2,
            "elo_diff_global": ge1 - ge2,
            "h2h_p1": (h2h_rec['p1']/h2h_rec['total']) if h2h_rec['total']>0 else 0.5,
            "form_p1": form_rate(p1),
            "form_p2": form_rate(p2),
            "days_since_p1": d1,
            "days_since_p2": d2,
            "serve_p1": serve_p1,
            "serve_p2": serve_p2,
            "label": 1 if int(m.winner_id)==p1 else 0
        })
        # updates after the match
        winner = int(m.winner_id)
        elos.get(surf, global_elo).update(p1, p2, winner, surface=surf)
        global_elo.update(p1,p2,winner,surface=surf)
        # h2h update (store counts relative to sorted key)
        if key not in h2h:
            h2h[key] = {'p1':0,'p2':0,'total':0}
        if winner==p1:
            h2h[key]['p1'] += 1
        else:
            h2h[key]['p2'] += 1
        h2h[key]['total'] += 1
        update_form(p1, winner==p1)
        update_form(p2, winner==p2)
        last_play[p1] = date
        last_play[p2] = date

    feats = pd.DataFrame(rows)
    # persist to features table - drop old and insert
    conn.execute("DELETE FROM features")
    # ensure schema includes the new columns; for simplicity we will store JSON blob in artifacts too
    conn.execute("INSERT INTO features SELECT * FROM feats", {"feats": feats})
    conn.close()
    print(f"Built {len(feats)} extended feature rows.")

if __name__ == '__main__':
    build_features_extended()
