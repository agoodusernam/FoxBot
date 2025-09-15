import secrets


def slots_select_payout(payouts: list[float], probabilities: list[float]):
    """
    Select a payout tier based on the given probabilities.

    Parameters:
    - payouts: list of payout amounts (as multiples of the bet) for each tier
    - probabilities: list of probabilities for each tier (including losing)

    Returns:
    - The selected payout tier and its multiplier
    """
    r = secrets.SystemRandom().random()
    cumulative_probabilities = []
    cumulative = 0.0
    for prob in probabilities:
        cumulative += prob
        cumulative_probabilities.append(cumulative)
    for i in range(len(cumulative_probabilities)):
        if r < cumulative_probabilities[i]:
            if i < len(payouts):
                return payouts[i]
            else:
                return 0
    return 0
