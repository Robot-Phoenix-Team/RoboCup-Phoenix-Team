import pygame
import math

k = 3 #factor for more visual
class Sim:

    def __init__(self, wide, longe):
        
        pygame.init()
        #self.k = k
        
        self.surface = pygame.display.set_mode((wide*k, longe*k))
        
        self.long = pygame.display.get_window_size()[0]
        self.larg = pygame.display.get_window_size()[1]
        self.ball = pygame.Vector2(self.long/2, self.larg/2)
    
    def draw(self):

        self.surface.fill((0, 0, 0))
        pygame.draw.rect(self.surface, (0, 128, 0), ((0, 0), (self.long, self.larg)))

        pygame.draw.rect(self.surface, (255, 255, 255), ((self.long/2-109.5*k, self.larg/2-79*k), (219*k, 158*k)))
        pygame.draw.rect(self.surface, (0, 128, 0), ((self.long/2-107.5*k, self.larg/2-77*k), (215*k, 154*k)))


        pygame.draw.line(self.surface, (255, 255, 255), (self.long-12*k-2*k, self.larg/2-40*k), (self.long-27*k, self.larg/2-40*k), width=2*k)
        pygame.draw.line(self.surface, (255, 255, 255), (self.long-12*k-2*k, self.larg/2+40*k), (self.long-27*k, self.larg/2+40*k), width=2*k)
        pygame.draw.line(self.surface, (255, 255, 255), (self.long-39*k+1*k, self.larg/2-30*k), (self.long-39*k+1*k, self.larg/2+30*k), width=2*k)
        pygame.draw.arc(self.surface, (255, 255, 255), (self.long-39*k, self.larg/2-41*k, 25*k, 25*k), math.pi/2, math.pi, 2*k)
        pygame.draw.arc(self.surface, (255, 255, 255), (self.long-39*k, self.larg/2+16*k, 25*k, 25*k), math.pi, 3*math.pi/2, 2*k)

        pygame.draw.line(self.surface, (255, 255, 255), (12*k+2*k, self.larg/2-40*k), (27*k, self.larg/2-40*k), width=2*k)
        pygame.draw.line(self.surface, (255, 255, 255), (12*k+2*k, self.larg/2+40*k), (27*k, self.larg/2+40*k), width=2*k)
        pygame.draw.line(self.surface, (255, 255, 255), (39*k-1*k, self.larg/2-30*k), (39*k-1*k, self.larg/2+30*k), width=2*k)
        pygame.draw.arc(self.surface, (255, 255, 255), (14*k, self.larg/2-41*k, 25*k, 25*k), 0, math.pi/2, 2*k)
        pygame.draw.arc(self.surface, (255, 255, 255), (14*k, self.larg/2+16*k, 25*k, 25*k), 3*math.pi/2, 2*math.pi, 2*k)

        pygame.draw.rect(self.surface, (0, 0, 0), ((0, ((self.larg/2)-32.5*k)), (12*k, 65*k)))
        pygame.draw.rect(self.surface, (0, 0, 255), ((4.6*k, ((self.larg/2)-30*k)), (7.4*k, 60*k)))

        pygame.draw.rect(self.surface, (0, 0, 0), ((self.long-12*k, ((self.larg/2)-32.5*k)), (12*k, 65*k)))
        pygame.draw.rect(self.surface, (255, 255, 0), ((self.long-12*k, ((self.larg/2)-30*k)), (7.4*k, 60*k)))
        
        
        
    
    def physic(self):
       self.ball.x += 5
       pygame.draw.circle(self.surface, (255, 165, 0), self.ball, 4.2*k)

        



running = True

clock = pygame.time.Clock()


sim = Sim(243, 182)


while running:
    for event in pygame.event.get():    
        if event.type == pygame.QUIT:
            running = False
    
    
    clock.tick(30)
    pygame.display.flip()
    sim.draw()
    sim.physic()
    

  #  print(pygame.display.get_window_size())
