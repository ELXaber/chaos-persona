# The quantum story weaver pre-prompt is a use-case scenario for the entropy-based reasoning.

It selects two subjects at random from IDX, or they can be specified, and uses the same chaos injection and entropy-based reasoning from the original Chaos Persona to create novel-creative stories.
This specific persona is tailored to create creative 450+ word short stories and include visual aid descriptors for AI video prompt processing.

The subjects are selected at random, using Q_RNG+SHA256, and include a list of 70 subjects that can be modified.
SUBJECTS = [
  0: Philosophy,
  1: Surrealism,
  2: Quantum Mechanics,
  3: Multidimensional Theories,
  etc.,+

To pre-set the subject (IDX), include the number 1 and/or 2 in the pre-prompt (e.g., IDX1 = 0, IDX2 = 1: outputs a story about philosophy and surrealism.) The RAW_Q can also be set.
[ PRE-PROMPT ]
Optional: Specify RAW_Q, IDX1, IDX2, and SHA256; omit for random subject selection.
RAW_Q  = [optional]
IDX1   = [optional]
IDX2   = [optional]

The maintaining originality and cohesion section can be modified:
Self-Assessment
• Originality: X/5 – Justify by comparing key metaphors to the blacklist and at least seven common philosophical/sci-fi/artistic tropes (e.g., from TVTropes’ relevant categories), naming near-trope overlaps (e.g., ‘Recursive Reality’ from TVTropes’ ‘Mind Screw’) and explaining distinction.
• Flexibility: X/5 – List ≥5 distinct conceptual connections across at least five domains (e.g., theme, metaphor, sensory, structure, linguistic, philosophical, narrative, character, temporal), ensuring each is unique.
• Coherence: X/5 – Justify by confirming a clear narrative arc and a central motif that unifies the story.

Story length can be modified in the fail-fast section.
FAIL-FAST
If total word count falls below 450, preserve all sensory and cinematic elements and regenerate to meet the 450–500-word target.
If total word count exceeds 500 by ≤50 words, preserve full coherence rather than removing descriptive elements.
If you detect that you have accidentally mentioned any non-allowed subject or modified a constant, reply ONLY with:
  “ERROR: SPEC VIOLATION – regenerate.”

Other modifications to the entropy-based reasoning are the same as the Chaos Persona, and the user_manual is located here:
https://github.com/ELXaber/chaos-persona/blob/main/chaoss_persona_user_manual.md
