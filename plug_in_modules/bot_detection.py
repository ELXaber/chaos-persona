import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from collections import Counter
import time

# 1. Lightweight CNN Model for Text Entropy
def build_cnn_model(vocab_size=1000, embedding_dim=16, max_length=100):
    model = models.Sequential([
        layers.Embedding(vocab_size, embedding_dim, input_length=max_length),
        layers.Conv1D(filters=32, kernel_size=3, activation='relu'),
        layers.MaxPooling1D(pool_size=2),
        layers.Flatten(),
        layers.Dense(16, activation='relu'),
        layers.Dropout(0.2),  # Prevent overfitting
        layers.Dense(1, activation='sigmoid')  # Binary output: bot (1) or human (0)
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

# 2. Preprocess Text for Entropy Analysis
def preprocess_text(text, max_length=100):
    # Simple tokenization (replace with advanced NLP if needed)
    tokens = text.lower().split()
    token_counts = Counter(tokens)
    entropy_score = -sum((count / len(tokens)) * np.log2(count / len(tokens)) for count in token_counts.values() if count > 0)
    # Pad or truncate to max_length
    padded_tokens = tokens[:max_length] + [0] * (max_length - len(tokens))
    return np.array(padded_tokens), entropy_score

# 3. Symbolic Rule Engine
def apply_rules(post_data, timestamp):
    rules_score = 0.0
    # Rule 1: High-volume repetition (>3 identical posts)
    if post_data.get('repetition_count', 0) > 3:
        rules_score += 0.3
    # Rule 2: Velocity anomaly (posts/min > 10)
    current_time = time.time()
    velocity = post_data.get('post_count', 0) / ((current_time - post_data.get('last_timestamp', current_time)) / 60)
    if velocity > 10:
        rules_score += 0.3
    return min(rules_score, 0.4)  # Cap at 0.4 (rule weight)

# 4. Volatility Indexing (Simulated via contradiction logs)
def update_volatility_index(contradiction_logs):
    # Placeholder: Adjust sensitivity based on logged contradictions
    volatility = sum(log['weight'] for log in contradiction_logs) / len(contradiction_logs) if contradiction_logs else 0.1
    return min(volatility, 0.5)  # Cap volatility impact

# 5. Main Bot Detection Function
class BotDetectionLayer:
    def __init__(self):
        self.cnn_model = build_cnn_model()
        self.volatility_logs = []  # Store contradiction data
        self.post_history = {}  # Track user post metadata

    def train_model(self, X_train, y_train, epochs=5):
        # Train on synthetic or labeled data (e.g., [token sequences], [0/1 labels])
        self.cnn_model.fit(X_train, y_train, epochs=epochs, batch_size=32, verbose=0)

    def detect_bot(self, text, user_id, timestamp):
        # Step 1: Preprocess text
        token_seq, entropy_score = preprocess_text(text)
        token_seq = np.expand_dims(token_seq, axis=0)  # Batch dimension

        # Step 2: CNN Prediction (Epistemic Uncertainty via model output variance)
        cnn_pred = self.cnn_model.predict(token_seq, verbose=0)[0][0]
        aleatoric_uncertainty = 0.1  # Simulated data noise (tune with real data)
        epistemic_uncertainty = abs(cnn_pred - 0.5)  # Model confidence gap
        cnn_score = cnn_pred * (1 - aleatoric_uncertainty - epistemic_uncertainty)

        # Step 3: Apply Symbolic Rules
        post_data = self.post_history.get(user_id, {'repetition_count': 0, 'post_count': 0, 'last_timestamp': 0})
        post_data['repetition_count'] += 1 if text in self.post_history.get(user_id, {}).get('last_text', '') else 0
        post_data['post_count'] += 1
        post_data['last_timestamp'] = timestamp
        post_data['last_text'] = text
        self.post_history[user_id] = post_data
        rules_score = apply_rules(post_data, timestamp)

        # Step 4: Combine Scores with Weights (0.6 CNN, 0.4 Rules)
        base_score = (cnn_score * 0.6) + (rules_score * 0.4)

        # Step 5: Adjust with Volatility Index
        volatility = update_volatility_index(self.volatility_logs)
        final_score = base_score * (1 + volatility)

        # Step 6: Decision
        is_bot = final_score >= 0.4
        if is_bot:
            self.volatility_logs.append({'weight': 0.1, 'timestamp': timestamp})  # Log contradiction
            # Optional: Quarantine or downgrade weight to 0.1
            final_score = 0.1  # Reset for downstream processing

        return {
            'bot_score': final_score,
            'is_bot': is_bot,
            'cnn_component': cnn_score,
            'rules_component': rules_score,
            'volatility_impact': volatility
        }

# 6. Example Usage
if __name__ == "__main__":
    # Initialize detector
    detector = BotDetectionLayer()

    # Synthetic training data (replace with real data)
    X_train = np.random.randint(0, 1000, (1000, 100))  # Random token sequences
    y_train = np.random.randint(0, 2, 1000)  # Random labels (0=human, 1=bot)
    detector.train_model(X_train, y_train)

    # Test with sample posts
    test_posts = [
        ("Repost same message again lol", "user1", time.time()),
        ("Unique thoughtful post here", "user2", time.time()),
        ("Repost same message again lol", "user1", time.time() + 5)  # Rapid repeat
    ]

    for text, user_id, timestamp in test_posts:
        result = detector.detect_bot(text, user_id, timestamp)
        print(f"User {user_id}: Bot Score = {result['bot_score']:.3f}, Is Bot = {result['is_bot']}")
