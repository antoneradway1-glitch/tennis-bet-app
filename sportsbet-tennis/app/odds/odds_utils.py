def implied_prob_from_decimal(odds):
    return 1.0 / odds if odds and odds > 0 else None

def remove_vig_two_outcomes(p1_implied, p2_implied):
    # Proportional vig removal
    total = p1_implied + p2_implied
    if total == 0:
        return p1_implied, p2_implied
    return p1_implied/total, p2_implied/total

def fair_odds_from_prob(prob):
    return 1.0 / prob if prob and prob > 0 else None

def edge(model_prob, fair_prob):
    # edge vs bookmaker's implied fair prob
    return model_prob - fair_prob
