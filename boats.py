import pygame

from constants import (
    HEIGHT,
    MAX_HEALTH,
    PLAYER_SPEED,
    WIDTH,
    YELLOW,
)


#Clase de bote
class PlayerBoat(pygame.sprite.Sprite):
    def __init__(self, x, y, sprite_image=None, sunken_image=None, name="P1"):
        super().__init__()
        #busca la img
        if sprite_image:
            self.base_image = sprite_image.copy()
        else:  # no la encuentra
            self.base_image = pygame.Surface((60, 30))
            self.base_image.fill(YELLOW)
        #rote con el jugador
        self.images = {
            "UP": self.base_image,
            "DOWN": pygame.transform.rotate(self.base_image, 180),
            "LEFT": pygame.transform.rotate(self.base_image, 90),
            "RIGHT": pygame.transform.rotate(self.base_image, -90),
        }
        self.direction = "UP"  # default
        self.image = self.images[self.direction]
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = PLAYER_SPEED
        self.health = MAX_HEALTH
        self.name = name
        #scale sunken sprite smaller than the boat to avoid oversized wreck
        if sunken_image:
            target_size = self.image.get_size()
            shrink = 0.6  # render wreck smaller for clarity
            target_size = (max(8, int(target_size[0] * shrink)),
                           max(8, int(target_size[1] * shrink)))
            self.sunken_image = pygame.transform.smoothscale(
                sunken_image.copy(), target_size
            )
        else:
            self.sunken_image = None
        self.is_sunk = False

    def update(self, keys, controls):
        dx = dy = 0
        #movimiento de el boat
        if keys[controls["left"]]:
            dx = -self.speed
            self._set_direction("LEFT")
        if keys[controls["right"]]:
            dx = self.speed
            self._set_direction("RIGHT")
        if keys[controls["up"]]:
            dy = -self.speed
            self._set_direction("UP")
        if keys[controls["down"]]:
            dy = self.speed
            self._set_direction("DOWN")

        self.rect.x += dx
        self.rect.y += dy
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    #hp
    def take_damage(self, amount=1):
        self.health = max(0, self.health - amount)
        if self.health <= 0 and not self.is_sunk:
            self.is_sunk = True
            prev_center = self.rect.center
            if self.sunken_image:
                self.image = self.sunken_image
            self.rect = self.image.get_rect(center=prev_center)

    #dirrecion
    def _set_direction(self, direction):
        if direction == self.direction:
            return
        self.direction = direction
        prev_center = self.rect.center
        self.image = self.images.get(direction, self.base_image)
        self.rect = self.image.get_rect(center=prev_center)
