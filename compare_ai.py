"""
Comparar dos agentes de IA jugando Tetris side-by-side.

Uso:
    python compare_ai.py
"""

import os
import sys

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import pygame
import tensorflow as tf

from tetris_engine import Tetris
from tetris_ui import (
    CELL, BG, TEXT, TEXT_DIM, BOARD_PX_W, BOARD_PX_H, SIDE_W, PAD, HEADER_H,
    draw_board, draw_piece_in_box, draw_panel, draw_overlay, init_fonts,
)

# Dimensiones personalizadas para pantalla dividida
COMPARE_WINDOW_W = 1480
COMPARE_WINDOW_H = 720


def load_model_or_fallback(path, fallback):
    if os.path.exists(path):
        print(f"Cargando modelo principal: {path}")
        return tf.keras.models.load_model(path)
    elif os.path.exists(fallback):
        print(f"Modelo {path} no encontrado. Cargando fallback: {fallback}")
        return tf.keras.models.load_model(fallback)
    else:
        print(f"ERROR: No se encontró ni {path} ni {fallback}.")
        return None


def update_ai_game(state, dt, speed_mult, drop_interval, pause_between):
    game = state["game"]
    model = state["model"]

    if game.game_over:
        return

    if state["phase"] == "idle":
        next_states = game.get_next_states()
        if not next_states:
            game.game_over = True
        else:
            keys = list(next_states.keys())
            feats = np.asarray([next_states[k] for k in keys], dtype=np.float32)
            vals = model(feats, training=False).numpy().flatten()
            target_rot, target_x = keys[int(np.argmax(vals))]
            game.current.rotation = target_rot
            game.current.x = target_x
            game.current.y = 0
            state["phase"] = "dropping"
            state["cooldown"] = pause_between / speed_mult
    elif state["phase"] == "dropping":
        state["cooldown"] -= dt
        while state["cooldown"] <= 0 and state["phase"] == "dropping":
            if not game._collides(game.current, y=game.current.y + 1):
                game.current.y += 1
                state["cooldown"] += drop_interval / speed_mult
            else:
                game._lock()
                state["phase"] = "idle"
                state["cooldown"] = pause_between / speed_mult


def draw_ai_game(screen, state, ox, fonts):
    game = state["game"]

    # Cabecera de cada juego
    title = fonts["font"].render(state["name"], True, state["color_title"])
    screen.blit(title, (ox + (700 - title.get_width()) // 2, 15))

    hold_x = ox
    board_x = hold_x + SIDE_W + PAD
    next_x = board_x + BOARD_PX_W + PAD
    board_y = HEADER_H + PAD

    # HOLD panel
    draw_panel(screen, "HOLD", hold_x, board_y, SIDE_W, 5 * CELL, fonts["font"])
    draw_piece_in_box(screen, game.hold, hold_x, board_y + 32, SIDE_W, 5 * CELL - 32)

    # STATS panel
    stats_y = board_y + 5 * CELL + PAD
    stats_h = 9 * CELL
    draw_panel(screen, "STATS", hold_x, stats_y, SIDE_W, stats_h, fonts["font"])
    rows = [
        ("Score", str(game.score)),
        ("Lines", str(game.lines)),
        ("Level", str(game.level)),
    ]
    for i, (lbl, val) in enumerate(rows):
        screen.blit(fonts["small"].render(lbl, True, TEXT_DIM),
                    (hold_x + 12, stats_y + 38 + i * 60))
        screen.blit(fonts["font"].render(val, True, TEXT),
                    (hold_x + 12, stats_y + 62 + i * 60))

    # BOARD con fantasmas
    draw_board(screen, game, board_x, board_y, draw_ghost=True)

    # NEXT panel
    next_h = 16 * CELL
    draw_panel(screen, "NEXT", next_x, board_y, SIDE_W, next_h, fonts["font"])
    for i in range(min(5, len(game.queue))):
        draw_piece_in_box(screen, game.queue[i],
                          next_x, board_y + 32 + i * 3 * CELL,
                          SIDE_W, 3 * CELL)

    if game.game_over:
        draw_overlay(screen, board_x, board_y, fonts,
                     "GAME OVER", "R reiniciar",
                     title_color=(255, 90, 90))


def main():
    pygame.init()
    screen = pygame.display.set_mode((COMPARE_WINDOW_W, COMPARE_WINDOW_H))
    pygame.display.set_caption("Tetris IA - Comparativa Side-by-Side")
    clock = pygame.time.Clock()
    fonts = init_fonts()

    # Cargar modelos
    model_1000 = load_model_or_fallback("models/tetris_1000.keras", "models/tetris_model.keras")
    model_advanced = load_model_or_fallback("models/tetris_3000.keras", "models/tetris_2000.keras")

    if model_1000 is None or model_advanced is None:
        print("Error: Se necesitan ambos modelos para realizar la comparación.")
        pygame.quit()
        return

    # Inicializar juegos
    game1 = Tetris()
    game2 = Tetris()

    state1 = {
        "game": game1,
        "phase": "idle",
        "target_rot": 0,
        "target_x": 3,
        "cooldown": 0.0,
        "model": model_1000,
        "name": "IA - 1000 Episodios (Models/tetris_1000.keras)",
        "color_title": (100, 200, 255),
    }

    state2 = {
        "game": game2,
        "phase": "idle",
        "target_rot": 0,
        "target_x": 3,
        "cooldown": 0.0,
        "model": model_advanced,
        "name": "IA - 3000 Episodios (Models/tetris_3000.keras)",
        "color_title": (255, 100, 150),
    }

    drop_interval = 0.04
    pause_between = 0.08
    speed_mult = 1.0
    paused = False

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    game1.reset()
                    game2.reset()
                    state1["phase"] = "idle"
                    state2["phase"] = "idle"
                    state1["cooldown"] = 0.0
                    state2["cooldown"] = 0.0
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    speed_mult = min(20.0, speed_mult * 1.5)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    speed_mult = max(0.1, speed_mult / 1.5)

        if not paused:
            update_ai_game(state1, dt, speed_mult, drop_interval, pause_between)
            update_ai_game(state2, dt, speed_mult, drop_interval, pause_between)

        # Render
        screen.fill(BG)

        # Dibujar Juego 1 (Izquierda, ox = 20)
        draw_ai_game(screen, state1, 20, fonts)

        # Dibujar Separador
        pygame.draw.line(screen, (50, 50, 70), (740, 0), (740, COMPARE_WINDOW_H), 3)

        # Dibujar Juego 2 (Derecha, ox = 760)
        draw_ai_game(screen, state2, 760, fonts)

        # Panel inferior de estado general
        status_text = f"Pausa: [Espacio] | Velocidad: x{speed_mult:.1f} [+/-] | Reiniciar todo: [R]"
        txt_surf = fonts["small"].render(status_text, True, TEXT_DIM)
        screen.blit(txt_surf, ((COMPARE_WINDOW_W - txt_surf.get_width()) // 2, COMPARE_WINDOW_H - 30))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
