import math
from collections import defaultdict

K_SURFACE = {
    "Hard": 24.0,
    "Clay": 26.0,
    "Grass": 20.0,
    "Indoor": 22.0,
}

def expected_score(r_a, r_b):
    return 1.0 / (1.0 + math.pow(10.0, (r_b - r_a) / 400.0))

class Elo:
    def __init__(self, base=1500.0, k_default=24.0):
        self.base = base
        self.k_default = k_default
        self.ratings = defaultdict(lambda: base)

    def update(self, player_a, player_b, winner_id, surface=None):
        ra = self.ratings[player_a]
        rb = self.ratings[player_b]
        ea = expected_score(ra, rb)
        eb = 1.0 - ea
        k = K_SURFACE.get(surface, self.k_default)
        sa = 1.0 if winner_id == player_a else 0.0
        sb = 1.0 - sa
        self.ratings[player_a] = ra + k * (sa - ea)
        self.ratings[player_b] = rb + k * (sb - eb)

    def get(self, player_id):
        return self.ratings[player_id]
