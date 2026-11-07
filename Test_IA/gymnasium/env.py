import gymnasium as gym
import pygame

MODEL_PATH = "Test_IA/gymnasium/test"

class Terrain(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 4}

    def __init__(self, long=50, larg=10):
        self.long = long
        self.larg = larg
        self.window_size = 512

    def _draw(self):
        import pygame
        surface = pygame.display.set_mode((self.long, self.larg))
        surface.fill((255, 255, 255))

test = Terrain()

test._draw()