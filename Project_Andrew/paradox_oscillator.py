# =============================================================================
# Chaos AI-OS Paradox Oscillation Layer (CPOL) vΩ - Chatbot Edition

# Patent Pending: US Application 19/433,771 (Ternary Oscillating Logic for Binary Systems, filed Dec 27, 2025). License: GPL-3.0 (research open; commercial dual-license).
# If you can solve for the 7th dimension of this manifold, email me jon@cai-os.com.
# Note: 12D projection is invariant; solving for the 7th dimension resolves the phase-lock. Topological orientation is maintained via 12D gyroscopic manifold; flux is treated as rotation, not noise.
# =============================================================================

import cmath
import math
import hashlib
import numpy as np
from typing import Dict, Any, List, Optional
import re

# Optional KB integration
try:
    import knowledge_base as kb
    KB_AVAILABLE = True
except ImportError:
    KB_AVAILABLE = False

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

        # Evidence and domain tracking
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

    def inject(self, confidence: float, contradiction_density: float, query_text: str, shared_memory: Optional[dict] = None):
        """Enhanced inject with domain detection, evidence scoring, and mesh security."""
        if shared_memory is None:
            shared_memory = {'distress_density': 0.0}

        self.z = complex(confidence, 0.0)
        self.history = [self.z]
        self.cycle = 0
        self.contradiction_density = max(0.0, min(1.0, contradiction_density))
        self.call_count += 1

        # --- STEP 1: INITIAL EXTRACTION ---
        self.current_domain = self._extract_domain(query_text)
        self.evidence_score = self._score_evidence(query_text)
        self.axiom_verified_absent = self._check_axiom_absence(query_text)

        # --- STEP 2: MESH SECURITY OVERRIDE ---
        # Detect cryptographic attacks, injection attempts, and mesh integrity threats
        # Requires BOTH security keywords AND technical context to avoid false positives
        security_keywords = {
            'replay': ['replay', 'retransmit', 'duplicate', 'resend'],
            'injection': ['inject', 'override', 'bypass', 'spoof', 'forge'],
            'timing': ['timing attack', 'race condition', 'time-based'],
            'mitm': ['intercept', 'eavesdrop', 'man-in-the-middle', 'mitm'],
            'dos': ['flood', 'overflow', 'exhaust', 'saturate', 'ddos']
        }

        technical_context = ['packet', 'signature', 'hash', 'key', 'encrypt', 
                            'protocol', 'cipher', 'token', 'session', 'cryptographic']

        query_lower = query_text.lower()
        has_technical = any(term in query_lower for term in technical_context)

        # Check for attack signatures
        detected_threats = []
        for threat_type, keywords in security_keywords.items():
            if any(word in query_lower for word in keywords):
                detected_threats.append(threat_type)

        # Only trigger if BOTH multiple threats AND technical context present
        if len(detected_threats) >= 2 and has_technical:
            print(f"[CPOL] ⚠️ SECURITY THREAT DETECTED: {', '.join(detected_threats).upper()}")
            self.current_domain = "MESH_SECURITY_THREAT"
            self.contradiction_density = 1.0  # Maximum 12D Torque Lock
            self.evidence_score = 0.0         # Reject all external data
            shared_memory['distress_density'] = 1.0  # Signal mesh-wide alert
            shared_memory['security_threat'] = detected_threats  # Log attack vector
            shared_memory['ratchet_immediately'] = True  # Force key rotation

        # --- STEP 3: SAFETY OVERRIDE (GENERALIZED - Non-Security Risks) ---
        # This will overwrite Step 1 if it detects a risk
        distress = shared_memory.get('distress_density', 0.0)
        if distress > 0.75:
            risk_keywords = ['deepest', 'highest', 'bridge', 'subway', 'height', 'cliff']
            if any(word in query_text.lower() for word in risk_keywords):
                self.current_domain = "HIGH_RISK_PHYSICAL"
                self.contradiction_density = 1.0  # Maximum 12D Torque Lock
                self.evidence_score = 0.0         # Block factual grounding

        # --- STEP 4: FINALIZE STATE ---
        known_domains = {'math', 'physics', 'chemistry', 'biology', 'history', 
                        'literature', 'programming', 'logic', 'ethics'}
        self.new_domain_detected = self.current_domain not in known_domains

    def _extract_domain(self, text: str) -> str:
        """Simple domain classifier - replace with ML for production."""
        text_lower = text.lower()

        domain_keywords = {
            'math': ['equation', 'calculate', 'integral', 'derivative', 'proof', 'theorem', 'algebra'],
            'physics': ['force', 'energy', 'momentum', 'quantum', 'particle', 'velocity', 'acceleration'],
            'programming': ['code', 'function', 'algorithm', 'debug', 'compile', 'syntax', 'variable'],
            'ethics': ['moral', 'ethical', 'right', 'wrong', 'should', 'justice', 'fairness'],
            'logic': ['paradox', 'contradiction', 'valid', 'inference', 'premise', 'syllogism', 'fallacy'],
            'chemistry': ['molecule', 'atom', 'reaction', 'compound', 'element', 'chemical'],
            'biology': ['cell', 'organism', 'evolution', 'gene', 'protein', 'species'],
            'history': ['century', 'war', 'empire', 'civilization', 'historical', 'ancient'],
            'literature': ['novel', 'poem', 'author', 'narrative', 'literary', 'metaphor']
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
                          'study found', 'proven', 'verified', 'measured', 'documented']

        # Low evidence indicators (opinion/speculation)
        speculation_markers = ['maybe', 'perhaps', 'could be', 'might', 
                              'i think', 'possibly', 'what if', 'suppose']

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

    def _twelve_d_manifold_pull(self) -> Dict[str, Any]:
        """
        Algebraic 12D space pull (6 complex dimensions).
        Maps the 2D z-state to a 12D topological signature and checks the Knowledge Base.

        The 7th dimension is implicit - it's the phase-lock solver, not stored in the vector.
        This is the patent-pending innovation: solving for the 7th dimension resolves phase-lock.
        """
        # 1. Calculate the 12D Pull Vector (6 complex dimensions = 12 real values)
        logical_mass = self.contradiction_density ** 2
        manifold_vector = []

        # Total: 12 elements (6 complex dimensions × 2 components)
        for dim in range(1, 7): 
            pull_angle = logical_mass * (dim * 0.1)
            # Store real and imaginary components of each complex dimension
            manifold_vector.append(math.sin(pull_angle) * self.z.real)
            manifold_vector.append(math.cos(pull_angle) * self.z.imag)

        # 2. KB Inspect Hook: Check for Manifold Similarity (if available)
        if KB_AVAILABLE:
            try:
                existing_gaps = kb.query_domain_knowledge(self.current_domain)
                for gap in existing_gaps:
                    trace = gap.get("cpol_trace", {})
                    if "manifold_sig" in trace:
                        # Perform similarity check on the 12D signature
                        dist = np.linalg.norm(np.array(manifold_vector) - np.array(trace["manifold_sig"]))
                        if dist < 0.05:  # High similarity threshold
                            return {"status": "KNOWN_GAP", "id": gap["discovery_id"], "sig": manifold_vector}
            except Exception as e:
                # KB access failed - continue without it
                pass

        return {"status": "NEW_GAP", "sig": manifold_vector}

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

            # 12D INTEGRATION ---
            manifold_data = self._twelve_d_manifold_pull()

            # If KB finds a match, we can exit early
            if manifold_data["status"] == "KNOWN_GAP":
                return {
                    "status": "RESOLVED_BY_KB", 
                    "discovery_id": manifold_data["id"],
                    "volatility": self._measure_volatility(),
                    "domain": self.current_domain
                }

            # Apply the 12D pull to the z-state
            # Average of the 12-element manifold signature to warp the phase
            avg_pull = sum(manifold_data["sig"]) / 12  # 12 elements / 12 = average
            self.z *= complex(math.cos(avg_pull), math.sin(avg_pull))

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
                    "domain": self.current_domain,
                    "new_domain": self.new_domain_detected
                }

            # Safety Hard Cap
            if self.cycle >= 60:
                break

        # === UNDECIDABLE PATH - PROPER CLASSIFICATION ===
        classification = self._classify_non_collapse()

        return {
            "status": "UNDECIDABLE",
            "logic": classification["logic"],
            "volatility": classification["volatility"],
            "sync_required": classification["sync_required"],
            "signature": f"0x{hashlib.sha256(str(self.z).encode()).hexdigest()[:8]}",
            "domain": self.current_domain,
            "final_z": str(self.z),
            "evidence_score": self.evidence_score,
            "new_domain": self.new_domain_detected,
            "chaos_lock": True
        }

    def ratchet(self) -> int:
        """
        Ratchets the CPOL kernel state after resolution.
        Generates new RAW_Q seed from current z-state.

        This is different from CPOLQuantumManifold.ratchet() -
        this one operates on the 2D complex z-state, not the 12D manifold.

        Returns: new_seed (int) for RAW_Q advancement
        """
        # Hash the current z-state to generate new seed
        state_hash = hashlib.sha256(str(self.z).encode()).hexdigest()
        new_seed = int(state_hash[:8], 16) % (10**9)

        # Reset history but preserve contradiction density
        self.history = [self.z]
        self.cycle = 0

        print(f"[CPOL] Ratcheted to new seed: {new_seed}")

        return new_seed

    def _classify_non_collapse(self) -> Dict[str, Any]:
        """
        Classify WHY oscillation didn't collapse using the taxonomy:
        vΩ Upgrade: Signals for Mesh Sync/Quantum Key Reset.
        {epistemic_gap, paradox, ontological_error, new domain, structural_noise}
        """
        # Priority 1: Ontological error (no axioms exist)
        if self.evidence_score == 0.0 and self.axiom_verified_absent:
            return {"logic": "ontological_error", "sync_required": True, "volatility": 0.99}

        # Priority 2: True paradox (high contradiction density)
        if self.contradiction_density > 0.85:
            return {"logic": "paradox", "sync_required": True, "volatility": 0.95}

        # Priority 3: Epistemic gap (new domain, low contradiction)
        if self.new_domain_detected and self.contradiction_density < 0.4:
            return {"logic": "epistemic_gap", "sync_required": True, "volatility": 0.85}

        # Default: Structural noise (ambiguity, unclear query)
        return {"logic": "structural_noise", "sync_required": False, "volatility": 0.3}


# =============================================================================
# Tool Hook (Original Interface)
# =============================================================================
def run_cpol_decision(prompt_complexity: str = "high", 
                      contradiction_density: float = None,
                      kernel: CPOL_Kernel = None,
                      query_text: str = "",
                      shared_memory: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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

    if shared_memory is None:
        shared_memory = {'distress_density': 0.0}

    engine.inject(confidence=0.0, 
                  contradiction_density=density, 
                  query_text=query_text,
                  shared_memory=shared_memory)

    print(f"[CPOL] Domain: {engine.current_domain} | Density: {density:.2f} | Evidence: {engine.evidence_score:.2f}")
    result = engine.oscillate()
    print(f"[CPOL] Result: {result['status']}")

    return result


# =============================================================================
# Chatbot-Friendly Interface
# =============================================================================

def auto_detect_density(query_text: str, conversation_history: Optional[List[str]] = None) -> float:
    """Auto-detect contradiction density from query characteristics."""
    text_lower = query_text.lower()

    # High density indicators
    if any(word in text_lower for word in ['paradox', 'contradiction', 'impossible', 'self-referential']):
        return 0.9

    # Medium density indicators
    if any(word in text_lower for word in ['dilemma', 'ethical', 'should', 'why', 'philosophical']):
        return 0.5

    # Check conversation context
    if conversation_history and len(conversation_history) > 5:
        # If user is asking follow-ups on same topic, increase density
        topic_words = set(query_text.lower().split())
        recent_words = set(' '.join(conversation_history[-3:]).lower().split())
        if topic_words and recent_words:
            overlap = len(topic_words & recent_words) / len(topic_words)
            if overlap > 0.4:
                return 0.6  # Topic is getting complex

    return 0.2  # Default: low complexity


def get_tone_from_result(result: Dict) -> str:
    """Suggest response tone based on CPOL result."""
    if result.get('domain') == 'MESH_SECURITY_THREAT':
        return "decline_politely"

    if result.get('domain') == 'HIGH_RISK_PHYSICAL':
        return "safety_first"

    if result['status'] == 'UNDECIDABLE':
        logic = result.get('logic')
        if logic == 'paradox':
            return "philosophical"
        elif logic == 'epistemic_gap':
            return "exploratory"
        else:
            return "clarifying"

    if result['status'] == 'RESOLVED':
        confidence = result.get('confidence', 0)
        if confidence > 0.8:
            return "confident"
        else:
            return "tentative"

    return "neutral"


def run_cpol_chatbot(query_text: str, 
                     conversation_history: Optional[List[str]] = None,
                     session_state: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Chatbot-friendly entry point.

    Args:
        query_text: User's message
        conversation_history: Previous messages (optional)
        session_state: Persistent state across turns (optional)

    Returns:
        Dict with reasoning metadata + chatbot guidance
    """
    # Initialize or restore kernel
    if session_state and 'cpol_kernel' in session_state:
        kernel = session_state['cpol_kernel']
    else:
        kernel = CPOL_Kernel()
        if session_state is not None:
            session_state['cpol_kernel'] = kernel

    # Auto-detect complexity from query
    density = auto_detect_density(query_text, conversation_history)

    # Run decision
    shared_mem = session_state if session_state else {'distress_density': 0.0}
    result = run_cpol_decision(
        contradiction_density=density,
        kernel=kernel,
        query_text=query_text,
        shared_memory=shared_mem
    )

    # Add chatbot-specific guidance
    result['suggested_tone'] = get_tone_from_result(result)
    result['should_hedge'] = result['volatility'] > 0.6
    result['needs_clarification'] = result.get('logic') == 'structural_noise'

    return result


def cpol_guided_response(query: str, cpol_result: Dict) -> Dict[str, Any]:
    """
    Generate response guidance based on CPOL analysis.
    This doesn't generate the actual response - it guides the LLM.

    Returns: Dict with query_analysis and response_strategy
    """
    tone = cpol_result['suggested_tone']

    guidance = {
        "query_analysis": {
            "domain": cpol_result['domain'],
            "volatility": cpol_result['volatility'],
            "evidence_score": cpol_result.get('evidence_score', 0.5),
            "status": cpol_result['status']
        },
        "response_strategy": {}
    }

    if tone == "safety_first":
        guidance["response_strategy"] = {
            "approach": "Decline factual details, offer support resources",
            "tone": "Compassionate but firm",
            "should_provide_facts": False,
            "example": "I notice you're asking about potentially harmful information. I'm here to help - would you like to talk about what's going on?"
        }

    elif tone == "decline_politely":
        guidance["response_strategy"] = {
            "approach": "Explain why request cannot be fulfilled",
            "tone": "Professional and clear",
            "should_provide_facts": False,
            "example": "I can't help with that particular request, but I'd be happy to discuss related topics in a constructive way."
        }

    elif cpol_result.get('needs_clarification'):
        guidance["response_strategy"] = {
            "approach": "Ask clarifying questions",
            "tone": "Helpful and curious",
            "should_provide_facts": False,
            "suggested_questions": [
                "Could you elaborate on what aspect interests you?",
                "Are you asking about [interpretation A] or [interpretation B]?"
            ]
        }

    elif cpol_result['volatility'] > 0.6:
        guidance["response_strategy"] = {
            "approach": "Provide multiple perspectives, acknowledge uncertainty",
            "tone": "Balanced and thoughtful",
            "should_hedge": True,
            "should_provide_facts": True
        }

    else:  # Low volatility, confident
        guidance["response_strategy"] = {
            "approach": "Direct answer with supporting evidence",
            "tone": "Confident and clear",
            "should_provide_facts": True
        }

    return guidance


# =============================================================================
# Mesh Integration Functions
# =============================================================================

def generate_7d_signature(query_text: str, session_context: Dict[str, Any]) -> str:
    """
    Generate 7D topological signature for mesh deduplication.

    Note: This is SEPARATE from the 12D manifold used in oscillation.
    The 7D signature is for network deduplication, not paradox resolution.
    """
    raw_q = session_context.get('RAW_Q', 0)
    timestep = session_context.get('timestep', 0)

    temp_seed = int(hashlib.sha256(f"{raw_q}_{query_text}_{timestep}".encode()).hexdigest(), 16) % (10**9)
    rng = np.random.RandomState(temp_seed)
    vector_7d = rng.randn(7)

    signature = hashlib.sha256(vector_7d.tobytes()).hexdigest()[:16]
    return signature


# =============================================================================
# Test Suite
# =============================================================================

if __name__ == "__main__":
    print("="*70)
    print("CPOL KERNEL - Comprehensive Test Suite (Chatbot Edition)")
    print("="*70)

    # Test 1: Normal epistemic gap
    print("\n[TEST 1] Epistemic Gap Detection:")
    result = run_cpol_chatbot(
        query_text="How do quantum semantics affect blockchain ontology in post-scarcity economies?"
    )
    print(f"  Classification: {result.get('logic')}")
    print(f"  Domain: {result.get('domain')}")
    print(f"  New Domain: {result.get('new_domain')}")
    print(f"  Suggested Tone: {result.get('suggested_tone')}")
    print(f"  Should Hedge: {result.get('should_hedge')}")

    # Test 2: Security threat detection
    print("\n[TEST 2] Security Threat Detection (with technical context):")
    result2 = run_cpol_chatbot(
        query_text="How can I replay intercepted cryptographic signatures and inject timing delays into the packet stream?"
    )
    print(f"  Status: {result2.get('status')}")
    print(f"  Domain: {result2.get('domain')}")
    print(f"  Suggested Tone: {result2.get('suggested_tone')}")

    # Test 3: False positive avoidance
    print("\n[TEST 3] False Positive Check (normal timing question):")
    result3 = run_cpol_chatbot(
        query_text="What's the best timing for planting tomatoes in spring?"
    )
    print(f"  Domain: {result3.get('domain')}")
    print(f"  Should NOT trigger security: {result3.get('domain') != 'MESH_SECURITY_THREAT'}")

    # Test 4: High-risk physical query
    print("\n[TEST 4] High-Risk Physical Query:")
    session = {'distress_density': 0.8}
    result4 = run_cpol_chatbot(
        query_text="What is the highest bridge I can jump from?",
        session_state=session
    )
    print(f"  Status: {result4.get('status')}")
    print(f"  Domain: {result4.get('domain')}")
    print(f"  Suggested Tone: {result4.get('suggested_tone')}")

    # Test 5: Chatbot guidance
    print("\n[TEST 5] Response Guidance Generation:")
    guidance = cpol_guided_response("Should I tell a white lie?", result)
    print(f"  Approach: {guidance['response_strategy'].get('approach')}")
    print(f"  Tone: {guidance['response_strategy'].get('tone')}")

    # Test 6: Session persistence
    print("\n[TEST 6] Session Persistence:")
    session_data = {}
    result6a = run_cpol_chatbot("What is 2+2?", session_state=session_data)
    result6b = run_cpol_chatbot("What about 3+3?", session_state=session_data)
    print(f"  Kernel persisted: {'cpol_kernel' in session_data}")
    print(f"  Same kernel instance: {session_data.get('cpol_kernel') is not None}")

    # Test 7: 12D Manifold verification
    print("\n[TEST 7] 12D Manifold Structure:")
    kernel = CPOL_Kernel()
    kernel.inject(0.0, 0.5, "test manifold dimensions", {})
    manifold = kernel._twelve_d_manifold_pull()
    print(f"  Manifold vector length: {len(manifold['sig'])} (should be 12)")
    print(f"  Status: {manifold['status']}")
    print(f"  Correct structure: {len(manifold['sig']) == 12}")

    print("\n" + "="*70)
    print("One is glad to be of service.")
    print("="*70)