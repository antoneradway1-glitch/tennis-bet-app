import duckdb
import argparse
from pathlib import Path
from .paths import DB_PATH

SCHEMA_SQL_PATH = Path(__file__).parent.parent / "data" / "schema.sql"

def get_conn(readonly=False):
    return duckdb.connect(str(DB_PATH), read_only=readonly)

def init_db():
    conn = get_conn()
    with open(SCHEMA_SQL_PATH, "r") as f:
        conn.execute(f.read())
    conn.close()
    print(f"DB initialized at {DB_PATH}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true")
    args = parser.parse_args()
    if args.init:
        init_db()
