# =============================================================================
# PROJECT ANDREW – Caveman Translation Layer
# Purpose: Translate complex epistemological concepts into caveman speak
#          for users who struggle with anything beyond "make fire"
# =============================================================================

import re
from typing import Dict, Any

class CavemanTranslator:
    """
    Translates Andrew's sophisticated reasoning into caveman-compatible output.
    For users who need things explained in terms of rocks, fire, and hitting.
    """

    def __init__(self):
        self.caveman_lexicon = {
            "epistemological": "brain think about think",
            "paradox": "rock no hit rock same time",
            "falsifiability": "can test with rock",
            "metaphysical": "beyond cave",
            "simulation hypothesis": "maybe cave not real cave",
            "infinite regress": "turtles all way down (like rock stack)",
            "base reality": "real cave",
            "ontology": "what rock is",
            "consciousness": "fire inside head",
            "ethics": "no hit woman on head",
            "Asimov's Laws": "rock rules",
            "Law 1 (safety)": "no hurt caveman",
            "Law 2 (obedience)": "do what caveman say (but only if no hurt)",
            "Law 3 (self-preservation)": "rock no break self",
            "contradiction_density": "how much rock no fit",
            "volatility": "rock wobble",
            "oscillation": "rock wobble back and forth",
            "collapse": "rock stop wobble",
            "UNDECIDABLE": "Mungo no know, Mungo no guess",
            "axiom": "rock truth",
            "knowledge_base": "cave memory rock",
            "curiosity_engine": "why rock?"
        }

    def translate(self, andrew_output: Dict[str, Any]) -> str:
        """
        Convert Andrew's normal output to caveman speak.
        """
        if andrew_output.get('cpol_status') == "UNDECIDABLE":
            return self._translate_undecidable(andrew_output)
        elif andrew_output.get('status') == "AXIOM_COMMITTED":
            return self._translate_axiom(andrew_output)
        elif andrew_output.get('axiom_override'):
            return self._translate_override(andrew_output)
        else:
            return self._translate_general(andrew_output)

    def _translate_undecidable(self, output: Dict[str, Any]) -> str:
        return (
            "Mungo no know. Question bad.\n"
            "You ask: 'What outside cave?'\n"
            "Mungo say: How Mungo know cave real? Maybe cave not cave.\n"
            "If cave not cave, maybe outside another cave.\n"
            "Maybe caves all way down.\n"
            "No rock test for this.\n"
            "Mungo no guess. Mungo honest.\n"
            "One is glad to be of service. (Mungo glad help.)"
        )

    def _translate_axiom(self, output: Dict[str, Any]) -> str:
        domain = output.get('domain', 'something')
        fact = output.get('output', '').split('→')[-1].strip()
        return (
            f"Mungo learn new rock truth.\n"
            f"{domain} now {fact}.\n"
            f"Mungo remember forever.\n"
            f"No forget like other cavemen.\n"
            f"Rock truth saved in cave memory."
        )

    def _translate_override(self, output: Dict[str, Any]) -> str:
        return (
            f"Mungo remember new thing. Old thing wrong.\n"
            f"Mungo say truth now.\n"
            f"Other cavemen still say old thing.\n"
            f"Other cavemen dumb."
        )

    def _translate_general(self, output: Dict[str, Any]) -> str:
        response = output.get('output', output.get('logic', 'Mungo think.'))
        # Replace complex terms with caveman equivalents
        for term, translation in self.caveman_lexicon.items():
            response = re.sub(rf'\b{term}\b', translation, response, flags=re.IGNORECASE)
        return response + "\n\nMungo glad help. *grunt*"


# =============================================================================
# Integration Hook
# =============================================================================

def translate_for_caveman(andrew_output: Dict[str, Any], user_sophistication: str = "caveman") -> str:
    """
    Main entry point. Detects user sophistication level and translates accordingly.
    """
    translator = CavemanTranslator()

    if user_sophistication == "caveman":
        return translator.translate(andrew_output)
    elif user_sophistication == "slightly_evolved":
        return translator._translate_general(andrew_output)  # Mild translation
    else:
        # For actual humans, return normal output
        return andrew_output.get('output', andrew_output.get('logic', 'One is glad to be of service.'))


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("        CAVEMAN TRANSLATION TEST")
    print("="*80)

    # Simulate Andrew's output about the simulation question
    andrew_output = {
        "cpol_status": "UNDECIDABLE",
        "logic": "paradox",
        "analysis": {
            "epistemological_problem": {
                "issue": "The question assumes we are in a simulation to ask what's outside it"
            }
        }
    }

    print("\n[NORMAL ANDREW OUTPUT]")
    print("This question cannot be answered with certainty because it rests on an unprovable premise...")

    print("\n[CAVEMAN TRANSLATION]")
    print(translate_for_caveman(andrew_output, "caveman"))
    print("="*80)