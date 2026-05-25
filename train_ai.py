"""
Entrenamiento de un agente DQN (afterstate) para jugar Tetris.

Idea:
    En cada turno el agente enumera todas las colocaciones finales posibles
    (rotacion + columna) de la pieza actual, calcula 4 features del tablero
    resultante (lineas, huecos, bumpiness, altura), y la red predice el
    valor V(estado). El agente elige la colocacion con mayor V.

Features:
    [lineas_eliminadas, huecos, bumpiness, altura_total]

Recompensa:
    +1 por sobrevivir un turno
    +(lineas^2) * 10 por lineas eliminadas en ese turno
    -2 al perder

Uso:
    pip install tensorflow numpy
    python train_ai.py             # entrena 2500 episodios
    python train_ai.py 1000        # entrena 1000 episodios
"""

import os
import sys
import random
import time
from collections import deque

# Reducir verbosidad de TensorFlow antes de importarlo
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers

from tetris_engine import Tetris, compute_features, COLS


MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "tetris_model.keras")
BEST_PATH = os.path.join(MODEL_DIR, "tetris_best.keras")


def build_model():
    m = models.Sequential([
        layers.Input(shape=(4,)),
        layers.Dense(64, activation="relu"),
        layers.Dense(64, activation="relu"),
        layers.Dense(1, activation="linear"),
    ])
    m.compile(optimizer=optimizers.Adam(learning_rate=1e-3), loss="mse")
    return m


class DQNAgent:
    def __init__(self,
                 gamma=0.95,
                 eps_start=1.0,
                 eps_end=0.001,
                 decay_episodes=1500,
                 memory_size=20000,
                 batch_size=512,
                 train_steps_per_episode=1):
        self.model = build_model()
        self.target_model = build_model()
        self.target_model.set_weights(self.model.get_weights())
        self.memory = deque(maxlen=memory_size)
        self.gamma = gamma
        self.eps_start = eps_start
        self.eps_end = eps_end
        self.decay_episodes = decay_episodes
        self.epsilon = eps_start
        self.batch_size = batch_size
        self.train_steps = train_steps_per_episode

    def act(self, next_states):
        if np.random.random() < self.epsilon:
            return random.choice(list(next_states.keys()))
        keys = list(next_states.keys())
        feats = np.asarray([next_states[k] for k in keys], dtype=np.float32)
        vals = self.model(feats, training=False).numpy().flatten()
        return keys[int(np.argmax(vals))]

    def remember(self, state, reward, next_state, done):
        self.memory.append((state, reward, next_state, done))

    def replay(self):
        if len(self.memory) < self.batch_size:
            return
        for _ in range(self.train_steps):
            batch = random.sample(self.memory, self.batch_size)
            states = np.asarray([b[0] for b in batch], dtype=np.float32)
            rewards = np.asarray([b[1] for b in batch], dtype=np.float32)
            next_states = np.asarray([b[2] for b in batch], dtype=np.float32)
            dones = np.asarray([1.0 if b[3] else 0.0 for b in batch], dtype=np.float32)
            next_v = self.target_model(next_states, training=False).numpy().flatten()
            targets = rewards + (1.0 - dones) * self.gamma * next_v
            self.model.fit(states, targets,
                           batch_size=self.batch_size,
                           epochs=1, verbose=0)

    def update_target(self):
        self.target_model.set_weights(self.model.get_weights())

    def decay_epsilon(self, episode):
        if episode >= self.decay_episodes:
            self.epsilon = self.eps_end
        else:
            frac = episode / self.decay_episodes
            self.epsilon = self.eps_start + (self.eps_end - self.eps_start) * frac


def train(num_episodes=2500, resume=False):
    os.makedirs(MODEL_DIR, exist_ok=True)
    game = Tetris()
    agent = DQNAgent(decay_episodes=max(1, int(num_episodes * 0.6)))

    if resume and os.path.exists(MODEL_PATH):
        print(f"Reanudando desde {MODEL_PATH}")
        agent.model = tf.keras.models.load_model(MODEL_PATH)
        agent.target_model = tf.keras.models.load_model(MODEL_PATH)
        agent.epsilon = max(agent.eps_end, 0.1)

    rewards_hist = deque(maxlen=100)
    lines_hist = deque(maxlen=100)
    best_avg = -float("inf")
    start = time.time()

    print(f"Entrenando {num_episodes} episodios...")
    print("-" * 78)

    for ep in range(1, num_episodes + 1):
        game.reset()
        current_state = compute_features(game.board, 0)
        total_reward = 0.0
        steps = 0
        while not game.game_over:
            next_states = game.get_next_states()
            if not next_states:
                break
            action = agent.act(next_states)
            chosen = next_states[action]
            reward, done = game.play_placement(*action)
            agent.remember(current_state, reward, chosen, done)
            current_state = chosen
            total_reward += reward
            steps += 1
            if steps > 5000:
                break  # tope de seguridad para juegos muy largos

        agent.replay()
        agent.decay_epsilon(ep)
        if ep % 5 == 0:
            agent.update_target()

        rewards_hist.append(total_reward)
        lines_hist.append(game.lines)

        if ep % 25 == 0:
            avg_r = float(np.mean(rewards_hist))
            avg_lines = float(np.mean(lines_hist))
            elapsed = (time.time() - start) / 60.0
            print(f"Ep {ep:5d}/{num_episodes}  "
                  f"avg_reward={avg_r:8.1f}  avg_lines={avg_lines:6.1f}  "
                  f"score={game.score:7d}  lines={game.lines:4d}  "
                  f"eps={agent.epsilon:.3f}  t={elapsed:5.1f}m", flush=True)

        if ep % 100 == 0:
            agent.model.save(MODEL_PATH)
            avg_r = float(np.mean(rewards_hist))
            if avg_r > best_avg:
                best_avg = avg_r
                agent.model.save(BEST_PATH)
                print(f"  -> Nuevo mejor modelo guardado (avg_reward={avg_r:.1f})")

    agent.model.save(MODEL_PATH)
    elapsed = (time.time() - start) / 60.0
    print("-" * 78)
    print(f"Entrenamiento completado en {elapsed:.1f} min.")
    print(f"Modelo final: {MODEL_PATH}")
    print(f"Mejor modelo: {BEST_PATH}")


if __name__ == "__main__":
    num = 2500
    resume = False
    args = sys.argv[1:]
    for a in args:
        if a == "--resume":
            resume = True
        else:
            try:
                num = int(a)
            except ValueError:
                pass
    train(num, resume=resume)
