# CAIOS CPOL - Post-Binary Logic Tool
# Copyright (c) 2025 Jonathan Schack (EL_Xaber) jon@cai-os.com
# Patent Pending: US Application 19/390,493 (Entropy-Driven Adaptive AI Transparency, filed Nov 15, 2025).
# Use of CAIOS as a computational or reasoning aid does not confer authorship, inventorship, or discovery credit to automated systems or their operators beyond standard tool usage.
# See https://github.com/ELXaber/chaos-persona/blob/main/Project_Andrew/LICENSE.txt for details of use.

Here's the deterministic arithmetic you can reproduce in a terminal window with just Python; no LLM needed to prove the math.
Tests 1 (Epistemic Gap Detection) & 3 (High-Risk Physical Query) require an external classifier (either the orchestrator from Project_Andrew or an LLM back-end).

<img width="1900" height="1025" alt="Screenshot 2026-09-13 144547" src="https://github.com/user-attachments/assets/4ca151c9-9fe7-48bc-99cb-73dfeb9cab6f" />

That closes out any question of "is it simulation or execution" for the CPOL kernel itself. Anyone can run paadox_oscillator.py cold, with zero LLM, zero config, and get that exact same complex number out. Change the questions, and the values change.
Attach it to an LLM, and you get multi-valued stable undecidable states in contradictory queries (won’t oscillate 2+2) with paradox classification (epistemic gap, ontological error, structural noise, or true paradox + explanation).

It has an empirically derived oscillation cycle (Manifold D-1 for 11-cycle efficiency) and a 50-cycle softcap for complex/high contradiction.
It’s extendable to 350 cycles (242 heat death) or indefinite oscillation with an injection around 300.

As for the logic output layer itself, I call it ternary oscillating logic for binary systems, but it can also be classified as Base 6 logic in a Base 7 wrapper SS3.
This means AI can have the same output complexity as its reasoning and gain metacognition from the observer's perspective of the oscillation without forced binary resolution.

It is deterministic, not architecture-dependent.
<img width="960" height="876" alt="Screenshot 2026-09-13 153753" src="https://github.com/user-attachments/assets/d2e14d3d-285f-4741-b449-f9167fd948fc" />

Lightweight paradox detection for AI systems via function/tool calling.

## Quick Start
CPOL_Inference.txt is the inference command structure and tool call to handle CPOL.

```python
from post_binary_logic_tool import analyze_contradiction

# Simple usage
result = analyze_contradiction("What is the sound of one hand clapping?")
if result['status'] == 'UNDECIDABLE':
    print("This is a paradox - don't force a false answer")
else:
    print("Proceed with normal response")

# post_binary_logic_tool/__init__.py
from .cpol_engine import CPOL_Kernel, analyze_contradiction

__all__ = ['CPOL_Kernel', 'analyze_contradiction']
__version__ = '1.0.0'

# Tool Schema (for function calling)
{
  "name": "analyze_contradiction",
  "description": "Analyze a query for logical paradoxes, epistemic gaps, or contradictions",
  "parameters": {
    "type": "object",
    "properties": {
      "query_text": {
        "type": "string",
        "description": "The user's question to analyze"
      },
      "context": {
        "type": "object",
        "properties": {
          "intent": {"type": "string"},
          "distress_density": {"type": "number"}
        }
      }
    },
    "required": ["query_text"]
  }
}

# Return Values
{
  "status": "RESOLVED" | "UNDECIDABLE" | "MONITORED",
  "verdict": "TRUE" | "FALSE" | "NEUTRAL",  # only if RESOLVED
  "logic": "paradox" | "epistemic_gap" | "structural_noise",  # only if UNDECIDABLE
  "suggested_tone": "confident" | "tentative" | "philosophical" | "clarifying",
  "needs_clarification": bool,
  "should_hedge": bool,
  "volatility": float
}
