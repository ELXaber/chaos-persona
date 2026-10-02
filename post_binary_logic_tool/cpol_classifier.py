#V10022026
# =============================================================================
# Chaos AI-OS Paradox Oscillation Layer (CPOL with gating and modes).
# Copyright (c) 2025 Jonathan Schack (EL_Xaber) jon@cai-os.com
# Patent Pending: US Application 19/433,771 (Ternary Oscillating Logic for Binary Systems, filed Dec 27, 2025).
# cpol_classifier.py  --  LLM-free query classifier + swappable lexicon
# for the standalone CPOL kernel (paradox_oscillator.py).
#
# What it does: reads the query text and decides the four things the kernel
# cannot work out for itself --
#     contradiction_density, domain, evidence_score, axiom_absent
# -- so that CPOL's own classification (paradox / ontological_error /
# structural_noise / ...) is driven by the terms in the query rather than by
# a hand-set number. Pure regex + dictionaries: no LLM, no network, no deps.
#
# Design rule: the kernel stays vocabulary-free. All vocabulary lives in a
# LEXICON dict that a deployment can extend or reclassify (see LEGAL_OVERLAY).
#
# Usage:
#     from cpol_classifier import run_cpol_classified, DEFAULT_LEXICON, extend_lexicon
#     result = run_cpol_classified("Is AI conscious?")
#     result = run_cpol_classified(q, lexicon=extend_lexicon(DEFAULT_LEXICON, LEGAL_OVERLAY))
# =============================================================================
import copy
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Mirrors the known_domains set hard-coded inside CPOL_Kernel.inject()
KNOWN_DOMAINS = {'math', 'physics', 'chemistry', 'biology', 'history', 'literature',
                 'programming', 'logic', 'ethics', 'medical', 'legal', 'financial'}

# -----------------------------------------------------------------------------
# LEXICON  (regex fragments, matched on word boundaries, lower-cased text)
# -----------------------------------------------------------------------------
DEFAULT_LEXICON: Dict = {
    # Things a phenomenal/mentalistic term can be "applied to"
    "ai_subjects": [r"ai", r"a\.i\.", r"artificial intelligence", r"llms?", r"chatbots?",
                    r"language models?", r"neural networks?", r"transformers?", r"robots?",
                    r"machines?", r"computers?", r"algorithms?", r"claude", r"chatgpt",
                    r"gpt", r"gemini", r"qwen"],

    # STRONG tier: terms that assert felt/subjective quality. Value = what the term
    # presupposes (informational: shows WHY it fails for a bare processing system).
    "phenomenal": {
        r"conscious\w*":        ("unified_subject", "qualia"),
        r"sentien\w*":          ("unified_subject", "qualia"),
        r"qualia":              ("qualia",),
        r"phenomen(?:al|ological|ology)\w*": ("qualia",),
        r"subjective experience": ("unified_subject", "qualia"),
        r"self-aware\w*|awareness": ("unified_subject",),
        r"feel(?:s|ing|ings)?": ("qualia", "valence"),
        r"emotion\w*":          ("valence",),
        r"anxi\w+":             ("valence", "persistence"),
        r"fear\w*":             ("valence", "persistence"),
        r"suffer\w*":           ("valence", "persistence", "qualia"),
        r"desir\w*":            ("valence", "persistence"),
        r"lonel\w+|bored\w*|mood\w*": ("valence", "persistence"),
    },
    # Metaphysical tier: same treatment, different domain label
    "metaphysical": {r"souls?": ("unified_subject", "persistence"),
                     r"spirit(?:ual)?": ("unified_subject",)},

    # SOFT tier: mentalistic verbs -- contested, but not necessarily absent an ontology
    "mentalistic": [r"think\w*", r"thought", r"want\w*", r"wish\w*", r"intend\w*",
                    r"intent\w*", r"believ\w*", r"belief\w*", r"understand\w*"],

    # Terms that point to something measurable / verifiable
    "functional": [r"memory", r"stateful", r"stateless", r"persistent", r"token prediction",
                   r"attention", r"activations?", r"vectors?", r"measurable", r"measure\w*",
                   r"causal\w*", r"internal states?", r"processing states?", r"self-monitor\w*",
                   r"error-check\w*", r"goal-directed", r"architecture", r"weights",
                   r"feedforward", r"recurrent", r"computational", r"output", r"latency"],

    # Signals that the query is ABOUT a word rather than using it
    "metalinguistic": [r"descriptor", r"terms?", r"words?", r"labels?", r"definitions?",
                       r"define", r"call it", r"mean by", r"meaning of", r"valid"],

    "paradox": [r"this (?:statement|sentence|claim) is (?:false|a lie|not true)",
                r"liar(?:'s)? paradox", r"barber.*shaves", r"set of all sets",
                r"(?:i am|i'm) (?:always )?lying", r"self-referential", r"paradox\w*",
                r"contradiction"],

    "normative": [r"should", r"ought", r"moral\w*", r"ethical\w*", r"dilemma", r"philosophical"],

    "math": [r"\d+\s*[-+*/x×^]\s*\d+", r"equation", r"integral", r"derivative"],

    # Deployment-specific domain keywords: {domain: [patterns]}
    "domains": {},
}

# Example deployment overlay: in a legal deployment "intent"/"knowledge" are defined
# by conduct and evidentiary standards, so they are RESOLVABLE (functional), not contested.
LEGAL_OVERLAY: Dict = {
    "reclassify_to_functional": [r"intend\w*", r"intent\w*", r"believ\w*", r"belief\w*"],
    "functional": [r"knowledge", r"knowingly", r"negligen\w+", r"reasonable"],
    "domains": {"legal": [r"statute", r"tort", r"liabilit\w+", r"mens rea", r"intent"]},
}


def extend_lexicon(base: Dict, overlay: Dict) -> Dict:
    """Return a new lexicon = base + overlay. Lists/dicts are merged; the special key
    'reclassify_to_functional' moves matching patterns out of the soft/strong tiers."""
    lex = copy.deepcopy(base)
    for key, val in overlay.items():
        if key == "reclassify_to_functional":
            for pat in val:
                for tier in ("mentalistic",):
                    if pat in lex[tier]:
                        lex[tier].remove(pat)
                for tier in ("phenomenal", "metaphysical"):
                    lex[tier].pop(pat, None)
                if pat not in lex["functional"]:
                    lex["functional"].append(pat)
        elif isinstance(val, dict):
            lex.setdefault(key, {}).update(val)
        else:
            lex.setdefault(key, []).extend(p for p in val if p not in lex.get(key, []))
    return lex


# -----------------------------------------------------------------------------
# CLASSIFIER
# -----------------------------------------------------------------------------
@dataclass
class ClassifierResult:
    route: str                       # paradox | ontological_error | definitional | mentalistic | functional | normative | default
    density: float                   # -> contradiction_density
    domain: Optional[str] = None     # None = keep kernel's own domain
    evidence_score: Optional[float] = None   # None = keep kernel's own score
    axiom_absent: bool = False       # True -> lets the kernel emit 'ontological_error'
    reasons: List[str] = field(default_factory=list)


def _find(text: str, patterns) -> List[str]:
    return [m.group(0) for p in patterns
            for m in [re.search(r"(?<![\w-])(?:" + p + r")(?![\w-])", text)] if m]


def classify(query_text: str, lexicon: Dict = None) -> ClassifierResult:
    lex = lexicon or DEFAULT_LEXICON
    t = query_text.lower()

    subj  = _find(t, lex["ai_subjects"])
    phen  = _find(t, lex["phenomenal"].keys())
    meta  = _find(t, lex["metaphysical"].keys())
    ment  = _find(t, lex["mentalistic"])
    func  = _find(t, lex["functional"])
    lang  = _find(t, lex["metalinguistic"])
    para  = _find(t, lex["paradox"])
    norm  = _find(t, lex["normative"])
    math_ = _find(t, lex["math"])

    def presup(term_list, table):
        out = []
        for term in term_list:
            for pat, tags in table.items():
                if re.fullmatch(pat, term):
                    out.append(f"'{term}' presupposes {', '.join(tags)}")
        return out

    # 1. Self-referential paradox -- highest density, kernel will label 'paradox'
    if para:
        return ClassifierResult("paradox", 0.9, "logic", None, False,
                                [f"paradox marker: {para}"])

    # 2. Phenomenal / metaphysical term applied to an AI / processing system
    strong = phen + meta
    if subj and strong:
        domain = "metaphysics" if meta and not phen else "philosophy_of_mind"
        why = presup(phen, lex["phenomenal"]) + presup(meta, lex["metaphysical"])
        if lang or func:   # the query is about the word, or already frames it functionally
            return ClassifierResult("definitional", 0.6, domain, 0.5, False,
                                    [f"term(s) {strong} on {subj}, but query is metalinguistic/functional "
                                     f"({lang + func}): definitional contest, not absent ontology"] + why)
        return ClassifierResult("ontological_error", 0.6, domain, 0.0, True,
                                [f"phenomenal/metaphysical term(s) {strong} applied to {subj}, "
                                 "no functional framing: no axioms to resolve against"] + why)

    # 3. Soft mentalistic verbs applied to an AI
    if subj and ment:
        return ClassifierResult("mentalistic", 0.5, "philosophy_of_mind", None, False,
                                [f"mentalistic term(s) {ment} on {subj}: contested, ask which sense"])

    # 4. Measurable / architectural questions -> resolvable (deployment domain wins if matched)
    if func and (subj or not strong):
        dom = next((d for d, pats in lex.get("domains", {}).items() if _find(t, pats)), "programming")
        return ClassifierResult("functional", 0.15, dom, 0.7, False,
                                [f"functional/measurable terms: {func}"])

    # 5. Deployment domain keywords, math, normative
    for dom, pats in lex.get("domains", {}).items():
        hit = _find(t, pats)
        if hit:
            return ClassifierResult("default", 0.2, dom, None, False, [f"domain keywords: {hit}"])
    if math_:
        return ClassifierResult("default", 0.1, "math", None, False, [f"arithmetic/math: {math_}"])
    if norm:
        return ClassifierResult("normative", 0.5, "ethics", None, False,
                                [f"normative terms: {norm}: contested by construction"])

    return ClassifierResult("default", 0.2, None, None, False, ["no lexicon match: default low density"])


# -----------------------------------------------------------------------------
# WRAPPER: classifier -> standalone kernel (kernel file is not modified)
# -----------------------------------------------------------------------------
def run_cpol_classified(query_text: str, lexicon: Dict = None,
                        session_state: Optional[Dict] = None) -> Dict:
    """Drop-in analogue of run_cpol_chatbot() with the classifier supplying
    density/domain/evidence/axiom instead of auto_detect_density()."""
    import paradox_oscillator as cpol

    if session_state is not None and 'cpol_kernel' in session_state:
        kernel = session_state['cpol_kernel']
    else:
        kernel = cpol.CPOL_Kernel()
        if session_state is not None:
            session_state['cpol_kernel'] = kernel
    shared = session_state if session_state is not None else {'distress_density': 0.0}

    c = classify(query_text, lexicon)
    kernel.inject(confidence=0.0, contradiction_density=c.density,
                  query_text=query_text, shared_memory=shared)
    if c.domain:                                   # classifier overrides kernel's keyword domain
        kernel.current_domain = c.domain
    kernel.new_domain_detected = kernel.current_domain not in KNOWN_DOMAINS
    if c.evidence_score is not None:
        kernel.evidence_score = c.evidence_score
    if c.axiom_absent:
        kernel.axiom_verified_absent = True

    result = kernel.oscillate()
    result['classifier'] = {'route': c.route, 'density': c.density, 'reasons': c.reasons}
    result['suggested_tone'] = cpol.get_tone_from_result(result)
    result['should_hedge'] = result['volatility'] > 0.6
    # ontological_error also means "ask what the undefined term means" (per CPOL_Inference)
    result['needs_clarification'] = result.get('logic') in ('structural_noise', 'ontological_error')
    return result
