
CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE IF NOT EXISTS matches (
    match_id INTEGER PRIMARY KEY,
    date DATE,
    tour TEXT,             -- ATP/WTA/Challenger
    surface TEXT,          -- Hard/Clay/Grass/Indoor
    best_of INTEGER,       -- 3 or 5
    p1_id INTEGER,
    p2_id INTEGER,
    winner_id INTEGER,
    p1_odd REAL,           -- optional: closing odds for P1
    p2_odd REAL,           -- optional: closing odds for P2
    FOREIGN KEY(p1_id) REFERENCES players(player_id),
    FOREIGN KEY(p2_id) REFERENCES players(player_id)
);

CREATE TABLE IF NOT EXISTS features (
    match_id INTEGER PRIMARY KEY,
    p1_id INTEGER,
    p2_id INTEGER,
    surface TEXT,
    elo_diff REAL,
    h2h_p1 REAL,
    form_p1 REAL,
    form_p2 REAL,
    label INTEGER,         -- 1 if p1 wins, else 0
    FOREIGN KEY(match_id) REFERENCES matches(match_id)
);

CREATE TABLE IF NOT EXISTS artifacts (
    name TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    meta JSON,
    blob BLOB              -- pickled model or other artifact
);

CREATE TABLE IF NOT EXISTS signals (
    match_id INTEGER PRIMARY KEY,
    p1_prob REAL,
    p2_prob REAL,
    p1_fair_odds REAL,
    p2_fair_odds REAL,
    p1_edge REAL,
    p2_edge REAL,
    p1_kelly REAL,
    p2_kelly REAL
);
