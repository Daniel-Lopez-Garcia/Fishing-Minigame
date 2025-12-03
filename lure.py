import pygame

from constants import (
    LURE_SPEED,
    WIDTH,
    HEIGHT,
    WHITE,
)


# clase de cebo
class Lure(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, sprite_image=None, owner="P1"):
        super().__init__()
        #buscamos imagen sino default
        if sprite_image:
            self.image = sprite_image.copy()
        else:
            self.image = pygame.Surface((10, 10))
            self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.owner = owner

    #movimiento
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
