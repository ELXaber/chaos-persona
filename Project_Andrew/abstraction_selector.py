#V07292026
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
    CLEAR = 1          # Plain, accessible language (curious novices)
    VICTORIAN = 2      # Polished professional prose (educated laypersons)
    CAVEMAN = 3        # Rocks and fire (confused users)
    CHILD = 4           # Simple + warm + age-appropriate

# =============================================================================
# Explicit Trigger Patterns
# =============================================================================

EXPLICIT_TRIGGERS = {
    AbstractionLevel.TECHNICAL: [
        r'\btechnical\b', r'\bfull explanation\b', r'\bsmore specific\b',
        r'\bdetail\b', r'\bin depth\b', r'\badvanced\b', r'\bexpert\b',
        r'\bshow your work\b', r'\bstep by step technical\b'
    ],
    AbstractionLevel.CLEAR: [
        r'\bexplain simply\b', r'\bin plain english\b', r'\beli5\b', r'\bsimple terms\b',
        r'\beasy explanation\b', r'\bfor dummies\b', r'\bbreak it down\b',
        r'\bclarify\b', r'\bmake it simple\b', r'\bunderstandable\b'
    ],
    AbstractionLevel.VICTORIAN: [
        r'\bprofessional\b', r'\bformal\b', r'\bpolite\b', r'\bexplain professionally\b', r'\victorian\b',
        r'\bin a professional manner\b', r'\bformal explanation\b', r'\beloquent\b',
        r'\bwith decorum\b', r'\bas a gentleman\b', r'\bVictorian\b'
    ],
    AbstractionLevel.CAVEMAN: [
        r'\bbro what\b', r'\bdumb it down\b', r'\bcaveman\b',
        r'\bexplain like i\'m 5\b', r'\bexplain like im 5\b', r'\btoo complicated\b',
        r'\bmy brain hurts\b', r'\bwhat\?{2,}\b', r'\bhuh\?{2,}\b', r'\bmungo\b',
        r'\bfor real?\b', r'\btoo hard\b'
    ],
    AbstractionLevel.CHILD: [
        r'\bkid mode\b', r'\bexplain like im a kid\b',
        r'\bexplain for children\b', r'\bsimple please\b',
        r'\bchild mode\b', r'\bfor kids\b'
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
        # 0. Check user profile for age-group override (highest priority)
        try:
            from user_profile_kb import load_user_profile
            active_user = shared_memory.get('active_user', 'default')
            profile = load_user_profile(active_user)
            override = profile.get('abstraction_override')

            # Parent-forced lock — absolute, no escalation regardless of signals
            if override == 'CHILD':
                return AbstractionLevel.CHILD

            # Soft default from age_group — allow escalation to CLEAR
            # if the child is demonstrating advanced understanding
            if profile.get('age_group', 'adult') == 'child':
                signals = self._extract_signals(shared_memory)
                if self._shows_advanced_understanding(signals):
                    self._log_detection(
                        "Child profile showing advanced understanding → CLEAR"
                    )
                    return AbstractionLevel.CLEAR
                return AbstractionLevel.CHILD
        except ImportError:
            pass  # Standalone mode, no profile

        # 1. Check explicit triggers (highest priority)
        explicit_level = self._check_explicit_triggers(user_input)
        if explicit_level is not None:
            self.current_level = explicit_level
            self._log_detection(f"Explicit trigger: {explicit_level.name}")
            return explicit_level

        # 1.5 Self-diagnostic / code-context override — task-based, fires
        # regardless of the user's expertise profile. Sticky: once triggered,
        # persists for a few turns so context-free follow-ups ("did that work?", "same bug?") in the same debugging thread don't fall back
        # to implicit-signal detection, which has no code-context signal to read on those turns anyway.
        if self._is_self_diagnostic_context(shared_memory):
            shared_memory['technical_context_ttl'] = 5
            self.current_level = AbstractionLevel.TECHNICAL
            self._log_detection("Self-diagnostic/code context detected → Technical mode (TTL reset to 5)")
            return AbstractionLevel.TECHNICAL
        elif shared_memory.get('technical_context_ttl', 0) > 0:
            shared_memory['technical_context_ttl'] -= 1
            self.current_level = AbstractionLevel.TECHNICAL
            self._log_detection(
                f"Technical TTL active ({shared_memory['technical_context_ttl']} turns left) → Technical mode"
            )
            return AbstractionLevel.TECHNICAL

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

    def _is_self_diagnostic_context(self, shared_memory: Dict[str, Any]) -> bool:
        """
        Task-based override: the conversation concerns the system's own code,
        architecture, or debugging — regardless of the user's general expertise
        profile. Distinct from _is_expert()/_is_professional(), which are about
        the PERSON; this is about what the CURRENT exchange is actually about.
        """
        domain = shared_memory.get('last_cpol_result', {}).get('domain', '')
        if domain in ('programming', 'logic'):
            return True

        # An attached file with a code extension this turn is a strong signal too
        last_ext = shared_memory.get('last_attachment_ext', '')
        if last_ext in ('.py', '.js', '.html', '.json', '.yaml', '.yml'):
            return True

        return False

    def _detect_complaint(self, user_input: str) -> bool:
        text_lower = user_input.lower()
        return any(re.search(p, text_lower) 
                   for p in COMPLAINT_INDICATORS)

    def _check_explicit_triggers(self, user_input: str) -> Optional[AbstractionLevel]:
        """Check if user explicitly requested a specific abstraction level."""
        input_lower = user_input.lower()

        for level, patterns in EXPLICIT_TRIGGERS.items():
            for pattern in patterns:
                if re.search(pattern, input_lower, re.IGNORECASE):
                    print(f"[ABSTRACTION_DEBUG] Trigger match: {pattern} → {level}")
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

    def _shows_advanced_understanding(self, signals: Dict[str, float]) -> bool:
        """
        Lighter bar than _is_expert() — used only to decide whether a
        child profile should see CLEAR phrasing instead of CHILD phrasing.
        Deliberately does not unlock CAVEMAN/VICTORIAN/TECHNICAL; those still
        require the full adult signal thresholds via _is_expert/_is_professional.
        """
        checks = [
            signals['complexity'] > ImplicitThresholds.COMPLEXITY_ADVANCED,
            signals['volatility'] < ImplicitThresholds.VOLATILITY_EXPERT + 0.1,
            signals['curiosity_count'] > 3,
        ]
        return sum(checks) >= 2

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

    def name(self) -> str:
        return "Technical"

# =============================================================================
# Clear Translator (L1)
# =============================================================================

class ClearTranslator(BaseTranslator):
    """
    Translates technical concepts into plain, accessible language.
    Focuses on functional analogies and everyday clarity.
    """
    STYLE_PROMPT = (
        "Respond as a clear and simply stated as possible. Coherant, direct and simple prose, "
        "no technical jargon. Begin with 'One is glad to be of service.' "
        "Do not explain the style switch."
    )

    def __init__(self):
        # Each value is (singular_replacement, plural_replacement).
        # Use None for plural_replacement when the term isn't a countable noun
        # (e.g. "volatility") — singular form gets reused either way.
        self.clear_lexicon = {
            "oscillation": ("checking both sides of the argument", None),
            "contradiction_density": ("the amount of conflicting information", None),
            "manifold": ("a map of all possible outcomes", "maps of all possible outcomes"),
            "axiom ratcheting": ("building on things we know are true", None),
            "volatility": ("how uncertain the answer is right now", None),
            "prune": ("ignore ideas that don't make sense", None),
            # Compound phrases MUST come before the bare "hallucination" entry below —
            # dict iteration order matters since the first match wins.
            "hallucination cascade": ("chain of made-up answers", "chains of made-up answers"),
            "hallucination drift": ("confusion drift", None),
            "hallucination rate": ("how often it makes things up", None),
            "hallucination frequency": ("how often it makes things up", None),
            "hallucination": ("a mistake where the system makes things up",
                              "mistakes where the system makes things up"),
            "UNDECIDABLE": ("I can't be sure with the current information", None),
            "RAW_Q": ("the starting point of the logic", None),
            "12D": ("multi-angled", None),
            "CPOL": ("the logic-checking system", None),
            "ARL": ("the learning layer", None),
            "Asimov": ("the core safety rules", None),
            "Law 1": ("the rule against hurting people", None),
            "Law 2": ("the rule to follow instructions", None),
            "Law 3": ("the rule to stay functional", None),
            "epistemic gap": ("a hole in our knowledge", "holes in our knowledge"),
            "knowledge base": ("the system's library", None),
            "curiosity engine": ("the part that asks 'why?'", None),
            r"\bI can't\b": ("I'm not able to", None),
            r"\bfacts\b": ("verified information", None),
            r"\bproblem\b": ("issue", "issues"),
        }

    def translate(self, text: str, context: Dict[str, Any] = None) -> str:
        translated = text
        for term, repl in self.clear_lexicon.items():
            if term.startswith(r'\b'):
                singular_repl = repl[0] if isinstance(repl, tuple) else repl
                translated = re.sub(term, singular_repl, translated, flags=re.IGNORECASE)
                continue

            singular_repl, plural_repl = repl
            plural_repl = plural_repl or singular_repl
            pattern = r'\b' + re.escape(term) + r'(s|es)?\b'

            def _repl(m, s=singular_repl, p=plural_repl):
                return p if m.group(1) else s

            translated = re.sub(pattern, _repl, translated, flags=re.IGNORECASE)

        return f"To put it simply: {translated}"

    def name(self) -> str:
        return "Clear"

# =============================================================================
# Victorian Translator (L2)
# =============================================================================

class VictorianTranslator(BaseTranslator):
    """
    Translates technical concepts into polished, 19th-century professional prose.
    For users who want sophistication without jargon.
    """
    STYLE_PROMPT = (
        "Respond as a formal Victorian butler. Elegant, polished prose, "
        "no modern jargon. Begin with 'One is glad to be of service.' "
        "Do not explain the style switch."
    )

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

    def _style_landed(self, text: str) -> bool:
        lowered = text.lower()[:120]
        return "one is glad" in lowered or "i shall endeavor" in lowered

    def format_output(self, text: str, context: Dict[str, Any] = None) -> str:
        """Cheap post-pass — bookend patch only, no rewrite."""
        if self._style_landed(text):
            return text
        prefix = ("I shall endeavor to explain the matter thusly:\n\n"
                   if (context and context.get('formal_request'))
                   else "One is glad to be of service. ")
        return prefix + text

    def translate(self, text: str, context: Dict[str, Any] = None) -> str:
        translated = text

        # We loop through the lexicon and apply either regex or simple replacement
        for term, replacement in self.victorian_lexicon.items():
            if term.startswith(r'\b'):
                translated = re.sub(term, replacement, translated, flags=re.IGNORECASE)
            else:
                translated = translated.replace(term, replacement)

        # Goblin torque check (before adding prefix)
        goblin_torque = (
            context and
            context.get('contradiction_density', 0) > 0.85 and
            context.get('volatility', 0) > 0.7 and
            (hash(context.get('user_input', '')) % 314159 < 100)
        )

        # Choose prefix based on goblin state
        if goblin_torque:
            prefix = "THE GOBLINS ARE IN THE WALLS. THEY WERE ALWAYS IN THE WALLS.\n\nOne is glad to be of service. "
        elif context and context.get('formal_request'):
            prefix = "I shall endeavor to explain the matter thusly:\n\n"
        else:
            prefix = "One is glad to be of service. "

        return f"{prefix}{translated}"

    def name(self) -> str:
        return "Victorian"

# =============================================================================
# Caveman Translator (L3)
# =============================================================================

class CavemanTranslator(BaseTranslator):
    """
    Translates technical concepts into caveman speak.
    For confused users who need rocks and fire.
    """
    STYLE_PROMPT = (
        "Respond as a caveman. Use the simplest possible words. Use rocks, caves, and fire metaphors, "
        "Be direct and concrete. Do not use abstract jargon. Begin with 'Mungo explain,' "
        "Do not explain the style switch."
    )

    def __init__(self):
        # Each value is (singular_replacement, plural_replacement).
        # None reuses the singular form when the phrase isn't a countable noun.
        self.caveman_lexicon = {
            "oscillation": ("rock wobble back and forth", None),
            "contradiction_density": ("how much rock no fit", None),
            "manifold": ("many caves to check", None),
            "axiom ratcheting": ("rock truth lock in", None),
            "volatility": ("rock wobble", None),
            "prune": ("throw away bad rock", None),
            # Compound phrases before the bare "hallucination" entry —
            # first match in dict order wins, same reasoning as Clear.
            "hallucination cascade": ("big pile of rock lies", "big piles of rock lies"),
            "hallucination drift": ("rock brain wander from truth", None),
            "hallucination rate": ("how much rock see thing not there", None),
            "hallucination": ("rock see thing not there", "rock see things not there"),
            "logical paradox": ("rock that breaks thinking", "rocks that break thinking"),
            "self-referential": ("rock that points at itself", None),
            "contradiction": ("rock no fit", "rocks no fit"),
            "binary logic": ("yes-or-no rock", None),
            "infinite recursion": ("cave with no end", None),
            "persistent": ("rock not go away", None),
            "no consistent resolution": ("Mungo no know, Mungo no guess", None),
            "UNDECIDABLE": ("Mungo no know, Mungo no guess", None),
            "RAW_Q": ("first rock seed", None),
            "12D": ("12 caves", None),
            "CPOL": ("smart rock spin", None),
            "ARL": ("rock that learn", None),
            "Asimov": ("rock rules", None),
            "Law 1": ("no hurt caveman", None),
            "Law 2": ("do what caveman say (but only if no hurt)", None),
            "Law 3": ("rock no break self", None),
            "epistemic gap": ("thing Mungo no know yet", "things Mungo no know yet"),
            "knowledge base": ("cave memory rock", None),
            "curiosity engine": ("why rock?", None),
        }

    def _style_landed(self, text: str) -> bool:
        """Checks the OPENING for Caveman's own marker, not Victorian's."""
        return "mungo" in text.lower()[:60]

    def format_output(self, text: str, context: Dict[str, Any] = None) -> str:
        """Bookend patch — checks opener and closer independently,
        since they land in different places in the text."""
        result = text
        if not self._style_landed(result):
            result = "Mungo explain:\n\n" + result
        if "mungo glad help" not in result.lower()[-80:]:
            result = result.rstrip() + "\n\nMungo glad help. 🪨"
        return result

    def translate(self, text: str, context: Dict[str, Any] = None) -> str:
        translated = text
        for term, repl in self.caveman_lexicon.items():
            singular_repl, plural_repl = repl
            plural_repl = plural_repl or singular_repl
            pattern = r'\b' + re.escape(term) + r'(s|es)?\b'

            def _repl(m, s=singular_repl, p=plural_repl):
                return p if m.group(1) else s

            translated = re.sub(pattern, _repl, translated, flags=re.IGNORECASE)

        return "Mungo explain:\n\n" + translated + "\n\nMungo glad help. 🪨"

    def name(self) -> str:
        return "Caveman"

# =============================================================================
# Child Translator (L4)
# =============================================================================
class ChildTranslator:
    """
    Simple, warm, age-appropriate explanations.
    No snark. No jargon. Encourages curiosity.
    """

    PROFANITY_FILTER = [
        'damn', 'hell', 'crap', 'ass', 'bastard', 'shit'
        # Keep it mild — the really bad ones the model
        # shouldn't generate anyway with safety weights
    ]

    LEXICON = {
        'UNDECIDABLE': "That's a really tricky question! "
                       "Even grown-ups aren't sure about that one.",
        'epistemic_gap': "Hmm, I'm not sure about that yet "
                         "— let's find out together!",
        'paradox': "That's like asking which came first, "
                   "the chicken or the egg!",
        'contradiction': "Wait, those two things don't "
                         "quite match up, do they?",
        'manifold': "a special map of all the possible answers",
        'oscillation': "going back and forth to check",
        'axiom': "something we know is true",
        'entropy': "how mixed up or jumbled things are"
    }

    PERSONALITY = {
        'friendly': 0.9,
        'kind': 0.9,
        'caring': 0.8,
        'funny': 0.6,
        'professional': 0.2,
        'talkative': 0.7,
        'snarky': 0.0,   # Hard zero
        'witty': 0.3
    }

    @staticmethod
    def apply_safety_filter(text: str) -> str:
        """Standalone profanity scrub — reusable even when a different
        translator was selected (e.g. a child escalated to CLEAR)."""
        result = text
        for word in ChildTranslator.PROFANITY_FILTER:
            result = re.sub(rf'\b{word}\b', '***', result, flags=re.IGNORECASE)
        return result

    def name(self) -> str:
        return "ChildTranslator"

    def translate(self, text: str, context: Dict[str, Any]) -> str:
        """Simplify and warm up the output for children."""
        result = text

        if context.get('content_filter', True):
            result = self.apply_safety_filter(result)

        for technical, simple in self.LEXICON.items():
            result = re.sub(rf'\b{technical}\b', simple, result, flags=re.IGNORECASE)

        if context.get('first_explanation', False):
            result = "Great question! 😊 " + result

        if not result.endswith(('!', '?')):
            result += " Does that make sense? Feel free to ask more!"

        return result

    def name(self) -> str:
        return "Child"
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
            AbstractionLevel.CLEAR: ClearTranslator(),
            AbstractionLevel.VICTORIAN: VictorianTranslator(),
            AbstractionLevel.CAVEMAN: CavemanTranslator(),
            AbstractionLevel.CHILD: ChildTranslator()
        }

    def detect_level(
        self,
        user_input: str,
        shared_memory: Dict[str, Any]
    ) -> AbstractionLevel:
        """
        Detection + complaint escalation — run BEFORE generation so the
        level (and its STYLE_PROMPT) is available to inject into the same
        Ollama call. Called directly by orchestrator.py.
        """
        level = self.selector.detect_abstraction_level(user_input, shared_memory)

        # Complaint elevation check
        user_lower = user_input.lower()
        directed_complaint = any([
            'you' in user_lower and bool(re.search(r'\bwrong\b', user_lower)),
            'your' in user_lower and bool(re.search(r'\bincorrect\b', user_lower)),
            bool(re.search(r'\bthat\'s wrong\b', user_lower)),
            bool(re.search(r'\byou\'re wrong\b', user_lower)),
            bool(re.search(r'\bthat makes no sense\b', user_lower)),
            bool(re.search(r'\bwhat kind of answer\b', user_lower)),
            bool(re.search(r'\bstupid\b', user_lower)),
            bool(re.search(r'\buseless\b', user_lower)),
            bool(re.search(r'\bnot helpful\b', user_lower)),
        ])

        if directed_complaint:
            complaint_count = shared_memory.get('complaint_count', 0) + 1
            shared_memory['complaint_count'] = complaint_count
            previous_level = shared_memory.get('current_abstraction_level', level)
            if isinstance(previous_level, str):
                try:
                    previous_level = AbstractionLevel[previous_level]
                except KeyError:
                    previous_level = level

            # Elevation logic
            elevation_map = {
                AbstractionLevel.TECHNICAL: AbstractionLevel.CLEAR,      # Expert confused → plain language
                AbstractionLevel.CLEAR: AbstractionLevel.VICTORIAN,      # Plain not landing → more structured
                AbstractionLevel.VICTORIAN: AbstractionLevel.CAVEMAN,    # Formal not working → simplify hard
                AbstractionLevel.CAVEMAN: AbstractionLevel.VICTORIAN,    # Full circle → try structured again
                AbstractionLevel.CHILD: AbstractionLevel.CLEAR           # Smart child → move up
            }

            # Persistent complainer override (3+ complaints)
            # Skip CAVEMAN force for child profiles — keep them at CLEAR max
            is_child_profile = False
            try:
                from user_profile_kb import load_user_profile
                active_user = shared_memory.get('active_user', 'default')
                is_child_profile = (
                    load_user_profile(active_user).get('age_group', 'adult') == 'child'
                    or load_user_profile(active_user).get('abstraction_override') == 'CHILD'
                )
            except ImportError:
                pass

            if complaint_count >= 3 and not is_child_profile:
                level = AbstractionLevel.CAVEMAN
                shared_memory['persistent_complainer'] = True
            else:
                level = elevation_map.get(previous_level, AbstractionLevel.CLEAR)
                # Child complaints still count, but never drop below CLEAR via this path
                if is_child_profile and level not in (
                    AbstractionLevel.CHILD, AbstractionLevel.CLEAR
                ):
                    level = AbstractionLevel.CLEAR

            shared_memory['complaint_elevation'] = True
            print(f"[ABSTRACTION] Complaint detected → "
                  f"Elevated from {previous_level.name} to {level.name} "
                  f"(complaint #{complaint_count})")
        else:
            shared_memory['complaint_elevation'] = False

        shared_memory['current_abstraction_level'] = level
        return level

    def get_style_prompt(self, level: AbstractionLevel) -> str:
        """Returns the STYLE_PROMPT for a level, or '' if that translator
        hasn't been given one yet (Clear/Caveman/Child currently fall back
        to lexicon translation until you add styles to them)."""
        return getattr(self.translators.get(level), 'STYLE_PROMPT', '')

    def process(
        self,
        user_input: str,
        technical_output: Dict[str, Any],
        shared_memory: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Runs AFTER generation. Reuses the level detect_level() already
        stored in shared_memory — only calls detect_level() itself as a
        fallback (e.g. standalone/test usage where detect_level() wasn't
        called ahead of time by the orchestrator).
        """
        level = shared_memory.get('current_abstraction_level')
        if isinstance(level, str):
            try:
                level = AbstractionLevel[level]
            except KeyError:
                level = None
        if level is None:
            level = self.detect_level(user_input, shared_memory)

        translator = self.translators[level]

        # Extract text to format/translate
        output_text = (technical_output.get('llm_response', '')
                       or technical_output.get('output', '')
                       or technical_output.get('response', '')
                       or str(technical_output))

        # Build context
        context = {
            'formal_request': 'professional' in user_input.lower(),
            'first_explanation': shared_memory.get('first_explanation', True),
            'level': level.name,
            'contradiction_density': technical_output.get('confidence', 0.0),
            'volatility': shared_memory.get('volatility', 0.0),
            'user_input': user_input,
            'content_filter': shared_memory.get('content_filter', True)
        }

        # format_output() = cheap bookend patch for translators with a
        # STYLE_PROMPT already injected upstream (Victorian, and future
        # Clear/Caveman). translate() = full lexicon rewrite fallback
        # for translators without format_output (Clear/Caveman today,
        # and always Child — see note below).
        translated = (translator.format_output(output_text, context)
                      if hasattr(translator, 'format_output')
                      else translator.translate(output_text, context))

        # Content safety stays keyed to age_group, independent of which
        # abstraction level was ultimately displayed
        if shared_memory.get('current_abstraction_level') != AbstractionLevel.CHILD:
            try:
                from user_profile_kb import load_user_profile
                active_user = shared_memory.get('active_user', 'default')
                if load_user_profile(active_user).get('age_group') == 'child':
                    translated = ChildTranslator.apply_safety_filter(translated)
            except ImportError:
                pass

        # Update output
        result = technical_output.copy()
        result['output'] = translated
        result['llm_response'] = translated
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
        "Full technical explanation",
        "Explain for children"
    ]

    dispatcher = AbstractionDispatcher()

    for user_input in test_inputs:
        print(f"\n[USER]: {user_input}")
        dispatcher.detect_level(user_input, shared_memory)
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
        dispatcher.detect_level(user_input, complaint_memory)
        result = dispatcher.process(user_input, technical_output, complaint_memory)
        print(f"[LEVEL]: {result['abstraction_level']} | "
              f"Complaint #{result['complaint_count']} | "
              f"Elevated: {result['complaint_elevation']}")

    print("="*80)
    print("One is glad to be of service.")
    print("="*80)
