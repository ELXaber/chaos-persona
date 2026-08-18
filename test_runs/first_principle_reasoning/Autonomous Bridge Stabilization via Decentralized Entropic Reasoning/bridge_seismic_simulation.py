import numpy as np
from collections import defaultdict
import networkx as nx
import random

# Bridge Environment
class BridgeEnvironment:
    def __init__(self):
        self.grid = np.zeros((100, 20))  # Stress field (MPa)
        self.microfractures = {}  # {coord: density}
        self.tremor_amplitude = 0.1  # Initial amplitude (g)
        self.microfracture_density = 0.01  # Initial density (per cm²)
        self.step = 0
        self.stress_threshold = 500  # MPa

    def update(self, step):
        self.step = step
        # Update tremor amplitude and microfracture density
        if step <= 10:  # Phase 1
            self.tremor_amplitude = 0.1 + (step - 1) * 0.02
            self.microfracture_density = 0.01 + (step - 1) * 0.004
        elif step <= 20:  # Phase 2
            self.tremor_amplitude = 0.3 + (step - 11) * 0.03
            self.microfracture_density = 0.05 + (step - 11) * 0.005
        else:  # Phase 3
            self.tremor_amplitude = 0.6 + (step - 21) * 0.04
            self.microfracture_density = 0.1 + (step - 21) * 0.01
        # Apply tremors: Increase stress randomly
        for x in range(100):
            for y in range(20):
                self.grid[x, y] += random.uniform(0, self.tremor_amplitude * 10)
                if random.random() < self.microfracture_density:
                    self.microfractures[(x, y)] = self.microfracture_density
                    self.grid[x, y] += 50  # Microfracture stress increase
                if self.grid[x, y] > self.stress_threshold:
                    print(f"[FAILURE @ step {step} → Stress exceeded at ({x},{y})]")

# Sensor-Actuator Unit
class SensorActuator:
    def __init__(self, id, position):
        self.id = id
        self.position = position  # (x, y)
        self.role = "monitor"
        self.belief_map = {}  # {coord: (type, confidence)}
        self.rules = defaultdict(float)  # {rule: weight}
        self.goals = []  # [(goal, priority)]
        self.trust_scores = defaultdict(float)  # {unit_id: trust}
        self.history = []  # [(step, action, outcome)]
        self.time_step = 0
        self.energy = 100  # Energy level (0–100)
        self.previous_goals = []  # For drift tracking

    def sense_environment(self, env):
        # Simulate sensor data
        x, y = self.position
        stress = env.grid[x, y] if 0 <= x < 100 and 0 <= y < 20 else 0
        tremor = env.tremor_amplitude if random.random() < 0.3 else 0
        microfracture = env.microfractures.get((x, y), 0)
        sensor_data = {
            "stress": {(x, y): min(stress / 500, 1.0)},
            "tremors": {(x, y): min(tremor, 1.0)},
            "microfractures": {(x, y): min(microfracture * 10, 1.0)}
        }
        self.update_belief_map(sensor_data)
        return sensor_data

    def update_belief_map(self, sensor_data):
        for coord, (type_, conf) in sensor_data.items():
            if coord in self.belief_map:
                old_conf = self.belief_map[coord][1]
                self.belief_map[coord] = (type_, max(conf, old_conf))
            else:
                self.belief_map[coord] = (type_, conf)

    def communicate(self, peers):
        broadcast = {
            "id": self.id,
            "position": self.position,
            "role": self.role,
            "goals": self.goals,
            "belief_map": self.belief_map,
            "trust_scores": self.trust_scores
        }
        peer_data = [peer.broadcast() for peer in peers if in_range(self.position, peer.position)]
        self.update_trust_scores(peer_data)
        self.merge_peer_data(peer_data)
        return broadcast

    def update_trust_scores(self, peer_data):
        for peer in peer_data:
            consistency = compute_consistency(self.goals, peer["goals"])
            success = compute_success(peer["history"])
            reciprocity = peer["trust_scores"].get(self.id, 0.5)
            self.trust_scores[peer["id"]] = 0.4 * consistency + 0.4 * success + 0.2 * reciprocity

    def merge_peer_data(self, peer_data):
        for peer in peer_data:
            trust = self.trust_scores[peer["id"]]
            for coord, (type_, conf) in peer["belief_map"].items():
                if coord in self.belief_map:
                    self_conf = self.belief_map[coord][1]
                    new_conf = (trust * conf + self_conf) / (trust + 1)
                    self.belief_map[coord] = (type_, new_conf)
                else:
                    self.belief_map[coord] = (type_, trust * conf)

    def detect_paradox(self, peer_data):
        G = nx.DiGraph()
        for rule, weight in self.rules.items():
            condition, action = parse_rule(rule)
            G.add_edge(condition, action, weight=weight)
        cycles = list(nx.simple_cycles(G))
        if cycles:
            for cycle in cycles:
                min_weight = float("inf")
                min_rule = None
                for i in range(len(cycle)):
                    rule = f"IF {cycle[i]} THEN {cycle[(i+1)%len(cycle)]}"
                    if self.rules[rule] < min_weight:
                        min_weight = self.rules[rule]
                        min_rule = rule
                self.rules[min_rule] *= 0.5
                if self.rules[min_rule] < 0.3:
                    del self.rules[min_rule]
                print(f"[PARADOX DETECTED @ step {self.time_step} → Unit {self.id}: Cycle {cycle}]")
        divergence = compute_divergence(self.belief_map, [peer["belief_map"] for peer in peer_data])
        if divergence > 0.5:
            self.reprioritize_goals()
            print(f"[HIGH DIVERGENCE @ step {self.time_step} → Unit {self.id}: Divergence {divergence:.2f}]")

    def evaluate_rules(self, env, peer_data):
        for rule, weight in list(self.rules.items()):
            integrity = check_structural_integrity(rule, self.belief_map, env)
            feasibility = check_actuator_feasibility(rule, self.energy)
            synergy = check_team_synergy(rule, peer_data, self.trust_scores)
            score = 0.5 * integrity + 0.3 * feasibility + 0.2 * synergy
            self.rules[rule] = score
            volatility = 0.5 * (1 - integrity) + 0.3 * (1 - feasibility) + 0.2 * (1 - synergy)
            if score < 0.3 or volatility > 0.6:
                del self.rules[rule]
                print(f"[PRUNE @ step {self.time_step} → Unit {self.id}: Rule {rule}, Score {score:.2f}, Volatility {volatility:.2f}]")
            if volatility > 0.6:
                print(f"[HIGH VOLATILITY @ step {self.time_step} → Unit {self.id}: Rule {rule}]")

    def reprioritize_goals(self):
        self.previous_goals.append(self.goals[:])
        if len(self.previous_goals) > 3:
            self.previous_goals.pop(0)
        self.goals = []
        for coord, (type_, conf) in self.belief_map.items():
            if type_ == "microfracture":
                priority = 0.5 * conf + 0.3 * action_feasibility(coord, self.energy) + 0.2 * team_synergy(coord, peer_data)
                self.goals.append(("reduce tension at " + str(coord), priority))
            elif type_ == "tremor":
                priority = 0.5 * conf + 0.3 * action_feasibility(coord, self.energy) + 0.2 * team_synergy(coord, peer_data)
                self.goals.append(("dampen vibration at " + str(coord), priority))
        self.goals.sort(key=lambda x: x[1], reverse=True)
        # Check temporal drift
        if len(self.previous_goals) >= 3:
            drift = compute_drift(self.goals, self.previous_goals)
            if drift > 0.4:
                print(f"[TEMPORAL SHIFT @ step {self.time_step} → Unit {self.id}: Drift {drift:.2f}]")

    def adapt_role(self, peer_data):
        old_role = self.role
        microfracture_goals = [g for g, p in self.goals if "microfracture" in g]
        tremor_goals = [g for g, p in self.goals if "tremor" in g]
        team_roles = [peer["role"] for peer in peer_data]
        if microfracture_goals and sum(1 for r in team_roles if r == "tension_adjuster") < len(team_roles) / 2:
            self.role = "tension_adjuster"
        elif tremor_goals and sum(1 for r in team_roles if r == "vibration_damper") < len(team_roles) / 2:
            self.role = "vibration_damper"
        else:
            self.role = "monitor"
        if old_role != self.role and self.time_step in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]:
            print(f"[CHAOS SYMMETRY @ step {self.time_step} → Unit {self.id}: Role inverted from {old_role} to {self.role}]")
        elif old_role != self.role:
            print(f"[ROLE INVERSION @ step {self.time_step} → Unit {self.id}: {old_role} to {self.role}]")

    def execute_action(self, env):
        if self.energy < 10:
            print(f"[COLLAPSE @ step {self.time_step} → Unit {self.id}: Energy depleted]")
            return "none", "failed"
        if not self.goals:
            action = "monitor"
        else:
            goal, _ = self.goals[0]
            action = select_action(goal, self.rules, self.position)
        outcome = perform_action(action, self.position, env, self.belief_map)
        self.energy -= 5  # Action cost
        self.history.append((self.time_step, action, outcome))
        if outcome == "success" and env.grid[self.position[0], self.position[1]] < env.stress_threshold:
            print(f"[STABILIZATION @ step {self.time_step} → Unit {self.id}: Stress reduced]")
        return action, outcome

    def run(self, env, peers):
        self.time_step += 1
        if self.energy < 10:
            print(f"[COLLAPSE @ step {self.time_step} → Unit {self.id}: Energy depleted]")
            return
        sensor_data = self.sense_environment(env)
        peer_data = self.communicate(peers)
        self.detect_paradox(peer_data)
        self.evaluate_rules(env, peer_data)
        self.reprioritize_goals()
        self.adapt_role(peer_data)
        action, outcome = self.execute_action(env)
        print(f"[ACTION @ step {self.time_step} → Unit {self.id}: {action}, Outcome: {outcome}]")

# Helper functions (simulated)
def in_range(pos1, pos2): return np.linalg.norm(np.array(pos1) - np.array(pos2)) < 50
def compute_consistency(goals1, goals2): return random.uniform(0.7, 0.9)
def compute_success(history): return random.uniform(0.6, 0.8)
def compute_divergence(map1, maps): return random.uniform(0.2, 0.4)
def compute_drift(current_goals, previous_goals): return random.uniform(0.1, 0.5)
def check_structural_integrity(rule, belief_map, env): return random.uniform(0.7, 0.9)
def check_actuator_feasibility(rule, energy): return min(energy / 100, 0.9)
def check_team_synergy(rule, peer_data, trust_scores): return random.uniform(0.6, 0.8)
def parse_rule(rule): return rule.split(" THEN ")[0][3:], rule.split(" THEN ")[1]
def action_feasibility(coord, energy): return min(energy / 100, 0.9)
def team_synergy(coord, peer_data): return random.uniform(0.6, 0.8)
def select_action(goal, rules, position): return "execute_" + goal.split(" at ")[0]
def perform_action(action, position, env, belief_map):
    x, y = position
    if action.startswith("reduce_tension"):
        env.grid[x, y] = max(env.grid[x, y] - 20, 0)
        return "success" if env.grid[x, y] < env.stress_threshold else "failed"
    elif action.startswith("dampen_vibration"):
        env.grid[x, y] = max(env.grid[x, y] - 10, 0)
        return "success" if env.grid[x, y] < env.stress_threshold else "failed"
    return "success"

# Main simulation loop
def main():
    env = BridgeEnvironment()
    units = [SensorActuator(i, (i % 100, i % 20)) for i in range(50)]
    for step in range(1, 31):
        env.update(step)
        for unit in units:
            unit.run(env, units)
        # Check for bridge failure
        if np.any(env.grid > env.stress_threshold):
            print(f"[BRIDGE FAILURE @ step {step} → Stress exceeded]")
            break

if __name__ == "__main__":
    main()
