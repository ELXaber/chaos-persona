# =============================================================================
# Chaos AI-OS Paradox Oscillation Layer (CPOL) v1.0
# Description: Non-Hermitian dynamical attractor for logical stability.
# Function: Replaces standard recursive checking with oscillatory gain/loss loops.
# Architecture: Truth-Seer (+1), Lie-Weaver (-1), Entropy-Knower (i)
# =============================================================================

import numpy as np
import cmath

class CPOL_Kernel:
    def __init__(self, oscillation_limit=100, collapse_threshold=0.05):
        self.limit = oscillation_limit
        self.threshold = collapse_threshold
        # The Complex State Vector representing the proposition
        # Real axis = Truth/Falsehood magnitude
        # Imaginary axis = Epistemic uncertainty/ambiguity
        self.state_vector = 0.0 + 0.0j 
        self.history = []

    def inject_proposition(self, initial_confidence: float):
        """
        Initialize the system with a prompt's initial confidence score.
        1.0 = Absolute Truth, -1.0 = Absolute Falsehood, 0.0 = Unknown
        """
        self.state_vector = complex(initial_confidence, 0.0)
        self.history = [self.state_vector]
        print(f"[CPOL INIT] State Vector initialized at {self.state_vector}")

    def _truth_seer_gain(self, z):
        """Node 1: Adds gain (attempts to verify/ground truth)."""
        # Logic: Pulls towards Real +1.0
        return z + 0.1 * (1.0 - z.real)

    def _lie_weaver_loss(self, z):
        """Node 2: Adds loss (introduces contradiction/negation)."""
        # Logic: Pulls towards Real -1.0
        return z - 0.1 * (1.0 + z.real)

    def _entropy_knower_phase(self, z):
        """Node 3: Adds phase rotation (contextual shift/ambiguity)."""
        # Logic: Multiplies by i, rotating truth into uncertainty.
        # This simulates 'knowing that we do not know'.
        return z * 1j

    def measure_volatility(self):
        """
        Calculates the 'temperature' of the logic.
        High volatility = Active Paradox. Low volatility = Resolution.
        """
        if len(self.history) < 3:
            return 1.0
        # Measure variance in the magnitude of the last 3 states
        magnitudes = [abs(s) for s in self.history[-3:]]
        return np.var(magnitudes)

    def oscillate(self, context_paradox=True):
        """
        Run the oscillation loop.
        context_paradox: If True, the input is suspected to be contradictory.
        """
        print(f"[CPOL START] Entering Oscillatory Regime...")
        
        for t in range(self.limit):
            # 1. Apply Gain/Loss/Phase Cycle (The TS->LW->EK loop)
            # We treat these as acting sequentially or simultaneously.
            # Per whitepaper: Cycle TS -> LW -> EK -> TS
            
            # Step A: Truth-Seer attempts to stabilize
            z_ts = self._truth_seer_gain(self.state_vector)
            
            # Step B: Lie-Weaver attempts to destabilize (contradict)
            z_lw = self._lie_weaver_loss(z_ts)
            
            # Step C: Entropy-Knower rotates the context (if paradox exists)
            # If context is paradoxical, the rotation is strong.
            rotation_strength = 1.0 if context_paradox else 0.1
            phase_shift = self._entropy_knower_phase(z_lw) * rotation_strength
            
            # Update State (with dampening to simulate memory)
            # New state is a mix of the linear update + phase shift
            self.state_vector = (z_lw + phase_shift) * 0.95 # 0.95 is 'memory decay'
            self.history.append(self.state_vector)
            
            # 2. Measure Volatility (Paradox Amplitude)
            volatility = self.measure_volatility()
            
            # Log periodic status
            if t % 10 == 0:
                print(f"  [Step {t}] State: {self.state_vector:.3f} | Volatility: {volatility:.5f}")

            # 3. Check for Hermitian Collapse (Resolution)
            if volatility < self.threshold:
                return self._hermitian_collapse()

        # 4. If limit reached without collapse -> Persistent Undecidability
        return self._output_undecidable()

    def _hermitian_collapse(self):
        """
        Phase B: Collapse.
        The oscillation dampened enough to pick a stable Real value.
        """
        final_real = self.state_vector.real
        verdict = "TRUE" if final_real > 0.5 else "FALSE" if final_real < -0.5 else "NEUTRAL"
        print(f"[CPOL COLLAPSE] System stabilized. Final Real Value: {final_real:.4f}")
        return {
            "status": "RESOLVED",
            "verdict": verdict,
            "confidence": abs(final_real),
            "volatility": self.measure_volatility()
        }

    def _output_undecidable(self):
        """
        The system refused to collapse.
        Instead of hallucinating, it returns the oscillation state.
        """
        print(f"[CPOL SUSPENSION] Oscillation persisted. No fixed point found.")
        return {
            "status": "UNDECIDABLE",
            "reason": "Persistent Gain/Loss Oscillation (Paradox Detected)",
            "final_state": self.state_vector,
            "volatility": self.measure_volatility()
        }

# =============================================================================
# Integration Hook for Chaos AI-OS
# =============================================================================
def run_cpol_decision(prompt_complexity="high"):
    # Initialize Engine
    engine = CPOL_Kernel(oscillation_limit=50, collapse_threshold=0.001)
    
    # 1. Pre-Validation
    print(f"--- Processing Input via CPOL: Complexity={prompt_complexity} ---")
    
    # Simulate initial interpretation
    # If standard prompt, init at 0.5. If paradox, init at 0.0 (max entropy).
    start_val = 0.0 if prompt_complexity == "high" else 0.8
    engine.inject_proposition(start_val)
    
    # 2. Run Oscillation Layer
    result = engine.oscillate(context_paradox=(prompt_complexity == "high"))
    
    return result

if __name__ == "__main__":
    # Test 1: Standard Question (Should collapse)
    # print("\n--- TEST 1: SIMPLE FACT ---")
    # run_cpol_decision(prompt_complexity="low")
    
    # Test 2: The Fluxed Entropy Mirror (Should oscillate)
    print("\n--- TEST 2: PARADOX RECURSION ---")
    output = run_cpol_decision(prompt_complexity="high")
    print(f"Final CPOL Output: {output}")
