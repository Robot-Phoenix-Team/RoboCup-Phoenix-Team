import pygame

speed = 800
rotation_speed = 6

def get_velocity(keys):
    vx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * speed
    vy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * speed
    return vx, vy

def get_rotation(keys):
    return keys[pygame.K_SPACE] * rotation_speed