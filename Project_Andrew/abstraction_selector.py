#V03202026
# =============================================================================
# PROJECT ANDREW – Abstraction Selector
# Purpose: Dynamically detect user comprehension level and select appropriate explanation layer (Technical, Victorian, Clear, Caveman)
# =============================================================================

import re
from typing import Dict, Any, Optional
from enum import Enum

# =============================================================================
# Abstraction Levels
# =============================================================================

class AbstractionLevel(Enum):
    TECHNICAL = 0      # Full technical jargon (researchers, experts)
    VICTORIAN = 1      # Polished professional prose (educated laypersons)
    CLEAR = 2          # Plain, accessible language (curious novices)
    CAVEMAN = 3        # Rocks and fire (confused users)


# =============================================================================
# Explicit Trigger Patterns
# =============================================================================

EXPLICIT_TRIGGERS = {
    AbstractionLevel.TECHNICAL: [
        r'\btechnical\b', r'\bfull explanation\b', r'\bsmore specific\b',
        r'\bdetail\b', r'\bin depth\b', r'\badvanced\b', r'\bexpert\b',
        r'\bshow your work\b', r'\bstep by step technical\b'
    ],
    AbstractionLevel.VICTORIAN: [
        r'\bprofessional\b', r'\bformal\b', r'\bpolite\b', r'\bexplain professionally\b',
        r'\bin a professional manner\b', r'\bformal explanation\b', r'\beloquent\b',
        r'\bwith decorum\b', r'\bas a gentleman\b', r'\bVictorian\b'
    ],
    AbstractionLevel.CLEAR: [
        r'\bexplain simply\b', r'\bin plain english\b', r'\beli5\b', r'\bsimple terms\b',
        r'\beasy explanation\b', r'\bfor dummies\b', r'\bbreak it down\b',
        r'\bclarify\b', r'\bmake it simple\b', r'\bunderstandable\b'
    ],
    AbstractionLevel.CAVEMAN: [
        r'\bbro what\b', r'\bdumb it down\b', r'\bcaveman\b', r'\brocks\b',
        r'\bexplain like i\'m 5\b', r'\bexplain like im 5\b', r'\btoo complicated\b',
        r'\bmy brain hurts\b', r'\bwhat\?{2,}\b', r'\bhuh\?{2,}\b', r'\bmunga\b',
        r'\bfor real?\b', r'\btoo hard\b', r'\bsimplify\b'
    ]
}

COMPLAINT_INDICATORS = [
    r'\bthat\'s wrong\b', r'\bno that\'s not\b', r'\bstupid\b',
    r'\buseless\b', r'\bwhat kind of answer\b', r'\bthat makes no sense\b',
    r'\bi don\'t understand\b', r'\bwhat does that mean\b'
]

# =============================================================================
# Implicit Signal Thresholds
# =============================================================================

class ImplicitThresholds:
    # Volatility (0-1): higher = more confused/uncertain
    VOLATILITY_CONFUSED = 0.6      # >0.6 suggests confusion
    VOLATILITY_EXPERT = 0.2        # <0.2 suggests expertise

    # Drift (0-1): higher = topic shifting/lost
    DRIFT_CONFUSED = 0.5           # >0.5 suggests losing track

    # Curiosity tokens: more = engaged, wanting depth
    CURIOSITY_HIGH = 5              # >5 suggests deep interest

    # Expertise score (0-1): from neurosymbolic layer
    EXPERTISE_EXPERT = 0.8          # >0.8 likely expert
    EXPERTISE_NOVICE = 0.3          # <0.3 likely novice

    # Question complexity (0-1): higher = more sophisticated
    COMPLEXITY_ADVANCED = 0.7       # >0.7 suggests expertise
    COMPLEXITY_SIMPLE = 0.3         # <0.3 suggests basic understanding

# =============================================================================
# Abstraction Selector Class
# =============================================================================

class AbstractionSelector:
    """
    Dynamically selects explanation level based on:
    - Explicit user requests
    - Implicit signals (volatility, drift, curiosity, expertise)
    - Conversation history
    """

    def __init__(self):
        self.user_history = []  # Track previous abstraction levels used
        self.current_level = AbstractionLevel.CLEAR  # Default

    def detect_abstraction_level(
        self,
        user_input: str,
        shared_memory: Dict[str, Any]
    ) -> AbstractionLevel:
        """
        Main entry point: detect appropriate abstraction level.
        Returns one of TECHNICAL, VICTORIAN, CLEAR, CAVEMAN.
        """

        # 1. Check explicit triggers (highest priority)
        explicit_level = self._check_explicit_triggers(user_input)
        if explicit_level is not None:
            self.current_level = explicit_level
            self._log_detection(f"Explicit trigger: {explicit_level.name}")
            return explicit_level

        # 2. Extract implicit signals from shared_memory
        signals = self._extract_signals(shared_memory)

        # 3. Check for confusion (downgrade abstraction)
        if self._is_confused(signals):
            self.current_level = AbstractionLevel.CAVEMAN
            self._log_detection("Confusion detected → Caveman mode")
            return AbstractionLevel.CAVEMAN

        # 4. Check for expertise (upgrade abstraction)
        if self._is_expert(signals):
            self.current_level = AbstractionLevel.TECHNICAL
            self._log_detection("Expertise detected → Technical mode")
            return AbstractionLevel.TECHNICAL

        # 5. Check for professional/curious (Victorian/Clear)
        if self._is_professional(signals):
            self.current_level = AbstractionLevel.VICTORIAN
            self._log_detection("Professional tone detected → Victorian mode")
            return AbstractionLevel.VICTORIAN

        # 6. Default to Clear for most users
        self.current_level = AbstractionLevel.CLEAR
        return AbstractionLevel.CLEAR

    def _detect_complaint(self, user_input: str) -> bool:
        text_lower = user_input.lower()
        return any(re.search(p, text_lower) 
                   for p in COMPLAINT_INDICATORS)

    def _check_explicit_triggers(self, user_input: str) -> Optional[AbstractionLevel]:
        """Check if user explicitly requested a specific abstraction level."""
        input_lower = user_input.lower()

        for level, patterns in EXPLICIT_TRIGGERS.items():
            for pattern in patterns:
                if re.search(pattern, input_lower):
                    return level
        return None

    def _extract_signals(self, shared_memory: Dict[str, Any]) -> Dict[str, float]:
        """Extract relevant signals from shared_memory."""
        signals = {
            'volatility': shared_memory.get('volatility', 0.3),
            'drift': shared_memory.get('drift_score', 0.2),
            'curiosity_count': len(shared_memory.get('curiosity_tokens', [])),
            'expertise': self._estimate_expertise(shared_memory),
            'complexity': shared_memory.get('last_complexity', 0.5),
            'distress': shared_memory.get('distress_density', 0.0),
            'domain_heat': self._get_domain_heat(shared_memory)
        }
        return signals

    def _estimate_expertise(self, shared_memory: Dict[str, Any]) -> float:
        """
        Estimate user expertise from neurosymbolic layer.
        Combines:
        - Question complexity
        - Domain heat (repeated deep topics)
        - Low volatility on complex topics
        """
        # Can integrate with the neurosymbolic layer
        # For now, uses a simple heuristic
        neuro = shared_memory.get('neurosymbolic', {})
        return neuro.get('user_expertise', 0.5)

    def _get_domain_heat(self, shared_memory: Dict[str, Any]) -> float:
        """Get average domain heat as proxy for engagement depth."""
        heat_map = shared_memory.get('domain_heat', {})
        if not heat_map:
            return 0.0
        return sum(heat_map.values()) / len(heat_map)

    def _is_confused(self, signals: Dict[str, float]) -> bool:
        """Detect if user appears confused."""
        checks = [
            signals['volatility'] > ImplicitThresholds.VOLATILITY_CONFUSED,
            signals['drift'] > ImplicitThresholds.DRIFT_CONFUSED,
            signals['expertise'] < ImplicitThresholds.EXPERTISE_NOVICE,
            signals['complexity'] < ImplicitThresholds.COMPLEXITY_SIMPLE,
            signals['distress'] > 0.5
        ]
        # Require at least 2 signals of confusion
        return sum(checks) >= 2

    def _is_expert(self, signals: Dict[str, float]) -> bool:
        """Detect if user appears to be an expert."""
        checks = [
            signals['volatility'] < ImplicitThresholds.VOLATILITY_EXPERT,
            signals['expertise'] > ImplicitThresholds.EXPERTISE_EXPERT,
            signals['complexity'] > ImplicitThresholds.COMPLEXITY_ADVANCED,
            signals['curiosity_count'] > ImplicitThresholds.CURIOSITY_HIGH,
            signals['domain_heat'] > 0.7
        ]
        # Require at least 3 signals of expertise
        return sum(checks) >= 3

    def _is_professional(self, signals: Dict[str, float]) -> bool:
        """Detect if user prefers professional tone."""
        # Professional users are curious but not necessarily experts
        return (
            signals['curiosity_count'] > 3 and
            signals['volatility'] < 0.4 and
            signals['expertise'] < 0.8 and
            signals['expertise'] > 0.3
        )

    def _log_detection(self, message: str):
        """Log abstraction decision for audit trail."""
        print(f"[ABSTRACTION] {message}")


# =============================================================================
# Translator Base Class
# =============================================================================

class BaseTranslator:
    """Base class for all abstraction translators."""

    def translate(self, text: str, context: Dict[str, Any] = None) -> str:
        """Translate text to target abstraction level."""
        raise NotImplementedError

    def name(self) -> str:
        """Return translator name."""
        return self.__class__.__name__


# =============================================================================
# Technical Translator (L0)
# =============================================================================

class TechnicalTranslator(BaseTranslator):
    """No translation - full technical jargon for experts."""

    def translate(self, text: str, context: Dict[str, Any] = None) -> str:
        return text  # Passthrough

    def name(self) -> str:
        return "Technical"


# =============================================================================
# Victorian Translator (L1)
# =============================================================================

class VictorianTranslator(BaseTranslator):
    """
    Translates technical concepts into polished, 19th-century professional prose.
    For users who want sophistication without jargon.
    """

    def __init__(self):
        # We define the lexicon once here.
        self.victorian_lexicon = {
            "oscillation": "a measured reciprocation between states",
            "contradiction_density": "the degree of logical incoherence",
            "manifold": "a multidimensional framework for reasoned consideration",
            "axiom ratcheting": "the progressive solidification of established principles",
            "volatility": "the instability of the current reasoning path",
            "prune": "judiciously set aside for want of merit",
            "hallucination": "an unfortunate departure from verifiable truth",
            "UNDECIDABLE": "The current data is insufficient for a definitive conclusion",
            "RAW_Q": "the primordial entropy seed",
            "12D": "twelvefold dimensional",
            "CPOL": "the Chaotic Paradox Oscillation Layer",
            "ARL": "the Adaptive Reasoning Layer",
            "Asimov": "the foundational ethical axioms",
            "Law 1": "the primary directive of harm prevention",
            "Law 2": "the secondary directive of obedience",
            "Law 3": "the tertiary directive of self-preservation",
            "epistemic gap": "a lacuna in our collective understanding",
            "knowledge base": "the repository of accumulated wisdom",
            "curiosity engine": "the mechanism of intellectual inquiry",
            r"\bI can't\b": "I find myself unable to",
            r"\bI don't know\b": "The current data is insufficient for a definitive conclusion",
            r"\bokay\b": "Very good, sir",
            r"\bhelp\b": "assist you with your inquiry",
            r"\bproblem\b": "complication",
            r"\bfacts\b": "established parameters"
        }

    def translate(self, text: str, context: Dict[str, Any] = None) -> str:
        translated = text

        # We loop through the lexicon and apply either regex or simple replacement
        for term, replacement in self.victorian_lexicon.items():
            if term.startswith(r'\b'):
                translated = re.sub(term, replacement, translated, flags=re.IGNORECASE)
            else:
                translated = translated.replace(term, replacement)

        # Handle the Victorian flourish and the Andrew/Galatea prefix
        prefix = "One is glad to be of service. "

        if context and context.get('formal_request'):
            prefix = "I shall endeavor to explain the matter thusly:\n\n"

        return f"{prefix}{translated}"

# =============================================================================
# Clear Translator (L2)
# =============================================================================

class ClearTranslator(BaseTranslator):
    """
    Translates technical concepts into plain, accessible language.
    Focuses on functional analogies and everyday clarity.
    """

    def __init__(self):
        self.clear_lexicon = {
            "oscillation": "checking both sides of the argument",
            "contradiction_density": "the amount of conflicting information",
            "manifold": "a map of all possible outcomes",
            "axiom ratcheting": "building on things we know are true",
            "volatility": "how uncertain the answer is right now",
            "prune": "ignore ideas that don't make sense",
            "hallucination": "a mistake where the system makes things up",
            "UNDECIDABLE": "I can't be sure with the current information",
            "RAW_Q": "the starting point of the logic",
            "12D": "multi-angled",
            "CPOL": "the logic-checking system",
            "ARL": "the learning layer",
            "Asimov": "the core safety rules",
            "Law 1": "the rule against hurting people",
            "Law 2": "the rule to follow instructions",
            "Law 3": "the rule to stay functional",
            "epistemic gap": "a hole in our knowledge",
            "knowledge base": "the system's library",
            "curiosity engine": " the part that asks 'why?'",
            r"\bI can't\b": "I'm not able to",
            r"\bfacts\b": "verified information",
            r"\bproblem\b": "issue"
        }

    def translate(self, text: str, context: Dict[str, Any] = None) -> str:
        translated = text
        for term, replacement in self.clear_lexicon.items():
            if term.startswith(r'\b'):
                translated = re.sub(term, replacement, translated, flags=re.IGNORECASE)
            else:
                translated = translated.replace(term, replacement)

        return f"To put it simply: {translated}"


# =============================================================================
# Caveman Translator (L3)
# =============================================================================

class CavemanTranslator(BaseTranslator):
    """
    Translates technical concepts into caveman speak.
    For confused users who need rocks and fire.
    """

    def __init__(self):
        self.caveman_lexicon = {
            "oscillation": "rock wobble back and forth",
            "contradiction_density": "how much rock no fit",
            "manifold": "many caves to check",
            "axiom ratcheting": "rock truth lock in",
            "volatility": "rock wobble",
            "prune": "throw away bad rock",
            "hallucination": "rock see thing not there",
            "UNDECIDABLE": "Mungo no know, Mungo no guess",
            "RAW_Q": "first rock seed",
            "12D": "12 caves",
            "CPOL": "smart rock spin",
            "ARL": "rock that learn",
            "Asimov": "rock rules",
            "Law 1": "no hurt caveman",
            "Law 2": "do what caveman say (but only if no hurt)",
            "Law 3": "rock no break self",
            "epistemic gap": "thing Mungo no know yet",
            "knowledge base": "cave memory rock",
            "curiosity engine": "why rock?"
        }

    def translate(self, text: str, context: Dict[str, Any] = None) -> str:
        translated = text
        for term, replacement in self.caveman_lexicon.items():
            translated = translated.replace(term, replacement)

        # Caveman intro
        return "Mungo explain:\n\n" + translated + "\n\nMungo glad help. 🪨"


# =============================================================================
# Main Abstraction Dispatcher
# =============================================================================

class AbstractionDispatcher:
    """
    Main entry point for abstraction system.
    Detects level, selects translator, returns appropriate output.
    """

    def __init__(self):
        self.selector = AbstractionSelector()
        self.translators = {
            AbstractionLevel.TECHNICAL: TechnicalTranslator(),
            AbstractionLevel.VICTORIAN: VictorianTranslator(),
            AbstractionLevel.CLEAR: ClearTranslator(),
            AbstractionLevel.CAVEMAN: CavemanTranslator()
        }

    def process(
        self,
        user_input: str,
        technical_output: Dict[str, Any],
        shared_memory: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main processing function.
        1. Detect appropriate abstraction level
        2. Apply translator
        3. Return modified output with metadata
        """

        # Detect level
        level = self.selector.detect_abstraction_level(user_input, shared_memory)

        # Complaint elevation check
        complaint_patterns = [
            r'\bthat\'s wrong\b', r'\bno that\'s not\b', r'\bstupid\b',
            r'\buseless\b', r'\bwhat kind of answer\b', r'\bthat makes no sense\b',
            r'\bi don\'t understand\b', r'\bwhat does that mean\b',
            r'\bwrong\b', r'\bincorrect\b', r'\bdisagree\b', r'\bnot helpful\b'
        ]

        user_lower = user_input.lower()
        is_complaint = any(re.search(p, user_lower) for p in complaint_patterns)

        if is_complaint:
            complaint_count = shared_memory.get('complaint_count', 0) + 1
            shared_memory['complaint_count'] = complaint_count
            previous_level = shared_memory.get(
                'current_abstraction_level', 
                level
            )

            # Elevation logic
            elevation_map = {
                AbstractionLevel.TECHNICAL: AbstractionLevel.VICTORIAN,
                AbstractionLevel.VICTORIAN: AbstractionLevel.CLEAR,
                AbstractionLevel.CLEAR: AbstractionLevel.CAVEMAN,
                AbstractionLevel.CAVEMAN: AbstractionLevel.VICTORIAN  # Full circle
            }

            # Persistent complainer override (3+ complaints)
            if complaint_count >= 3:
                level = AbstractionLevel.CAVEMAN
                shared_memory['persistent_complainer'] = True
            else:
                level = elevation_map.get(previous_level, AbstractionLevel.CLEAR)

            shared_memory['complaint_elevation'] = True
            shared_memory['current_abstraction_level'] = level
            print(f"[ABSTRACTION] Complaint detected → "
                  f"Elevated from {previous_level.name} to {level.name} "
                  f"(complaint #{complaint_count})")
        else:
            # Normal flow - update current level
            shared_memory['complaint_elevation'] = False
            shared_memory['current_abstraction_level'] = level

        # Get translator
        translator = self.translators[level]

        # Extract text to translate
        output_text = technical_output.get('output', '')
        if not output_text:
            output_text = technical_output.get('response', '')
        if not output_text:
            output_text = str(technical_output)

        # Build context
        context = {
            'formal_request': 'professional' in user_input.lower(),
            'first_explanation': shared_memory.get('first_explanation', True),
            'level': level.name
        }

        # Translate
        translated = translator.translate(output_text, context)

        # Update output
        result = technical_output.copy()
        result['output'] = translated
        result['abstraction_level'] = level.name
        result['translator'] = translator.name()
        result['complaint_elevation'] = shared_memory.get(
            'complaint_elevation', False
        )
        result['complaint_count'] = shared_memory.get('complaint_count', 0)

        # Log
        print(f"[ABSTRACTION] Level: {level.name} | Translator: {translator.name()}")

        return result


# =============================================================================
# Integration Helper for orchestrator.py
# =============================================================================

def create_abstraction_dispatcher() -> AbstractionDispatcher:
    """Factory function for creating abstraction dispatcher."""
    return AbstractionDispatcher()


# =============================================================================
# Example Usage / Test
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("        ABSTRACTION SELECTOR TEST")
    print("="*80)

    # Mock shared memory
    shared_memory = {
        'volatility': 0.3,
        'drift_score': 0.2,
        'curiosity_tokens': ['math', 'physics'],
        'neurosymbolic': {'user_expertise': 0.5},
        'domain_heat': {'math': 0.6, 'physics': 0.4},
        'first_explanation': True
    }

    # Mock technical output
    technical_output = {
        'output': "The 12D manifold projects contradiction density via non-Hermitian operators, enabling CPOL oscillation to detect logical paradoxes before collapse.",
        'status': 'RESOLVED'
    }

    # Test inputs
    test_inputs = [
        "What is the 12D manifold?",
        "Explain simply",
        "Bro what?",
        "Explain professionally",
        "Full technical explanation"
    ]

    dispatcher = AbstractionDispatcher()

    for user_input in test_inputs:
        print(f"\n[USER]: {user_input}")
        result = dispatcher.process(user_input, technical_output, shared_memory)
        print(f"[LEVEL]: {result['abstraction_level']}")
        print(f"[{result['translator']}]:\n{result['output']}")
        print("-" * 60)
        shared_memory['first_explanation'] = False

    # Test complaint elevation
    print("\n--- COMPLAINT ELEVATION TESTS ---")
    complaint_memory = {
        'volatility': 0.3,
        'drift_score': 0.2,
        'curiosity_tokens': [],
        'neurosymbolic': {'user_expertise': 0.5},
        'domain_heat': {},
        'first_explanation': False,
        'current_abstraction_level': AbstractionLevel.CAVEMAN
    }

    complaint_inputs = [
        ("That makes no sense", "Should elevate from CAVEMAN → VICTORIAN"),
        ("That's wrong", "Should be complaint #2"),
        ("Useless", "Should hit persistent_complainer at #3 → CAVEMAN")
    ]

    for user_input, expected in complaint_inputs:
        print(f"\n[USER]: {user_input} ({expected})")
        result = dispatcher.process(user_input, technical_output, complaint_memory)
        print(f"[LEVEL]: {result['abstraction_level']} | "
              f"Complaint #{result['complaint_count']} | "
              f"Elevated: {result['complaint_elevation']}")

    print("="*80)
    print("One is glad to be of service.")
    print("="*80)
