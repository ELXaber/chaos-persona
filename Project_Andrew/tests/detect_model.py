# V06222026
# detect_model.py  — called by run_caios.bat and run_caios.sh
import subprocess, sys, platform

def get_vram_mb():
    # NVIDIA
    try:
        out = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=memory.total',
             '--format=csv,noheader,nounits'],
            stderr=subprocess.DEVNULL, text=True
        )
        return max(int(x.strip()) for x in out.strip().splitlines() if x.strip())
    except Exception:
        pass

    # AMD (Linux/Windows)
    try:
        out = subprocess.check_output(
            ['rocm-smi', '--showmeminfo', 'vram', '--csv'],
            stderr=subprocess.DEVNULL, text=True
        )
        for line in out.splitlines():
            if 'Total' in line:
                mb = int(line.split(',')[-1].strip()) // (1024 * 1024)
                return mb
    except Exception:
        pass

    # Apple Silicon — unified memory, use ~60% of total RAM as usable GPU headroom
    if platform.system() == 'Darwin' and platform.processor() == 'arm':
        try:
            out = subprocess.check_output(
                ['sysctl', '-n', 'hw.memsize'],
                stderr=subprocess.DEVNULL, text=True
            )
            total_mb = int(out.strip()) // (1024 * 1024)
            return int(total_mb * 0.6)
        except Exception:
            pass

    return None  # detection failed

def select_model(vram_mb):
    # Matches the hardware tiers in SETUP.md and readme.txt
    if vram_mb is None:
        return None
    if vram_mb >= 20000:   # 24 GB card — 27b fits comfortably
        return 'qwen3:27b'
    if vram_mb >= 10000:   # 12 GB card — 14-16b is the sweet spot
        return 'qwen3:14b'
    return 'qwen2.5:7b'    # 6-8 GB — edge node safe

vram = get_vram_mb()
model = select_model(vram)

if model:
    print(model)
    sys.exit(0)
else:
    sys.exit(1)  # caller handles fallback