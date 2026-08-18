import numpy as np
from collections import defaultdict
import networkx as nx  # For belief graph cycle detection

# Sensor-Actuator Unit
class SensorActuator:
    def __init__(self, id, position):
        self.id = id
        self.position = position  # (x, y, z) on bridge
        self.role = "monitor"  # Initial role
        self.belief_map = {}  # {coord: (type, confidence)} e.g., {(x,y,z): ("microfracture", 0.9)}
        self.rules = defaultdict(float)  # {rule: weight} e.g., {"IF microfracture THEN reduce_tension": 0.8}
        self.goals = []  # [(goal, priority)] e.g., [("reduce tension at (x,y,z)", 0.9)]
        self.trust_scores = defaultdict(float)  # {unit_id: trust}
        self.history = []  # [(step, action, outcome)]
        self.time_step = 0

    def sense_environment(self):
        # Simulate sensor data (strain, vibration, acoustic)
        sensor_data = {
            "stress": detect_stress(self.position),  # e.g., {(x,y,z): value}
            "tremors": detect_tremors(self.position),  # e.g., {(x,y,z): (freq, amp)}
            "microfractures": detect_microfractures(self.position)  # e.g., {(x,y,z): confidence}
        }
        self.update_belief_map(sensor_data)
        return sensor_data

    def update_belief_map(self, sensor_data):
        # Merge sensor data with belief map
        for coord, (type_, conf) in sensor_data.items():
            if coord in self.belief_map:
                old_conf = self.belief_map[coord][1]
                self.belief_map[coord] = (type_, max(conf, old_conf))
            else:
                self.belief_map[coord] = (type_, conf)

    def communicate(self, peers):
        # Share position, role, goals, and belief map with peers in range
        broadcast = {
            "id": self.id,
            "position": self.position,
            "role": self.role,
            "goals": self.goals,
            "belief_map": self.belief_map
        }
        # Receive peer broadcasts
        peer_data = [peer.broadcast() for peer in peers if in_range(self.position, peer.position)]
        self.update_trust_scores(peer_data)
        self.merge_peer_data(peer_data)
        return broadcast

    def update_trust_scores(self, peer_data):
        # Update trust based on consistency, success, reciprocity
        for peer in peer_data:
            consistency = compute_consistency(self.goals, peer["goals"])
            success = compute_success(peer["history"])
            reciprocity = peer["trust_scores"].get(self.id, 0.5)
            self.trust_scores[peer["id"]] = 0.4 * consistency + 0.4 * success + 0.2 * reciprocity

    def merge_peer_data(self, peer_data):
        # Merge peer belief maps with trust-weighted confidence
        for peer in peer_data:
            trust = self.trust_scores[peer["id"]]
            for coord, (type_, conf) in peer["belief_map"].items():
                if coord in self.belief_map:
                    self_conf = self.belief_map[coord][1]
                    new_conf = (trust * conf + self_conf) / (trust + 1)
                    self.belief_map[coord] = (type_, new_conf)
                else:
                    self.belief_map[coord] = (type_, trust * conf)

    def detect_paradox(self):
        # Build belief graph
        G = nx.DiGraph()
        for rule, weight in self.rules.items():
            condition, action = parse_rule(rule)
            G.add_edge(condition, action, weight=weight)
        # Check for cycles
        cycles = list(nx.simple_cycles(G))
        if cycles:
            # Resolve by reducing weight of least-trusted rule
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
                print(f"[PARADOX DETECTED @ step {self.time_step} → Cycle: {cycle}]")
        # Check divergence with peers
        divergence = compute_divergence(self.belief_map, [peer["belief_map"] for peer in peer_data])
        if divergence > 0.5:
            self.reprioritize_goals()
            print(f"[HIGH DIVERGENCE @ step {self.time_step} → Divergence: {divergence}]")

    def evaluate_rules(self):
        # Score rules based on integrity, feasibility, synergy
        for rule, weight in self.rules.items():
            integrity = check_structural_integrity(rule, self.belief_map)
            feasibility = check_actuator_feasibility(rule)
            synergy = check_team_synergy(rule, peer_data, self.trust_scores)
            score = 0.5 * integrity + 0.3 * feasibility + 0.2 * synergy
            self.rules[rule] = score
            # Prune low-scoring or high-volatility rules
            volatility = 0.5 * (1 - integrity) + 0.3 * (1 - feasibility) + 0.2 * (1 - synergy)
            if score < 0.3 or volatility > 0.6:
                del self.rules[rule]
                print(f"[PRUNE @ step {self.time_step} → Rule: {rule}, Score: {score}, Volatility: {volatility}]")

    def reprioritize_goals(self):
        # Recompute goal priorities based on belief map and peer data
        self.goals = []
        for coord, (type_, conf) in self.belief_map.items():
            if type_ == "microfracture":
                priority = 0.5 * conf + 0.3 * action_feasibility(coord) + 0.2 * team_synergy(coord, peer_data)
                self.goals.append(("reduce tension at " + str(coord), priority))
            elif type_ == "tremor":
                priority = 0.5 * conf + 0.3 * action_feasibility(coord) + 0.2 * team_synergy(coord, peer_data)
                self.goals.append(("dampen vibration at " + str(coord), priority))
        self.goals.sort(key=lambda x: x[1], reverse=True)

    def adapt_role(self):
        # Update role based on goals and team state
        microfracture_goals = [g for g, p in self.goals if "microfracture" in g]
        tremor_goals = [g for g, p in self.goals if "tremor" in g]
        team_roles = [peer["role"] for peer in peer_data]
        if microfracture_goals and sum(1 for r in team_roles if r == "tension_adjuster") < len(team_roles) / 2:
            self.role = "tension_adjuster"
        elif tremor_goals and sum(1 for r in team_roles if r == "vibration_damper") < len(team_roles) / 2:
            self.role = "vibration_damper"
        else:
            self.role = "monitor"
        print(f"[ROLE UPDATE @ step {self.time_step} → New role: {self.role}]")

    def execute_action(self):
        # Select highest-priority goal and execute
        if not self.goals:
            action = "monitor"
        else:
            goal, _ = self.goals[0]
            action = select_action(goal, self.rules, self.position)
        outcome = perform_action(action, self.position, self.belief_map)
        self.history.append((self.time_step, action, outcome))
        return action, outcome

    def run(self, peers):
        self.time_step += 1
        sensor_data = self.sense_environment()
        peer_data = self.communicate(peers)
        self.detect_paradox()
        self.evaluate_rules()
        self.reprioritize_goals()
        self.adapt_role()
        action, outcome = self.execute_action()
        print(f"[ACTION @ step {self.time_step} → Unit {self.id}: {action}, Outcome: {outcome}]")

# Helper functions (simulated)
def detect_stress(pos): return {}  # Simulated strain data
def detect_tremors(pos): return {}  # Simulated vibration data
def detect_microfractures(pos): return {}  # Simulated acoustic data
def in_range(pos1, pos2): return np.linalg.norm(np.array(pos1) - np.array(pos2)) < 50
def compute_consistency(goals1, goals2): return 0.8  # Simulated
def compute_success(history): return 0.7  # Simulated
def compute_divergence(map1, maps): return 0.3  # Simulated
def check_structural_integrity(rule, belief_map): return 0.9  # Simulated
def check_actuator_feasibility(rule): return 0.8  # Simulated
def check_team_synergy(rule, peer_data, trust_scores): return 0.7  # Simulated
def parse_rule(rule): return rule.split(" THEN ")[0][3:], rule.split(" THEN ")[1]
def action_feasibility(coord): return 0.9  # Simulated
def team_synergy(coord, peer_data): return 0.7  # Simulated
def select_action(goal, rules, position): return "execute_" + goal.split(" at ")[0]  # Simulated
def perform_action(action, position, belief_map): return "success"  # Simulated

# Main simulation loop
def main():
    units = [SensorActuator(i, (0, 0, 0)) for i in range(50)]  # 50 units
    for step in range(100):  # Run for 100 steps
        for unit in units:
            unit.run(units)

if __name__ == "__main__":
    main()
