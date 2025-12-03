import random
import pygame

from constants import (
    BASE_FISH_SPEED,
    HEIGHT,
    WIDTH,
    BLUE,
    RED,
)


#class peces 
class Fish(pygame.sprite.Sprite):

   #buscamos las imagenes
    def __init__(self, x, y, is_predator=False,
                 friendly_images=None, predator_images=None):
        
        super().__init__() #llama al init para iniciar sprites
        self.is_predator = is_predator

        image_pool = predator_images if is_predator else friendly_images
        self.base_image = None
        self.alt_image = None

    #escojemos img
        if image_pool:
            chosen = random.choice(image_pool)
            self.base_image = chosen.copy()
            self.alt_image = pygame.transform.flip(self.base_image, True, False) #imagen para cuando voltee
        else:
            self.base_image = pygame.Surface((40, 20), pygame.SRCALPHA)
            self.alt_image = pygame.Surface((40, 20), pygame.SRCALPHA) #transparencia

            if is_predator:#shark
                color1 = RED
                color2 = (255, 100, 100)
            else:
                color1 = BLUE
                color2 = (100, 150, 255)

            self.base_image.fill(color1)
            self.alt_image.fill(color2)

        if self.alt_image is None:
            self.alt_image = self.base_image

    #dirrecion, velocidad y pos
        self.image = self.base_image
        self.rect = self.image.get_rect(center=(x, y))

        self.speed = BASE_FISH_SPEED + random.uniform(-1, 2)
        self.direction = random.choice([-1, 1])
        self._apply_direction_image()

    def update(self, dt_ms):

        self.rect.x += self.direction * self.speed
    #moviminento de peces con rebote de screen
        if self.rect.left < 0:
            self.rect.left = 0
            self.direction = 1
            self._apply_direction_image()
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.direction = -1
            self._apply_direction_image()
            
    #que cambie la img a la pocicion que va el pez
    def _apply_direction_image(self):
        prev_center = self.rect.center
        if self.direction < 0 and self.alt_image:
            self.image = self.alt_image
        else:
            self.image = self.base_image
        self.rect = self.image.get_rect(center=prev_center)
