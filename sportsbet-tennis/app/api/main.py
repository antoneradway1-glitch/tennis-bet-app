from fastapi import FastAPI
from pydantic import BaseModel
import io, json, joblib
from ..utils.db import get_conn
from ..odds.odds_utils import implied_prob_from_decimal, remove_vig_two_outcomes, fair_odds_from_prob
from ..ev.decision import stake_size, expected_value

app = FastAPI(title="SportsBet Tennis API")

class MatchOdds(BaseModel):
    match_id: int
    p1_decimal: float
    p2_decimal: float

def load_model(conn):
    row = conn.execute("SELECT blob, meta FROM artifacts WHERE name='model_latest'").fetchone()
    if not row:
        return None, None
    blob, meta = row
    model = joblib.load(io.BytesIO(blob))
    meta = json.loads(meta)
    return model, meta

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/signal")
def signal(payload: MatchOdds):
    conn = get_conn(readonly=True)
    feats = conn.execute("SELECT * FROM features WHERE match_id=?", [payload.match_id]).fetchdf()
    if feats.empty:
        return {"error":"unknown match_id"}
    model, meta = load_model(conn)
    if not model:
        return {"error":"no model"}
    X = feats[['elo_diff','h2h_p1','form_p1','form_p2']]
    p1 = float(model.predict_proba(X)[:,1][0])
    p2 = 1.0 - p1
    p1_imp = implied_prob_from_decimal(payload.p1_decimal)
    p2_imp = implied_prob_from_decimal(payload.p2_decimal)
    p1_fair, p2_fair = remove_vig_two_outcomes(p1_imp, p2_imp)
    p1_edge = p1 - p1_fair
    p2_edge = p2 - p2_fair
    suggestion = "P1" if p1_edge > p2_edge and p1_edge>0 else ("P2" if p2_edge>0 else "PASS")
    odds = payload.p1_decimal if suggestion=="P1" else payload.p2_decimal
    prob = p1 if suggestion=="P1" else p2
    stake = stake_size(prob, odds) if suggestion!="PASS" else 0.0
    ev = expected_value(prob, odds, stake) if suggestion!="PASS" else 0.0
    return {
        "match_id": payload.match_id,
        "p1_prob": p1, "p2_prob": p2,
        "p1_fair_odds": 1.0/max(p1_fair, 1e-9), "p2_fair_odds": 1.0/max(p2_fair,1e-9),
        "p1_edge": p1_edge, "p2_edge": p2_edge,
        "suggestion": suggestion,
        "stake": stake,
        "expected_value": ev
    }
