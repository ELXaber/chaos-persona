from crb import ChaosReasoner
reasoner = ChaosReasoner(raw_q="paradox_loop_1")
reasoner.inject_entropy(swap_trigger=3)
print(reasoner.solve_puzzle("nonlinear_time"))
