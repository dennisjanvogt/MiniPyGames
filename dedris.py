import pygame
import random
import sys

# Grid dimensions
ROWS, COLS = 20, 10
CELL_SIZE = 30
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 700
PADDING = 20

# Colors for an Apple-like aesthetic
BG_COLOR = (242, 242, 247)  # System Gray 6
GRID_BG_COLOR = (255, 255, 255)  # White
TEXT_COLOR = (28, 28, 30)  # Label color
ACCENT_COLOR = (0, 122, 255)  # System Blue
SHAPE_COLORS = [
    ACCENT_COLOR,
    (255, 59, 48),
    (52, 199, 89),
    (255, 149, 0),
    (175, 82, 222),
    (255, 204, 0),
    (88, 86, 214),
]

# Face mouth types based on rotation: smile, surprise, sad, wink
MOUTH_TYPES = ["smile", "surprise", "sad", "wink"]

# Define Tetromino shapes
S = [
    [".....", ".....", "..00.", ".00..", "....."],
    [".....", "..0..", "..00.", "...0.", "....."],
]
Z = [
    [".....", ".....", ".00..", "..00.", "....."],
    [".....", "..0..", ".00..", ".0...", "....."],
]
I = [
    ["..0..", "..0..", "..0..", "..0..", "....."],
    [".....", "0000.", ".....", ".....", "....."],
]
O = [[".....", ".....", ".00..", ".00..", "....."]]
J = [
    [".....", ".0...", ".000.", ".....", "....."],
    [".....", "..00.", "..0..", "..0..", "....."],
    [".....", ".....", ".000.", "...0.", "....."],
    [".....", "..0..", "..0..", ".00..", "....."],
]
L = [
    [".....", "...0.", ".000.", ".....", "....."],
    [".....", "..0..", "..0..", "..00.", "....."],
    [".....", ".....", ".000.", ".0...", "....."],
    [".....", ".00..", "..0..", "..0..", "....."],
]
T = [
    [".....", "..0..", ".000.", ".....", "....."],
    [".....", "..0..", "..00.", "..0..", "....."],
    [".....", ".....", ".000.", "..0..", "....."],
    [".....", "..0..", ".00..", "..0..", "....."],
]
SHAPES = [S, Z, I, O, J, L, T]


class Piece:
    def __init__(self, shape):
        self.x = COLS // 2 - 2
        self.y = 0
        self.shape = shape
        self.color = SHAPE_COLORS[SHAPES.index(shape)]
        self.rotation = 0


def create_grid(locked_positions={}):
    return [[BG_COLOR for _ in range(COLS)] for _ in range(ROWS)]


def convert_shape_format(piece):
    positions = []
    format = piece.shape[piece.rotation % len(piece.shape)]
    for i, line in enumerate(format):
        for j, char in enumerate(line):
            if char == "0":
                positions.append((piece.x + j - 2, piece.y + i - 4))
    return positions


def valid_space(piece, grid):
    accepted = [
        (j, i) for i in range(ROWS) for j in range(COLS) if grid[i][j] == BG_COLOR
    ]
    for pos in convert_shape_format(piece):
        if pos not in accepted and pos[1] > -1:
            return False
    return True


def check_lost(locked_positions):
    return any(y < 1 for x, y in locked_positions)


def get_shape(bag):
    if not bag:
        bag.extend(SHAPES[:])
        random.shuffle(bag)
    shape = bag.pop()
    return Piece(shape), bag


def clear_rows(grid, locked):
    cleared = 0
    for i in range(ROWS - 1, -1, -1):
        if BG_COLOR not in grid[i]:
            cleared += 1
            for j in range(COLS):
                locked.pop((j, i), None)
    if cleared > 0:
        for x, y in sorted(list(locked), key=lambda pos: pos[1])[::-1]:
            if y < i:
                locked[(x, y + cleared)] = locked.pop((x, y))
    return cleared


def draw_face(surface, cell_rect, face_type):
    cx, cy = cell_rect.x + CELL_SIZE // 2, cell_rect.y + CELL_SIZE // 2
    eye_radius = CELL_SIZE // 10
    eye_offset_x = CELL_SIZE // 4
    eye_y = cy - CELL_SIZE // 8
    # Eyes
    pygame.draw.circle(surface, TEXT_COLOR, (cx - eye_offset_x, eye_y), eye_radius)
    pygame.draw.circle(surface, TEXT_COLOR, (cx + eye_offset_x, eye_y), eye_radius)
    # Mouth
    mouth_type = MOUTH_TYPES[face_type % len(MOUTH_TYPES)]
    mouth_width = CELL_SIZE // 2
    mouth_height = CELL_SIZE // 6
    mouth_rect = pygame.Rect(0, 0, mouth_width, mouth_height)
    mouth_rect.center = (cx, cy + CELL_SIZE // 8)
    if mouth_type == "smile":
        pygame.draw.arc(surface, TEXT_COLOR, mouth_rect, 3.14, 0, 2)
    elif mouth_type == "sad":
        pygame.draw.arc(surface, TEXT_COLOR, mouth_rect, 0, 3.14, 2)
    elif mouth_type == "surprise":
        pygame.draw.circle(surface, TEXT_COLOR, (cx, cy + CELL_SIZE // 8), mouth_height)
    elif mouth_type == "wink":
        pygame.draw.line(
            surface,
            TEXT_COLOR,
            (cx - eye_offset_x, eye_y),
            (cx - eye_offset_x + eye_radius * 2, eye_y),
            2,
        )
        pygame.draw.circle(surface, TEXT_COLOR, (cx + eye_offset_x, eye_y), eye_radius)
        pygame.draw.arc(surface, TEXT_COLOR, mouth_rect, 3.14, 0, 2)


def draw_window(surface, grid, locked, score, level):
    surface.fill(BG_COLOR)
    # Draw grid background
    grid_rect = pygame.Rect(PADDING, PADDING, COLS * CELL_SIZE, ROWS * CELL_SIZE)
    pygame.draw.rect(surface, GRID_BG_COLOR, grid_rect, border_radius=12)
    # Draw cells and faces
    for i in range(ROWS):
        for j in range(COLS):
            cell_color = grid[i][j]
            cell_rect = pygame.Rect(
                PADDING + j * CELL_SIZE, PADDING + i * CELL_SIZE, CELL_SIZE, CELL_SIZE
            )
            pygame.draw.rect(surface, cell_color, cell_rect, border_radius=4)
    # Draw locked block faces
    for (x, y), (color, face) in locked.items():
        cell_rect = pygame.Rect(
            PADDING + x * CELL_SIZE, PADDING + y * CELL_SIZE, CELL_SIZE, CELL_SIZE
        )
        draw_face(surface, cell_rect, face)
    # Draw moving piece faces
    for x, y in convert_shape_format(current_piece):
        if y > -1:
            cell_rect = pygame.Rect(
                PADDING + x * CELL_SIZE, PADDING + y * CELL_SIZE, CELL_SIZE, CELL_SIZE
            )
            draw_face(surface, cell_rect, current_piece.rotation)
    # Draw stats
    font_title = pygame.font.SysFont("Helvetica Neue", 48)
    font_stats = pygame.font.SysFont("Helvetica Neue", 24)
    surface.blit(
        font_title.render("Dedris", True, TEXT_COLOR),
        (COLS * CELL_SIZE + 2 * PADDING, PADDING),
    )
    surface.blit(
        font_stats.render(f"Score: {score}", True, TEXT_COLOR),
        (COLS * CELL_SIZE + 2 * PADDING, PADDING + 60),
    )
    surface.blit(
        font_stats.render(f"Level: {level}", True, TEXT_COLOR),
        (COLS * CELL_SIZE + 2 * PADDING, PADDING + 90),
    )


def main():
    global current_piece  # needed for draw_window
    pygame.init()
    win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Dedris")

    locked = {}
    bag = []
    current_piece, bag = get_shape(bag)
    next_piece, bag = get_shape(bag)
    hold_piece = None
    hold_used = False

    clock = pygame.time.Clock()
    fall_time = 0
    fall_speed = 0.5
    score = 0
    level = 0

    run = True
    while run:
        grid = create_grid(locked)
        fall_time += clock.get_rawtime()
        clock.tick()
        if score // 1000 > level:
            level += 1
            fall_speed = max(0.1, fall_speed - 0.05)
        if fall_time / 1000 >= fall_speed:
            fall_time = 0
            current_piece.y += 1
            if not valid_space(current_piece, grid) and current_piece.y > 0:
                current_piece.y -= 1
                change_piece = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_piece.x -= 1
                    if not valid_space(current_piece, grid):
                        current_piece.x += 1
                elif event.key == pygame.K_RIGHT:
                    current_piece.x += 1
                    if not valid_space(current_piece, grid):
                        current_piece.x -= 1
                elif event.key == pygame.K_DOWN:
                    current_piece.y += 1
                    if not valid_space(current_piece, grid):
                        current_piece.y -= 1
                elif event.key == pygame.K_UP:
                    current_piece.rotation = (current_piece.rotation + 1) % len(
                        current_piece.shape
                    )
                    if not valid_space(current_piece, grid):
                        current_piece.rotation = (current_piece.rotation - 1) % len(
                            current_piece.shape
                        )
                elif event.key == pygame.K_SPACE:
                    while valid_space(current_piece, grid):
                        current_piece.y += 1
                    current_piece.y -= 1
                    change_piece = True
                elif event.key == pygame.K_c and not hold_used:
                    if hold_piece:
                        current_piece, hold_piece = hold_piece, current_piece
                        current_piece.x, current_piece.y = COLS // 2 - 2, 0
                    else:
                        hold_piece = current_piece
                        current_piece, bag = get_shape(bag)
                    hold_used = True
                elif event.key == pygame.K_p:
                    paused = True
                    draw_window(win, grid, locked, score, level)
                    pygame.display.update()
                    while paused:
                        for pe in pygame.event.get():
                            if pe.type == pygame.KEYDOWN and pe.key == pygame.K_p:
                                paused = False
                            if pe.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
        shape_positions = convert_shape_format(current_piece)
        for x, y in shape_positions:
            if y > -1:
                locked_color = current_piece.color
                # store color and face type per block
                locked[(x, y)] = (locked_color, current_piece.rotation)
        if "change_piece" in locals() and change_piece:
            lines = clear_rows(grid, locked)
            score += {1: 100, 2: 300, 3: 500}.get(lines, 800)
            current_piece = next_piece
            next_piece, bag = get_shape(bag)
            change_piece = False
            hold_used = False
        draw_window(win, grid, locked, score, level)
        pygame.display.update()
        if check_lost(locked):
            draw_window(win, grid, locked, score, level)
            font = pygame.font.SysFont("Helvetica Neue", 48)
            label = font.render("Game Over", True, (255, 59, 48))
            win.blit(
                label,
                (WINDOW_WIDTH // 2 - label.get_width() // 2, WINDOW_HEIGHT // 2 - 50),
            )
            pygame.display.update()
            pygame.time.delay(2000)
            run = False
    pygame.quit()


if __name__ == "__main__":
    main()
