import pygame

speed = 200

def get_velocity(keys):
    vx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * speed
    vy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * speed
    return vx, vy
