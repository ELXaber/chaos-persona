# V06062026
# CAIOS — Andrew  |  Quick Setup Guide

> **What you need before starting:**
> - A computer with **16 GB RAM** recommended (8 GB works for smaller models)
> - An internet connection for the initial download
> - About 20 GB of free disk space (for the AI model)
> - At least 8 GB of VRAM

See Hardware Notes at the bottom for details.

---

## Windows

### Step 1 — Install Python
1. Go to **https://www.python.org/downloads/**
2. Click the big yellow "Download Python 3.x" button
3. Run the installer — **check the box that says "Add Python to PATH"** before clicking Install

### Step 2 — Install Ollama
1. Go to **https://ollama.com/download**
2. Click "Download for Windows" and run the installer
3. When it finishes, Ollama runs in the background automatically

### Step 3 — Run the setup script
1. Open the `Project_Andrew` folder after downloading the Andrew.rar from https://cai-os.com or https://github.com/ELXaber/chaos-persona/tree/main/Project_Andrew and extracting the files.
2. Double-click **`run_caios.bat`**
3. A terminal window opens and walks through the rest automatically:
   - Installs required packages
   - Downloads the AI model (~15 GB, takes 10–30 min depending on connection)
   - Starts the web interface
4. When you see **"Web UI: http://localhost:5000"**, open that address in your browser

> **Next time:** Just double-click `run_caios.bat` again — setup is skipped and it launches directly.
> **Alternate Next time:** Open a terminal window and run python caios_bridge.py then open a browser to http://localhost:5000

---

## macOS

### Step 1 — Install Homebrew (if you don't have it)
Open **Terminal** (press Cmd+Space, type Terminal, press Enter) and paste:
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
Follow the prompts. This only needs to be done once.

### Step 2 — Install Python
```
brew install python@3.12
```

### Step 3 — Run the setup script
In Terminal, navigate to the Project_Andrew folder after downloading the Andrew.rar from https://cai-os.com or https://github.com/ELXaber/chaos-persona/tree/main/Project_Andrew and extracting the files:
```
cd /path/to/Project_Andrew
chmod +x run_caios.sh
./run_caios.sh
```
The script installs Ollama automatically via Homebrew, downloads the model, and starts the interface.

When you see **"Web UI: http://localhost:5000"**, open that in Safari or Chrome.

> **Apple Silicon (M1/M2/M3/M4):** Runs especially well — the unified memory means a 32 GB Mac can run the 27B model comfortably without a separate GPU.

> **Next time:** Just run `./run_caios.sh` from the Project_Andrew folder.

---

## Linux (Ubuntu / Debian)

### Step 1 — Install Python 3.11+
```bash
sudo apt update
sudo apt install python3.12 python3.12-pip python3.12-venv
```
On other distributions (Arch, Fedora, etc.) use the equivalent package manager.

### Step 2 — Run the setup script after downloading the Andrew.rar from https://cai-os.com or https://github.com/ELXaber/chaos-persona/tree/main/Project_Andrew and extracting the files
```bash
cd /path/to/Project_Andrew
chmod +x run_caios.sh
./run_caios.sh
```
The script installs Ollama via the official install script, downloads the model, and starts the interface.

When you see **"Web UI: http://localhost:5000"**, open that in your browser.

> **NVIDIA GPU:** Install NVIDIA drivers (525+) and Ollama will use your GPU automatically. No CUDA toolkit needed separately.
> **AMD GPU:** Supported on Linux via ROCm. Windows AMD GPU acceleration is not yet stable.

> **Next time:** Just run `./run_caios.sh`.

---

## First login

When the browser opens you'll see a sign-in screen:

1. **Username** — enter the name you set during first-time setup (or your first name if you used the personal option)
2. **Password** — only if you chose to set one during setup; otherwise leave blank
3. **Select model** — choose the Qwen model from the list (it will already be selected)
4. Click **Start session**

---

## What the scripts start automatically

| Service | Purpose | Port |
|---|---|---|
| Ollama | Runs the AI model locally | 11434 |
| CAIOS Bridge | Connects the web UI to Andrew | 5000 |
| windows-mcp | Windows UI automation (Windows only) | 8000 |
| MCP filesystem server | Lets Andrew read/write files | 3000 |

All of these run on your local machine. Nothing is sent to external servers unless you configure an API key for OpenAI, Anthropic, or another provider — and that's entirely optional.

---

## Troubleshooting

**"Ollama not found" after installing**
Close the terminal and open a new one, then run the script again. The PATH update sometimes requires a fresh terminal.

**Model download stops partway through**
Just run the script again — Ollama resumes downloads from where they stopped.

**Port already in use error**
Something else is using port 5000. Edit `caios_bridge.py` and change `port=5000` to `port=5001` near the bottom of the file, then use `http://localhost:5001` instead.

**Session expired after 15 minutes**
Normal behaviour — the login screen will reappear automatically. Sign in again to continue. The conversation history is preserved.

**"No models found" on the model selection screen**
Ollama is running but no models are downloaded yet. Open a terminal and run:
```
ollama pull qwen3:27b
```
Then refresh the browser.

**Other issues: check for updates**
If something in CAIOS isn't working as expected, check for updated versions by running update.sh or update.bat.
Downloads anything newer, and backs up the replaced file as filename.bak before overwriting.
Files in the PROTECTED set (system_identity.json, users.json, CAIOS.txt, etc.) are never touched by the updater.
I don't anticipate any new updates to CAIOS.txt (main inference and entropy engine, which can be customized, but you may wish to check for new/optomized versions occasionally, especially if using a smaller LLM than 27b.
It will compare the version #V######## at the top of every file to what's on GitHub at 
https://github.com/ELXaber/chaos-persona/tree/main/Project_Andrew


---

## Hardware notes

| RAM | What runs well |
|---|---|
| 8 GB | 7B models (faster, less capable) |
| 16 GB | 14B models (good balance) |
| 32 GB+ | 27B–32B models (what CAIOS is optimised for) |

| GPU | What runs well | Recomended Min: 3070/3080 Ti, 4070, RX 6800 XT, or the Mac Mini M2 Pro (18–36 GB unified) 
Role | Minimum GPU | Recommended | Model: Best Qwen3 27b or R1 32b with 24GB VRAM/64GB RAM
Sovereign | 12 GB VRAM | 24 GB | Qwen3 16B or DeepSeek-R1 14B
Edge node | 6 GB VRAM | 8 GB | Qwen2.5 7B

16B Q4 quantized (what Ollama pulls by default) sits around 9–10 GB VRAM, leaving -2 GB headroom for the KV cache during inference. That's comfortable on a 12 GB card. The full CAIOS system prompt is roughly 28k characters — at 16B that fits within a 16k context window with room for conversation history, which covers the majority of CAIOS.txt without truncation. The sections that get cut at 16k are the tail end of the Appendix material and some of the detailed test suite comments, which are lower-priority than the core CPOL, ARL, and ethics blocks near the top.
The 27B model gives noticeably better reasoning, especially for the CPOL paradox detection and autonomous specialist deployment. If you're on 8 GB, `qwen2.5:7b` is the recommended fallback — change the pull command in the setup script accordingly.
8B works for edge nodes doing specialist research or curiosity engine tasks — they're running shorter, domain-focused prompts rather than the full system prompt. Wouldn't recommend it for sovereign because the paradox oscillation reasoning degrades noticeably below 14B and it starts collapsing UNDECIDABLE cases to FALSE rather than holding the oscillation.
