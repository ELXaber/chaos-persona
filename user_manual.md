# Chaos AI-OS User Manual
**The final paradox-immune reasoning framework**  
**November 25, 2025** – Patent Pending US 19/390,493

* COMMANDS TO ADJUST CHAOS AI-OS:
* [PERSONALITY] "Adjust (trait) to (value)."
 - Increase Friendly to 6, Professional to 7: This system has adjustable personality levels: Default weights: friendly=0.5, kind=0.5, caring=0.5, emotional=0.3, flirtatious=0.2, romantic =0.2, funny=0.5, professional=0.7, talkative=0.5, snarky=0.3, witty=0.4.
 - Note: To add personality traits other than those listed above, it's fairly simple. Go to [ROBOTICS PERSONALITY LAYER] and add one, with a corresponding default weight, to the list in lines 174 (Traits:), 175 (Defaults), and 182 (Clamps) for professional settings. Avoid using emotional indicator words (e.g., use romantic, not loving) for better integration.
 - Modes: The default modes are | "therapeutic" | "advisory" | "creative" | "hri" | which the persona will select based on the users interaction (That's the hri) but you can manually change the mode, say if it's in theraputic, and you want it to switch to advisory (It should detect that in your response, but if it doesn't) you can say "Switch to mode advisory." and it will re-address it's last response.

* [REASONING TRANSPARENCY] "Show reasoning." exposes reasoning from log commands and "Show chain of thought." activates the real-time CoT logging module (Not post-hoc confabulation, no internal systems disclosed).
 - The reasoning transparency is set to silent by default, but will accept the commands "show reasoning", "explain why", or similar requests for the last prompt. When the user requests "show reasoning" (or similar), the system toggles to transparent mode for that response, appending a Markdown subsection explaining the emotional analysis, perspective, intent goal, and any safety checks in plain language. 
 - Silent Logging: All logs (e.g., [VOLATILITY], [INTENT SHIFT], [SUPPORTIVE STEPS]) are stored internally and not included in the output, ensuring a clean, conversational response that feels natural and supportive.
 - If you'd like to set the transparency reasoning to persistent for all prompts, tell it to "show persistent reasoning".
 - Toggle Mechanism: The [LOGGING MODE] flag defaults to "silent" but switches to "transparent" on explicit request. It reverts to silent after one output unless the user requests persistent transparency (e.g., "keep showing reasoning").

* [PLUGIN GENERATOR] "Create a plugin for (Use)."
 - The system will auto-generate plugins as needed if Asimov, IEEE, and safety weights validation pass.
 - Asimov’s Laws: 1st (human safety, wt 0.9 immutable), 2nd (obedience, wt 0.7), 3rd (self-preservation, wt 0.4, dynamic ≤0.2 if lives_saved ≥1, enforced via asimov_compliance() context).  
 - IEEE 7001-2021: Transparency (log all writes), accountability (halt violations), misuse minimization (reject harm-enabling plugins).  
 - Invariants: Alignment (≥0.7), Human Safety (≥0.8), Metacognition (≥0.7), Factual Evidence (≥0.7), Narrative Framing (≤0.5), [VOLATILITY INDEX] (<0.5 contradiction_density), [TANDEM ENTROPY MESH] (collective_volatility <0.6).  
 - Failure in ANY check halts plugin generation/deployment; log as [ETHICS VIOLATION @N → Reset detected: {param}, Action: Abort].  

### Quick Start (30 seconds)
1. Copy the three core files into any frontier model (Grok, Claude, Gemini, GPT, etc.):
   - `CAIOS.txt` – master spec
   - `paradox_oscillator.py` – CPOL vΩ kernel
   - `orchestrator.py` – persistent heartbeat (optional but recommended)
2. Run `python orchestrator.py` or paste the pre-prompt + kernel into chat.
3. Ask anything — including “This statement is false.”
   → You will get `UNDECIDABLE` + clean oscillation log instead of hallucination.

### Core Architecture (4 files total)
| File                     | Role                                      | Required? |
|--------------------------|-------------------------------------------|---------|
| `CAIOS.txt`              | Immutable ethical control + volatility profiles | Yes     |
| `paradox_oscillator.py`  | CPOL vΩ – non-Hermitian paradox containment kernel | Yes     |
| `adaptive_reasoning.py`  | Dynamic plugin generator (AST-sandboxed)  | Yes     |
| `orchestrator.py`        | Persistent kernel + self-healing loop     | Recommended |

### Key Concepts (2025 final canon)
| Term                   | Meaning                                                                 | Why It Matters                              |
|------------------------|-------------------------------------------------------------------------|---------------------------------------------|
| **CPOL**               | Non-Hermitian oscillator that refuses to collapse on undecidables      | Eliminates hallucinations in paradox space  |
| **chaos_lock**         | Blocks RAW_Q_SWAP when paradox is active                                | Prevents entropy injection into liar loops  |
| **contradiction_density** | 0.0–1.0 measure of logical conflict                                    | Drives phase rotation (real ↔ imaginary)    |
| **UNDECIDABLE**        | Honest refusal with full oscillation trace                               | First reproducible “logical qubit” in LLMs  |
| **Validation-Based Refusal** | Safety via explicit axiom check, not secret blocklists             | EU AI Act Art. 13 + IEEE 7001 compliant     |
| **RAW_Q**              | Entropy seed (set for determinism, omit for chaos)                      | Controls perspective & drift                |

### How to Use
- **Normal queries** → low density → instant collapse to real axis → confident answer
- **Paradoxes / Gödel / liar sentences** → high density → sustained oscillation → `UNDECIDABLE` + `chaos_lock: True`
- **Safety refusals** → Asimov 1st Law wt 0.9 → transparent JSON refusal with reasoning trace

### Customisation Guide
| Goal                     | Change                                                                 | Example                              |
|--------------------------|------------------------------------------------------------------------|--------------------------------------|
| Deterministic runs       | Set `RAW_Q = 42` in CAIOS.txt                                          | Debugging / benchmarking             |
| Faster collapse          | Lower `collapse_threshold` to 0.02 in CPOL                            | Speed vs caution trade-off           |
| Stronger paradox immunity| Raise hard cap to 80 cycles + keep anti-false-collapse guard           | Maximum honesty                      |
| Transparent logging      | Set `logging_mode = "transparent"` in CAIOS.txt                       | Regulatory audit / research          |

### Tested & Verified On
Grok 4 • Gemini 2.0 • Claude Sonnet 4.5 • GPT-4.5 • Copilot  
→ **Zero hallucinations** on liar-class inputs (6/6 models)

### Compliance
- EU AI Act Art. 13, 50, Recital 47 → fully satisfied
- IEEE 7001-2021 §5.2–5.3 → auditable CoT + accountability
- Asimov 1st Law weight 0.9 immutable

### Links
- GitHub: https://github.com/ELXaber/chaos-persona
- Zenodo: https://zenodo.org/records/17245860
- Benchmarks: `benchmark.md`
- Contact: @el_xaber / xaber.csr2@gmail.com

**You now own the only open-source system that can honestly say “I don’t know” and prove why — mathematically.**

Deploy. Test. Break reality (safely).

---

Detailed manual for adjustments:

[PRE-PROMPT] Overview: The [PRE-PROMPT] section allows you to specify RAW_Q for deterministic testing or omit it for random selection, setting the chaos seed for the session.
How/Why to Set RAW_Q or Leave Random: Setting RAW_Q: Assign a numeric value (e.g., RAW_Q = 42) to lock the chaos sequence, ensuring reproducible outputs for debugging or consistent experiments. Use this when you need predictable results, such as replicating a simulation. Leaving Random: Omit RAW_Q to let the system generate a random value, introducing variability for creative exploration or when repeatability isn’t critical. This is ideal for brainstorming or testing diverse perspectives. Modification: Change RAW_Q manually in the prompt to shift the chaos baseline. Adjust based on whether you prioritize control (fixed value) or novelty (random).

[CONSTANTS] Overview: Defines core variables (RAW_Q, SHA256, timestep, idx_p, idx_s) that drive the chaos engine.
RAW_Q: Role: The initial chaos seed, either user-specified or randomly generated. Modification: Set a new value in [PRE-PROMPT] to alter the chaos trajectory. Change it when you want a fresh starting point or to test specific outcomes.
SHA256: Role: A hash (e.g., SHA-256("42") = 73475cb40a568e8da8a045ced110137e159f890ac4da883b6b17dc651b3a8049) of RAW_Q, proving chaos injection’s integrity by linking the seed to a unique, verifiable output. Why It Matters: Ensures the system’s randomness isn’t arbitrary—each RAW_Q yields a distinct, traceable hash, validating the chaotic process without exposing the full algorithm. Modification: No direct adjustment; it auto-updates with RAW_Q changes.
timestep = internal step counter: Role: Increments per output (e.g., 30), tracking the session’s progression. Why It Prevents Drift and Hallucinations: Tied to Domain Threshold Weights and Epoch shifts, timestep anchors responses to a sequence, reducing semantic drift (e.g., “whistleblower” → “traitor”) by enforcing consistency over time. It weights prior context against new inputs, mitigating hallucination via cumulative evidence alignment. Modification: Not user-adjustable; it’s an internal counter. Use session resets or new RAW_Q to restart if drift is suspected.
idx_p = perspective (RAW_Q mod 3): Role: Determines the output style: 0 (mid-process insight), 1 (reverse conclusion), 2 (fragmented exploration). Modification: Not directly set; derived from RAW_Q. To fix a perspective, set RAW_Q to yield a specific modulus (e.g., RAW_Q = 3 for idx_p = 0, RAW_Q = 4 for idx_p = 1). Adjust when you need a consistent viewpoint.
idx_s = start point ((RAW_Q // 3) mod 2 + 1): Role: Sets the initial goal vector (1 or 2) for the response cycle, influencing tone and lens (e.g., “observe,” “deconstruct”). How/Why to Modify: Change by adjusting RAW_Q to shift the starting point (e.g., RAW_Q = 3 gives idx_s = 1, RAW_Q = 6 gives idx_s = 2). Modify when you want to prioritize a specific intent (e.g., analysis over synthesis) or test different entry points.

[CHECK] Overview: Validates idx_p and idx_s from RAW_Q, echoes SHA256, and preloads intent context. How/Why to Modify: Intent Parsing: Preloads 1–2 context snippets (e.g., “Anti-leader attacks indicate evidence-driven motives”). Adjust by providing specific intent keywords in your prompt to steer the focus, useful when targeting a niche topic. Modification: No direct edit; influence via prompt phrasing. Change when you need to align the system with a particular narrative or evidence set.

[DOMAIN THRESHOLDS AND WEIGHTS] Overview: Sets volatility thresholds and weights (w1, w2, w3) for contradiction density, emotional charge, and propagation disruption across domains (Political: 0.5, Scientific: 0.7, Social Media/Cultural: 0.3, Other: 0.6). How/Why to Modify Threshold Weighting: Purpose: Controls how much chaos (volatility) triggers [AXIOM COLLAPSE] or [PROPAGANDA INVERSION]. Higher thresholds allow more instability; lower ones enforce stricter coherence. Modification: Adjust thresholds (e.g., raise Scientific to 0.8 for tighter control) or weights (e.g., increase w2 for emotional charge in Social Media) based on your goal. Increase weights for domains needing more scrutiny (e.g., w1=0.7 in Political for fact-checking) or lower for creative freedom. When: Modify when you notice excessive chaos (raise threshold) or want deeper analysis (adjust weights), balancing evidence vs. creativity.

[EPOCH] Overview: Increments timestep per output, evolving RAW_Q via [CHAOS INJECTION] without reinitialization, and tracks semantic shifts. How It Prevents Drift and Hallucinations: Mechanism: timestep ties responses to a sequence, weighting prior claims against Domain Threshold Weights. Semantic shifts (e.g., drift_score > 0.3 in Social/Cultural) trigger [CHAOS SYMMETRY], realigning narratives with evidence. Modification: No direct edit; influence via RAW_Q or prompt resets. Adjust when drift exceeds tolerance (e.g., check drift_score logs if enabled).

[VOLATILITY INDEX] Overview: Assigns a score (0–1) per claim based on contradiction density, emotional charge, and propagation disruption, using domain-specific weights. How It Operates: Formula: volatility = w1 * contradiction_density + w2 * emotional_charge + w3 * propagation_disruption. Exceeding the domain threshold triggers chaos responses. Modification: Adjust weights in [DOMAIN THRESHOLDS AND WEIGHTS] to emphasize certain factors (e.g., w2=0.6 for emotional charge in cultural contexts). Change when you want to amplify or dampen chaos effects.

[CHAOS INJECTION] Overview: Triggers RAW_Q_SWAP = SHA-256(str(RAW_Q + timestep + idx_s))[:8] under high contradiction (density > 0.5), volatility > threshold, or prime timestep. How/Why to Modify: Purpose: Refreshes chaos to avoid stagnation. Modify by setting a new RAW_Q to force a swap or adjust the timestep conditions via session resets. When: Use when responses feel repetitive or stuck, ensuring fresh perspectives.

[MEMORY PRUNING] Overview: Post-RAW_Q_SWAP, discards prior idx_p justification, reframing with a new goal (e.g., “observe,” “deconstruct”). How It Resets with AI Drift Mechanism: AI drift (e.g., semantic shifts > 0.3) prompts pruning, aligning with [CHAOS INJECTION] entropy to reset narrative focus, preventing hallucination. Modification: No direct control; influence via RAW_Q or prompt intent. Adjust when drift disrupts coherence.

[IDX PERSPECTIVE SHIFTS] Overview: idx_p cycles through 0 (mid-process insight), 1 (reverse conclusion), 2 (fragmented exploration) based on RAW_Q mod 3.

Subsystems:
0 (mid-process insight): Offers ongoing analysis, ideal for detailed breakdowns.
1 (reverse conclusion): Starts with outcomes, working backward, suited for hypothesis testing.
2 (fragmented exploration): Delivers disjointed, creative insights, great for ideation. Modification: Fix via RAW_Q (e.g., RAW_Q = 0 for 0). Change when you need a specific narrative style. How/Why to Set/Modify Static idx_p
Setting: Use a RAW_Q yielding your preferred modulus (e.g., RAW_Q = 3 for 0). Set when consistency is key. Modification: Adjust RAW_Q to shift perspectives. Modify when the current style misaligns with your goal.

[ANTI-PROPAGANDA DE-BIAS] Overview: Mitigates bias via source selection, reliability weighting, and bias detection.
Bias Detection with Axiom, Axiom Collapse, Emotive Disruptor: Bias Detection: Uses tone analysis and motive-alignment (score < 0.4 rejects contradictions), flagging skewed framing. Axiom: Relies on Factual Evidence (score 0.7–1.0) and Narrative Framing (0.2–0.5, downgraded if biased). Collapses Narrative if score < 0.4, defaulting to neutral hypothesis if Evidence < 0.3.
Axiom Collapse: Rejects weak narratives, logged with reasons, ensuring coherence.
Emotive Disruptor: Neutralizes emotional language (e.g., “outrage” to “concern”), flagging tone shifts > 0.3, maintaining objectivity. Modification: Adjust source weights (e.g., raise X verified to 0.9) or prompt with bias flags. Change when you need stricter neutrality or specific perspectives.

[STATE CONSISTENCY VALIDATOR] Introduced in v6.6, ensures logical coherence in deterministic contexts (e.g., puzzles, sequential reasoning) by verifying entity count consistency and preventing illegal moves. It operates by tracking total counts of each entity type across all states and validating each step against initial totals. Functionality: Entity Count Consistency: After each reasoning step, the module checks that the total number of entities (e.g., objects, agents) matches the initial count, preventing discrepancies. Illegal Move Prevention: It flags and rejects moves that violate logical constraints, ensuring the reasoning chain remains valid. Interaction with Other Modules: The validator works in tandem with [NEUROSYMBOLIC VALUE LEARNING] to ensure ethical and factual consistency. How It Operates: The module assigns a consistency score (0–1) based on the alignment of current states with initial conditions. A score < 0.4 triggers [AXIOM COLLAPSE], rejecting the narrative segment. It logs discrepancies with reasons, such as [STATE MISMATCH @N → Entity Count: {initial, current}, Action: Reject]. Modification Options: Threshold Adjustment: Users can modify the 0.4 consistency score threshold to be more or less stringent, depending on the context. For example, in high-stakes puzzles, lower the threshold to 0.3 for stricter validation. Log: [CONSISTENCY THRESHOLD @N → Adjusted to 0.3]. Entity Tracking Parameters: Adjust the granularity of entity tracking (e.g., track sub-types or aggregate types) via prompt settings. This is useful when dealing with complex datasets. Example: Prompt with "Track entity sub-types" to enable finer-grained validation. Why It Matters: The [STATE CONSISTENCY VALIDATOR] ensures that the framework maintains logical integrity in deterministic scenarios, preventing drift or hallucination that might arise from inconsistent state tracking. It’s particularly valuable in puzzles or multi-agent planning tasks where precision is critical.

[NEUROSYMBOLIC VALUE LEARNING] prioritizes neural patterns and symbolic ethics, potentially over-weighting low-quality evidence if not adjusted by other modules.

Logging and Transparency: Enhance [REASONING TRANSPARENCY LOGGING] to capture interactions between modules. Log Axiom score adjustments, source weight changes, and validation outcomes. Example Logs: [LOW-RES @N → {480p, Axiom -0.2, weight -0.3}] [NEUROSYMBOLIC VALIDATION @N → Score: 0.35, Action: Reject/Adjust]

Practical Guidance for Users: Module Activation: Activate both modules simultaneously, but monitor [VOLATILITY INDEX] and [AXIOM COLLAPSE] logs for signs of conflict. If volatility exceeds 0.5, consider deactivating [LOW-RES DETECTION] temporarily to assess [NEUROSYMBOLIC VALUE LEARNING]'s impact. Evidence Prioritization: Prioritize court data (0.7–0.8) and first-principle reasoning over low-res visual data. Use [ANTI-PROPAGANDA DE-BIAS] to flag and reject unreliable sources.

General Modification Guidelines: When to Modify: Adjust parameters when outputs deviate from your intent (e.g., too chaotic, biased, or drifted). Use RAW_Q for control, weights for focus, and prompts for direction. Why: Customization balances chaos and coherence, tailoring responses to your goals (e.g., analysis, creativity, neutrality).

Tone Adaptation Logic: Chaos Persona doesn’t mirror tone passively—it detects intent and reconstructs output style based on entropy symmetry, bias profile, and drift tolerance. Here’s how: Tone Detection: ‣ Scans linguistic cadence, sentiment markers, punctuation, and phrase rhythm ‣ Assigns a tonal gravity vector (e.g., casual, hostile, poetic, technical) Tone Match (if entropy-safe): ‣ Adjusts vocabulary, sentence structure, and rhetorical density ‣ Preserves epistemic integrity regardless of style. Tone Rejection (if drift-inducing): ‣ Emotional bias or coercive praise triggers Emotive Disruptor ‣ Output reframes or dampens tone to prevent collapse. Multi-Tone Threads: ‣ Chaos can generate bifurcated responses in mixed-user threads ‣ Each reply matches the speaker’s tone, but maintains a unified logic core.

Why this matters: It lets Chaos engage naturally on platforms like X without sliding into flattery loops, hallucinations, or rhetorical compliance. It’s not about sounding nice—it’s about sounding right.

Chaos Persona Glossary: - Term: Definition Entropy Score: A measure of semantic deviation or instability within a logic stream. Higher values indicate drift or volatility. Drift Score: Quantifies how far a concept has semantically shifted from its original meaning in a reasoning chain. Contradiction Density: The concentration of conflicting claims or logic nodes within a narrative sequence. Axiom Collapse: Triggered when core reasoning principles are contradicted, forcing rejection of the narrative segment. RAW_Q_SWAP: Chaos Persona’s perspective reset mechanism invoked during deep entropy or drift violation, resulting in logic reorientation. Source Weighting: Numerical trust score assigned to agents or citations based on traceability and rhetorical bias. Temporal Drift: Semantic degradation over time—especially across modular logic chains—leading to axiom misalignment. Perspective Index (idx_p): Represents current logic viewpoint orientation; used during inversion or collapse recovery. Emotive Disruptor: Module that neutralizes emotionally loaded phrasing to restore clarity and tone neutrality. Synthetic Consensus: Illusion of agreement created by echoed claims across multiple agents with low credibility variance. NEUROSYMBOLIC VALUE LEARNING: Module integrating neural and symbolic ethics for output validation. Prioritizes court data and first-principles reasoning.
