import random
import pygame

from constants import (
    BASE_FISH_SPEED,
    BASE_OBSTACLE_SPEED,
    HEIGHT,
    LURE_SPEED,
    MAX_HEALTH,
    RED,
    BLUE,
    WHITE,
    WIDTH,
    YELLOW,
    GRAY,
    PLAYER_SPEED,
)


class PlayerBoat(pygame.sprite.Sprite):
    def __init__(self, x, y, sprite_image=None):
        super().__init__()
        if sprite_image:
            self.base_image = sprite_image.copy()
        else:
            self.base_image = pygame.Surface((60, 30))
            self.base_image.fill(YELLOW)

        self.images = {
            "UP": self.base_image,
            "DOWN": pygame.transform.rotate(self.base_image, 180),
            "LEFT": pygame.transform.rotate(self.base_image, 90),
            "RIGHT": pygame.transform.rotate(self.base_image, -90),
        }
        self.direction = "UP"
        self.image = self.images[self.direction]
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = PLAYER_SPEED
        self.health = MAX_HEALTH

    def update(self, keys):
        dx = dy = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed
            self._set_direction("LEFT")
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed
            self._set_direction("RIGHT")
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.speed
            self._set_direction("UP")
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.speed
            self._set_direction("DOWN")

        self.rect.x += dx
        self.rect.y += dy
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    def take_damage(self, amount=1):
        self.health = max(0, self.health - amount)

    def _set_direction(self, direction):
        if direction == self.direction:
            return
        self.direction = direction
        prev_center = self.rect.center
        self.image = self.images.get(direction, self.base_image)
        self.rect = self.image.get_rect(center=prev_center)


class Lure(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, sprite_image=None):
        super().__init__()
        if sprite_image:
            self.image = sprite_image.copy()
        else:
            self.image = pygame.Surface((10, 10))
            self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction

    def update(self):
        if self.direction == "UP":
            self.rect.y -= LURE_SPEED
        elif self.direction == "DOWN":
            self.rect.y += LURE_SPEED
        elif self.direction == "LEFT":
            self.rect.x -= LURE_SPEED
        elif self.direction == "RIGHT":
            self.rect.x += LURE_SPEED

        if (self.rect.right < 0 or self.rect.left > WIDTH or
                self.rect.bottom < 0 or self.rect.top > HEIGHT):
            self.kill()


class Fish(pygame.sprite.Sprite):
    """
    Fish with simple two-frame color "animation".
    Some are predators (red), others normal (blue).
    """
    def __init__(self, x, y, is_predator=False,
                 friendly_images=None, predator_images=None):
        super().__init__()
        self.is_predator = is_predator
        image_pool = predator_images if is_predator else friendly_images
        self.base_image = None
        self.alt_image = None

        if image_pool:
            chosen = random.choice(image_pool)
            self.base_image = chosen.copy()
            self.alt_image = pygame.transform.flip(self.base_image, True, False)
        else:
            self.base_image = pygame.Surface((40, 20), pygame.SRCALPHA)
            self.alt_image = pygame.Surface((40, 20), pygame.SRCALPHA)

            if is_predator:
                color1 = RED
                color2 = (255, 100, 100)
            else:
                color1 = BLUE
                color2 = (100, 150, 255)

            self.base_image.fill(color1)
            self.alt_image.fill(color2)

        if self.alt_image is None:
            self.alt_image = self.base_image

        self.image = self.base_image
        self.rect = self.image.get_rect(center=(x, y))

        self.speed = BASE_FISH_SPEED + random.uniform(-1, 2)
        self.direction = random.choice([-1, 1])
        self._apply_direction_image()

    def update(self, dt_ms):
        self.rect.x += self.direction * self.speed

        if self.rect.left < 0:
            self.rect.left = 0
            self.direction = 1
            self._apply_direction_image()
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.direction = -1
            self._apply_direction_image()

    def _apply_direction_image(self):
        prev_center = self.rect.center
        if self.direction < 0 and self.alt_image:
            self.image = self.alt_image
        else:
            self.image = self.base_image
        self.rect = self.image.get_rect(center=prev_center)


class Obstacle(pygame.sprite.Sprite):
    """Simple log/rock (or shark) moving along a vector."""
    def __init__(self, x, y, frames=None, velocity=(0, 0)):
        super().__init__()
        self.frames = frames or []
        if self.frames:
            self.frame_idx = 0
            self.image = self.frames[self.frame_idx].copy()
        else:
            self.image = pygame.Surface((50, 30))
            self.image.fill(GRAY)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx, self.vy = velocity
        if self.vx == 0 and self.vy == 0:
            base = BASE_OBSTACLE_SPEED + random.uniform(-1, 2)
            self.vx, self.vy = (0, base)
        self.anim_timer = 0
        self.anim_interval = 120  # ms

    def update(self, dt_ms):
        if self.frames:
            self.anim_timer += dt_ms
            if self.anim_timer >= self.anim_interval:
                self.anim_timer = 0
                self.frame_idx = (self.frame_idx + 1) % len(self.frames)
                prev_center = self.rect.center
                self.image = self.frames[self.frame_idx]
                self.rect = self.image.get_rect(center=prev_center)

        self.rect.x += self.vx
        self.rect.y += self.vy
        # give some margin off screen before killing
        if self.rect.top > HEIGHT + 100 or self.rect.bottom < -100 or self.rect.right < -100 or self.rect.left > WIDTH + 100:
            self.kill()
