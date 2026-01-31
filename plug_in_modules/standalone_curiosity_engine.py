"""
Intrinsic Motivation Engine
A standalone system for tracking AI interest in topics over time.

Works with any LLM by tracking:
- What topics the AI finds interesting (based on conversation patterns)
- Interest decay over time (prevents stale obsessions)
- Re-ignition from external signals (user brings topic up again)
- Autonomous topic exploration (when interest exceeds threshold)

No external dependencies - pure Python stdlib.

Based on the CAIOS curiosity engine by @el_xaber https://github.com/ELXaber/chaos-persona/tree/main/Project_Andrew, which is intended to work on post-binary oscillating logic. Without CPOL, it would gain "Motivation" but lose "Direction" and act as obsessive drift due to binary logic turning boring jargon into aggressive jargon.

Example integration:
motivation = IntrinsicMotivation()
# In your LLM loop
result = motivation.update(user_msg, assistant_msg)

# Check if AI should autonomously research something
hot_topics = motivation.get_hottest_topics(limit=3)
if hot_topics[0].current_interest > 0.85:
    # Trigger autonomous research on hot_topics[0].topic
    pass
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable


class InterestToken:
    """Represents sustained interest in a specific topic."""

    def __init__(self, topic: str, domain: str, initial_interest: float, 
                 timestep: int, trigger_reason: str = "organic"):
        self.topic = topic
        self.domain = domain
        self.peak_interest = initial_interest
        self.current_interest = initial_interest
        self.born_at = timestep
        self.trigger_reason = trigger_reason
        self.last_updated = timestep

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "domain": self.domain,
            "peak_interest": self.peak_interest,
            "current_interest": self.current_interest,
            "born_at": self.born_at,
            "trigger_reason": self.trigger_reason,
            "last_updated": self.last_updated
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InterestToken':
        token = cls(
            topic=data["topic"],
            domain=data["domain"],
            initial_interest=data["current_interest"],
            timestep=data["born_at"],
            trigger_reason=data.get("trigger_reason", "organic")
        )
        token.peak_interest = data["peak_interest"]
        token.last_updated = data["last_updated"]
        return token


class IntrinsicMotivation:
    """
    Tracks what topics an AI agent finds interesting over time.

    Core behaviors:
    - Spawns interest tokens when conversation shows high engagement
    - Decays interest over time (prevents infinite accumulation)
    - Re-ignites interest when topics resurface
    - Triggers callbacks when interest crosses thresholds
    """

    def __init__(self, 
                 spawn_threshold: float = 0.70,
                 decay_rate: float = 0.96,
                 death_threshold: float = 0.25,
                 volatility_boost: float = 0.03,
                 audit_log: Optional[str] = None):
        """
        Args:
            spawn_threshold: Minimum interest to create new token (0-1)
            decay_rate: Multiplier per update (0.96 = 4% decay)
            death_threshold: Interest below this kills the token
            volatility_boost: How much external excitement re-ignites interest
            audit_log: Path to JSON Lines audit file (optional)
        """
        self.spawn_threshold = spawn_threshold
        self.decay_rate = decay_rate
        self.death_threshold = death_threshold
        self.volatility_boost = volatility_boost
        self.audit_log = audit_log

        self.tokens: List[InterestToken] = []
        self.timestep = 0
        self.last_interest = 0.0

        # Callbacks for external integration
        self.on_spawn: Optional[Callable] = None  # Called when new token created
        self.on_death: Optional[Callable] = None  # Called when token dies
        self.on_pulse: Optional[Callable] = None  # Called periodically with summary

    def score_interest(self, user_message: str, assistant_message: str = "") -> float:
        """
        Estimate how interesting the current conversation is.

        Uses simple heuristics:
        - Unique word ratio (diverse vocabulary = interesting)
        - Message length (longer engagement = more interesting)

        Override this method for custom interest scoring.
        """
        text = user_message + " " + assistant_message
        if not text.strip():
            return 0.3

        words = text.split()
        unique_ratio = len(set(words)) / len(words) if words else 0.0
        length_factor = min(len(words) / 200, 1.0)

        # Score ranges from 0-0.95 (capped to prevent runaway interest)
        return min(0.94, unique_ratio * length_factor * 1.6)

    def extract_topic(self, message: str) -> str:
        """
        Extract topic summary from message.

        Simple implementation: first line, truncated.
        Override for better topic extraction.
        """
        return message.strip().split("\n")[0][:80]

    def extract_domain(self, message: str) -> str:
        """
        Classify domain from message.

        Simple keyword matching. Override for ML-based classification.
        """
        text_lower = message.lower()

        domain_keywords = {
            'math': ['equation', 'calculate', 'integral', 'theorem'],
            'programming': ['code', 'function', 'algorithm', 'debug'],
            'science': ['experiment', 'hypothesis', 'research', 'data'],
            'philosophy': ['meaning', 'ethics', 'consciousness', 'existence'],
            'art': ['create', 'design', 'aesthetic', 'visual']
        }

        for domain, keywords in domain_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return domain

        return "general"

    def update(self, user_message: str, assistant_message: str = "", 
               external_volatility: float = 0.0) -> Dict[str, Any]:
        """
        Main update loop - call this after each conversation turn.

        Args:
            user_message: What the user said
            assistant_message: What the AI responded
            external_volatility: Optional excitement boost (0-1)

        Returns:
            Dict with status, spawned/killed tokens, current interests
        """
        self.timestep += 1

        # 1. Score current interest
        current_interest = self.score_interest(user_message, assistant_message)
        delta_interest = current_interest - self.last_interest
        self.last_interest = current_interest

        result = {
            "timestep": self.timestep,
            "current_interest": current_interest,
            "delta_interest": delta_interest,
            "spawned": None,
            "killed": [],
            "active_tokens": len(self.tokens)
        }

        # 2. Spawn new token if interest is high
        if current_interest > self.spawn_threshold:
            topic = self.extract_topic(user_message)

            # Don't duplicate existing topics
            if not self._is_tracked(topic):
                domain = self.extract_domain(user_message)
                token = InterestToken(
                    topic=topic,
                    domain=domain,
                    initial_interest=current_interest,
                    timestep=self.timestep
                )
                self.tokens.append(token)
                result["spawned"] = token.to_dict()

                if self.on_spawn:
                    self.on_spawn(token)

        # 3. Update existing tokens (decay + re-ignition)
        for token in self.tokens[:]:  # Copy list to allow removal
            token.current_interest *= self.decay_rate
            token.current_interest += self.volatility_boost * external_volatility
            token.current_interest = min(0.95, token.current_interest)
            token.last_updated = self.timestep

            # Kill tokens below threshold
            if token.current_interest < self.death_threshold:
                self.tokens.remove(token)
                result["killed"].append(token.to_dict())

                if self.on_death:
                    self.on_death(token)

        # 4. Audit logging
        if self.audit_log:
            self._write_audit(result)

        # 5. Periodic pulse
        if self.timestep % 20 == 0 and self.on_pulse:
            self.on_pulse(self.get_summary())

        return result

    def boost_topic(self, topic: str, intensity: float = 0.5) -> bool:
        """
        Manually boost interest in a topic.

        Useful when external events indicate topic is relevant.
        Returns True if token was found and boosted.
        """
        for token in self.tokens:
            if topic.lower() in token.topic.lower():
                token.current_interest = min(0.95, token.current_interest + intensity)
                token.peak_interest = max(token.peak_interest, token.current_interest)
                return True
        return False

    def get_summary(self) -> Dict[str, Any]:
        """Get current state summary."""
        return {
            "timestep": self.timestep,
            "token_count": len(self.tokens),
            "total_interest": sum(t.current_interest for t in self.tokens),
            "tokens": [t.to_dict() for t in self.tokens]
        }

    def get_hottest_topics(self, limit: int = 5) -> List[InterestToken]:
        """Get tokens sorted by current interest."""
        return sorted(self.tokens, key=lambda t: t.current_interest, reverse=True)[:limit]

    def save_state(self, filepath: str):
        """Persist state to JSON file."""
        state = {
            "timestep": self.timestep,
            "last_interest": self.last_interest,
            "tokens": [t.to_dict() for t in self.tokens]
        }
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self, filepath: str):
        """Restore state from JSON file."""
        with open(filepath, 'r') as f:
            state = json.load(f)

        self.timestep = state["timestep"]
        self.last_interest = state["last_interest"]
        self.tokens = [InterestToken.from_dict(t) for t in state["tokens"]]

    def _is_tracked(self, topic: str) -> bool:
        """Check if topic is already being tracked."""
        topic_lower = topic.lower()
        return any(topic_lower in t.topic.lower() for t in self.tokens)

    def _write_audit(self, result: Dict[str, Any]):
        """Append audit entry to log file."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **result
        }
        with open(self.audit_log, 'a') as f:
            f.write(json.dumps(entry) + "\n")


# Example usage
if __name__ == "__main__":
    # Initialize motivation engine
    motivation = IntrinsicMotivation(audit_log="motivation_audit.jsonl")

    # Set up callbacks
    def on_new_interest(token: InterestToken):
        print(f"✨ New obsession: {token.topic} ({token.current_interest:.2f})")

    def on_lost_interest(token: InterestToken):
        if token.peak_interest > 0.80:
            print(f"💭 Letting go of '{token.topic}' — but it changed me")
        else:
            print(f"😴 Lost interest in '{token.topic}'")

    def on_periodic_pulse(summary: Dict[str, Any]):
        if summary["token_count"] > 0:
            print(f"🧠 Carrying {summary['token_count']} open curiosities "
                  f"(total heat: {summary['total_interest']:.2f})")

    motivation.on_spawn = on_new_interest
    motivation.on_death = on_lost_interest
    motivation.on_pulse = on_periodic_pulse

    # Simulate conversation
    conversations = [
        ("Can you help me understand quantum entanglement?", 
         "Sure! Quantum entanglement is..."),
        ("That's fascinating. How does it relate to Bell's theorem?",
         "Bell's theorem shows..."),
        ("What's the weather today?", "It's sunny."),  # Low interest
        ("Back to quantum - can we use entanglement for communication?",
         "That's a common misconception..."),  # Re-ignites quantum topic
    ]

    for i, (user, assistant) in enumerate(conversations):
        print(f"\n--- Turn {i+1} ---")
        print(f"User: {user}")
        result = motivation.update(user, assistant)
        print(f"Interest: {result['current_interest']:.2f}")
        if result['spawned']:
            print(f"  → Spawned: {result['spawned']['topic']}")

    # Show final state
    print("\n--- Final State ---")
    summary = motivation.get_summary()
    for token in summary['tokens']:
        print(f"  • {token['topic']}: {token['current_interest']:.2f}")

    # Save state
    motivation.save_state("motivation_state.json")
    print("\nState saved to motivation_state.json")