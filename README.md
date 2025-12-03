# Fishing-Minigame
This is a proyect for CCOM4440

This is a 2D arcade-style fishing game where the player controls a fisherman in a small boat, moving around freely and casting the fishing line in any direction. The player must catch different types of fish to earn points while carefully avoiding dangerous sharks that roam the waters.

The main objective is to achieve the highest possible score before the timer runs out or the boat takes too much damage. Friendly fish reward the player with points when caught, while predator fish (sharks) and falling obstacles can damage the boat on contact. As time passes, the game gradually becomes more challenging: fish and obstacles spawn more frequently, and sharks pose an increasing threat, forcing the player to balance risk and reward with every cast.

- Daniel Lopez & Kevin Santiago
- Made with Pygame
- Music: Banjo-Kazooie (placeholder)
- Sounds: https://pixabay.com/sound-effects/search/game-over/
- Sprites:
    - Stingray: https://opengameart.org/content/stingray-sprite-animated-4-directional
    - Fish: https://agdawkwardgamedev.itch.io/free-fish-assets
    - Shark: https://opengameart.org/content/shark-sprites-animated-4-directional
    - Bait: https://www.vecteezy.com/vector-art/56636730-pixel-art-illustration-fishing-bob-pixelated-fishing-bobber-float-fishing-bob-bobber-icon-pixelated-for-the-pixel-art-game-and-icon-for-website-and-game-old-school-retro

## How to Run
1. Install Python 3.10+ and pip.
2. Install dependencies: `pip install pygame`
3. From the repo root, start the game: `python main.py`

## Controls
- Move: WASD or Arrow Keys
- Cast lure: Space (max 3 at a time)
- Pause/Resume: P or Esc
- Menu/Confirm: Enter

## Gameplay Notes
- Timer counts down from 60s; game ends at 0 or if the boat loses all health.
- Friendly fish give +20 points; predators give +50 but bite on contact.
- Falling/side sharks damage the boat; staying still for 2.5s attracts a chasing shark.
- Spawn rates and danger increase as time passes.

## Known Issues
- Window is fixed to 900x600; resizing is not supported.
- Audio depends on available codecs; if music fails to load, effects still play.


