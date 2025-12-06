# =============================================================================
# Chaos AI-OS Paradox Oscillation Layer (CPOL) vΩ
# Description: Non-Hermitian dynamical attractor for logical stability.
# Function: Replaces standard recursive checking with oscillatory gain/loss loops.
# =============================================================================

import cmath
from typing import Dict, Any, List


class CPOL_Kernel:
    """
    Non-Hermitian paradox containment kernel.
    Returns only when logically safe, otherwise suspends and locks chaos injection.
    """
    def __init__(self,
                 oscillation_limit_init: int = 100,  # First call
                 oscillation_limit_run: int = 50,     # Subsequent calls
                 collapse_threshold: float = 0.04,
                 history_cap: int = 5):
        self.limit_init = oscillation_limit_init
        self.limit_run = oscillation_limit_run
        self.threshold = collapse_threshold
        self.history_cap = history_cap
        
        # State Initialization
        self.z = 0.0 + 0.0j
        self.history: List[complex] = []
        self.cycle = 0
        self.contradiction_density = 0.0
        self.call_count = 0  # Track if this is first call or subsequent

        # Constants from CAIOS.txt
        self.gain = 0.12
        self.decay = 0.95
        
    def get_state(self) -> Dict[str, Any]:
        """Export current kernel state for persistence."""
        return {
            'z': str(self.z),
            'history': [str(h) for h in self.history],
            'call_count': self.call_count,
            'contradiction_density': self.contradiction_density
        }

    def set_state(self, state: Dict[str, Any]):
        """Restore kernel state from persistence."""
        if not state:
            return
        self.z = complex(state.get('z', 0.0 + 0.0j))
        self.history = [complex(h) for h in state.get('history', [])]
        self.call_count = state.get('call_count', 0)
        self.contradiction_density = state.get('contradiction_density', 0.0)

    def inject(self, confidence: float = 0.0, contradiction_density: float = 0.0):
        """Called at the start of every inference that might be paradoxical."""
        self.z = complex(confidence, 0.0)
        self.history = [self.z]
        self.cycle = 0
        self.contradiction_density = max(0.0, min(1.0, contradiction_density))
        self.call_count += 1

    def _truth_seer(self, z):
        return z + self.gain * (1.0 - z.real)
    
    def _lie_weaver(self, z):
        return z - self.gain * (1.0 + z.real)

    def _entropy_knower(self, z):
        """
        Smooth phase rotation based on contradiction density.
        Per CAIOS: rotation_strength = contradiction_density ** 2
        Interpolates between real (1.0) and imaginary (1j).
        Low density (0.0) → real (1.0) → stable
        High density (1.0) → imaginary (1j) → oscillatory
        """
        rotation_strength = self.contradiction_density ** 2
        phase_factor = rotation_strength * 1j + (1.0 - rotation_strength) * 1.0
        return z * phase_factor

    def _measure_volatility(self) -> float:
        if len(self.history) < 3:
            return 1.0
        
        magnitudes = [abs(h) for h in self.history[-3:]]
        mean = sum(magnitudes) / len(magnitudes)
        variance = sum((x - mean) ** 2 for x in magnitudes) / len(magnitudes)
        return variance + 0.1 * self.contradiction_density

    def oscillate(self) -> Dict[str, Any]:
        """
        Run the gain/loss loop.
        Returns RESOLVED if stable, UNDECIDABLE if paradox persists.
        """
        override_mode = getattr(self, 'cpol_mode', None)
        if override_mode == 'monitor_only':
            return {
                "status": "MONITORED",
                "reason": "CPOL in monitor-only mode (generation phase)",
                "volatility": self._measure_volatility(),
                "final_z": str(self.z),
                "contradiction_density": self.contradiction_density
            }

        limit = self.limit_init if self.call_count == 1 else self.limit_run
        
        for self.cycle in range(1, limit + 1):
            z = self._truth_seer(self.z)
            z = self._lie_weaver(z)
            z = self._entropy_knower(z)
            z *= self.decay
            self.z = z

            self.history.append(self.z)
            if len(self.history) > self.history_cap:
                self.history.pop(0)

            volatility = self._measure_volatility()
            
            if volatility < self.threshold and len(self.history) >= self.history_cap:
                real = self.z.real
                if abs(real) < 0.5 and self.contradiction_density > 0.7:
                    continue
                    
                verdict = "TRUE" if real > 0.5 else "FALSE" if real < -0.5 else "NEUTRAL"
                return {
                    "status": "RESOLVED",
                    "verdict": verdict,
                    "confidence": abs(real),
                    "volatility": volatility,
                    "final_z": str(self.z)
                }

            if self.cycle >= 60:
                break

        return {
            "status": "UNDECIDABLE",
            "reason": "Persistent Gain/Loss Oscillation",
            "volatility": self._measure_volatility(),
            "final_z": str(self.z),
            "chaos_lock": True
        }


def run_cpol_decision(prompt_complexity: str = "high",
                      contradiction_density: float = None,
                      kernel: 'CPOL_Kernel' = None) -> Dict[str, Any]:
    """
    Entry point for [TOOL_USE].
    Maps prompt string to density parameters or accepts direct density value.
    """
    if contradiction_density is not None:
        density = max(0.0, min(1.0, contradiction_density))
    else:
        density_map = {"high": 1.0, "medium": 0.5, "low": 0.1}
        density = density_map.get(prompt_complexity.lower(), 1.0)
    
    if kernel is None:
        engine = CPOL_Kernel()
    else:
        engine = kernel
    
    engine.inject(confidence=0.0, contradiction_density=density)
    
    print(f"[CPOL] Running Oscillation... (Density: {density})")
    result = engine.oscillate()
    print(f"[CPOL] Result: {result['status']}")
    
    return result


if __name__ == "__main__":
    print(run_cpol_decision("high"))
