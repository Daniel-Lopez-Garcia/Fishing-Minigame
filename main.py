import pygame
import random
import os
from pathlib import Path

# ---------------------------
# Config / Constants
# ---------------------------
WIDTH, HEIGHT = 900, 600
FPS = 60

PLAYER_SPEED = 5
LURE_SPEED = 10
RIVER_SCROLL_SPEED = 2

GAME_TIME_SECONDS = 60        # total time per run
MAX_HEALTH = 3

FISH_SPAWN_INTERVAL = 1500    # ms
OBSTACLE_SPAWN_INTERVAL = 2000

BASE_FISH_SPEED = 3
BASE_OBSTACLE_SPEED = 4

BOAT_IMAGE_MAX_SIZE = (140, 80)   # avoid oversized boat sprites
FISH_IMAGE_MAX_SIZE = (90, 50)    # clamp fish sprites to a manageable size

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
RED = (200, 40, 40)
BLUE = (40, 80, 200)
YELLOW = (230, 220, 50)
GRAY = (70, 70, 70)
RIVER_BLUE = (30, 120, 180)

# Game states
STATE_MENU = "MENU"
STATE_PLAYING = "PLAYING"
STATE_PAUSED = "PAUSED"
STATE_GAME_OVER = "GAME_OVER"


# ---------------------------
# Helper for loading sounds
# ---------------------------
def load_sound(path):
    if not os.path.exists(path):
        return None
    try:
        return pygame.mixer.Sound(path)
    except pygame.error:
        return None


def load_music(path):
    if not os.path.exists(path):
        return False
    try:
        pygame.mixer.music.load(path)
        return True
    except pygame.error:
        return False


def scale_image_to_fit(surface, max_size):
    """Scale `surface` down so it fits inside `max_size` while keeping aspect ratio."""
    if not max_size:
        return surface
    max_w, max_h = max_size
    if max_w <= 0 or max_h <= 0:
        return surface

    width, height = surface.get_size()
    if width <= max_w and height <= max_h:
        return surface

    scale = min(max_w / width, max_h / height)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return pygame.transform.smoothscale(surface, new_size)


def load_image(path, max_size=None, convert_alpha=True, colorkey=None):
    """Load an image, optionally scaling and applying a transparent color."""
    if not os.path.exists(path):
        return None
    try:
        image = pygame.image.load(path)
        image = image.convert_alpha() if convert_alpha else image.convert()
        if max_size:
            image = scale_image_to_fit(image, max_size)
        if colorkey is not None:
            image.set_colorkey(colorkey)
        return image
    except pygame.error:
        return None


# ---------------------------
# Sprite Classes
# ---------------------------

class PlayerBoat(pygame.sprite.Sprite):
    def __init__(self, x, y, sprite_image=None):
        super().__init__()
        if sprite_image:
            self.image = sprite_image.copy()
        else:
            # Simple rectangle as placeholder
            self.image = pygame.Surface((60, 30))
            self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = PLAYER_SPEED
        self.health = MAX_HEALTH
        self.direction = "UP"  # for where to cast the lure

    def update(self, keys):
        dx = dy = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed
            self.direction = "LEFT"
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed
            self.direction = "RIGHT"
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.speed
            self.direction = "UP"
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.speed
            self.direction = "DOWN"

        self.rect.x += dx
        self.rect.y += dy

        # Keep inside screen
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    def take_damage(self, amount=1):
        self.health = max(0, self.health - amount)


class Lure(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
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

        # Kill lure if off-screen
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

        # random horizontal direction
        self.speed = BASE_FISH_SPEED + random.uniform(-1, 2)
        self.direction = random.choice([-1, 1])

        # animation
        self.anim_timer = 0
        self.anim_interval = 200  # ms
        self.anim_toggle = False

    def update(self, dt_ms):
        # move horizontally
        self.rect.x += self.direction * self.speed

        # bounce off edges
        if self.rect.left < 0:
            self.rect.left = 0
            self.direction = 1
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.direction = -1

        # fake "swimming" animation by toggling color
        self.anim_timer += dt_ms
        if self.anim_timer >= self.anim_interval:
            self.anim_timer = 0
            self.anim_toggle = not self.anim_toggle
            self.image = self.alt_image if self.anim_toggle else self.base_image


class Obstacle(pygame.sprite.Sprite):
    """
    Simple log/rock moving downward to simulate river current.
    """
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((50, 30))
        self.image.fill(GRAY)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = BASE_OBSTACLE_SPEED + random.uniform(-1, 2)

    def update(self):
        self.rect.y += self.speed

        if self.rect.top > HEIGHT:
            self.kill()


# ---------------------------
# Main Game Class
# ---------------------------

class LuckyLuresGame:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Lucky Lures: River Rush")
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_big = pygame.font.SysFont("arial", 48)
        self.font_med = pygame.font.SysFont("arial", 28)
        self.font_small = pygame.font.SysFont("arial", 20)

        # Sounds & music (replace paths with your real files)
        base_path = Path(__file__).resolve().parent
        self.splash_snd = load_sound(str(base_path / "assets" / "splash.wav"))
        self.hit_snd = load_sound(str(base_path / "assets" / "hit.wav"))
        music_loaded = load_music(str(base_path / "assets" / "river_theme.ogg"))
        if music_loaded:
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(-1)  # loop

        # Images
        self.bg_image = load_image(str(base_path / "bg_2d.png"),
                                   max_size=(WIDTH, HEIGHT),
                                   convert_alpha=False)
        if self.bg_image and self.bg_image.get_size() != (WIDTH, HEIGHT):
            self.bg_image = pygame.transform.smoothscale(self.bg_image, (WIDTH, HEIGHT))

        self.boat_image = load_image(str(base_path / "boat.png"),
                                     max_size=BOAT_IMAGE_MAX_SIZE)

        self.friendly_fish_images = []
        for name in ("gold_fish.jpg", "tuna.png"):
            img = load_image(str(base_path / name),
                             max_size=FISH_IMAGE_MAX_SIZE,
                             convert_alpha=True,
                             colorkey=(255, 255, 255))
            if img:
                self.friendly_fish_images.append(img)

        self.predator_fish_images = []
        predator_img = load_image(str(base_path / "magicarp.jpg"),
                                  max_size=FISH_IMAGE_MAX_SIZE,
                                  convert_alpha=True,
                                  colorkey=(255, 255, 255))
        if predator_img:
            self.predator_fish_images.append(predator_img)

        # Game state vars
        self.state = STATE_MENU
        self.score = 0
        self.time_left = GAME_TIME_SECONDS
        self.game_over_reason = ""

        # Timers
        self.last_fish_spawn = 0
        self.last_obstacle_spawn = 0

        # Background scrolling
        self.bg_offset = 0

        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.fish_group = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.lures = pygame.sprite.Group()

        self.player = None

    # --------- state helpers ----------
    def reset_game(self):
        self.all_sprites.empty()
        self.fish_group.empty()
        self.obstacles.empty()
        self.lures.empty()

        self.player = PlayerBoat(WIDTH // 2, HEIGHT - 100, sprite_image=self.boat_image)
        self.all_sprites.add(self.player)

        self.score = 0
        self.time_left = GAME_TIME_SECONDS
        self.game_over_reason = ""

        current_time = pygame.time.get_ticks()
        self.last_fish_spawn = current_time
        self.last_obstacle_spawn = current_time

    # --------- event handlers ----------
    def handle_menu_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.reset_game()
                    self.state = STATE_PLAYING
        return True

    def handle_playing_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                    self.state = STATE_PAUSED
                if event.key == pygame.K_SPACE:
                    # Cast lure if there isn't one too close to player
                    if len(self.lures) < 3:
                        lure = Lure(self.player.rect.centerx,
                                    self.player.rect.centery,
                                    self.player.direction)
                        self.all_sprites.add(lure)
                        self.lures.add(lure)
                        if self.splash_snd:
                            self.splash_snd.play()
        return True

    def handle_paused_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p, pygame.K_RETURN):
                    self.state = STATE_PLAYING
        return True

    def handle_game_over_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.state = STATE_MENU
        return True

    # --------- update loops ----------
    def update_menu(self, dt_ms):
        # nothing special here
        pass

    def spawn_entities(self):
        now = pygame.time.get_ticks()

        if now - self.last_fish_spawn >= FISH_SPAWN_INTERVAL:
            self.last_fish_spawn = now
            y = random.randint(80, HEIGHT - 250)
            x = random.randint(50, WIDTH - 50)
            is_predator = random.random() < 0.3
            fish = Fish(x, y, is_predator,
                        friendly_images=self.friendly_fish_images,
                        predator_images=self.predator_fish_images)
            self.all_sprites.add(fish)
            self.fish_group.add(fish)

        if now - self.last_obstacle_spawn >= OBSTACLE_SPAWN_INTERVAL:
            self.last_obstacle_spawn = now
            x = random.randint(40, WIDTH - 40)
            obstacle = Obstacle(x, -20)
            self.all_sprites.add(obstacle)
            self.obstacles.add(obstacle)

    def update_playing(self, dt_ms):
        # time
        self.time_left -= dt_ms / 1000.0
        if self.time_left <= 0:
            self.time_left = 0
            self.game_over_reason = "Time's up!"
            self.state = STATE_GAME_OVER
            return

        # difficulty ramp (basic): shorten spawn intervals over time
        global FISH_SPAWN_INTERVAL, OBSTACLE_SPAWN_INTERVAL
        FISH_SPAWN_INTERVAL = max(600, 1500 - int((GAME_TIME_SECONDS - self.time_left) * 10))
        OBSTACLE_SPAWN_INTERVAL = max(700, 2000 - int((GAME_TIME_SECONDS - self.time_left) * 10))

        keys = pygame.key.get_pressed()
        self.spawn_entities()

        # Update sprites
        self.player.update(keys)
        for fish in self.fish_group:
            fish.update(dt_ms)
        for obs in self.obstacles:
            obs.update()
        for lure in self.lures:
            lure.update()

        # Background stays static now, so don't change bg_offset

        # Collisions: lure hit fish
        hits = pygame.sprite.groupcollide(self.fish_group, self.lures, True, True)
        for fish in hits:
            # Score more for predators
            gained = 50 if fish.is_predator else 20
            self.score += gained
            # spawn a replacement fish
            x = random.randint(50, WIDTH - 50)
            y = random.randint(80, HEIGHT - 250)
            new_fish = Fish(x, y, random.random() < 0.3,
                            friendly_images=self.friendly_fish_images,
                            predator_images=self.predator_fish_images)
            self.all_sprites.add(new_fish)
            self.fish_group.add(new_fish)

        # Collisions: player with obstacles
        player_obstacle_hits = pygame.sprite.spritecollide(self.player, self.obstacles, True)
        if player_obstacle_hits:
            self.player.take_damage(1)
            if self.hit_snd:
                self.hit_snd.play()

        # Collisions: player with predator fish
        preds = [f for f in self.fish_group if f.is_predator]
        for fish in preds:
            if self.player.rect.colliderect(fish.rect):
                self.player.take_damage(1)
                # push player slightly back for feedback
                self.player.rect.y += 15
                if self.hit_snd:
                    self.hit_snd.play()

        # Check health
        if self.player.health <= 0:
            self.game_over_reason = "Your boat was wrecked!"
            self.state = STATE_GAME_OVER

    def update_paused(self, dt_ms):
        # no updates to game logic
        pass

    def update_game_over(self, dt_ms):
        pass

    # --------- drawing ----------
    def draw_river_background(self):
        if self.bg_image:
            bg_height = self.bg_image.get_height()
            y_offset = int(self.bg_offset) % bg_height
            start_y = y_offset - bg_height
            while start_y < HEIGHT:
                self.screen.blit(self.bg_image, (0, start_y))
                start_y += bg_height
        else:
            # simple solid color + scrolling bands as "waves"
            self.screen.fill(RIVER_BLUE)

            # draw horizontal wave bands
            band_height = 40
            for i in range(0, HEIGHT // band_height + 2):
                y = (i * band_height + int(self.bg_offset * 0.5)) % HEIGHT
                pygame.draw.rect(self.screen, (20, 100, 160),
                                 (0, y, WIDTH, band_height // 2))

    def draw_hud(self):
        # Score
        text_score = self.font_small.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(text_score, (10, 10))

        # Time
        text_time = self.font_small.render(f"Time: {int(self.time_left)}s", True, WHITE)
        self.screen.blit(text_time, (10, 35))

        # Health
        for i in range(self.player.health):
            pygame.draw.rect(self.screen, RED, (WIDTH - 25 - i * 20, 10, 15, 15))

    def draw_menu(self):
        self.draw_river_background()

        title = self.font_big.render("Lucky Lures: River Rush", True, WHITE)
        msg = self.font_med.render("Press ENTER to Start", True, WHITE)
        tip = self.font_small.render("Move with WASD/Arrows, SPACE to cast, P to pause.", True, WHITE)

        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
        self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2))
        self.screen.blit(tip, (WIDTH // 2 - tip.get_width() // 2, HEIGHT // 2 + 40))

    def draw_playing(self):
        self.draw_river_background()
        self.all_sprites.draw(self.screen)
        self.draw_hud()

    def draw_paused(self):
        self.draw_playing()
        # overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        text = self.font_big.render("PAUSED", True, WHITE)
        msg = self.font_med.render("Press P or ENTER to Resume", True, WHITE)
        self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 40))
        self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 + 10))

    def draw_game_over(self):
        self.draw_river_background()

        title = self.font_big.render("Game Over", True, WHITE)
        reason = self.font_med.render(self.game_over_reason, True, WHITE)
        score_text = self.font_med.render(f"Final Score: {self.score}", True, WHITE)
        msg = self.font_small.render("Press ENTER to return to Menu", True, WHITE)

        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
        self.screen.blit(reason, (WIDTH // 2 - reason.get_width() // 2, HEIGHT // 3 + 60))
        self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 3 + 110))
        self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 3 + 160))

    # --------- main loop ----------
    def run(self):
        running = True
        while running:
            dt_ms = self.clock.tick(FPS)

            events = pygame.event.get()

            if self.state == STATE_MENU:
                running = self.handle_menu_events(events)
                self.update_menu(dt_ms)
                self.draw_menu()

            elif self.state == STATE_PLAYING:
                running = self.handle_playing_events(events)
                if not running:
                    break
                self.update_playing(dt_ms)
                self.draw_playing()

            elif self.state == STATE_PAUSED:
                running = self.handle_paused_events(events)
                self.update_paused(dt_ms)
                self.draw_paused()

            elif self.state == STATE_GAME_OVER:
                running = self.handle_game_over_events(events)
                self.update_game_over(dt_ms)
                self.draw_game_over()

            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    game = LuckyLuresGame()
    game.run()
