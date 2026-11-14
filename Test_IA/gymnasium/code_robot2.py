import pygame
import __main__

speed = 800
rotation_speed = 6


def get_velocity(keys):
    return (
        keys[pygame.K_RIGHT] - keys[pygame.K_LEFT],
        keys[pygame.K_DOWN] - keys[pygame.K_UP],
    )


def get_rotation(keys):
    return rotation_speed if keys[pygame.K_SPACE] else 0


def get_position():
    return __main__.sim.robot2.copy()
