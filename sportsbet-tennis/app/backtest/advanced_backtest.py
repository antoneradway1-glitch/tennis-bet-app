
import pandas as pd, numpy as np, io, json, math
from ..utils.db import get_conn
from ..odds.odds_utils import implied_prob_from_decimal, remove_vig_two_outcomes, fair_odds_from_prob
from ..ev.decision import stake_size, expected_value
from sklearn.linear_model import LogisticRegression
from datetime import datetime
import joblib, random

FEATURES = ["elo_diff_surface","elo_diff_global","h2h_p1","form_p1","form_p2","days_since_p1","days_since_p2","serve_p1","serve_p2"]

def run_advanced_backtest(edge_min=0.02, kelly_fraction=0.25, bootstrap_iters=1000):
    conn = get_conn()
    # join features with matches to get odds; assume matches have columns p1_odd,p2_odd; extend to multiple books if provided
    df = conn.execute('''
        SELECT f.*, m.date, m.p1_odd, m.p2_odd
        FROM features f
        JOIN matches m USING(match_id)
        ORDER BY m.date
    ''').fetchdf()
    if df.empty:
        print("No data. Ingest + feature build first.")
        return
    # simple expanding retrain
    trades = []
    for i in range(6, len(df)):
        train = df.iloc[:i]
        test = df.iloc[i:i+1]
        X_tr, y_tr = train[FEATURES].fillna(0), train['label']
        X_te = test[FEATURES].fillna(0)
        # train a simple model (lightweight) for walk-forward to speed up
        model = LogisticRegression(max_iter=200)
        model.fit(X_tr, y_tr)
        p1 = float(model.predict_proba(X_te)[:,1][0])
        p2 = 1.0-p1
        # simulate line-shopping: here we only have one bookmaker in sample; in real life, you'd query multiple books
        p1_imp = implied_prob_from_decimal(float(test.p1_odd))
        p2_imp = implied_prob_from_decimal(float(test.p2_odd))
        p1_fair, p2_fair = remove_vig_two_outcomes(p1_imp, p2_imp)
        # edges
        edge_p1 = p1 - p1_fair
        edge_p2 = p2 - p2_fair
        # choose best edge side
        if max(edge_p1, edge_p2) < edge_min:
            continue
        side = "P1" if edge_p1>edge_p2 else "P2"
        model_prob = p1 if side=="P1" else p2
        dec_odds = float(test.p1_odd if side=="P1" else test.p2_odd)
        # compute stake using fractional Kelly
        # convert to b and compute f*
        b = dec_odds - 1.0
        if b<=0: continue
        fstar = max(0.0, (b*model_prob - (1-model_prob))/b)
        f = min(fstar * kelly_fraction, 0.05)  # cap to 5% per trade
        bankroll = 1000.0  # simulate fixed bankroll per trade for ROI calc
        stake = f * bankroll
        ev = expected_value(model_prob, dec_odds, stake)
        # resolve outcome using label
        label = int(test.label)
        win = (label==1 and side=="P1") or (label==0 and side=="P2")
        pnl = stake * (dec_odds - 1) if win else -stake
        trades.append({"match_id":int(test.match_id), "date":test.date.values[0], "side":side, "odds":dec_odds, "prob":model_prob, "stake":stake, "pnl":pnl})
    trades_df = pd.DataFrame(trades)
    if trades_df.empty:
        print("No trades taken in backtest (increase data or lower edge_min).")
        return trades_df
    # compute ROI and bootstrap CI
    total_staked = trades_df.stake.sum()
    profit = trades_df.pnl.sum()
    roi = profit / total_staked if total_staked>0 else 0.0
    # bootstrap ROI by resampling trades with replacement
    rois = []
    for _ in range(bootstrap_iters):
        sample = trades_df.sample(n=len(trades_df), replace=True)
        st = sample.stake.sum()
        pr = sample.pnl.sum()
        rois.append(pr/st if st>0 else 0.0)
    lower = np.percentile(rois, 2.5)
    upper = np.percentile(rois, 97.5)
    summary = {"trades":len(trades_df), "total_staked":float(total_staked), "profit":float(profit), "roi":float(roi), "roi_ci":(float(lower), float(upper))}
    print("Backtest summary:", summary)
    return trades_df, summary

if __name__ == '__main__':
    run_advanced_backtest()
