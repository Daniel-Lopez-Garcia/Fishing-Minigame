import math
import os
import array
import pygame


def load_sound(path):
    """Load a sound if it exists, returning None on failure."""
    if not os.path.exists(path):
        return None
    try:
        return pygame.mixer.Sound(path)
    except pygame.error:
        return None


def load_music(path):
    """Load music into pygame's mixer; returns True on success."""
    if not os.path.exists(path):
        return False
    try:
        pygame.mixer.music.load(path)
        return True
    except pygame.error:
        return False


def _generate_tone_sound(frequency=440, duration_ms=250, volume=0.35):
    """Create a simple sine wave Sound as a fallback when assets are missing."""
    init = pygame.mixer.get_init()
    if not init:
        # default mixer settings if not initialized yet
        pygame.mixer.init()
        init = pygame.mixer.get_init()
    sample_rate, fmt, channels = init

    bits = abs(fmt)
    if bits not in (8, 16):
        bits = 16
    amplitude = int((2 ** (bits - 1) - 1) * volume)
    sample_count = int(sample_rate * (duration_ms / 1000.0))

    samples = array.array("h")
    for i in range(sample_count):
        sample_val = int(amplitude * math.sin(2 * math.pi * frequency * i / sample_rate))
        for _ in range(channels):
            samples.append(sample_val)

    return pygame.mixer.Sound(buffer=samples.tobytes())


def load_or_generate_sound(path, fallback_freq=440, duration_ms=250, volume=0.35):
    """Load a sound if available; otherwise return a generated tone."""
    snd = load_sound(path)
    if snd:
        return snd
    return _generate_tone_sound(frequency=fallback_freq, duration_ms=duration_ms, volume=volume)


def load_spritesheet_row(path, columns, rows=None, row_index=0, max_size=None):
    """
    Load a sprite sheet and slice the specified row into frames.
    Returns a list of Surfaces (possibly scaled).
    """
    sheet = load_image(path, convert_alpha=True)
    if not sheet or columns <= 0:
        return []

    sheet_width, sheet_height = sheet.get_size()
    frame_width = sheet_width // columns
    if frame_width <= 0:
        return []

    if rows is None or rows <= 0:
        rows = sheet_height // frame_width if frame_width else 1
        rows = max(rows, 1)
    frame_height = sheet_height // rows
    row_index = max(0, min(row_index, rows - 1))

    frames = []
    for col in range(columns):
        rect = pygame.Rect(col * frame_width, row_index * frame_height, frame_width, frame_height)
        frame = sheet.subsurface(rect).copy()
        if max_size:
            frame = scale_image_to_fit(frame, max_size)
        frames.append(frame)
    return frames


def generate_ambient_loop(frequency=180, duration_ms=800, volume=0.18):
    """Generate a low-volume tone to use as background 'music' if none is available."""
    return _generate_tone_sound(frequency=frequency, duration_ms=duration_ms, volume=volume)


def scale_image_to_fit(surface, max_size):
    """Scale `surface` down to fit inside `max_size` while keeping aspect ratio."""
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
