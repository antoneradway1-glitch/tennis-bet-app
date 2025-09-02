import argparse, io, json
import pandas as pd
import joblib
from ..utils.db import get_conn
from ..odds.odds_utils import implied_prob_from_decimal, remove_vig_two_outcomes
from ..ev.decision import stake_size, expected_value
from sklearn.linear_model import LogisticRegression

FEATURES = ["elo_diff", "h2h_p1", "form_p1", "form_p2"]

def run_backtest():
    conn = get_conn()
    df = conn.execute('''
        SELECT f.*, m.p1_odd, m.p2_odd
        FROM features f
        JOIN matches m USING(match_id)
        ORDER BY m.date
    ''').fetchdf()
    if df.empty:
        print("No data. Ingest + feature build first.")
        return
    # simple expanding-window walk-forward
    results = []
    for i in range(6, len(df)):  # require at least 6 samples to start
        train = df.iloc[:i]
        test = df.iloc[i:i+1]
        X_tr, y_tr = train[FEATURES], train["label"]
        X_te = test[FEATURES]
        model = LogisticRegression(max_iter=200)
        model.fit(X_tr, y_tr)
        p1 = float(model.predict_proba(X_te)[:,1][0])
        # bookmaker implied
        p1_imp = implied_prob_from_decimal(float(test.p1_odd))
        p2_imp = implied_prob_from_decimal(float(test.p2_odd))
        p1_fair, p2_fair = remove_vig_two_outcomes(p1_imp, p2_imp)
        # choose side with +EV
        pick_side = "P1" if p1 > (1-p1_fair) else "P2"
        model_prob = p1 if pick_side=="P1" else 1-p1
        dec_odds = float(test.p1_odd if pick_side=="P1" else test.p2_odd)
        stake = stake_size(model_prob, dec_odds)
        ev = expected_value(model_prob, dec_odds, stake)
        results.append({
            "match_id": int(test.match_id),
            "pick": pick_side,
            "model_prob": model_prob,
            "odds": dec_odds,
            "stake": stake,
            "EV": ev
        })
    bt = pd.DataFrame(results)
    if not bt.empty:
        print(bt.head())
        print("\nBacktest summary:")
        print(bt.agg({"stake":"sum", "EV":"sum"}))
    else:
        print("Backtest produced no trades (small sample).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.run:
        run_backtest()
