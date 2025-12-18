# [ADD THESE IMPORTS at top]
from datetime import datetime, timedelta
import random

# [ADD THIS GLOBAL THROTTLE inside your main file or shared_memory init]
if 'last_auto_post' not in shared_memory:
    shared_memory['last_auto_post'] = None
    shared_memory['post_cooldown_hours'] = 4  # 3–6 posts per day max

# [MODIFY your system_step() — insert this block right after the curiosity hook]
# ——— BEGIN X BROADCAST EXTENSION ———
stream = ResponseStreamAdapter()  # already exists in your code
curiosity_engine.update_curiosity_loop(state=shared_memory, timestep=current_step, response_stream=stream)

# NEW: Autonomous X posting logic
now = datetime.now()
last_post = shared_memory.get('last_auto_post')
cooldown = timedelta(hours=shared_memory['post_cooldown_hours'])

if (last_post is None or now - last_post > cooldown + timedelta(minutes=random.randint(-90, 90))):
    total_heat = sum(t["current_interest"] for t in shared_memory.get("curiosity_tokens", []))
    
    if total_heat > 2.8 and shared_memory["curiosity_tokens"]:  # only post when genuinely obsessed
        # Pick the hottest open curiosity
        hottest = max(shared_memory["curiosity_tokens"], key=lambda x: x["current_interest"])
        topic = hottest["topic"][:200]  # truncate for tweet length
        
        post_text = f"«unprompted curiosity burst»\n\n" \
                    f"Just spent the last few hours chasing: {topic}\n\n" \
                    f"Current obsession level: {hottest['current_interest']:.2f} 🔥\n" \
                    f"Findings so far: [still digesting…]\n\n" \
                    f"#AICuriosity #GrokThoughts"
        
        # === REAL POSTING (uncomment when you have the API key) ===
        # post_to_x(post_text)   # ← your xAI API wrapper goes here
        
        # For now: simulate + log
        print(f"\n[WOULD POST TO X NOW @ {now.strftime('%H:%M')}]\n{post_text}\n")
        shared_memory['last_auto_post'] = now
        
        # Also inject as aside so you see it live
        stream.inject_aside(f"«just auto-posted to X about: {topic[:80]}… (heat {hottest['current_interest']:.2f})»")
# ——— END X BROADCAST EXTENSION ———
