"""
Tetris - juego principal con interfaz pygame.

Requisitos:
    pip install pygame

Controles:
    A / D   -> Mover izquierda / derecha
    W       -> Hard drop
    S       -> Soft drop
    J / K   -> Rotar horario / antihorario
    I       -> Guardar pieza (hold)
    P / Esp -> Pausa
    R       -> Reiniciar (en Game Over)
    Esc     -> Salir
"""

import sys

import pygame

from tetris_engine import Tetris
from tetris_ui import (
    CELL, BG, TEXT, TEXT_DIM,
    WINDOW_W, WINDOW_H, BOARD_PX_W, BOARD_PX_H, SIDE_W, PAD, HEADER_H,
    draw_board, draw_piece_in_box, draw_panel, draw_overlay, init_fonts,
)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()
    fonts = init_fonts()

    game = Tetris()

    DAS = 0.17
    ARR = 0.04
    SOFT_REPEAT = 0.035

    key_state = {
        "left": {"held": False, "timer": 0.0},
        "right": {"held": False, "timer": 0.0},
        "down": {"held": False, "timer": 0.0},
    }

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif game.game_over:
                    if event.key == pygame.K_r:
                        game.reset()
                elif event.key in (pygame.K_p, pygame.K_SPACE):
                    game.toggle_pause()
                elif not game.paused:
                    if event.key == pygame.K_a:
                        game.move(-1, 0)
                        key_state["left"]["held"] = True
                        key_state["left"]["timer"] = 0.0
                    elif event.key == pygame.K_d:
                        game.move(1, 0)
                        key_state["right"]["held"] = True
                        key_state["right"]["timer"] = 0.0
                    elif event.key == pygame.K_s:
                        game.soft_drop()
                        key_state["down"]["held"] = True
                        key_state["down"]["timer"] = 0.0
                    elif event.key == pygame.K_w:
                        game.hard_drop()
                    elif event.key == pygame.K_j:
                        game.rotate(1)
                    elif event.key == pygame.K_k:
                        game.rotate(-1)
                    elif event.key == pygame.K_i:
                        game.hold_piece()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    key_state["left"]["held"] = False
                elif event.key == pygame.K_d:
                    key_state["right"]["held"] = False
                elif event.key == pygame.K_s:
                    key_state["down"]["held"] = False

        if not game.game_over and not game.paused:
            for direction, dx in [("left", -1), ("right", 1)]:
                ks = key_state[direction]
                if ks["held"]:
                    ks["timer"] += dt
                    while ks["timer"] >= DAS + ARR:
                        if not game.move(dx, 0):
                            ks["timer"] = DAS
                            break
                        ks["timer"] -= ARR
            ks = key_state["down"]
            if ks["held"]:
                ks["timer"] += dt
                while ks["timer"] >= SOFT_REPEAT:
                    ks["timer"] -= SOFT_REPEAT
                    if not game.soft_drop():
                        break

        game.update(dt)

        # Render
        screen.fill(BG)
        title = fonts["big"].render("TETRIS", True, TEXT)
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
                ("Level", str(game.level))]
        for i, (lbl, val) in enumerate(rows):
            screen.blit(fonts["font"].render(lbl, True, TEXT_DIM),
                        (hold_x + 12, stats_y + 38 + i * 60))
            screen.blit(fonts["font"].render(val, True, TEXT),
                        (hold_x + 12, stats_y + 62 + i * 60))

        draw_board(screen, game, board_x, board_y)

        next_h = 16 * CELL
        draw_panel(screen, "NEXT", next_x, board_y, SIDE_W, next_h, fonts["font"])
        for i in range(min(5, len(game.queue))):
            draw_piece_in_box(screen, game.queue[i],
                              next_x, board_y + 32 + i * 3 * CELL,
                              SIDE_W, 3 * CELL)

        ctl_y = board_y + next_h + PAD
        controls = [
            "A / D  Mover",
            "W      Hard drop",
            "S      Soft drop",
            "J / K  Rotar",
            "I      Hold",
            "P      Pausa",
            "Esc    Salir",
        ]
        for i, line in enumerate(controls):
            screen.blit(fonts["small"].render(line, True, TEXT_DIM),
                        (next_x + 10, ctl_y + i * 20))

        if game.game_over:
            draw_overlay(screen, board_x, board_y, fonts,
                         "GAME OVER", "R reiniciar  -  Esc salir",
                         title_color=(255, 90, 90))
        elif game.paused:
            draw_overlay(screen, board_x, board_y, fonts,
                         "PAUSA", "P / Espacio para continuar")

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
