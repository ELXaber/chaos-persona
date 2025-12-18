# =============================================================================
# Chaos AI-OS Paradox Oscillation Layer (CPOL) vΩ - FIXED
# Added: Evidence scoring, domain extraction, proper non-collapse classification
# =============================================================================

import cmath
import math
from typing import Dict, Any, List
import re

class CPOL_Kernel:
    def __init__(self,
                 oscillation_limit_init: int = 100,
                 oscillation_limit_run: int = 50,
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
        self.call_count = 0
        
        # NEW: Evidence and domain tracking
        self.evidence_score = 0.0
        self.axiom_verified_absent = False
        self.current_domain = "general"
        self.new_domain_detected = False
        
        # Constants
        self.gain = 0.12
        self.decay = 0.95
        
    def get_state(self) -> Dict[str, Any]:
        return {
            'z': str(self.z),
            'history': [str(h) for h in self.history],
            'call_count': self.call_count,
            'contradiction_density': self.contradiction_density,
            'evidence_score': self.evidence_score,
            'current_domain': self.current_domain
        }

    def set_state(self, state: Dict[str, Any]):
        if not state:
            return
        self.z = complex(state.get('z', 0.0 + 0.0j))
        self.history = [complex(h) for h in state.get('history', [])]
        self.call_count = state.get('call_count', 0)
        self.contradiction_density = state.get('contradiction_density', 0.0)
        self.evidence_score = state.get('evidence_score', 0.0)
        self.current_domain = state.get('current_domain', 'general')

    def inject(self, confidence: float = 0.0, contradiction_density: float = 0.0, 
               query_text: str = ""):
        """Enhanced inject with domain detection and evidence scoring."""
        self.z = complex(confidence, 0.0)
        self.history = [self.z]
        self.cycle = 0
        self.contradiction_density = max(0.0, min(1.0, contradiction_density))
        self.call_count += 1
        
        # NEW: Extract domain and score evidence
        self.current_domain = self._extract_domain(query_text)
        self.evidence_score = self._score_evidence(query_text)
        self.axiom_verified_absent = self._check_axiom_absence(query_text)
        
        # Detect if this is a new/unfamiliar domain
        known_domains = {'math', 'physics', 'chemistry', 'biology', 'history', 
                        'literature', 'programming', 'logic', 'ethics'}
        self.new_domain_detected = self.current_domain not in known_domains

    def _extract_domain(self, text: str) -> str:
        """Simple domain classifier - replace with ML for production."""
        text_lower = text.lower()
        
        domain_keywords = {
            'math': ['equation', 'calculate', 'integral', 'derivative', 'proof'],
            'physics': ['force', 'energy', 'momentum', 'quantum', 'particle'],
            'programming': ['code', 'function', 'algorithm', 'debug', 'compile'],
            'ethics': ['moral', 'ethical', 'right', 'wrong', 'should'],
            'logic': ['paradox', 'contradiction', 'valid', 'inference', 'premise'],
        }
        
        for domain, keywords in domain_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return domain
        
        # Extract noun phrases as potential new domain
        words = text_lower.split()
        if len(words) > 2:
            return words[0]  # First word as proxy
        return "general"
    
    def _score_evidence(self, text: str) -> float:
        """Score query for factual evidence/grounding."""
        text_lower = text.lower()
        
        # High evidence indicators
        evidence_markers = ['according to', 'research shows', 'data indicates', 
                          'study found', 'proven', 'verified', 'measured']
        
        # Low evidence indicators (opinion/speculation)
        speculation_markers = ['maybe', 'perhaps', 'could be', 'might', 
                              'i think', 'possibly', 'what if']
        
        evidence_count = sum(1 for m in evidence_markers if m in text_lower)
        speculation_count = sum(1 for m in speculation_markers if m in text_lower)
        
        base_score = 0.5
        base_score += 0.1 * evidence_count
        base_score -= 0.15 * speculation_count
        
        return max(0.0, min(1.0, base_score))
    
    def _check_axiom_absence(self, text: str) -> bool:
        """Check if query references concepts without established axioms."""
        text_lower = text.lower()
        
        # Markers of undefined/ungrounded concepts
        undefined_markers = ['suppose that', 'imagine if', 'what would happen',
                            'hypothetically', 'in a world where', 'if we assume']
        
        return any(m in text_lower for m in undefined_markers)

    def _truth_seer(self, z):   
        return z + self.gain * (1.0 - z.real)
    
    def _lie_weaver(self, z):   
        return z - self.gain * (1.0 + z.real)

    def _entropy_knower(self, z):
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
        """Run oscillation with proper non-collapse classification."""
        
        # Respect ARL override
        override_mode = getattr(self, 'cpol_mode', None)
        if override_mode == 'monitor_only':
            return {
                "status": "MONITORED",
                "reason": "CPOL in monitor-only mode",
                "volatility": self._measure_volatility(),
                "final_z": str(self.z),
                "contradiction_density": self.contradiction_density,
                "domain": self.current_domain
            }

        limit = self.limit_init if self.call_count == 1 else self.limit_run
        
        for self.cycle in range(1, limit + 1):
            # The Cycle
            z = self._truth_seer(self.z)
            z = self._lie_weaver(z)
            z = self._entropy_knower(z)
            z *= self.decay
            self.z = z

            # History Management
            self.history.append(self.z)
            if len(self.history) > self.history_cap:
                self.history.pop(0)

            # Check for Collapse
            volatility = self._measure_volatility()
            
            if volatility < self.threshold and len(self.history) >= self.history_cap:
                real = self.z.real

                # Prevent collapse in neutral zone with high density
                if abs(real) < 0.5 and self.contradiction_density > 0.7:
                    continue
                    
                verdict = "TRUE" if real > 0.5 else "FALSE" if real < -0.5 else "NEUTRAL"
                return {
                    "status": "RESOLVED",
                    "verdict": verdict,
                    "confidence": abs(real),
                    "volatility": volatility,
                    "final_z": str(self.z),
                    "domain": self.current_domain
                }
                        
            # Safety Hard Cap
            if self.cycle >= 60:
                break

        # === UNDECIDABLE PATH - PROPER CLASSIFICATION ===
        non_collapse_reason = self._classify_non_collapse()
        
        return {
            "status": "UNDECIDABLE",
            "reason": "Persistent Gain/Loss Oscillation",
            "volatility": self._measure_volatility(),
            "final_z": str(self.z),
            "chaos_lock": True,
            "non_collapse_reason": non_collapse_reason,
            "domain": self.current_domain,
            "evidence_score": self.evidence_score,
            "new_domain": self.new_domain_detected
        }
    
    def _classify_non_collapse(self) -> str:
        """
        Classify WHY oscillation didn't collapse using the taxonomy:
        {epistemic_gap, paradox, ontological_error, structural_noise}
        """
        # Priority 1: Ontological error (no axioms exist)
        if self.evidence_score == 0.0 and self.axiom_verified_absent:
            return "ontological_error"
        
        # Priority 2: True paradox (high contradiction density)
        if self.contradiction_density > 0.85:
            return "paradox"
        
        # Priority 3: Epistemic gap (new domain, low contradiction)
        if self.new_domain_detected and self.contradiction_density < 0.4:
            return "epistemic_gap"
        
        # Default: Structural noise (ambiguity, unclear query)
        return "structural_noise"


# =============================================================================
# Tool Hook
# =============================================================================
def run_cpol_decision(prompt_complexity: str = "high", 
                      contradiction_density: float = None,
                      kernel: CPOL_Kernel = None,
                      query_text: str = "") -> Dict[str, Any]:
    """Entry point with query text for domain extraction."""
    
    if contradiction_density is not None:
        density = max(0.0, min(1.0, contradiction_density))
    else:
        density_map = {"high": 1.0, "medium": 0.5, "low": 0.1}
        density = density_map.get(prompt_complexity.lower(), 1.0)
    
    if kernel is None:
        engine = CPOL_Kernel()
    else:
        engine = kernel
     
    engine.inject(confidence=0.0, contradiction_density=density, query_text=query_text)
    
    print(f"[CPOL] Domain: {engine.current_domain} | Density: {density:.2f} | Evidence: {engine.evidence_score:.2f}")
    result = engine.oscillate()
    print(f"[CPOL] Result: {result['status']}")
    
    return result


if __name__ == "__main__":
    # Test epistemic gap detection
    result = run_cpol_decision(
        contradiction_density=0.3,
        query_text="How do quantum semantics affect blockchain ontology in post-scarcity economies?"
    )
    print(f"\nNon-collapse reason: {result.get('non_collapse_reason')}")
    print(f"Domain: {result.get('domain')}")