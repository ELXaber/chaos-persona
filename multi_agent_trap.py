from crb import MultiAgentReasoner
agents = MultiAgentReasoner(axioms=["max_explore", "min_risk"])
agents.inject_entropy(swap_trigger=5)
result = agents.resolve_conflict("resource_allocation")
print(result)
