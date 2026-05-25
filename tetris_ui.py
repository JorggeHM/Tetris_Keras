"""
Helpers de renderizado en pygame, compartidos entre tetris.py y play_ai.py.
"""

import pygame

from tetris_engine import SHAPES, COLS, ROWS


CELL = 30
BOARD_PX_W = COLS * CELL
BOARD_PX_H = ROWS * CELL
SIDE_W = 6 * CELL
PAD = 20
HEADER_H = 60
WINDOW_W = SIDE_W + BOARD_PX_W + SIDE_W + 4 * PAD
WINDOW_H = BOARD_PX_H + 2 * PAD + HEADER_H

BG = (15, 15, 25)
GRID_COLOR = (40, 40, 55)
PANEL = (25, 25, 40)
TEXT = (235, 235, 245)
TEXT_DIM = (140, 140, 160)
BORDER = (80, 80, 100)
GHOST_ALPHA = 70

COLORS = {
    "I": (0, 215, 215),
    "O": (215, 215, 0),
    "T": (155, 0, 215),
    "S": (0, 215, 0),
    "Z": (215, 0, 50),
    "J": (0, 80, 215),
    "L": (215, 130, 0),
}


def init_fonts():
    return {
        "font": pygame.font.SysFont("consolas", 22, bold=True),
        "big": pygame.font.SysFont("consolas", 48, bold=True),
        "small": pygame.font.SysFont("consolas", 16),
    }


def draw_cell(surf, x, y, color, ghost=False):
    rect = pygame.Rect(x, y, CELL, CELL)
    if ghost:
        s = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        s.fill((*color, GHOST_ALPHA))
        surf.blit(s, (x, y))
        pygame.draw.rect(surf, color, rect, 2)
    else:
        pygame.draw.rect(surf, color, rect)
        inner = (min(255, color[0] + 50),
                 min(255, color[1] + 50),
                 min(255, color[2] + 50))
        pygame.draw.rect(surf, inner, rect, 2)
        pygame.draw.rect(surf, (0, 0, 0), rect, 1)


def draw_board(surf, game, ox, oy, draw_ghost=True):
    pygame.draw.rect(surf, (10, 10, 20), (ox, oy, BOARD_PX_W, BOARD_PX_H))
    for c in range(COLS + 1):
        pygame.draw.line(surf, GRID_COLOR,
                         (ox + c * CELL, oy),
                         (ox + c * CELL, oy + BOARD_PX_H))
    for r in range(ROWS + 1):
        pygame.draw.line(surf, GRID_COLOR,
                         (ox, oy + r * CELL),
                         (ox + BOARD_PX_W, oy + r * CELL))

    for r in range(ROWS):
        for c in range(COLS):
            if game.board[r][c]:
                draw_cell(surf, ox + c * CELL, oy + r * CELL,
                          COLORS[game.board[r][c]])

    if not game.game_over and game.current is not None:
        if draw_ghost:
            gy = game.ghost_y()
            for cx, cy in game.current.cells(y=gy):
                if 0 <= cy < ROWS and 0 <= cx < COLS:
                    draw_cell(surf, ox + cx * CELL, oy + cy * CELL,
                              COLORS[game.current.kind], ghost=True)
        for cx, cy in game.current.cells():
            if 0 <= cy < ROWS and 0 <= cx < COLS:
                draw_cell(surf, ox + cx * CELL, oy + cy * CELL,
                          COLORS[game.current.kind])

    pygame.draw.rect(surf, BORDER,
                     (ox - 2, oy - 2, BOARD_PX_W + 4, BOARD_PX_H + 4), 2)


def draw_piece_in_box(surf, kind, box_x, box_y, box_w, box_h):
    if kind is None:
        return
    cells = SHAPES[kind][0]
    min_x = min(c[0] for c in cells)
    max_x = max(c[0] for c in cells)
    min_y = min(c[1] for c in cells)
    max_y = max(c[1] for c in cells)
    w = (max_x - min_x + 1) * CELL
    h = (max_y - min_y + 1) * CELL
    ox = box_x + (box_w - w) // 2 - min_x * CELL
    oy = box_y + (box_h - h) // 2 - min_y * CELL
    for cx, cy in cells:
        draw_cell(surf, ox + cx * CELL, oy + cy * CELL, COLORS[kind])


def draw_panel(surf, title, x, y, w, h, font):
    pygame.draw.rect(surf, PANEL, (x, y, w, h))
    pygame.draw.rect(surf, BORDER, (x, y, w, h), 2)
    label = font.render(title, True, TEXT)
    surf.blit(label, (x + 10, y + 6))


def draw_overlay(surf, board_x, board_y, fonts, title, subtitle, title_color=TEXT):
    overlay = pygame.Surface((BOARD_PX_W, BOARD_PX_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surf.blit(overlay, (board_x, board_y))
    msg1 = fonts["big"].render(title, True, title_color)
    msg2 = fonts["font"].render(subtitle, True, TEXT_DIM)
    surf.blit(msg1, (board_x + (BOARD_PX_W - msg1.get_width()) // 2,
                     board_y + BOARD_PX_H // 2 - 50))
    surf.blit(msg2, (board_x + (BOARD_PX_W - msg2.get_width()) // 2,
                     board_y + BOARD_PX_H // 2 + 10))
