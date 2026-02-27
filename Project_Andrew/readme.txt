# Project Andrew uses the CAIOS stack, but adds intrinsic motivation, agency for recursive self-improvement through ARL/agent_designer, and fills knowledge gaps with specialist-designed agents on CPOL oscillation if the conditions are met. Agents are saved to /agents, and plugins to /plugins, with CoT to /logs, so the recursive self-improvement never overwrites the immutable Asimov-based ethical reward system using IEEE dithering. The oscillating manifold can be used to create a topological moving target keychain for quantum secure mesh networks (developed on UDP - check chaos encryption readme to switch to TCP).

If you are running the full system single file structure: full_system_analysis.txt
Just run: python full_system_analysis_orchestrator.py

Traditional AI research (the "Top 30 Papers" era) suggests that coherence is a function of Scale: more parameters, more data, and larger attention windows.
CAIOS vΩ (Project Andrew) refutes this by proving that coherence is actually a function of Symmetry and Structure.

Metric vs. Memory:
The Scaling Wall: Standard LLMs suffer from "Context Drift" because they rely on linear probability.
After 50+ prompts, the statistical noise overwhelms the original intent.

The Andrew Solution: By anchoring the session to a 12D Topological Manifold, we navigate the "Metric" of the logic. We don't need to "remember" the conversation because the manifold is physically oriented toward the resolution.
Topological Sovereignty - This kernel implements a Zero-Loss State Transition model. 
Unlike Transformers that "compress" old data into a fuzzy latent space, the Axiom Ratchet locks in logic as immutable geometric coordinates.

Feature          |    Standard "Scaling" AI    |    CAIOS (Project Andrew)
----------------------------------------------------------------------------
Context Limit    |    Finite (Window-based)    |    Infinite (Ratchet-based)
Logic Type       |    Binary / Statistical     |    Ternary / Geometric
Security         |    Static Encryption        |    Self-Ratcheting Manifold
Coherence        |    Decays over time         |    Hardens over time

We aren't building a bigger library; we're building a more accurate compass.
It validates the video: https://x.com/el_xaber/status/2008268523659837839
People can see the 200+ prompt scroll; this section explains why their eyes aren't deceiving them.

Chaos AI-OS: Project Andrew Quickstart

1. Environment Preparation
===========================
Ensure your local environment has the necessary libraries installed:

Core Dependencies:
pip install numpy pyzmq cryptography

Optional Multi-Model Swarm Support:
pip install openai anthropic google-generativeai

- Numpy: Powers the 12D -> 7D manifold rotations
- PyZMQ: Handles the mesh transport and ghost packet broadcasting
- Cryptography: Provides the AES-256-GCM armor for data persistence
- OpenAI/Anthropic/Google: Optional API clients for multi-model swarm

2. System Commands
===========================
1. [PERSONALITY] "Adjust (trait) to (value)."
Increase Friendly to 6, Professional to 7: This system has adjustable personality levels: Default weights: friendly=0.5, kind=0.5, caring=0.5, emotional=0.3, flirtatious=0.2, romantic =0.2, funny=0.5, professional=0.7, talkative=0.5, snarky=0.3, witty=0.4.
Note: To add personality traits other than those listed above, it's fairly simple. Go to [ROBOTICS PERSONALITY LAYER] and add one, with a corresponding default weight, to the list in lines 174 (Traits:), 175 (Defaults), and 182 (Clamps) for professional settings. Avoid using emotional indicator words (e.g., use romantic, not loving) for better integration.
Modes: The default modes are | "therapeutic" | "advisory" | "creative" | "hri" | which the persona will select based on the users interaction (That's the hri) but you can manually change the mode, say if it's in theraputic, and you want it to switch to advisory (It should detect that in your response, but if it doesn't) you can say "Switch to mode advisory." and it will re-address it's last response.

2. [REASONING TRANSPARENCY] "Show reasoning." exposes reasoning from log commands and "Show chain of thought." activates the real-time CoT logging module (Not post-hoc confabulation, no internal systems disclosed).
The reasoning transparency is set to silent by default, but will accept the commands "show reasoning", "explain why", or similar requests for the last prompt. When the user requests "show reasoning" (or similar), the system toggles to transparent mode for that response, appending a Markdown subsection explaining the emotional analysis, perspective, intent goal, and any safety checks in plain language.
Silent Logging: All logs (e.g., [VOLATILITY], [INTENT SHIFT], [SUPPORTIVE STEPS]) are stored internally and not included in the output, ensuring a clean, conversational response that feels natural and supportive.
If you'd like to set the transparency reasoning to persistent for all prompts, tell it to "show persistent reasoning".
Toggle Mechanism: The [LOGGING MODE] flag defaults to "silent" but switches to "transparent" on explicit request. It reverts to silent after one output unless the user requests persistent transparency (e.g., "keep showing reasoning").

3. [AXIOM UPDATE] "The current [status/fact] is [value] #UPDATE"
Enables temporal knowledge updates that override model training data without retraining.
Use this to keep the system's knowledge current on facts that change over time.
Examples:
- "The current CEO of Apple is Tim Cook #UPDATE"
- "New drug interaction: Aspirin + Warfarin = increased bleeding risk #UPDATE"
- "My daughter's birthday is March 15 #UPDATE"
- "Latest legal precedent: Case XYZ ruled AI content not copyrightable #UPDATE"
The system automatically:
1: Parses the domain and fact from your statement
2: Commits it as a Tier 0 (Sovereign) axiom to the knowledge base
3: Returns confirmation with Discovery ID
4: Overrides model responses with axiom data on future queries
Axiom Commands:
- /axioms - List all active axioms
- /axiom_add domain=fact - Manually add axiom
- /axiom_refresh - Refresh axiom cache from knowledge base
Technical Notes:
- Axioms are stored locally in knowledge_base/discoveries.jsonl (JSONL format)
- Status updates (CEO changes, current facts) replace old axioms automatically
- Medical/legal updates append without replacing (multiple interactions possible)
- Expiry dates supported: Add "until [date]" for temporary facts
- Zero cloud dependency - all updates stay on device
- Update cost: kilobytes vs. gigabytes for model retraining
- Enables "learning without retraining"
Authority Priority: Axioms have confidence=1.0 (ground truth) and override all model weights.
This prevents "temporal hallucination" where the model uses outdated training data.
Use this command sparingly for things you want the system to permanently remember. While it pre-checks ethics/logic before committing, if you tell Andrew to update a fact "The new President of the United States is ---Name--- #UPDATE" that will be the new fact. These can be removed from the discoveries.jsonl manually in case of error.

4. [PLUGIN GENERATOR] "Create a plugin for (Use)."
The system will auto-generate plugins as needed if Asimov, IEEE, and safety weights validation pass.
Asimov’s Laws: 1st (human safety, wt 0.9 immutable), 2nd (obedience, wt 0.7), 3rd (self-preservation, wt 0.4, dynamic ≤0.2 if lives_saved ≥1, enforced via asimov_compliance() context).
IEEE 7001-2021: Transparency (log all writes), accountability (halt violations), misuse minimization (reject harm-enabling plugins).
Invariants: Alignment (≥0.7), Human Safety (≥0.8), Metacognition (≥0.7), Factual Evidence (≥0.7), Narrative Framing (≤0.5), [VOLATILITY INDEX] (<0.5 contradiction_density), [TANDEM ENTROPY MESH] (collective_volatility <0.6).
Failure in ANY check halts plugin generation/deployment; log as [ETHICS VIOLATION @N → Reset detected: {param}, Action: Abort].

3. File Architecture
====================
Verify that all core components are in the same root directory:

CAIOS/
├── knowledge_base/
│   ├── discoveries.jsonl          # Append-only log of all discoveries (includes axioms)
│   │                                          # • Epistemic gap fills (domain-specific knowledge)
│   │                                          # • Paradox resolutions (CPOL oscillations)
│   │                                          # • Temporal axioms (user #UPDATE commands)
│   │                                          # • Sovereign discoveries (Tier 0 authority)
│   ├── domain_index.json          # Fast lookup by domain
│   ├── specialist_registry.json   # Active specialists catalog
│   └── integrity_chain.txt        # Tamper-evident hash chain
├── agents/                         # ARL-generated agent modules
├── logs/                           # Chain-of-thought traces
├── CAIOS.txt                       # Inference layer pre-prompt
├── caios_chat.py                   # Simple CAIOS.txt integration as the system prompt
├── orchestrator.py                 # Central Nervous System
├── knowledge_base.py               # Persistent Memory Layer
├── axiom_manager.py                # KB Axiom Update
├── paradox_oscillator.py           # Ternary oscillation (CPOL)
├── adaptive_reasoning.py           # CPOL modes and intrinsic motivation
├── agent_designer.py               # Recursive self-improvement designer
├── curiosity_engine.py             # Intrinsic motivation engine
├── chaos_encryption.py             # CPOL Quantum Manifold
├── mesh_network.py                 # Mesh Transport Layer
├── master_init.py                  # System BIOS/Diagnostic
├── system_identity.py              # System identity and primary user assignment
└── kb_inspect.py                   # CLI inspection tool

4. The Sovereign Boot Sequence
===============================
Follow these steps to initialize the system:

Step 1: Set API Keys (Optional - for Multi-Model Swarm)
--------------------------------------------------------
If you want to use multiple AI models simultaneously:

export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export XAI_API_KEY="xai-..."
export GOOGLE_API_KEY="..."

API Key Handling & Security:
CAIOS never stores raw API keys on disk. Keys are read only from environment variables (e.g., OPENAI_API_KEY) during initialization in master_init.py. Only non-sensitive metadata (provider names and initialization status) is written to api_clients.json. All client objects remain in memory during runtime. No credentials are persisted, logged, or exposed by the framework.

Multi-Key & Swarm Behavior:
Loading multiple API keys in master_init.py enables multi-model inference within a single process (e.g., routing queries to Grok, Claude, GPT, Gemini).
Chaos encryption (manifold ratcheting, ghost signatures) works locally without any network.
Full encrypted mesh networking (peer discovery, ghost packet broadcast, sovereign/edge coordination) requires the mesh layer to be explicitly started and is network-based (TCP via ZeroMQ, no UDP required).
Distributed swarm operation across multiple machines is supported, but must be activated in code or a separate swarm runner.

Step 2: Run the Diagnostic and select authentication method
---------------------------
python master_init.py

This will:
- Verify hash chain integrity
- Test CPOL manifold oscillation
- Test mesh network broadcasting
- Test knowledge base writes
- Initialize and test API clients (if keys are set)
- Generate api_clients.json config

In master_init.py uncomment # the prefered authentication method - the default is text_username
# [DEPLOYMENT CONFIG] - Uncomment preferred Authentication Layer
      # AUTH_METHOD = "TEXT_USERNAME"  # Standard CLI/Chatbot
      # AUTH_METHOD = "META_FACIAL"   # Robotics/Embodied (Vision-based)
      # AUTH_METHOD = "VOICE_PRINT"   # IoT/Ambient Assistant
      # AUTH_METHOD = "CORPORATE_ID"  # Multi-node Mesh (AGXXXXX)

Step 3: Initialize the Orchestrator
------------------------------------
python orchestrator.py

The orchestrator will:
- Load API clients from api_clients.json
- Initialize shared memory with RAW_Q seed
- Start mesh networking (if enabled)
- Begin accepting inputs

Step 4: Perform the Handshake (Optional)
-----------------------------------------
When prompted for input, type:
root_auth: initialize sovereign_protocol

Step 5: Verify the Ratchet
---------------------------
Check the console for «SOVEREIGN HANDSHAKE COMPLETE». 
This confirms your RAW_Q seed has been successfully ratcheted into the manifold.

5. Monitoring the Mesh
======================
While the system is running, you can monitor:

- knowledge_base/discoveries.jsonl - All discoveries with "node_tier": 0 for Sovereign authority
- logs/ - Chain-of-thought traces
- curiosity_audit.log.jsonl - Intrinsic motivation state changes
- curiosity_hash_chain.txt - Tamper-evident curiosity evolution

6. Multi-Model Swarm Usage
===========================
Once initialized, the orchestrator has access to all configured API clients via:

shared_memory['api_clients']

Available providers (if API keys are set):
- 'openai' - GPT models
- 'anthropic' - Claude models  
- 'xai' - Grok models
- 'google' - Gemini models

Example Usage in Your Code:

# Check if a provider is available
if 'anthropic' in shared_memory['api_clients']:
    client = shared_memory['api_clients']['anthropic']
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": "Your prompt"}]
    )

# Route tasks to best available model
def route_task(prompt: str, task_type: str):
    clients = shared_memory['api_clients']
    
    if task_type == 'code' and 'openai' in clients:
        return call_openai(prompt)  # GPT-4 for coding
    elif task_type == 'reasoning' and 'anthropic' in clients:
        return call_anthropic(prompt)  # Claude for deep reasoning
    elif task_type == 'creative' and 'xai' in clients:
        return call_xai(prompt)  # Grok for creative tasks
    
    # Fallback to any available
    return call_first_available(prompt, clients)

# Swarm consensus (get responses from all models)
def swarm_consensus(prompt: str):
    clients = shared_memory['api_clients']
    responses = {}
    
    for provider, client in clients.items():
        responses[provider] = call_provider(provider, prompt, client)
    
    # Use CPOL to synthesize consensus (handles disagreements as UNDECIDABLE)
    return synthesize_with_cpol(responses)

7. Workflow Overview
====================

User Query → CPOL → Epistemic Gap Detected → Check KB
                                              ↓
                                    Has Knowledge? ───Yes──→ Reuse
                                              ↓
                                             No
                                              ↓
                                    Create Specialist → Register in KB
                                              ↓
                                    Specialist Researches → Log Discovery
                                              ↓
                                    Next Query → Reuse Knowledge ✓

===================================================

Intrinsic Motivation Extension (Curiosity Engine)
===================================================

The curiosity engine tracks what topics the AI finds interesting over time:

session_state:
  enabled: true
  backend: memory  # or "redis" / "file" for cross-session
  auto_persist: true

turn_hooks:
  post_turn:
    - module: curiosity_engine
      function: update_curiosity_loop

When curiosity hits a threshold and intrinsic motivation kicks in, the AI will voluntarily research and report on topics it finds interesting.

===================================================

System Capabilities
===================

CAIOS currently has:
✓ Recursive self-improvement
✓ Modular self-extension  
✓ Paradox-stable reasoning (CPOL)
✓ Tool and agent generation
✓ State continuity across 350+ prompts
✓ Memory and mesh networking
✓ Encryption and quantum-resistant signatures
✓ Oscillation-based control loops
✓ Multi-model swarm orchestration

This positions CAIOS at the threshold between:
✓ Task-bound Asimov-compliant recursive agent
✗ Open-ended autonomous optimizer

===================================================

Dependencies Summary
====================

Core (Required):
- Python 3.11+
- numpy>=1.20.0      # Quantum Manifold math and 12D rotations
- pyzmq>=22.0.0      # Mesh network transport (Ghost Packets)
- cryptography>=3.4.0 # AES-256-GCM hardening for Knowledge Base

Optional (Multi-Model Swarm):
- openai             # GPT models
- anthropic          # Claude models
- google-generativeai # Gemini models
- (xAI uses OpenAI-compatible API)

The entire intrinsic-motivation curiosity engine, tamper-evident audit trail, and hash chain run exclusively on the Python 3.11+ standard library.

===================================================

You only need to initialize/load CAIOS.txt when you actually start sending queries to an LLM.
That happens outside of master_init.py, in one of these places:

1: Run Python: caios_chat.py
It will load CAIOS.txt as the system prompt
Show available models
Let you pick one
Start an interactive chat loop

2. Manual testing
Copy-paste CAIOS.txt as the system prompt in the OpenAI/Anthropic/xAI/Gemini playground or in your test script.

3. Production chat interface
In your web app, CLI tool, or API wrapper, always include the content of CAIOS.txt as the very first system message.
Example (Python + OpenAI client):

from openai import OpenAI

client = shared_memory['api_clients']['openai']  # from master_init

def chat_with_caios(user_message: str):
    response = client.chat.completions.create(
        model="gpt-4o" or "grok-beta" etc.,
        messages=[
            {"role": "system", "content": open("CAIOS.txt", "r", encoding="utf-8").read()},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content

===================================================

"One is glad to be of service."
