from pathlib import Path
import os

from dotenv import load_dotenv
load_dotenv()

DB_PATH = Path(os.getenv("DB_PATH", "./app/data/tennis.duckdb")).resolve()
ARTIFACTS_DIR = Path("./app/data").resolve()
