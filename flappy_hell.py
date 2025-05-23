import pygame
import sys
import random
import math

# --- Einstellungen ---
WIDTH, HEIGHT = 400, 600
FPS = 60
GRAVITY = 0.5
FLAP_STRENGTH = -9
PIPE_GAP = 150
PIPE_WIDTH = 70
PIPE_DISTANCE = 200
PIPE_SPEED = 3
BG_COLOR_TOP = (30, 0, 0)
BG_COLOR_BOTTOM = (0, 0, 0)
LAVA_HEIGHT = 80

# --- Initialisierung ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font_large = pygame.font.SysFont("arialblack", 60)
font_small = pygame.font.SysFont("arial", 36)


# --- Particle System für Flamme beim Flap ---
class Particle:
    def __init__(self, pos):
        self.x, self.y = pos
        self.vel = [random.uniform(-1, 1), random.uniform(-3, 0)]
        self.life = random.randint(20, 40)
        self.size = random.randint(3, 6)

    def update(self):
        self.x += self.vel[0]
        self.y += self.vel[1]
        self.vel[1] += GRAVITY * 0.1
        self.life -= 1

    def draw(self, surf):
        t = max(self.life, 0) / 40
        color = (255, int(100 + 155 * t), 0)
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), int(self.size * t))


# --- Spielfigur Schildkröte ---
class Turtle:
    def __init__(self):
        self.start_x = 100
        self.start_y = HEIGHT // 2
        self.reset()

    def reset(self):
        self.x = self.start_x
        self.y = self.start_y
        self.vel = 0
        self.radius = 20
        self.particles = []

    def flap(self):
        self.vel = FLAP_STRENGTH
        # generiere Partikel
        for _ in range(5):
            self.particles.append(Particle((self.x - self.radius, self.y)))

    def update(self):
        self.vel += GRAVITY
        self.y += self.vel
        # update Partikel
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surf):
        # draw particles
        for p in self.particles:
            p.draw(surf)
        # rotate based on velocity
        angle = -self.vel * 3
        # Shell
        shell = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            shell, (34, 139, 34), (self.radius, self.radius), self.radius
        )
        # Hex-Muster
        for i in range(6):
            ang = math.radians(i * 60)
            x1 = self.radius + math.cos(ang) * self.radius * 0.6
            y1 = self.radius + math.sin(ang) * self.radius * 0.6
            x2 = self.radius + math.cos(ang + math.pi / 3) * self.radius * 0.6
            y2 = self.radius + math.sin(ang + math.pi / 3) * self.radius * 0.6
            pygame.draw.line(shell, (0, 100, 0), (x1, y1), (x2, y2), 3)
        # Kopf
        pygame.draw.circle(
            shell,
            (34, 139, 34),
            (int(self.radius * 1.6), int(self.radius * 0.8)),
            self.radius // 2,
        )
        # Augen
        pygame.draw.circle(
            shell,
            (255, 255, 255),
            (int(self.radius * 1.6 + 4), int(self.radius * 0.8 - 4)),
            4,
        )
        pygame.draw.circle(
            shell,
            (0, 0, 0),
            (int(self.radius * 1.6 + 4), int(self.radius * 0.8 - 4)),
            2,
        )
        # drehen und zeichnen
        rot = pygame.transform.rotate(shell, angle)
        rect = rot.get_rect(center=(int(self.x), int(self.y)))
        surf.blit(rot, rect.topleft)

    def get_rect(self):
        return pygame.Rect(
            self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2
        )


# --- Hindernisse ---
class Pipe:
    def __init__(self, x):
        self.x = x
        self.height = random.randint(50, HEIGHT - PIPE_GAP - 50)
        self.passed = False

    def update(self):
        self.x -= PIPE_SPEED

    def draw(self, surf):
        # Rohr
        pygame.draw.rect(surf, (60, 30, 30), (self.x, 0, PIPE_WIDTH, self.height))
        pygame.draw.rect(
            surf,
            (60, 30, 30),
            (
                self.x,
                self.height + PIPE_GAP,
                PIPE_WIDTH,
                HEIGHT - self.height - PIPE_GAP - LAVA_HEIGHT,
            ),
        )
        # Zacken
        for y in range(self.height - 10, -10, -20):
            points = [(self.x, y), (self.x + 10, y - 10), (self.x + 20, y)]
            pygame.draw.polygon(surf, (100, 0, 0), points)
        for y in range(self.height + PIPE_GAP + 10, HEIGHT - LAVA_HEIGHT + 10, 20):
            points = [
                (self.x + PIPE_WIDTH, y),
                (self.x + PIPE_WIDTH - 10, y + 10),
                (self.x + PIPE_WIDTH - 20, y),
            ]
            pygame.draw.polygon(surf, (100, 0, 0), points)

    def off_screen(self):
        return self.x + PIPE_WIDTH < 0

    def collides_with(self, rect):
        top_rect = pygame.Rect(self.x, 0, PIPE_WIDTH, self.height)
        bottom_rect = pygame.Rect(
            self.x, self.height + PIPE_GAP, PIPE_WIDTH, HEIGHT - self.height - PIPE_GAP
        )
        return rect.colliderect(top_rect) or rect.colliderect(bottom_rect)


# --- Hintergrund & Lava ---
def draw_background(surf):
    # Farbverlauf
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(BG_COLOR_TOP[0] * (1 - t) + BG_COLOR_BOTTOM[0] * t)
        g = int(BG_COLOR_TOP[1] * (1 - t) + BG_COLOR_BOTTOM[1] * t)
        b = int(BG_COLOR_TOP[2] * (1 - t) + BG_COLOR_BOTTOM[2] * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (WIDTH, y))
    # flackernde Flammen
    for i in range(10):
        x = random.randint(0, WIDTH)
        h = random.randint(50, 150)
        points = [
            (x, h),
            (x + random.randint(-20, 20), h + random.randint(20, 40)),
            (x + random.randint(-30, 30), h // 2),
        ]
        pygame.draw.polygon(surf, (255, random.randint(50, 150), 0), points)


def draw_lava(surf):
    points = []
    for x in range(0, WIDTH + 1, 10):
        y = (
            HEIGHT
            - LAVA_HEIGHT
            + math.sin(x * 0.1 + pygame.time.get_ticks() * 0.005) * 10
        )
        points.append((x, y))
    points += [(WIDTH, HEIGHT), (0, HEIGHT)]
    pygame.draw.polygon(surf, (255, 100, 0), points)


# --- Spielfunktionen ---
turtle = Turtle()
pipes = []
score = 0
high_score = 0
state = "start"


# Text mit Outline
def draw_text(surf, text, font, pos):
    x, y = pos
    base = font.render(text, True, (255, 255, 255))
    outline = font.render(text, True, (0, 0, 0))
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        surf.blit(outline, (x + dx, y + dy))
    surf.blit(base, (x, y))


# Reset
def reset_game():
    global pipes, score
    turtle.reset()
    pipes = [Pipe(WIDTH + i * PIPE_DISTANCE) for i in range(3)]
    score = 0


# Hauptschleife
running = True
while running:
    dt = clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if state == "start":
                state = "playing"
                reset_game()
            elif state == "playing":
                turtle.flap()
            elif state == "game_over":
                state = "start"

    # Update
    if state == "playing":
        turtle.update()
        for pipe in pipes:
            pipe.update()
            if pipe.collides_with(turtle.get_rect()):
                state = "game_over"
                high_score = max(high_score, score)
            if not pipe.passed and pipe.x + PIPE_WIDTH < turtle.x:
                score += 1
                pipe.passed = True
        if pipes and pipes[0].off_screen():
            pipes.pop(0)
            pipes.append(Pipe(pipes[-1].x + PIPE_DISTANCE))
        if (
            turtle.y - turtle.radius < 0
            or turtle.y + turtle.radius > HEIGHT - LAVA_HEIGHT
        ):
            state = "game_over"
            high_score = max(high_score, score)

    # Zeichnen
    draw_background(screen)
    for pipe in pipes:
        if state != "start":
            pipe.draw(screen)
    draw_lava(screen)
    if state == "start":
        draw_text(screen, "Flappy Turtle", font_large, (50, HEIGHT // 3))
        draw_text(screen, "Press SPACE", font_small, (120, HEIGHT // 2))
    elif state == "playing":
        turtle.draw(screen)
        draw_text(screen, f"Score: {score}", font_small, (10, 10))
    elif state == "game_over":
        turtle.draw(screen)
        draw_text(screen, "Game Over", font_large, (60, HEIGHT // 3))
        draw_text(screen, f"Score: {score}", font_small, (140, HEIGHT // 2))
        draw_text(
            screen, f"High Score: {high_score}", font_small, (100, HEIGHT // 2 + 40)
        )
        draw_text(screen, "Press SPACE", font_small, (120, HEIGHT // 2 + 80))
    if state == "playing":
        turtle.draw(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()
