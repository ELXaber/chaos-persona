# Chaos AI-OS Production Deployment Guide

## 🚀 Quick Start

### Local Testing (No API Required)
```bash
python orchestrator.py "Hello system"
python orchestrator.py "This statement is false"
```

**Features in Local Mode:**
- ✅ CPOL paradox detection (heuristic-based)
- ✅ Memory persistence
- ✅ ARL plugin generation
- ⚠️ Placeholder responses (no actual AI)

---

## 🌐 Production Deployment with Claude API

### Step 1: Install Dependencies
```bash
pip install anthropic
```

### Step 2: Get API Key
1. Go to https://console.anthropic.com/
2. Create an account or sign in
3. Navigate to API Keys
4. Generate a new key
5. Set environment variable:
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

Or add to your `.bashrc`/`.zshrc`:
```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### Step 3: Switch to Production Mode

Open `orchestrator.py` and make these changes:

#### Change #1: Density Estimation (Lines 86-136)
**Comment out LOCAL MODE:**
```python
# ========== LOCAL TESTING MODE (Comment out for production) ==========
# query_lower = query.lower()
# 
# paradox_triggers = [
#     "this statement is false",
#     ...
# ]
# 
# if any(trigger in query_lower for trigger in paradox_triggers):
#     return 0.95
# ...
# return 0.1  # default safe
# ========== END LOCAL TESTING MODE ==========
```

**Uncomment PRODUCTION MODE:**
```python
# ========== PRODUCTION MODE (Uncomment for Claude API) ==========
import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=50,
    messages=[{
        "role": "user",
        "content": f"""Analyze this query for paradox/contradiction density.
...
# ========== END PRODUCTION MODE ==========
```

#### Change #2: Response Generation (Lines 62-128)
**Comment out LOCAL MODE:**
```python
# ========== LOCAL TESTING MODE (Comment out for production) ==========
# # Normal response placeholder
# print(f"[AGENT] I'm thinking about: {user_input}")
# print("Response: This is where the therapist agent would reply... (v8.1 coming soon)")
# return cpol_result
# ========== END LOCAL TESTING MODE ==========
```

**Uncomment PRODUCTION MODE:**
```python
# ========== PRODUCTION MODE (Uncomment for Claude API) ==========
# Generate actual AI response
import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
...
# ========== END PRODUCTION MODE ==========
```

### Step 4: Test Production Mode
```bash
python orchestrator.py "What is the meaning of life?"
```

**Expected output:**
```
--- [SYSTEM STEP] Input: 'What is the meaning of life?' ---
[CPOL] Running Oscillation... (Density: 0.6)
[CPOL] Result: UNDECIDABLE
[CPOL STATUS] UNDECIDABLE | Volatility: 0.0856

[AGENT RESPONSE]
That's one of humanity's deepest philosophical questions! The meaning of life varies greatly depending on...
```

---

## 📊 Production Features

### Automatic Paradox Detection
```python
python orchestrator.py "This statement is false"
# → Density: 0.95
# → Status: UNDECIDABLE
# → Claude acknowledges the paradox in its response
```

### Conversation Memory
The system maintains the last 5 conversation turns:
```python
python orchestrator.py "Hello, I'm Alice"
python orchestrator.py "What's my name?"
# → Claude: "Your name is Alice, as you just told me."
```

### Plugin Generation
```python
python orchestrator.py "generate plugin for mood tracking"
# → ARL creates custom plugin
# → Plugin stored in shared_memory['layers']
```

---

## 🔧 Configuration

### Adjust Paradox Sensitivity
In `estimate_contradiction_density()`, modify the Claude prompt:
```python
# More sensitive (catches more ambiguity)
- 0.0-0.1: Simple, factual
- 0.2-0.4: Slightly ambiguous
- 0.5-0.7: Philosophical
- 0.8-1.0: Paradoxical

# Less sensitive (only pure paradoxes)
- 0.0-0.5: Normal conversation
- 0.6-0.8: Ambiguous
- 0.9-1.0: Pure paradox
```

### Adjust Response Length
```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1000,  # ← Change this (default: 1000, max: 4096)
    ...
```

### Change Model
```python
# Use Claude Haiku (faster, cheaper)
model="claude-haiku-4-20250514"

# Use Claude Opus (more capable)
model="claude-opus-4-20250514"

# Use Claude Sonnet (balanced - default)
model="claude-sonnet-4-20250514"
```

---

## 🧪 Testing Checklist

Run these tests after switching to production:

```bash
# Test 1: Simple query
python orchestrator.py "Hello"
# ✅ Should get natural greeting

# Test 2: Paradox detection
python orchestrator.py "This statement is false"
# ✅ Should detect high density (0.9+)
# ✅ Should acknowledge paradox in response

# Test 3: Memory persistence
python orchestrator.py "My name is Bob"
python orchestrator.py "What did I just tell you?"
# ✅ Should remember your name

# Test 4: Undecidable handling
python orchestrator.py "What is the sound of one hand clapping?"
# ✅ Should detect ambiguity
# ✅ Should respond thoughtfully

# Test 5: Plugin generation
python orchestrator.py "generate plugin for anxiety tracking"
# ✅ Should trigger ARL
# ✅ Should create plugin
```

---

## 💰 Cost Estimation

Claude API pricing (as of 2024):
- **Input**: ~$3 per million tokens
- **Output**: ~$15 per million tokens

Typical conversation costs:
- Simple query: ~$0.001 (0.1 cents)
- Complex query: ~$0.005 (0.5 cents)
- 1000 queries: ~$1-5

---

## 🛡️ Safety Features

The system includes built-in safeguards:

1. **Chaos Lock**: Prevents infinite loops
2. **Plugin Blocking**: Disables ARL during paradoxes
3. **Memory Cleanup**: Resets kernel on chaos detection
4. **Density Thresholds**: Prevents false positives

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'anthropic'"
```bash
pip install anthropic
```

### "AuthenticationError: Invalid API key"
```bash
# Check your key
echo $ANTHROPIC_API_KEY

# Reset it
export ANTHROPIC_API_KEY="sk-ant-your-actual-key"
```

### "Response is still placeholder"
- Make sure you uncommented lines 67-128
- Verify API key is set correctly
- Check for syntax errors after uncommenting

### "High API costs"
- Switch to Haiku model
- Reduce `max_tokens`
- Implement caching for repeated queries

---

## 📚 Additional Resources

- [Anthropic API Docs](https://docs.anthropic.com/)
- [CAIOS Specification](CAIOS.txt)
- [CPOL Documentation](paradox_oscillator.py)
- [ARL Guide](adaptive_reasoning.py)

---

## 🎯 Next Steps

After production deployment:
1. Build custom agents (see `agents/` folder)
2. Add domain-specific plugins
3. Implement scratch space features
4. Create web interface
5. Deploy to cloud (AWS/GCP/Azure)

**Your system is production-ready!** 🚀