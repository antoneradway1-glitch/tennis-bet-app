import argparse, json, io
import joblib
import pandas as pd
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss, accuracy_score
from ..utils.db import get_conn

FEATURES = ["elo_diff", "h2h_p1", "form_p1", "form_p2"]

def train():
    conn = get_conn()
    df = conn.execute("SELECT * FROM features").fetchdf()
    if df.empty:
        print("No features found. Build features first.")
        return
    X = df[FEATURES]
    y = df["label"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, shuffle=False)
    model = LogisticRegression(max_iter=200)
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:,1]
    metrics = {
        "roc_auc": float(roc_auc_score(y_test, proba)) if len(set(y_test))>1 else None,
        "brier": float(brier_score_loss(y_test, proba)),
        "log_loss": float(log_loss(y_test, proba)),
        "accuracy": float(accuracy_score(y_test, (proba>0.5).astype(int))),
    }
    # persist model in artifacts
    buf = io.BytesIO()
    joblib.dump(model, buf)
    buf.seek(0)
    conn.execute(
        "INSERT OR REPLACE INTO artifacts VALUES (?, ?, ?, ?)",
        ["model_latest", datetime.utcnow(), json.dumps({"features": FEATURES, "metrics": metrics}), buf.read()]
    )
    conn.close()
    print("Model trained. Metrics:", metrics)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", action="store_true")
    args = parser.parse_args()
    if args.train:
        train()
