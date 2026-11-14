# code_robot.py
import pygame
import __main__

speed = 800
rotation_speed = 6

def get_velocity(keys):
    balle = __main__.sim.ball
    robot = __main__.sim.robot
    delta = balle - robot
    if delta.length() < 30:
        return 0, 0
    delta.scale_to_length(speed)
    return delta.x, delta.y

def get_rotation(keys):
    return keys[pygame.K_SPACE] * rotation_speed