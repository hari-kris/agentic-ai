# Ollama + Llama 3.1:8B — Installation Guide
### Agentic AI Course | Module 8 — Local LLM Setup

> **What this covers:** Installing Ollama, pulling Llama 3.1:8B, managing model storage,
> freeing disk space, and running the Streamlit demo app — on Windows, Ubuntu, and macOS.

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Windows Installation](#2-windows-installation)
3. [Ubuntu Installation](#3-ubuntu-installation)
4. [macOS Installation](#4-macos-installation)
5. [Pull and Run Llama 3.1:8B](#5-pull-and-run-llama-318b)
6. [Change Model Storage Location](#6-change-model-storage-location)
7. [Free Up Disk Space](#7-free-up-disk-space)
8. [Run the Streamlit Demo App](#8-run-the-streamlit-demo-app)
9. [Python Wrapper Quick Reference](#9-python-wrapper-quick-reference)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 8 GB | 16 GB |
| Disk (free) | 8 GB | 20 GB+ |
| CPU | 4-core | 6-core (e.g. Ryzen 5 3600) |
| GPU (optional) | — | NVIDIA RTX 3060 12GB |
| OS | Windows 10, Ubuntu 20.04, macOS 12 | Latest version |

> **No GPU?** Ollama runs in CPU-only mode at ~5–8 tokens/sec on a Ryzen 5 3600.
> Good enough for course demos. GPU accelerates to ~40–55 tokens/sec.

---

## 2. Windows Installation

### Step 1 — Download and install Ollama

1. Go to [https://ollama.com/download/windows](https://ollama.com/download/windows)
2. Download `OllamaSetup.exe`
3. Run the installer — click through the wizard (no configuration needed)
4. Ollama starts automatically in the system tray

### Step 2 — Verify installation

Open **Command Prompt** or **PowerShell**:

```powershell
ollama --version
```

Expected output:
```
ollama version 0.x.x
```

### Step 3 — Change model storage location (optional)

By default, Windows stores models at:
```
C:\Users\<YourName>\.ollama\models
```

To change to a custom drive (e.g. `D:\AI\ollama-models`):

```powershell
# Create the folder
mkdir D:\AI\ollama-models
```

Then set the environment variable permanently:

1. Press `Win + R` → type `sysdm.cpl` → Enter
2. Click **Advanced** → **Environment Variables**
3. Under **User variables**, click **New**
4. Variable name: `OLLAMA_MODELS`
5. Variable value: `D:\AI\ollama-models`
6. Click OK → OK → OK
7. **Restart Ollama** from the system tray

Or set it temporarily in PowerShell for the current session:

```powershell
$env:OLLAMA_MODELS = "D:\AI\ollama-models"
```

### Step 4 — Install Python dependencies

```powershell
pip install streamlit requests anthropic
```

---

## 3. Ubuntu Installation

### Step 1 — Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

This installs Ollama as a **systemd service** that starts automatically on boot.

### Step 2 — Verify installation

```bash
ollama --version
sudo systemctl status ollama
```

Expected: `active (running)`

### Step 3 — Change model storage location

Default location (systemd service):
```
/usr/share/ollama/.ollama/models/
```

To move models to a custom location (e.g. `/data/ONLINE_COURSE/Agentic-AI-B1/ollama-models`):

```bash
# 1. Create the folder
sudo mkdir -p /data/ONLINE_COURSE/Agentic-AI-B1/ollama-models

# 2. Set correct ownership
sudo chown -R ollama:ollama /data/ONLINE_COURSE/Agentic-AI-B1/ollama-models

# 3. Write the systemd override
sudo tee /etc/systemd/system/ollama.service.d/override.conf << 'EOF'
[Service]
Environment="OLLAMA_MODELS=/data/ONLINE_COURSE/Agentic-AI-B1/ollama-models"
EOF

# 4. Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart ollama

# 5. Confirm the variable is active
sudo systemctl show ollama | grep Environment
```

### Step 4 — Free up disk space (if root is full)

Check disk usage:
```bash
df -h /
```

Find what is filling root:
```bash
sudo du -sh /usr/local/lib/ollama/* 2>/dev/null | sort -rh | head -10
```

Remove unused CUDA/GPU libraries (safe if you have no GPU):
```bash
sudo rm -rf /usr/local/lib/ollama/cuda_v12
sudo rm -rf /usr/local/lib/ollama/mlx_cuda_v13
sudo rm -rf /usr/local/lib/ollama/cuda_v13
sudo rm -rf /usr/local/lib/ollama/vulkan
```

> **Keep these** — they run inference on CPU:
> `libggml-cpu-*.so`, `libggml-base.so`

General cleanup:
```bash
sudo apt autoremove --purge -y
sudo apt clean
sudo journalctl --vacuum-time=3d
pip cache purge
```

### Step 5 — Install Python dependencies

```bash
pip install streamlit requests anthropic
```

---

## 4. macOS Installation

### Step 1 — Install Ollama

**Option A — Download the app (easiest):**

1. Go to [https://ollama.com/download/mac](https://ollama.com/download/mac)
2. Download `Ollama.dmg`
3. Open the DMG → drag Ollama to Applications
4. Launch Ollama from Applications — it appears in the menu bar

**Option B — Homebrew:**

```bash
brew install ollama
```

Start the service:
```bash
ollama serve &
```

### Step 2 — Verify installation

```bash
ollama --version
```

### Step 3 — Change model storage location (optional)

Default location on macOS:
```
~/.ollama/models/
```

To use a custom path:

```bash
# Add to ~/.zshrc (or ~/.bash_profile)
echo 'export OLLAMA_MODELS="/Volumes/ExternalDrive/ollama-models"' >> ~/.zshrc
source ~/.zshrc

# Create the folder
mkdir -p /Volumes/ExternalDrive/ollama-models
```

For the macOS app (not CLI), set it via launchd:

```bash
sudo mkdir -p /etc/launchd.conf
echo 'setenv OLLAMA_MODELS /Volumes/ExternalDrive/ollama-models' | sudo tee -a /etc/launchd.conf
```

Then restart your Mac for the change to take effect.

### Step 4 — Install Python dependencies

```bash
pip3 install streamlit requests anthropic
```

> **Apple Silicon (M1/M2/M3)?** Ollama uses Metal GPU acceleration automatically.
> Models run significantly faster (~30–50 tokens/sec) with no extra configuration.

---

## 5. Pull and Run Llama 3.1:8B

Same commands on all three operating systems:

```bash
# Download the model (~4.7 GB — runs once)
ollama pull llama3.1:8b

# Verify it downloaded
ollama list

# Test in interactive chat mode
ollama run llama3.1:8b
```

Inside the chat, type your message and press Enter. Type `/bye` to exit.

**Quick one-line test:**

```bash
ollama run llama3.1:8b "What is an agentic AI system? Answer in 2 sentences."
```

> **First response** takes 15–30 seconds on CPU (model loading into RAM).
> Subsequent responses are faster (~5–8 tokens/sec on Ryzen 5 3600).

**Check model storage after download:**

```bash
# Linux / macOS
du -sh ~/.ollama/models/          # default (macOS / manual run)
du -sh /usr/share/ollama/.ollama/models/  # Ubuntu systemd default

# Windows (PowerShell)
Get-ChildItem "$env:USERPROFILE\.ollama\models" | Measure-Object -Property Length -Sum
```

---

## 6. Change Model Storage Location

### Summary table

| OS | Default location | Override method |
|----|-----------------|-----------------|
| Windows | `C:\Users\<name>\.ollama\models` | Environment variable via System Properties |
| Ubuntu (systemd) | `/usr/share/ollama/.ollama/models` | `/etc/systemd/system/ollama.service.d/override.conf` |
| Ubuntu (manual) | `~/.ollama/models` | `export OLLAMA_MODELS=...` in `~/.bashrc` |
| macOS (app) | `~/.ollama/models` | `/etc/launchd.conf` + restart |
| macOS (CLI) | `~/.ollama/models` | `export OLLAMA_MODELS=...` in `~/.zshrc` |

---

## 7. Free Up Disk Space

### Remove a model

```bash
ollama rm llama3.1:8b
```

### Remove all models

```bash
# List all models first
ollama list

# Remove each one
ollama rm <model-name>
```

### Ubuntu — remove GPU libraries if no GPU installed

```bash
sudo du -sh /usr/local/lib/ollama/* | sort -rh
sudo rm -rf /usr/local/lib/ollama/cuda_v12
sudo rm -rf /usr/local/lib/ollama/mlx_cuda_v13
sudo rm -rf /usr/local/lib/ollama/cuda_v13
sudo rm -rf /usr/local/lib/ollama/vulkan
```

Frees ~5 GB. Ollama continues to work on CPU.

### Windows — clear model cache

```powershell
# Remove all model blobs
Remove-Item "$env:USERPROFILE\.ollama\models\blobs\*" -Recurse -Force
Remove-Item "$env:USERPROFILE\.ollama\models\manifests\*" -Recurse -Force
```

### macOS — clear model cache

```bash
rm -rf ~/.ollama/models/blobs/*
rm -rf ~/.ollama/models/manifests/*
```

---

## 8. Run the Streamlit Demo App

The demo app (`app.py`) demonstrates three agentic patterns using Ollama (local) or Anthropic (cloud).

### Step 1 — Make sure Ollama is running

```bash
# Ubuntu
sudo systemctl start ollama
ollama list   # confirm llama3.1:8b is present

# macOS / Windows
# Launch the Ollama app from Applications/Start Menu
```

### Step 2 — Install dependencies

```bash
pip install streamlit requests anthropic
```

### Step 3 — Run the app

```bash
# Navigate to your course folder
cd /data/ONLINE_COURSE/Agentic-AI-B1/   # Ubuntu
# cd C:\ONLINE_COURSE\Agentic-AI-B1\    # Windows
# cd ~/ONLINE_COURSE/Agentic-AI-B1/     # macOS

streamlit run app.py
```

Opens at: [http://localhost:8501](http://localhost:8501)

### Step 4 — Switch between providers

In the **sidebar**:
- Select `ollama` → uses local Llama 3.1:8B (no cost, no API key)
- Select `anthropic` → uses Claude (requires API key from [console.anthropic.com](https://console.anthropic.com))

The agent code is **identical** for both providers — this is the core lesson.

---

## 9. Python Wrapper Quick Reference

```python
from app import LLMWrapper

# ── Local Ollama ──────────────────────────────────────────────
llm = LLMWrapper(
    provider="ollama",
    model="llama3.1:8b",
    temperature=0.7,       # 0.0 = deterministic, 1.0 = creative
    max_tokens=512
)

# ── Anthropic Claude ──────────────────────────────────────────
llm = LLMWrapper(
    provider="anthropic",
    model="claude-haiku-4-5-20251001",
    temperature=0.7,
    max_tokens=512,
    api_key="sk-ant-..."
)

# ── Same call interface for both ──────────────────────────────
response, elapsed = llm.call(
    prompt="What is an agentic AI system?",
    system="You are a helpful tutor."
)
print(f"Response ({elapsed}s): {response}")
```

### Temperature guide (course colour coding)

| Temperature | Use case | Colour |
|------------|----------|--------|
| `0.0` | Evaluators, routers, classifiers | 🔵 Blue |
| `0.2` | Planners, structured output | 🔵 Blue |
| `0.5` | Executors, general tasks | 🟠 Orange |
| `0.9–1.0` | Creative generation | 🔴 Red |

---

## 10. Troubleshooting

### Ollama service not starting (Ubuntu)

```bash
sudo systemctl status ollama
sudo journalctl -u ollama -n 50
sudo systemctl restart ollama
```

### Cannot connect to Ollama (Python / Streamlit)

```bash
# Check the service is running
curl http://localhost:11434/api/tags

# Expected: JSON list of installed models
```

### apt lock error during install (Ubuntu)

```bash
# Wait for background apt to finish
ps aux | grep apt

# If no apt process running, remove stale lock
sudo rm /var/lib/apt/lists/lock
sudo rm /var/cache/apt/archives/lock
sudo rm /var/lib/dpkg/lock-frontend
sudo apt-get update
```

### Model pulls to wrong location (Ubuntu)

```bash
# Verify the environment variable is set
sudo systemctl show ollama | grep Environment

# If missing, rewrite the override file
sudo tee /etc/systemd/system/ollama.service.d/override.conf << 'EOF'
[Service]
Environment="OLLAMA_MODELS=/data/ONLINE_COURSE/Agentic-AI-B1/ollama-models"
EOF

sudo systemctl daemon-reload && sudo systemctl restart ollama
```

### Slow responses on CPU

Expected performance on Ryzen 5 3600 (no GPU):
- First token: 15–30 seconds (model loading)
- Subsequent tokens: 5–8 tokens/sec
- Full response (200 tokens): ~30–40 seconds

This is normal. For faster responses during live demos, use shorter prompts and set `max_tokens` to 256.

### Streamlit port already in use

```bash
streamlit run app.py --server.port 8502
```

---

*Agentic AI Course — Module 8 | Updated May 2026*
