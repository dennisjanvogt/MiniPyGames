import pygame
import sys
import random
import time
import math

# --- Einstellungen ---
DEFAULT_WIDTH, DEFAULT_HEIGHT = 800, 900
FPS = 60
STAT_DECAY_INTERVAL = 3000  # ms
STAT_DECAY_AMOUNT = 1
MAX_STAT = 100
BUTTON_HEIGHT = 60
BUTTON_PADDING = 15
BUTTON_COLOR = (180, 220, 255)
BUTTON_HOVER_COLOR = (210, 240, 255)
BG_COLOR_TOP = (255, 230, 200)
BG_COLOR_BOTTOM = (255, 200, 230)

# --- Initialisierung ---
pygame.init()
screen = pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Cute Dino Tamagotchi")
clock = pygame.time.Clock()
font_large = pygame.font.SysFont("comic sans ms", 48)
font_medium = pygame.font.SysFont("comic sans ms", 36)
font_small = pygame.font.SysFont("arial", 24)

STAT_COLORS = {
    "fullness": (255, 100, 100),
    "happiness": (255, 200, 100),
    "cleanliness": (100, 200, 255),
    "energy": (200, 100, 255),
    "thirst": (100, 255, 200),
}


# --- Particle für Effekte ---
class Particle:
    def __init__(self, pos, kind, screen_size):
        self.screen_w, self.screen_h = screen_size
        self.x, self.y = pos
        angle = random.uniform(-math.pi / 3, -2 * math.pi / 3)
        self.vel = [
            math.cos(angle) * random.uniform(1, 3),
            math.sin(angle) * random.uniform(1, 3),
        ]
        self.life = random.randint(40, 80)
        self.size = random.randint(8, 16)
        self.kind = kind

    def update(self):
        self.x += self.vel[0]
        self.y += self.vel[1]
        self.life -= 1

    def draw(self, surf):
        t = max(self.life / 80, 0)
        if self.kind == "heart":
            color = (255, max(100, int(255 * t)), max(100, int(255 * t)))
            # draw heart with two circles and a triangle
            r = int(self.size * t)
            center = (int(self.x), int(self.y))
            pygame.draw.circle(surf, color, (center[0] - r // 2, center[1]), r)
            pygame.draw.circle(surf, color, (center[0] + r // 2, center[1]), r)
            points = [
                (center[0] - r, center[1]),
                (center[0], center[1] + r),
                (center[0] + r, center[1]),
            ]
            pygame.draw.polygon(surf, color, points)
        else:
            # bubble
            color = (200, 230, 255, int(255 * t))
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (self.size, self.size), self.size)
            surf.blit(s, (self.x - self.size, self.y - self.size))


# --- Dino-Tamagotchi ---
class Dino:
    def __init__(self, screen_size):
        self.screen_w, self.screen_h = screen_size
        self.reset()

    def reset(self):
        self.stats = {
            k: MAX_STAT
            for k in ("fullness", "happiness", "cleanliness", "energy", "thirst")
        }
        now = pygame.time.get_ticks()
        self.birth = now
        self.last_decay = now
        self.age = 0
        self.alive = True
        self.blink_time = now
        self.blink_duration = 200
        self.is_blinking = False
        self.particles = []
        self.state = "idle"
        self.sleep_start = 0

    def pos(self):
        return self.screen_w // 2, self.screen_h // 2 + 50

    def update(self):
        now = pygame.time.get_ticks()
        self.age = (now - self.birth) // 10000
        # decay stats
        if now - self.last_decay > STAT_DECAY_INTERVAL and self.alive:
            for k in self.stats:
                self.stats[k] = max(0, self.stats[k] - STAT_DECAY_AMOUNT)
            self.last_decay = now
        # death check
        if any(v == 0 for v in self.stats.values()):
            self.alive = False
        # blinking
        if not self.is_blinking and now - self.blink_time > random.randint(2000, 5000):
            self.is_blinking = True
            self.blink_time = now
        if self.is_blinking and now - self.blink_time > self.blink_duration:
            self.is_blinking = False
            self.blink_time = now
        # particles
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]
        # sleep recovery
        if self.state == "sleep" and now - self.sleep_start > 5000:
            self.stats["energy"] = min(MAX_STAT, self.stats["energy"] + 20)
            self.state = "idle"

    def feed(self):
        if self.alive:
            self.stats["fullness"] = min(MAX_STAT, self.stats["fullness"] + 30)
            for _ in range(10):
                self.particles.append(
                    Particle(self.pos(), "bubble", (self.screen_w, self.screen_h))
                )

    def play(self):
        if self.alive:
            # mini-game: random bug appears to click
            self.stats["happiness"] = min(MAX_STAT, self.stats["happiness"] + 30)
            self.stats["energy"] = max(0, self.stats["energy"] - 10)
            for _ in range(10):
                self.particles.append(
                    Particle(self.pos(), "heart", (self.screen_w, self.screen_h))
                )

    def clean(self):
        if self.alive:
            self.stats["cleanliness"] = min(MAX_STAT, self.stats["cleanliness"] + 40)
            self.stats["happiness"] = max(0, self.stats["happiness"] - 5)
            for _ in range(15):
                self.particles.append(
                    Particle(self.pos(), "bubble", (self.screen_w, self.screen_h))
                )

    def sleep(self):
        if self.alive:
            self.state = "sleep"
            self.sleep_start = pygame.time.get_ticks()

    def drink(self):
        if self.alive:
            self.stats["thirst"] = min(MAX_STAT, self.stats["thirst"] + 40)
            for _ in range(10):
                self.particles.append(
                    Particle(self.pos(), "bubble", (self.screen_w, self.screen_h))
                )

    def draw(self, surf):
        x, y = self.pos()
        # body
        size = 200 + int(self.age * 2)
        body = pygame.Rect(0, 0, size, size * 0.6)
        body.center = (x, y)
        pygame.draw.ellipse(surf, (150, 200, 100), body)
        # limb
        leg = pygame.Rect(x - 40, y + size * 0.3, 30, 50)
        pygame.draw.rect(surf, (120, 160, 80), leg, border_radius=10)
        leg2 = leg.copy()
        leg2.x += 60
        pygame.draw.rect(surf, (120, 160, 80), leg2, border_radius=10)
        # tail
        points = [
            (x - body.width // 2, y),
            (x - body.width // 2 - 80, y - 20),
            (x - body.width // 2 - 60, y),
        ]
        pygame.draw.polygon(surf, (150, 200, 100), points)
        # spikes
        for i in range(5):
            sx = x - body.width // 4 + i * (body.width / 5)
            sy = y - body.height // 2
            tri = [(sx, sy), (sx + 10, sy - 30), (sx + 20, sy)]
            pygame.draw.polygon(surf, (200, 100, 100), tri)
        # eyes
        eye_y = y - body.height * 0.2
        if self.is_blinking:
            pygame.draw.line(
                surf, (0, 0, 0), (x - size * 0.1, eye_y), (x - size * 0.05, eye_y), 5
            )
            pygame.draw.line(
                surf, (0, 0, 0), (x + size * 0.05, eye_y), (x + size * 0.1, eye_y), 5
            )
        else:
            pygame.draw.circle(
                surf, (0, 0, 0), (int(x - size * 0.1), int(eye_y)), int(size * 0.03)
            )
            pygame.draw.circle(
                surf, (0, 0, 0), (int(x + size * 0.1), int(eye_y)), int(size * 0.03)
            )
        # mouth
        mouth = pygame.Rect(0, 0, int(size * 0.2), int(size * 0.1))
        mouth.center = (x, y - body.height * 0.1)
        if not self.alive:
            pygame.draw.arc(surf, (150, 0, 0), mouth, math.pi, 2 * math.pi, 5)
        elif self.state == "sleep":
            surf.blit(
                font_medium.render("Zzz...", True, (0, 0, 0)),
                (x + size * 0.2, y - body.height * 0.5),
            )
        elif self.stats["happiness"] > 50:
            pygame.draw.arc(surf, (0, 0, 0), mouth, 0, math.pi, 5)
        else:
            pygame.draw.arc(surf, (0, 0, 0), mouth, math.pi, 2 * math.pi, 5)
        # particles
        for p in self.particles:
            p.draw(surf)


# --- Button-Klasse ---
class Button:
    def __init__(self, rect, text, action):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action

    def draw(self, surf):
        color = (
            BUTTON_HOVER_COLOR
            if self.rect.collidepoint(pygame.mouse.get_pos())
            else BUTTON_COLOR
        )
        pygame.draw.rect(surf, color, self.rect, border_radius=15)
        surf.blit(
            font_small.render(self.text, True, (0, 0, 0)),
            self.rect.center - pygame.Vector2(font_small.size(self.text)) / 2,
        )

    def handle(self, event):
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        ):
            self.action()


# --- Hilfsfunktionen ---
def draw_stats(surf, pet):
    w, h = surf.get_size()
    x = 20
    y = 20
    bar_h = 25
    for k, color in STAT_COLORS.items():
        # bg
        pygame.draw.rect(
            surf, (200, 200, 200), (x, y, w - 2 * x, bar_h), border_radius=10
        )
        val = pet.stats[k]
        pygame.draw.rect(
            surf, color, (x, y, (w - 2 * x) * (val / MAX_STAT), bar_h), border_radius=10
        )
        surf.blit(
            font_small.render(f"{k.capitalize()}: {val}", True, (0, 0, 0)), (x, y - 2)
        )
        y += bar_h + 10


def draw_text(surf, text, pos, font):
    surf.blit(font.render(text, True, (0, 0, 0)), pos)


# --- Setup ---
screen_w, screen_h = screen.get_size()
dino = Dino((screen_w, screen_h))
labels = ["Feed", "Play", "Clean", "Sleep", "Drink"]
actions = [dino.feed, dino.play, dino.clean, dino.sleep, dino.drink]
buttons = []
bw = (screen_w - (len(labels) + 1) * BUTTON_PADDING) / len(labels)
for i, (l, a) in enumerate(zip(labels, actions)):
    x = BUTTON_PADDING + (bw + BUTTON_PADDING) * i
    y = screen_h - BUTTON_HEIGHT - BUTTON_PADDING
    buttons.append(Button((x, y, bw, BUTTON_HEIGHT), l, a))

# --- Hauptschleife ---
running = True
while running:
    dt = clock.tick(FPS)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode(e.size, pygame.RESIZABLE)
            screen_w, screen_h = e.size
            dino.screen_w, dino.screen_h = e.size
            # recalc buttons
            bw = (screen_w - (len(labels) + 1) * BUTTON_PADDING) / len(labels)
            for i, b in enumerate(buttons):
                b.rect.topleft = (
                    BUTTON_PADDING + (bw + BUTTON_PADDING) * i,
                    screen_h - BUTTON_HEIGHT - BUTTON_PADDING,
                )
                b.rect.size = (bw, BUTTON_HEIGHT)
        for b in buttons:
            b.handle(e)

    dino.update()
    # background
    for y in range(screen_h):
        t = y / screen_h
        r = int(BG_COLOR_TOP[0] * (1 - t) + BG_COLOR_BOTTOM[0] * t)
        g = int(BG_COLOR_TOP[1] * (1 - t) + BG_COLOR_BOTTOM[1] * t)
        b = int(BG_COLOR_TOP[2] * (1 - t) + BG_COLOR_BOTTOM[2] * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (screen_w, y))
    draw_stats(screen, dino)
    draw_text(screen, f"Age: {dino.age}", (20, screen_h - 120), font_medium)
    dino.draw(screen)
    for b in buttons:
        b.draw(screen)
    pygame.display.flip()

pygame.quit()
sys.exit()
