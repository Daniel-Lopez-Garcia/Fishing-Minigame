import math
import random
from pathlib import Path
import pygame
from assets import (load_image, load_music, load_sound,)
from constants import ( 
    BOAT_IMAGE_MAX_SIZE,
    BASE_OBSTACLE_SPEED,
    FISH_IMAGE_MAX_SIZE,
    FISH_SPAWN_INTERVAL,
    FPS,
    GAME_TIME_SECONDS,
    HEIGHT,
    OBSTACLE_SPAWN_INTERVAL,
    RIVER_BLUE,
    STATE_GAME_OVER,
    STATE_MENU,
    STATE_PAUSED,
    STATE_PLAYING,
    WIDTH,
    WHITE,
    RED,
    IDLE_SHARK_DELAY_MS,
    IDLE_SHARK_SPEED,
)
from boats import PlayerBoat
from fish import Fish
from lure import Lure
from obstacle import Obstacle


def _load_first_image(base_path, candidates, **kwargs):
    #intenta una lista en orden de imagenes

    for name in candidates:
        img = load_image(str(base_path / name), **kwargs)

        if img:
            return img
    return None


def _load_sequence(base_path, names, **kwargs):
    #para cargarlos frames
    frames = []
    for name in names:

        img = load_image(str(base_path / name), **kwargs)
        if img:
            frames.append(img)
    return frames


def _rotate_frames(frames, angle):
    #rota los frames para cuando sale por otros angulos
    if not frames:
        return []
    
    return [pygame.transform.rotate(f, angle) for f in frames]


class LuckyLuresGame:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

        pygame.display.set_caption("Lucky Lures: River Rush") #hay que cambiarlo me thinks

        self.clock = pygame.time.Clock()

        #font sizes
        self.font_big = pygame.font.SysFont("arial", 48)
        self.font_med = pygame.font.SysFont("arial", 28)
        self.font_small = pygame.font.SysFont("arial", 20)

        base_path = Path(__file__).resolve().parent #consigue la carpeta parent para cargar asssets
        assets_dir = base_path / "assets"

        self.splash_snd = load_sound(str(assets_dir / "splash.wav"))
        self.hit_snd = load_sound(str(assets_dir / "hit.wav"))

        #sound for game over
        self.game_over_snd = None
        for candidate in (
            "game-over-deep-male-voice-clip-352695.mp3",
            
        ):
            self.game_over_snd = load_sound(str(assets_dir / candidate))
            if self.game_over_snd:
                break

        music_loaded = False #por defalut, se cambia a true si no hay error al cargarla

        mp3_candidate = next((p for p in assets_dir.glob("*.mp3")), None)

        if mp3_candidate:
            music_loaded = load_music(str(mp3_candidate))
        if not music_loaded:
            music_loaded = load_music(str(assets_dir / "river_theme.ogg"))
        if music_loaded:
            pygame.mixer.music.set_volume(0.45)
            pygame.mixer.music.play(-1)
        self.music_loaded = music_loaded

        
        self.bg_image = _load_first_image(
            base_path,
            (
                "bg_2d.png",
                "bg_2d.jpg",
                "bg_2d.gif",
                "background.png",
                "background.jpg",
                "background.gif",
                "assets/bg_2d.png",
                "assets/bg_2d.jpg",
                "assets/bg_2d.gif",
                "assets/background.png",
                "assets/background.jpg",
                "assets/background.gif",
            ),
            max_size=(WIDTH, HEIGHT),
            convert_alpha=False,
        )
        if self.bg_image and self.bg_image.get_size() != (WIDTH, HEIGHT):
            self.bg_image = pygame.transform.smoothscale(self.bg_image, (WIDTH, HEIGHT)) #escalea/redimensiona

        self.boat_image = _load_first_image(
            base_path,
            (
                "boat.png",
                "boat.jpg",
                "boat.gif",
                "assets/boat.png",
                "assets/boat.jpg",
                "assets/boat.gif",
            ),
            max_size=BOAT_IMAGE_MAX_SIZE,
        )


        self.lure_image = _load_first_image(
            base_path,
            (
                "bait.png",
                "assets/bait.png",
            ),
            max_size=(18, 18),
            convert_alpha=True,
        )

        self.sunken_image = _load_first_image(
            base_path,
            (
                "sunken.png",
                "assets/sunken.png",
            ),
            max_size=BOAT_IMAGE_MAX_SIZE,
            convert_alpha=True,
        )

        obstacle_frame_names = {
            "shark1.png", "shark2.png", "shark3.png", "shark4.png",
        }
        predator_frame_names = {"s1.png", "s2.png", "s3.png"}

        self.friendly_fish_images = []
        default_friendly_sets = (
            ("gold_fish.png", "gold_fish.jpg", "gold_fish.gif",
             "assets/gold_fish.png", "assets/gold_fish.jpg", "assets/gold_fish.gif"),
            ("tuna.png", "tuna.jpg", "tuna.gif",
             "assets/tuna.png", "assets/tuna.jpg", "assets/tuna.gif"),
        )
        for name in default_friendly_sets:
            img = _load_first_image(
                base_path,
                name,
                max_size=FISH_IMAGE_MAX_SIZE,
                convert_alpha=True,
                colorkey=(255, 255, 255),
            )
            if img:
                self.friendly_fish_images.append(img)

        #escoge automaticamente fotos de peces excepto:
        skip_names = {
            "boat.png", "boat.jpg", "boat.gif",
            "bg_2d.png", "bg_2d.jpg", "bg_2d.gif",
            "background.png", "background.jpg", "background.gif",
            "magicarp.png", "magicarp.jpg", "magicarp.gif",
            "predator.png", "predator.jpg", "predator.gif",
            "bait.png",
            "sunken.png", "sunken.jpg", "sunken.gif",
        }

        skip_names |= obstacle_frame_names | predator_frame_names
        for ext in ("*.png", "*.jpg", "*.gif"):
                #cargamos imagenes
            for path in assets_dir.glob(ext):

                if path.name.lower() in skip_names:
                    continue
                img = load_image(
                    str(path),
                    max_size=FISH_IMAGE_MAX_SIZE,
                    convert_alpha=True,
                    colorkey=(255, 255, 255),
                )

                if img:
                    self.friendly_fish_images.append(img)

        self.predator_fish_images = []
        predator_img = _load_first_image(
            base_path,
            (
                "magicarp.png",
                "magicarp.jpg",
                "magicarp.gif",
                "predator.png",
                "predator.jpg",
                "predator.gif",
                "assets/magicarp.png",
                "assets/magicarp.jpg",
                "assets/magicarp.gif",
                "assets/predator.png",
                "assets/predator.jpg",
                "assets/predator.gif",
            ),
            max_size=FISH_IMAGE_MAX_SIZE,
            convert_alpha=True,
            colorkey=(255, 255, 255),

        )


        if predator_img:
            self.predator_fish_images.append(predator_img)

        predator_frames = _load_sequence(
            assets_dir,
            ["s1.png", "s2.png", "s3.png"],

            max_size=FISH_IMAGE_MAX_SIZE,
            convert_alpha=True,
            colorkey=(255, 255, 255),
        )
        self.predator_fish_images.extend(predator_frames)


        #puse esto por si las moscas, si añadimos luego mas predators
        predator_keywords = ("predator", "shark", "piranha", "angry", "evil")
        for ext in ("*.png", "*.jpg", "*.gif"):

            for path in assets_dir.glob(ext):
                name_lower = path.name.lower()

                if name_lower in obstacle_frame_names:
                    continue

                if any(k in name_lower for k in predator_keywords):
                    img = load_image(
                        str(path),
                        max_size=FISH_IMAGE_MAX_SIZE,
                        convert_alpha=True,
                        colorkey=(255, 255, 255),
                    )
                    if img:
                        self.predator_fish_images.append(img)

        #por si no hay fotos de depredadores
        if not self.predator_fish_images and self.friendly_fish_images:
            #usa fotos existentes

            for img in self.friendly_fish_images:
                tinted = img.copy()

                overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)

                overlay.fill((220, 60, 60, 255))

                tinted.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                self.predator_fish_images.append(tinted)

        #no tocar #lo toque jijija
        #ayuda a la secuencia de images de depredadores
        self.obstacle_frames = _load_sequence(

            assets_dir,
            ["shark1.png", "shark2.png", "shark3.png", "shark4.png"],
            max_size=(100, 70),
            convert_alpha=True,
            colorkey=(255, 255, 255),
        )


        #base
        self.state = STATE_MENU
        self.score = 0
        self.score_p2 = 0
        self.game_over_reason = ""

        self.last_fish_spawn = 0
        self.last_obstacle_spawn = 0

        self.fish_spawn_interval = FISH_SPAWN_INTERVAL
        self.obstacle_spawn_interval = OBSTACLE_SPAWN_INTERVAL

        self.bg_offset = 0

        self.all_sprites = pygame.sprite.Group()
        self.fish_group = pygame.sprite.Group()

        self.obstacles = pygame.sprite.Group()
        self.lures = pygame.sprite.Group()

        self.player = None
        self.player2 = None
        self.last_player_move_time = pygame.time.get_ticks()
        self.idle_threat_triggered = False

        self.time_left = GAME_TIME_SECONDS

    #controlers p1 y p2
        self.controls_p1 = {
            "up": pygame.K_w,
            "down": pygame.K_s,
            "left": pygame.K_a,
            "right": pygame.K_d,
        }


        self.controls_p2 = {
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
        }

    def reset_game(self):


        self.all_sprites.empty()
        self.fish_group.empty()
        self.obstacles.empty()
        self.lures.empty()

        self.player = PlayerBoat(WIDTH // 2 - 100, HEIGHT - 100, sprite_image=self.boat_image, sunken_image=self.sunken_image, name="P1")
        self.player2 = PlayerBoat(WIDTH // 2 + 100, HEIGHT - 100, sprite_image=self.boat_image, sunken_image=self.sunken_image, name="P2")
        self.all_sprites.add(self.player, self.player2)

        self.score = 0
        self.score_p2 = 0

        self.time_left = GAME_TIME_SECONDS
        self.game_over_reason = ""

        current_time = pygame.time.get_ticks()

        self.last_fish_spawn = current_time
        self.last_obstacle_spawn = current_time
        self.fish_spawn_interval = FISH_SPAWN_INTERVAL
        self.obstacle_spawn_interval = OBSTACLE_SPAWN_INTERVAL
        self.last_player_move_time = current_time

        self.idle_threat_triggered = False

        if self.music_loaded and not pygame.mixer.music.get_busy():
            pygame.mixer.music.set_volume(0.45)
            pygame.mixer.music.play(-1)

    def trigger_game_over(self, reason):
        if self.state == STATE_GAME_OVER:
            return

        self.game_over_reason = reason
        self.state = STATE_GAME_OVER

        pygame.mixer.music.stop()
        if self.game_over_snd:
            self.game_over_snd.play()

    def handle_menu_events(self, events):

        for event in events:
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.reset_game()
                self.state = STATE_PLAYING
        return True
    
    #procesando inputs
    def handle_playing_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:

                #pause keysS
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                    self.state = STATE_PAUSED

                    #reeling keys
                if event.key == pygame.K_SPACE and self.player and self.player.health > 0:
                    if sum(1 for l in self.lures if l.owner == "P1") < 3:


                        lure = Lure(self.player.rect.centerx,
                                    self.player.rect.centery,
                                    self.player.direction,
                                    sprite_image=self.lure_image,
                                    owner="P1")
                        
                        self.all_sprites.add(lure)
                        self.lures.add(lure)

                        if self.splash_snd:
                            self.splash_snd.play()

                if event.key in (pygame.K_RSHIFT, pygame.K_RETURN) and self.player2 and self.player2.health > 0:
                    if sum(1 for l in self.lures if l.owner == "P2") < 3:

                        lure = Lure(self.player2.rect.centerx,
                                    self.player2.rect.centery,
                                    self.player2.direction,
                                    sprite_image=self.lure_image,
                                    owner="P2")
                        
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
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.state = STATE_MENU
        return True

    def update_menu(self, dt_ms):
        pass


    def spawn_entities(self):
        now = pygame.time.get_ticks()

        if now - self.last_fish_spawn >= self.fish_spawn_interval:
            self.last_fish_spawn = now
            y = random.randint(80, HEIGHT - 250)
            x = random.randint(50, WIDTH - 50)

            is_predator = random.random() < 0.3

            fish = Fish(x, y, is_predator,
                        friendly_images=self.friendly_fish_images,
                        predator_images=self.predator_fish_images)
            
            self.all_sprites.add(fish)
            self.fish_group.add(fish)

        if now - self.last_obstacle_spawn >= self.obstacle_spawn_interval:
            self.last_obstacle_spawn = now
            #desoues de 30 segundos, tiburones vienen de cualquier lado


            if self.time_left <= GAME_TIME_SECONDS / 2 and self.obstacle_frames:

                direction = random.choice(["UP", "DOWN", "LEFT", "RIGHT"])
                if direction == "DOWN":
                    x = random.randint(40, WIDTH - 40)
                    frames = _rotate_frames(self.obstacle_frames, 0)
                    obstacle = Obstacle(x, -20, frames=frames, velocity=(0, BASE_OBSTACLE_SPEED + random.uniform(-1, 2)))
                
                elif direction == "UP":
                    x = random.randint(40, WIDTH - 40)
                    frames = _rotate_frames(self.obstacle_frames, 180)
                    obstacle = Obstacle(x, HEIGHT + 20, frames=frames, velocity=(0, -(BASE_OBSTACLE_SPEED + random.uniform(-1, 2))))
                
                elif direction == "LEFT":
                    y = random.randint(40, HEIGHT - 40)
                    frames = _rotate_frames(self.obstacle_frames, -90)
                    obstacle = Obstacle(WIDTH + 20, y, frames=frames, velocity=(-(BASE_OBSTACLE_SPEED + random.uniform(-1, 2)), 0))
                
                else:  # RIGHT
                    y = random.randint(40, HEIGHT - 40)
                    frames = _rotate_frames(self.obstacle_frames, 90)
                    obstacle = Obstacle(-20, y, frames=frames, velocity=((BASE_OBSTACLE_SPEED + random.uniform(-1, 2)), 0))
            else:

                x = random.randint(40, WIDTH - 40)
                obstacle = Obstacle(x, -20, frames=self.obstacle_frames)


            self.all_sprites.add(obstacle)
            self.obstacles.add(obstacle)

    #funcion que previene que el jugador se quede quieto
    def spawn_idle_predator(self):
        alive_players = [p for p in (self.player, self.player2) if p and p.health > 0]
        if not alive_players:
            return

        target = random.choice(alive_players)
        player_pos = pygame.math.Vector2(target.rect.center)

        #de donde vendra el ataque
        side = random.choice(("TOP", "BOTTOM", "LEFT", "RIGHT"))

        if side == "TOP":
            spawn_pos = pygame.math.Vector2(random.randint(40, WIDTH - 40), -60)
        elif side == "BOTTOM":
            spawn_pos = pygame.math.Vector2(random.randint(40, WIDTH - 40), HEIGHT + 60)
        elif side == "LEFT":
            spawn_pos = pygame.math.Vector2(-60, random.randint(40, HEIGHT - 40))
        else:  #derecha
            spawn_pos = pygame.math.Vector2(WIDTH + 60, random.randint(40, HEIGHT - 40))

        direction = player_pos - spawn_pos

        if direction.length() == 0:
            direction = pygame.math.Vector2(0, 1)

        velocity = direction.normalize() * IDLE_SHARK_SPEED #veloz
        angle = math.degrees(math.atan2(velocity.x, velocity.y))
        frames = _rotate_frames(self.obstacle_frames, angle)

        obstacle = Obstacle(int(spawn_pos.x), int(spawn_pos.y),
                            frames=frames, velocity=(velocity.x, velocity.y))
        
        self.all_sprites.add(obstacle)
        self.obstacles.add(obstacle)

    def update_playing(self, dt_ms):

        self.time_left -= dt_ms / 1000.0
        
        if self.time_left <= 0:
            self.time_left = 0
            self.trigger_game_over("Time's up!")
            return

        elapsed = GAME_TIME_SECONDS - self.time_left
        self.fish_spawn_interval = max(600, 1500 - int(elapsed * 10))
        self.obstacle_spawn_interval = max(700, 2000 - int(elapsed * 10))

        keys = pygame.key.get_pressed()
        self.spawn_entities()

        moved = False


        if self.player and self.player.health > 0:
            prev_center = self.player.rect.center
            self.player.update(keys, self.controls_p1)
            moved = moved or (self.player.rect.center != prev_center)

        if self.player2 and self.player2.health > 0:
            prev_center2 = self.player2.rect.center
            self.player2.update(keys, self.controls_p2)
            moved = moved or (self.player2.rect.center != prev_center2)

        if moved:
            self.last_player_move_time = pygame.time.get_ticks()
            self.idle_threat_triggered = False

        now_ticks = pygame.time.get_ticks()
        if (not self.idle_threat_triggered and
                now_ticks - self.last_player_move_time >= IDLE_SHARK_DELAY_MS):
            self.spawn_idle_predator()
            self.idle_threat_triggered = True

        for fish in self.fish_group:
            fish.update(dt_ms)
        for obs in self.obstacles:
            obs.update(dt_ms)
        for lure in self.lures:
            lure.update()

        hits = pygame.sprite.groupcollide(self.fish_group, self.lures, True, True)

        for fish, lures_hit in hits.items():
            gained = 50 if fish.is_predator else 20
            owner = lures_hit[0].owner if lures_hit else "P1"

            if owner == "P2":
                self.score_p2 += gained
            else:
                self.score += gained

            x = random.randint(50, WIDTH - 50)
            y = random.randint(80, HEIGHT - 250)

            new_fish = Fish(x, y, random.random() < 0.3,
                            friendly_images=self.friendly_fish_images,
                            predator_images=self.predator_fish_images)
            self.all_sprites.add(new_fish)
            self.fish_group.add(new_fish)

        player_obstacle_hits = pygame.sprite.spritecollide(self.player, self.obstacles, True) if self.player else []
        player2_obstacle_hits = pygame.sprite.spritecollide(self.player2, self.obstacles, True) if self.player2 else []


        if player_obstacle_hits and self.player:
            self.player.take_damage(1)
            if self.hit_snd:
                self.hit_snd.play()

        if player2_obstacle_hits and self.player2:
            self.player2.take_damage(1)
            if self.hit_snd:
                self.hit_snd.play()

        preds = [f for f in self.fish_group if f.is_predator]

        for fish in preds:

            if self.player and self.player.rect.colliderect(fish.rect):
                self.player.take_damage(1)
                self.player.rect.y += 15
                if self.hit_snd:
                    self.hit_snd.play()

            if self.player2 and self.player2.rect.colliderect(fish.rect):
                self.player2.take_damage(1)
                self.player2.rect.y += 15
                if self.hit_snd:
                    self.hit_snd.play()

        if (self.player and self.player.health <= 0) and (self.player2 and self.player2.health <= 0):
            self.trigger_game_over("Both boats were wrecked!")

    def update_paused(self, dt_ms):
        pass

    def update_game_over(self, dt_ms):
        pass

    def draw_river_background(self):

        if self.bg_image:
            bg_height = self.bg_image.get_height()
            y_offset = int(self.bg_offset) % bg_height
            start_y = y_offset - bg_height

            while start_y < HEIGHT:
                self.screen.blit(self.bg_image, (0, start_y))
                start_y += bg_height

        else:
            self.screen.fill(RIVER_BLUE)
            band_height = 40

            for i in range(0, HEIGHT // band_height + 2):
                y = (i * band_height + int(self.bg_offset * 0.5)) % HEIGHT

                pygame.draw.rect(self.screen, (20, 100, 160),
                                 (0, y, WIDTH, band_height // 2))

    def draw_hud(self):
        
        text_score1 = self.font_small.render(f"P1 Score: {self.score}", True, WHITE)
        self.screen.blit(text_score1, (10, 10))

        text_score2 = self.font_small.render(f"P2 Score: {self.score_p2}", True, WHITE)
        self.screen.blit(text_score2, (WIDTH - text_score2.get_width() - 10, 10))

        text_time = self.font_small.render(f"Time: {int(self.time_left)}s", True, WHITE)
        self.screen.blit(text_time, (WIDTH // 2 - text_time.get_width() // 2, 10))

        #players hp
        if self.player:
            for i in range(self.player.health):
                pygame.draw.rect(self.screen, RED, (10 + i * 18, 35, 15, 15))
        if self.player2:
            for i in range(self.player2.health):
                pygame.draw.rect(self.screen, RED, (WIDTH - 25 - i * 18, 35, 15, 15))

    def draw_menu(self):

        self.draw_river_background()

        #enter screen
        title = self.font_big.render("Lucky Lures: River Rush", True, WHITE)
        msg = self.font_med.render("Press ENTER to Start", True, WHITE)
        tip = self.font_small.render("Move with WASD/Arrows, SPACE to cast, P to pause.", True, WHITE)

        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
        self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2))
        self.screen.blit(tip, (WIDTH // 2 - tip.get_width() // 2, HEIGHT // 2 + 40))

    def draw_playing(self):

        self.draw_river_background()
        #dibujar el fishingl ine
       
        for lure in self.lures:
            if lure.owner == "P2" and self.player2:
                start_pos = self.player2.rect.center
            else:
                if not self.player:
                    continue
                start_pos = self.player.rect.center
            pygame.draw.line(self.screen, WHITE, start_pos, lure.rect.center, 2)

        self.all_sprites.draw(self.screen)
        self.draw_hud()



    def draw_paused(self):

        self.draw_playing()
        #pause screen


        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        text = self.font_big.render("PAUSED", True, WHITE)
        msg = self.font_med.render("Press P or ENTER to Resume", True, WHITE)

        self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 40))
        self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 + 10))




    def draw_game_over(self):
        self.draw_river_background()

    #game over screen
        title = self.font_big.render("Game Over", True, WHITE)
        reason = self.font_med.render(self.game_over_reason, True, WHITE)
        score_text = self.font_med.render(f"P1 Score: {self.score}", True, WHITE)
        score_text_p2 = self.font_med.render(f"P2 Score: {self.score_p2}", True, WHITE)


        if self.score > self.score_p2:
            winner_text = f"P1 Wins!"
        elif self.score_p2 > self.score:
            winner_text = f"P2 Wins!"
        else:
            winner_text = "Tie Game!"

        winner_render = self.font_med.render(winner_text, True, WHITE)
        msg = self.font_small.render("Press ENTER to return to Menu", True, WHITE)

        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
        self.screen.blit(reason, (WIDTH // 2 - reason.get_width() // 2, HEIGHT // 3 + 60))


        self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 3 + 110))
        self.screen.blit(score_text_p2, (WIDTH // 2 - score_text_p2.get_width() // 2, HEIGHT // 3 + 150))
        
        self.screen.blit(winner_render, (WIDTH // 2 - winner_render.get_width() // 2, HEIGHT // 3 + 190))
        self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 3 + 230))

    def run(self):

        running = True
        #main loop
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
