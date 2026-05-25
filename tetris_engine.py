"""
Motor de juego Tetris - logica pura, sin dependencia de pygame.

Expone:
    - Constantes (COLS, ROWS, SHAPES, kicks, etc.)
    - Clases Piece, Tetris
    - Funciones de features para IA (compute_features)
    - API IA en Tetris: get_next_states(), play_placement()
"""

import random


COLS = 10
ROWS = 20

LINE_SCORES = {1: 40, 2: 100, 3: 300, 4: 1200}

SHAPES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

JLSTZ_KICKS = {
    (0, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (1, 0): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (1, 2): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (2, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (2, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (3, 2): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (3, 0): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (0, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
}

I_KICKS = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
}

# Rotaciones unicas para enumeracion IA (evita evaluar duplicados)
UNIQUE_ROTATIONS = {
    "I": [0, 1],
    "O": [0],
    "T": [0, 1, 2, 3],
    "S": [0, 1],
    "Z": [0, 1],
    "J": [0, 1, 2, 3],
    "L": [0, 1, 2, 3],
}


def gravity_for_level(level):
    if level >= 20:
        return 0.01
    return (0.8 - (level - 1) * 0.007) ** (level - 1)


def new_bag():
    bag = list("IOTSZJL")
    random.shuffle(bag)
    return bag


def compute_features(board, lines_cleared=0):
    """
    Calcula 4 features de un tablero:
        - lineas eliminadas en este movimiento
        - huecos totales (celdas vacias con un bloque encima en la misma columna)
        - bumpiness (suma de diferencias de altura entre columnas adyacentes)
        - altura agregada
    Devuelve una lista de 4 floats.
    """
    heights = [0] * COLS
    for c in range(COLS):
        for r in range(ROWS):
            if board[r][c] is not None:
                heights[c] = ROWS - r
                break

    holes = 0
    for c in range(COLS):
        if heights[c] == 0:
            continue
        top = ROWS - heights[c]
        for r in range(top + 1, ROWS):
            if board[r][c] is None:
                holes += 1

    bumpiness = sum(abs(heights[i] - heights[i + 1]) for i in range(COLS - 1))
    total_height = sum(heights)

    return [float(lines_cleared), float(holes), float(bumpiness), float(total_height)]


class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.rotation = 0
        self.x = 3
        self.y = 0

    def cells(self, rotation=None, x=None, y=None):
        r = self.rotation if rotation is None else rotation
        px = self.x if x is None else x
        py = self.y if y is None else y
        return [(px + cx, py + cy) for cx, cy in SHAPES[self.kind][r]]


class Tetris:
    LOCK_DELAY = 0.5
    MAX_MOVE_RESETS = 15

    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [[None] * COLS for _ in range(ROWS)]
        self.bag = []
        self.queue = []
        self._refill_queue()
        self.hold = None
        self.can_hold = True
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.gravity_timer = 0.0
        self.lock_timer = 0.0
        self.move_resets = 0
        self.on_ground = False
        self.current = None
        self._spawn()

    def _refill_queue(self):
        while len(self.queue) < 7:
            if not self.bag:
                self.bag = new_bag()
            self.queue.append(self.bag.pop(0))

    def _spawn(self, kind=None):
        if kind is None:
            kind = self.queue.pop(0)
            self._refill_queue()
        self.current = Piece(kind)
        self.lock_timer = 0.0
        self.move_resets = 0
        if self._collides(self.current):
            self.game_over = True

    def _collides(self, piece, rotation=None, x=None, y=None):
        for cx, cy in piece.cells(rotation, x, y):
            if cx < 0 or cx >= COLS or cy >= ROWS:
                return True
            if cy >= 0 and self.board[cy][cx] is not None:
                return True
        return False

    def _on_ground(self):
        return self._collides(self.current, y=self.current.y + 1)

    def _reset_lock_if_grounded(self):
        if self._on_ground() and self.move_resets < self.MAX_MOVE_RESETS:
            self.lock_timer = 0.0
            self.move_resets += 1

    def move(self, dx, dy):
        if self.game_over or self.paused:
            return False
        if not self._collides(self.current, x=self.current.x + dx, y=self.current.y + dy):
            self.current.x += dx
            self.current.y += dy
            self._reset_lock_if_grounded()
            return True
        return False

    def rotate(self, direction):
        if self.game_over or self.paused:
            return False
        if self.current.kind == "O":
            return True
        cur = self.current.rotation
        new = (cur + direction) % 4
        table = I_KICKS if self.current.kind == "I" else JLSTZ_KICKS
        kicks = table.get((cur, new), [(0, 0)])
        for dx, dy in kicks:
            if not self._collides(self.current, rotation=new,
                                  x=self.current.x + dx, y=self.current.y + dy):
                self.current.rotation = new
                self.current.x += dx
                self.current.y += dy
                self._reset_lock_if_grounded()
                return True
        return False

    def soft_drop(self):
        if self.move(0, 1):
            self.score += 1
            return True
        return False

    def hard_drop(self):
        if self.game_over or self.paused:
            return
        distance = 0
        while self.move(0, 1):
            distance += 1
        self.score += distance * 2
        self._lock()

    def hold_piece(self):
        if self.game_over or self.paused or not self.can_hold:
            return
        cur = self.current.kind
        if self.hold is None:
            self.hold = cur
            self._spawn()
        else:
            nxt = self.hold
            self.hold = cur
            self._spawn(nxt)
        self.can_hold = False

    def ghost_y(self):
        y = self.current.y
        while not self._collides(self.current, y=y + 1):
            y += 1
        return y

    def _lock(self):
        for cx, cy in self.current.cells():
            if 0 <= cy < ROWS and 0 <= cx < COLS:
                self.board[cy][cx] = self.current.kind

        cleared = [r for r in range(ROWS) if all(c is not None for c in self.board[r])]
        for r in cleared:
            del self.board[r]
            self.board.insert(0, [None] * COLS)

        n = len(cleared)
        if n:
            self.score += LINE_SCORES.get(n, 0) * self.level
            self.lines += n
            new_level = self.lines // 10 + 1
            if new_level > self.level:
                self.level = new_level

        self.can_hold = True
        self.gravity_timer = 0.0
        self._spawn()
        return n

    def update(self, dt):
        if self.game_over or self.paused:
            return
        self.on_ground = self._on_ground()
        if self.on_ground:
            self.lock_timer += dt
            if self.lock_timer >= self.LOCK_DELAY:
                self._lock()
                return
        else:
            self.lock_timer = 0.0
            self.move_resets = 0
            self.gravity_timer += dt
            g = gravity_for_level(self.level)
            while self.gravity_timer >= g:
                self.gravity_timer -= g
                if not self.move(0, 1):
                    break

    def toggle_pause(self):
        if not self.game_over:
            self.paused = not self.paused

    # =========================================================
    # API para el agente IA
    # =========================================================

    def get_next_states(self):
        """
        Enumera todas las colocaciones finales validas de la pieza actual.
        Devuelve dict {(rotacion, x): features} donde features es una lista de 4 floats
        del tablero resultante (despues de bloquear y limpiar lineas).
        """
        states = {}
        kind = self.current.kind
        for rot in UNIQUE_ROTATIONS[kind]:
            cells = SHAPES[kind][rot]
            min_x = min(c[0] for c in cells)
            max_x = max(c[0] for c in cells)
            for piece_x in range(-min_x, COLS - max_x):
                # Verificar que la pieza cabe en y=0 (posicion de spawn de la enumeracion)
                spawn_ok = True
                for cx, cy in cells:
                    px, py = piece_x + cx, cy
                    if py >= 0 and self.board[py][px] is not None:
                        spawn_ok = False
                        break
                if not spawn_ok:
                    continue
                # Caer hasta el fondo
                y = 0
                while True:
                    next_y = y + 1
                    collision = False
                    for cx, cy in cells:
                        ny = cy + next_y
                        nx = cx + piece_x
                        if ny >= ROWS or (ny >= 0 and self.board[ny][nx] is not None):
                            collision = True
                            break
                    if collision:
                        break
                    y = next_y
                # Construir tablero resultante
                new_board = [row[:] for row in self.board]
                valid = True
                for cx, cy in cells:
                    py, px = cy + y, cx + piece_x
                    if py < 0:
                        valid = False
                        break
                    new_board[py][px] = kind
                if not valid:
                    continue
                # Contar y limpiar lineas
                lines = [r for r in range(ROWS) if all(c is not None for c in new_board[r])]
                for r in lines:
                    del new_board[r]
                    new_board.insert(0, [None] * COLS)
                features = compute_features(new_board, len(lines))
                states[(rot, piece_x)] = features
        return states

    def play_placement(self, rotation, x):
        """
        Aplica directamente la colocacion (rotacion, x):
        ajusta la pieza, la deja caer hasta el fondo, bloquea, limpia lineas,
        hace spawn de la siguiente. Devuelve (reward, done).

        Reward = 1 (sobrevivir) + (lineas)^2 * COLS (bonus por multi-linea) - 2 si pierde.
        """
        self.current.rotation = rotation
        self.current.x = x
        self.current.y = 0
        while not self._collides(self.current, y=self.current.y + 1):
            self.current.y += 1
        n_cleared = self._lock()
        reward = 1.0 + (n_cleared ** 2) * COLS
        if self.game_over:
            reward -= 2.0
            return reward, True
        return reward, False
