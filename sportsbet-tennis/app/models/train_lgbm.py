
import argparse, io, json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss, accuracy_score
from ..utils.db import get_conn
import lightgbm as lgb

FEATURES = ["elo_diff_surface","elo_diff_global","h2h_p1","form_p1","form_p2","days_since_p1","days_since_p2","serve_p1","serve_p2"]

def train_lgbm_model():
    conn = get_conn()
    df = conn.execute("SELECT * FROM features").fetchdf()
    if df.empty:
        print("No features found. Build features first.")
        return
    X = df[FEATURES].fillna(0.0)
    y = df["label"]
    # time-ordered split: last 20% as test
    split = int(len(df)*0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    lgb_train = lgb.LGBMClassifier(
        objective='binary',
        n_estimators=1000,
        learning_rate=0.05,
        num_leaves=31,
        n_jobs=1
    )
    lgb_train.fit(X_train, y_train, eval_set=[(X_test,y_test)], early_stopping_rounds=50, verbose=False)
    # calibration via isotonic on validation (use small split)
    calib = CalibratedClassifierCV(lgb_train, method='isotonic', cv='prefit')
    calib.fit(X_test, y_test)
    proba = calib.predict_proba(X_test)[:,1]
    metrics = {
        "roc_auc": float(roc_auc_score(y_test, proba)) if len(set(y_test))>1 else None,
        "brier": float(brier_score_loss(y_test, proba)),
        "log_loss": float(log_loss(y_test, proba)),
        "accuracy": float(accuracy_score(y_test, (proba>0.5).astype(int))),
    }
    # persist model in artifacts
    buf = io.BytesIO()
    joblib.dump(calib, buf)
    buf.seek(0)
    conn.execute(
        "INSERT OR REPLACE INTO artifacts VALUES (?, ?, ?, ?)",
        ["model_latest", datetime.utcnow(), json.dumps({"features": FEATURES, "metrics": metrics}), buf.read()]
    )
    conn.close()
    print("LightGBM model trained + calibrated. Metrics:", metrics)

if __name__ == '__main__':
    train_lgbm_model()
