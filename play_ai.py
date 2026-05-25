"""
Ver el agente entrenado jugando Tetris en una ventana pygame.

Uso:
    python play_ai.py                          # carga models/tetris_best.keras
    python play_ai.py models/tetris_model.keras

Controles:
    Espacio   Pausar / reanudar
    + / -     Acelerar / ralentizar
    R         Reiniciar partida
    Esc       Salir
"""

import os
import sys

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import pygame
import tensorflow as tf

from tetris_engine import Tetris
from tetris_ui import (
    CELL, BG, TEXT, TEXT_DIM,
    WINDOW_W, WINDOW_H, BOARD_PX_W, BOARD_PX_H, SIDE_W, PAD, HEADER_H,
    draw_board, draw_piece_in_box, draw_panel, draw_overlay, init_fonts,
)


def pick_model_path():
    if len(sys.argv) > 1:
        return sys.argv[1]
    for p in ("models/tetris_best.keras", "models/tetris_model.keras"):
        if os.path.exists(p):
            return p
    return None


def main():
    path = pick_model_path()
    if path is None or not os.path.exists(path):
        print("No se encontro modelo entrenado.")
        print("Ejecuta primero: python train_ai.py")
        return
    print(f"Cargando modelo: {path}")
    model = tf.keras.models.load_model(path)

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Tetris - IA")
    clock = pygame.time.Clock()
    fonts = init_fonts()

    game = Tetris()

    # Estado de la animacion de caida
    phase = "idle"        # idle -> dropping -> idle
    target_rot = 0
    target_x = 3
    cooldown = 0.0

    drop_interval = 0.04       # segundos por celda al caer
    pause_between = 0.08       # pausa entre piezas
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
                    game.reset()
                    phase = "idle"
                    cooldown = 0.0
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    speed_mult = min(20.0, speed_mult * 1.5)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    speed_mult = max(0.1, speed_mult / 1.5)

        if not paused and not game.game_over:
            if phase == "idle":
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
                    phase = "dropping"
                    cooldown = pause_between / speed_mult
            elif phase == "dropping":
                cooldown -= dt
                while cooldown <= 0 and phase == "dropping":
                    if not game._collides(game.current, y=game.current.y + 1):
                        game.current.y += 1
                        cooldown += drop_interval / speed_mult
                    else:
                        game._lock()
                        phase = "idle"
                        cooldown = pause_between / speed_mult

        # === Render ===
        screen.fill(BG)
        title = fonts["big"].render("TETRIS - IA", True, TEXT)
        screen.blit(title, ((WINDOW_W - title.get_width()) // 2, 5))

        hold_x = PAD
        board_x = hold_x + SIDE_W + PAD
        next_x = board_x + BOARD_PX_W + PAD
        board_y = HEADER_H + PAD

        draw_panel(screen, "HOLD", hold_x, board_y, SIDE_W, 5 * CELL, fonts["font"])
        draw_piece_in_box(screen, game.hold, hold_x, board_y + 32, SIDE_W, 5 * CELL - 32)

        stats_y = board_y + 5 * CELL + PAD
        stats_h = 9 * CELL
        draw_panel(screen, "STATS", hold_x, stats_y, SIDE_W, stats_h, fonts["font"])
        rows = [("Score", str(game.score)),
                ("Lines", str(game.lines)),
                ("Level", str(game.level)),
                ("Speed", f"x{speed_mult:.1f}")]
        for i, (lbl, val) in enumerate(rows):
            screen.blit(fonts["small"].render(lbl, True, TEXT_DIM),
                        (hold_x + 12, stats_y + 38 + i * 48))
            screen.blit(fonts["font"].render(val, True, TEXT),
                        (hold_x + 12, stats_y + 56 + i * 48))

        draw_board(screen, game, board_x, board_y, draw_ghost=True)

        next_h = 16 * CELL
        draw_panel(screen, "NEXT", next_x, board_y, SIDE_W, next_h, fonts["font"])
        for i in range(min(5, len(game.queue))):
            draw_piece_in_box(screen, game.queue[i],
                              next_x, board_y + 32 + i * 3 * CELL,
                              SIDE_W, 3 * CELL)

        ctl_y = board_y + next_h + PAD
        controls = [
            "Espacio Pausa",
            "+ / -   Velocidad",
            "R       Reiniciar",
            "Esc     Salir",
        ]
        for i, line in enumerate(controls):
            screen.blit(fonts["small"].render(line, True, TEXT_DIM),
                        (next_x + 10, ctl_y + i * 20))

        if game.game_over:
            draw_overlay(screen, board_x, board_y, fonts,
                         "GAME OVER", "R reiniciar  -  Esc salir",
                         title_color=(255, 90, 90))
        elif paused:
            draw_overlay(screen, board_x, board_y, fonts,
                         "PAUSA", "Espacio para continuar")

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
