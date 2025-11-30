import os
import pygame


def load_sound(path):
    #carga audio solo si existe, sino devuelve none
    if not os.path.exists(path):
        return None
    try:
        return pygame.mixer.Sound(path)
    except pygame.error:
        return None


def load_music(path):
    #carga musica, devuelve falso si hay eror
    if not os.path.exists(path):
        return False
    try:
        pygame.mixer.music.load(path)
        return True
    except pygame.error:
        return False

def scale_image_to_fit(surface, max_size):
    #escala suave manteniendo proporcion
    
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
    #abre imagen y la escala/aplica colorkey si se pide

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
