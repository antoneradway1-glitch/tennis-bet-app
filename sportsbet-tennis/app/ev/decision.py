import math, os
from dotenv import load_dotenv
load_dotenv()

BANKROLL = float(os.getenv("BANKROLL", "1000"))
MAX_STAKE_FRACTION = float(os.getenv("MAX_STAKE_FRACTION", "0.02"))
KELLY_FRACTION = float(os.getenv("KELLY_FRACTION", "0.5"))

def kelly_fraction(p, dec_odds):
    b = dec_odds - 1.0
    return max(0.0, min((p*(b+1)-1)/b if b>0 else 0.0, 1.0))

def stake_size(p, dec_odds):
    f = kelly_fraction(p, dec_odds) * KELLY_FRACTION
    f = min(f, MAX_STAKE_FRACTION)
    return f * BANKROLL

def expected_value(p, dec_odds, stake):
    b = dec_odds - 1.0
    return p * b * stake - (1 - p) * stake
