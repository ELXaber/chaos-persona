# CAIOS CPOL - Post-Binary Logic Tool
# Copyright (c) 2025 Jonathan Schack (EL_Xaber) jon@cai-os.com
# Patent Pending: US Application 19/390,493 (Entropy-Driven Adaptive AI Transparency, filed Nov 15, 2025).
# Use of CAIOS as a computational or reasoning aid does not confer authorship, inventorship, or discovery credit to automated systems or their operators beyond standard tool usage.
# See https://github.com/ELXaber/chaos-persona/blob/main/Project_Andrew/LICENSE.txt for details of use.

Lightweight paradox detection for AI systems via function/tool calling.

## Quick Start
CPOL_Inferance.txt is the inferance command structure and tool call to handle CPOL.

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