import pygame
import math
#factor for more visual
class Sim:

    def __init__(self, wide, longe, k):
        
        pygame.init()
        self.k = k
        
        self.surface = pygame.display.set_mode((wide*self.k, longe*self.k))
        
        self.long = pygame.display.get_window_size()[0]
        self.larg = pygame.display.get_window_size()[1]
        self.ball = pygame.Vector2(self.long/2, self.larg/2)
        self.velocity = pygame.Vector2(0, 0)
        self.friction = 0.1
    
    def draw(self):
        # dessiner le terrain
        self.surface.fill((0, 0, 0))
        pygame.draw.rect(self.surface, (0, 128, 0), ((0, 0), (self.long, self.larg)))

        pygame.draw.rect(self.surface, (255, 255, 255), ((self.long/2-109.5*self.k, self.larg/2-79*self.k), (219*self.k, 158*self.k)))
        pygame.draw.rect(self.surface, (0, 128, 0), ((self.long/2-107.5*self.k, self.larg/2-77*self.k), (215*self.k, 154*self.k)))

        pygame.draw.line(self.surface, (255, 255, 255), (self.long-12*self.k-2*self.k, self.larg/2-40*self.k), (self.long-27*self.k, self.larg/2-40*self.k), width=2*self.k)
        pygame.draw.line(self.surface, (255, 255, 255), (self.long-12*self.k-2*self.k, self.larg/2+40*self.k), (self.long-27*self.k, self.larg/2+40*self.k), width=2*self.k)
        pygame.draw.line(self.surface, (255, 255, 255), (self.long-39*self.k+1*self.k, self.larg/2-30*self.k), (self.long-39*self.k+1*self.k, self.larg/2+30*self.k), width=2*self.k)
        pygame.draw.arc(self.surface, (255, 255, 255), (self.long-39*self.k, self.larg/2-41*self.k, 25*self.k, 25*self.k), math.pi/2, math.pi, 2*self.k)
        pygame.draw.arc(self.surface, (255, 255, 255), (self.long-39*self.k, self.larg/2+16*self.k, 25*self.k, 25*self.k), math.pi, 3*math.pi/2, 2*self.k)

        pygame.draw.line(self.surface, (255, 255, 255), (12*self.k+2*self.k, self.larg/2-40*self.k), (27*self.k, self.larg/2-40*self.k), width=2*self.k)
        pygame.draw.line(self.surface, (255, 255, 255), (12*self.k+2*self.k, self.larg/2+40*self.k), (27*self.k, self.larg/2+40*self.k), width=2*self.k)
        pygame.draw.line(self.surface, (255, 255, 255), (39*self.k-1*self.k, self.larg/2-30*self.k), (39*self.k-1*self.k, self.larg/2+30*self.k), width=2*self.k)
        pygame.draw.arc(self.surface, (255, 255, 255), (14*self.k, self.larg/2-41*self.k, 25*self.k, 25*self.k), 0, math.pi/2, 2*self.k)
        pygame.draw.arc(self.surface, (255, 255, 255), (14*self.k, self.larg/2+16*self.k, 25*self.k, 25*self.k), 3*math.pi/2, 2*math.pi, 2*self.k)

        pygame.draw.rect(self.surface, (0, 0, 0), ((0, ((self.larg/2)-32.5*self.k)), (12*self.k, 65*self.k)))
        pygame.draw.rect(self.surface, (0, 0, 255), ((4.6*self.k, ((self.larg/2)-30*self.k)), (7.4*self.k, 60*self.k)))

        pygame.draw.rect(self.surface, (0, 0, 0), ((self.long-12*self.k, ((self.larg/2)-32.5*self.k)), (12*self.k, 65*self.k)))
        pygame.draw.rect(self.surface, (255, 255, 0), ((self.long-12*self.k, ((self.larg/2)-30*self.k)), (7.4*self.k, 60*self.k)))
        
        
        
    
    def physic(self, dt):
        self.ball += self.velocity * dt
        pygame.draw.circle(self.surface, (255, 165, 0), self.ball, 4.2*self.k)
        self.velocity *= self.friction ** dt
        
    def kick(self, forcex, forcey):
        self.velocity.xy = forcex, forcey

    
    
    #  position=position+velocity×Δt 



running = True

clock = pygame.time.Clock()


sim = Sim(243, 182, 5)

while running:
    for event in pygame.event.get():    
        if event.type == pygame.QUIT:
            running = False
    
    
    clock.tick(30)
    pygame.display.flip()
    sim.draw()
    sim.physic(1/30)

    if event.type == pygame.MOUSEBUTTONDOWN:
        sim.kick(100, 0)



  #  print(pygame.display.get_window_size())
