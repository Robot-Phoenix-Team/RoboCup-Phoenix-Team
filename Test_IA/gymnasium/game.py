import pygame



running = True
k = 4 #factor for more visual

pygame.init()
surface = pygame.display.set_mode((243*k, 182*k))
surface.fill((0, 128, 0))
long = pygame.display.get_window_size()[0]
larg = pygame.display.get_window_size()[1]


pygame.draw.rect(surface, (0, 0, 0), ((0, ((larg/2)-30*k)), (10*k, 60*k)))
pygame.draw.rect(surface, (0, 0, 255), ((3.6*k, ((larg/2)-30*k)), (7.4*k, 60*k)))

pygame.draw.rect(surface, (0, 0, 0), ((long-10*k, ((larg/2)-30*k)), (10*k, 60*k)))
pygame.draw.rect(surface, (255, 255, 0), ((long-10*k, ((larg/2)-30*k)), (7.4*k, 60*k)))

while running:
    for event in pygame.event.get():    
        if event.type == pygame.QUIT:
            running = False
    pygame.display.update()
  #  print(pygame.display.get_window_size())
