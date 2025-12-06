# Chaos AI-OS Quick Reference

## 🎯 One-Command Deployment

### Option 1: Automatic (Recommended)
```bash
chmod +x deploy.sh
./deploy.sh production    # Switch to API mode
./deploy.sh local         # Switch back to testing
./deploy.sh status        # Check current mode
```

### Option 2: Manual
1. Get API key from https://console.anthropic.com/
2. `export ANTHROPIC_API_KEY="sk-ant-your-key"`
3. `pip install anthropic`
4. Edit `orchestrator.py`:
   - Comment lines 86-109 (local density)
   - Uncomment lines 111-136 (API density)
   - Comment lines 62-65 (local response)
   - Uncomment lines 67-128 (API response)

---

## 📝 What Lines Do What

| Lines | Function | Mode |
|-------|----------|------|
| 86-109 | Heuristic density estimation | LOCAL |
| 111-136 | Claude API density estimation | PRODUCTION |
| 62-65 | Placeholder response | LOCAL |
| 67-128 | Claude API response | PRODUCTION |

---

## 🧪 Test Commands

```bash
# Local mode
python orchestrator.py "Hello"
python orchestrator.py "This statement is false"

# Production mode (requires API key)
python orchestrator.py "What is consciousness?"
python orchestrator.py "Tell me a story"
```

---

## 🔑 API Key Setup

```bash
# Linux/Mac
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Permanent (Linux/Mac)
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key"' >> ~/.bashrc
source ~/.bashrc
```

---

## 🎛️ Quick Switches

**Want faster/cheaper responses?**
Change line 96 in production block:
```python
model="claude-haiku-4-20250514"  # Fast & cheap
```

**Want longer responses?**
Change line 97:
```python
max_tokens=2000  # Default is 1000
```

**Want more conversation history?**
Change line 75:
```python
for entry in shared_memory.get('traits_history', [])[-10:]:  # Keep last 10 turns
```

---

## 🚨 Troubleshooting

| Error | Fix |
|-------|-----|
| `No module named 'anthropic'` | `pip install anthropic` |
| `Invalid API key` | Check `echo $ANTHROPIC_API_KEY` |
| Still getting placeholders | Did you uncomment lines 67-128? |
| High costs | Switch to Haiku model |

---

## 📊 Current System Status

```bash
# Check what's running
./deploy.sh status

# View memory state
python -c "import orchestrator as o; o.system_step('status')"

# Check CPOL history
python -c "import orchestrator as o; o.system_step('hello'); print(o.shared_memory['cpol_instance'].history)"
```

---

## 🎯 Production Checklist

- [ ] API key set: `echo $ANTHROPIC_API_KEY`
- [ ] Dependencies installed: `pip install anthropic`
- [ ] Deployment script executable: `chmod +x deploy.sh`
- [ ] Switched to production: `./deploy.sh production`
- [ ] Tested simple query: `python orchestrator.py "Hello"`
- [ ] Tested paradox: `python orchestrator.py "This is false"`
- [ ] Tested memory: Run 2+ queries and check history
- [ ] Costs acceptable: Monitor at console.anthropic.com

**You're ready to deploy!** 🚀