import pygame
import random

from constants import (
    BASE_OBSTACLE_SPEED,
    HEIGHT,
    WIDTH,
    GRAY,
)


class Obstacle(pygame.sprite.Sprite):
    
    def __init__(self, x, y, frames=None, velocity=(0, 0)):
        super().__init__()
        #imagen velocidad y poss
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
        self.anim_interval = 120  # milisegs
        #movimeinto
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
        
        #removes obs when off screen
        if self.rect.top > HEIGHT + 100 or self.rect.bottom < -100 or self.rect.right < -100 or self.rect.left > WIDTH + 100:
            self.kill()
