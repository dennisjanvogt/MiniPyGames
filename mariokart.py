import pygame
import random
import os
import math

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Paths
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")


class Car(pygame.sprite.Sprite):
    def __init__(self, image_path, pos):
        super().__init__()
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.image = self.original_image
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        self.velocity = pygame.math.Vector2(0, 0)
        self.angle = 0
        self.speed = 0
        self.max_speed = 300  # pixels per second
        self.acceleration = 200
        self.friction = 150
        self.rotation_speed = 200  # degrees per second
        self.item = None
        self.laps = 0

    def update(self, dt, track_mask):
        keys = pygame.key.get_pressed()
        # Acceleration & braking
        if keys[pygame.K_UP]:
            self.speed += self.acceleration * dt
        elif keys[pygame.K_DOWN]:
            self.speed -= self.acceleration * dt
        else:
            # Apply friction
            if self.speed > 0:
                self.speed -= self.friction * dt
            elif self.speed < 0:
                self.speed += self.friction * dt
        self.speed = max(-self.max_speed / 2, min(self.speed, self.max_speed))

        # Steering
        if keys[pygame.K_LEFT]:
            self.angle += self.rotation_speed * dt * (self.speed / self.max_speed)
        if keys[pygame.K_RIGHT]:
            self.angle -= self.rotation_speed * dt * (self.speed / self.max_speed)

        # Movement
        rad = math.radians(self.angle)
        self.velocity.x = -math.sin(rad) * self.speed
        self.velocity.y = -math.cos(rad) * self.speed
        self.pos += self.velocity * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # Collision with track boundaries
        if track_mask.get_at((self.rect.centerx, self.rect.centery)) == 0:
            # Off-track: slow down
            self.speed *= 0.5

        # Rotate image
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

        # Lap detection (simple checkpoint system)
        # TODO: implement real checkpoints

    def collect_item(self, item):
        self.item = item

    def use_item(self):
        if self.item:
            self.item.activate(self)
            self.item = None


class ItemBox(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.image.load(
            os.path.join(ASSETS_DIR, "item_box.png")
        ).convert_alpha()
        self.rect = self.image.get_rect(center=pos)

    def spawn_item(self):
        # Randomly choose an item
        choice = random.choice([Banana, RedShell, GreenShell, Mushroom])
        return choice()


class Banana(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load(
            os.path.join(ASSETS_DIR, "banana.png")
        ).convert_alpha()
        self.rect = self.image.get_rect()

    def activate(self, user_car):
        # Drop banana behind the car
        banana = BananaObstacle(user_car.pos - pygame.math.Vector2(0, 50))
        return banana


class RedShell(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load(
            os.path.join(ASSETS_DIR, "red_shell.png")
        ).convert_alpha()
        self.rect = self.image.get_rect()

    def activate(self, user_car):
        # Launch shell in facing direction
        shell = ShellProjectile(user_car.pos, user_car.angle)
        return shell


class GreenShell(RedShell):
    def activate(self, user_car):
        shell = ShellProjectile(user_car.pos, user_car.angle, homing=False)
        return shell


class Mushroom(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load(
            os.path.join(ASSETS_DIR, "mushroom.png")
        ).convert_alpha()
        self.rect = self.image.get_rect()

    def activate(self, user_car):
        user_car.speed += 200  # Temporary speed boost
        return None


class BananaObstacle(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.image.load(
            os.path.join(ASSETS_DIR, "banana_obstacle.png")
        ).convert_alpha()
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))

    def update(self, dt, *args):
        pass


class ShellProjectile(pygame.sprite.Sprite):
    def __init__(self, pos, angle, homing=True):
        super().__init__()
        self.original_image = pygame.image.load(
            os.path.join(ASSETS_DIR, "shell.png")
        ).convert_alpha()
        self.image = self.original_image
        self.pos = pygame.math.Vector2(pos)
        self.angle = angle
        self.speed = 400
        self.homing = homing
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt, target_car=None):
        if self.homing and target_car:
            # Simple homing logic
            direction = (target_car.pos - self.pos).normalize()
            self.pos += direction * self.speed * dt
        else:
            rad = math.radians(self.angle)
            self.pos.x += -math.sin(rad) * self.speed * dt
            self.pos.y += -math.cos(rad) * self.speed * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))


class Track:
    def __init__(self, image_path, mask_path, start_pos, item_box_positions):
        self.image = pygame.image.load(image_path).convert()
        self.mask_image = pygame.image.load(mask_path).convert()
        self.mask = pygame.mask.from_surface(self.mask_image)
        self.start_pos = start_pos
        self.item_box_positions = item_box_positions

    def draw(self, surface):
        surface.blit(self.image, (0, 0))

    def get_mask(self):
        return self.mask


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Mario Kart Clone")
    clock = pygame.time.Clock()

    # Load track
    track = Track(
        os.path.join(ASSETS_DIR, "track.png"),
        os.path.join(ASSETS_DIR, "track_mask.png"),
        start_pos=(512, 384),
        item_box_positions=[(300, 300), (700, 300), (300, 500), (700, 500)],
    )

    # Sprite groups
    all_sprites = pygame.sprite.Group()
    items_group = pygame.sprite.Group()
    obstacles_group = pygame.sprite.Group()

    # Player car
    car = Car(os.path.join(ASSETS_DIR, "kart.png"), track.start_pos)
    all_sprites.add(car)

    # Item boxes
    item_boxes = pygame.sprite.Group()
    for pos in track.item_box_positions:
        box = ItemBox(pos)
        item_boxes.add(box)
        all_sprites.add(box)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000  # Delta time in seconds
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    spawned = car.use_item()
                    if spawned:
                        obstacles_group.add(spawned)
                        all_sprites.add(spawned)

        # Update
        all_sprites.update(dt, track.get_mask())

        # Check collisions with item boxes
        hits = pygame.sprite.spritecollide(car, item_boxes, False)
        for hit in hits:
            item = hit.spawn_item()
            car.collect_item(item)
            hit.kill()

        # Draw
        track.draw(screen)
        all_sprites.draw(screen)

        # HUD
        font = pygame.font.SysFont(None, 24)
        text = font.render(f"Speed: {int(car.speed)} | Laps: {car.laps}", True, WHITE)
        screen.blit(text, (10, 10))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
