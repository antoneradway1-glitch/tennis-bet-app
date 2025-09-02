
import streamlit as st
import duckdb, requests, os, json
from pathlib import Path
from ..utils.paths import DB_PATH

st.set_page_config(page_title="🎾 Tennis Bets (Mobile)", page_icon="🎾", layout="centered")

st.title("🎾 Tennis — Best Bet Finder (Mobile)")
st.write("Tap a match and fetch model signal (powered by the deployed API).")

conn = duckdb.connect(str(DB_PATH), read_only=True)
df = conn.execute('''
    SELECT m.match_id, m.date, m.surface, p1.name as p1, p2.name as p2, m.p1_odd, m.p2_odd
    FROM matches m
    LEFT JOIN players p1 ON m.p1_id = p1.player_id
    LEFT JOIN players p2 ON m.p2_id = p2.player_id
    ORDER BY date DESC
''').fetchdf()

if df.empty:
    st.info("No matches found. Load sample data first.")
else:
    # show compact list suitable for mobile
    for _, row in df.iterrows():
        label = f\"{row.date.date()} — {row.p1} vs {row.p2} ({row.surface})\"
        if st.button(label):
            st.markdown("**Fetching signal...**")
            # Try to call local API URL or environment variable DEPLOY_URL
            deploy_url = os.getenv('DEPLOY_URL', 'http://127.0.0.1:8000')
            try:
                payload = {
                    "match_id": int(row.match_id),
                    "p1_decimal": float(row.p1_odd) if row.p1_odd else 0.0,
                    "p2_decimal": float(row.p2_odd) if row.p2_odd else 0.0
                }
                r = requests.post(f"{deploy_url}/signal", json=payload, timeout=8)
                if r.status_code==200:
                    data = r.json()
                    st.json(data)
                else:
                    st.error(f"API error: {r.status_code} - {r.text}")
            except Exception as e:
                st.error(f"Could not reach API at {deploy_url}: {e}")
                st.info("If deployed to Render, set DEPLOY_URL to your public URL in environment variables.")

st.caption("Tip: Use Share → Add to Home Screen in Safari to pin this app.")
