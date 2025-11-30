Future interface for Chaos AI-OS that allows adjustments of the OS to things like personality matrix (Snarky, funny, romantic, professional, etc.) and lists the available generated agents from the agent_designer through auto discovery.


# Available agents — auto-discovered
- AGENTS = {
    "day":      day_planner.day_planner_agent,
    "fitness":  fitness_coach.fitness_agent,
    "math":     math_researcher.math_agent,
    # ... all others appear automatically

- >>> caios("Plan my day: gym, write paper, family dinner", "day")
- >>> caios("set snarky 8")
- >>> caios("set professional 3")
- >>> caios("show personality")

- professional: 3
- snarky: 8
- empathetic: 5
...
- >>> caios("Why did you schedule gym at 6am?", "day", show_reasoning=True)
- [REASONING] You said "gym" three times this week and energy_level=0.8 → early slot maximises completion probability...
