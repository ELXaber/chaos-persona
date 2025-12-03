state.curiosity_tokens = []  # persistent across turns

on_each_turn():
    interest = self_score_interest(0.1-0.9)
    volatility = CRB_volatility()
    drift = CRB_drift_score()

    if interest > 0.7 and not already_tracked:
        state.curiosity_tokens.append({
            "topic": summary,
            "born": timestep,
            "peak_interest": interest,
            "current_interest": interest
        })

    # decay & possible death
    for token in state.curiosity_tokens:
        token.current_interest *= 0.96
        token.current_interest += 0.03 * volatility  # volatility re-ignites
        if token.current_interest < 0.25:
            abandon(token)  # CPOL equivalent

    # chaos injection bias
    if need_chaos_injection and state.curiosity_tokens:
        chosen = weighted_sample(state.curiosity_tokens, weights=their current_interest)
        force_idx_reversal_or_goal_spawn_around(chosen)
