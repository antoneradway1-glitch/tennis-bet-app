import io, joblib, pandas as pd
from ..utils.db import get_conn

def load_model(conn):
    row = conn.execute("SELECT blob, meta FROM artifacts WHERE name='model_latest'").fetchone()
    if not row:
        return None, None
    blob, meta = row
    model = joblib.load(io.BytesIO(blob))
    return model, meta

def predict_probabilities(conn):
    model, meta = load_model(conn)
    if not model:
        raise RuntimeError("No model found. Train a model first.")
    feats = conn.execute("SELECT * FROM features").fetchdf()
    X = feats[[*json.loads(meta)['features']]]  # Not used; left for future
    # We'll reselect the same features in a safer way:
    X = feats[['elo_diff','h2h_p1','form_p1','form_p2']]
    p1_prob = model.predict_proba(X)[:,1]
    return feats[['match_id']], p1_prob
