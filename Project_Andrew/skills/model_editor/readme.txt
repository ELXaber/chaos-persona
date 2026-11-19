Prereqs: a neuron-steering checkout with uv, the HF weights for the target (the first export downloads them), the env vars (CAIOS_NEURON_STEERING_DIR, CAIOS_EDIT_BASE_GGUF, optional export/probe backends), and skills/model_editor/ copied into the project.

E.g., https://github.com/metrovoc/neuron-steering

For the tool editor to work, rename the tool_dispatcher in /CAIOS to tool_dispatcher_old and place this tool_dispatcher in /CAIOS
Leave everything else (init, apply, probe, schema, skills, verify, and readme) in this directory /skills/model_editor/.

Start order:
Ollama with the driver model, then the bridge (python caios_bridge.py). Set CAIOS_BACKEND=ollama explicitly.
Target llama-server on port 8081 (no control vector): llama-server.exe -m <target.gguf> --port 8081 --ctx-size 8192 -ngl 99 --chat-template chatml.

Session: ask the model to load the skill and describe the failure. When it runs apply_edits, a confirmation prompt appears in the bridge terminal and auto-denies after 30 seconds, so the user needs to be watching it.

Relaunch: start the printed launch_command on 8082, then tell Andrew “steered server is up”. It calls check_steered.

VRAM warning: the 27B plus a bf16 4B plus a second 4B copy is a lot. Suggest stopping the 8081 server once the baseline is captured (it’s stored in the manifest), or running the 4B quantized if memory is tight. The export itself also loads the HF model briefly.

Known gap: the probe step has no backend yet; apply_edits and check_steered work today, and users can supply candidate neurons by hand until a probe backend is configured.