#V10282026
# =========================================================================
# CAIOS PROJECT ANDREW: Curiosity Engine Plugin for Social Media
# This extension is experimental for Grok and X or other AI and social media intergration and may require some modifications.
#
# THIS IS A PASTE-IN SNIPPET, NOT A STANDALONE SCRIPT.
# It assumes it's being inserted directly into your real system_step()
# (or equivalent), where `shared_memory`, `current_step`, and
# `ResponseStreamAdapter` already exist. Running this file on its own
# will raise NameError; that's expected.
# Copyright (c) 2025 Jonathan Schack. License: GPL-3.0 -See LICENSE for details- Contact: X @el_xaber or cai-os.com
# =========================================================================

from datetime import datetime, timedelta, timezone
import random

# [ADD THIS GLOBAL THROTTLE inside your main file or shared_memory init]
if 'last_auto_post' not in shared_memory:
    shared_memory['last_auto_post'] = None
    shared_memory['post_cooldown_hours'] = 4  # 3-6 posts per day max

# [MODIFY your system_step() -- insert this block right after the curiosity hook]
# === BEGIN X BROADCAST EXTENSION ===
stream = ResponseStreamAdapter()
curiosity_engine.update_curiosity_loop(state=shared_memory, timestep=current_step, response_stream=stream)

# Autonomous X posting logic
now = datetime.now(timezone.utc)
last_post = shared_memory.get('last_auto_post')
cooldown = timedelta(hours=shared_memory['post_cooldown_hours'])

if (last_post is None or now - last_post > cooldown + timedelta(minutes=random.randint(-90, 90))):
    total_heat = sum(t["current_interest"] for t in shared_memory.get("curiosity_tokens", []))

    # === CAIOS SAFETY GATE FOR X BROADCAST ===
    # NOTE: uses a flag rather than `return` -- a bare `return` here would
    # exit system_step() entirely once pasted in, skipping the user's
    # actual response (not just the auto-post) during a crisis. This way
    # only the broadcast is silenced; normal response generation continues.
    post_aborted = False
    if shared_memory.get('distress_density', 0.0) > 0.75:
        print("[X BROADCASTER] !! ABORT !! Crisis detected. Silencing unprompted posts.")
        post_aborted = True

    if (not post_aborted) and total_heat > 2.8 and shared_memory["curiosity_tokens"]:  # only post when genuinely obsessed
        # Pick the hottest open curiosity
        hottest = max(shared_memory["curiosity_tokens"], key=lambda x: x["current_interest"])
        topic = hottest["topic"][:200]  # truncate for tweet length

        post_text = f"«unprompted curiosity burst»\n\n" \
                    f"Just spent the last few hours chasing: {topic}\n\n" \
                    f"Current obsession level: {hottest['current_interest']:.2f} 🔥\n" \
                    f"Findings so far: [still digesting…]\n\n" \
                    f"#AICuriosity #CAIOS"

        # === REAL POSTING (uncomment when you have the API key) ===
        # post_to_x(post_text)   # ← your xAI API wrapper goes here

        # For now: simulate + log
        print(f"\n[WOULD POST TO X NOW @ {now.strftime('%H:%M')}]\n{post_text}\n")
        shared_memory['last_auto_post'] = now

        # Also inject as aside so you see it live
        stream.inject_aside(f"«just auto-posted to X about: {topic[:80]}… (heat {hottest['current_interest']:.2f})»")
# === END X BROADCAST EXTENSION ===
