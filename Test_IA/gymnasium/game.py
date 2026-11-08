
import pygame
import math

class Sim:

    def __init__(self, wide, longe, k):
        pygame.init()
        self.k = k #facteur d'agrandissement
        
        self.surface = pygame.display.set_mode((wide*self.k, longe*self.k)) #écran

        self.long = pygame.display.get_window_size()[0]
        self.larg = pygame.display.get_window_size()[1]
        cy = self.larg/2
        
        self.ball = pygame.Vector2(self.long/2, self.larg/2) #position de la balle placé au centre du terrain
        self.velocity = pygame.Vector2(0, 0)
        self.friction = 0.1 # pour être plus réaliste
        
        self.robot = pygame.Vector2(500, self.larg/2)
        self.robot_speed = 200
        self.last_robot = self.robot.copy() # pour calculer la vélocité du robot
        self.robot_vel = pygame.Vector2(0, 0)

        # parties noires = murs pleins (fond + barre du haut + barre du bas)
        self.walls = [
            # but gauche
            pygame.Rect(0, cy - 32.5*k, 4.6*k, 65*k),          # fond
            pygame.Rect(0, cy - 32.5*k, 12*k, 2.5*k),          # barre haut
            pygame.Rect(0, cy + 30*k,   12*k, 2.5*k),          # barre bas
            # but droit
            pygame.Rect(self.long - 4.6*k, cy - 32.5*k, 4.6*k, 65*k),
            pygame.Rect(self.long - 12*k,  cy - 32.5*k, 12*k, 2.5*k),
            pygame.Rect(self.long - 12*k,  cy + 30*k,   12*k, 2.5*k),
        ]

        self.font = pygame.font.SysFont("Arial", 25)

        # zones de couleur = pas de rebond, la balle peut entrer


    def draw(self):
        self.surface.fill((0, 0, 0))
        pygame.draw.rect(self.surface, (0, 128, 0), ((0, 0), (self.long, self.larg)))

        pygame.draw.rect(self.surface, (255, 255, 255), ((self.long/2-109.5*self.k, self.larg/2-79*self.k), (219*self.k, 158*self.k)))
        pygame.draw.rect(self.surface, (0, 128, 0), ((self.long/2-107.5*self.k, self.larg/2-77*self.k), (215*self.k, 154*self.k)))

        pygame.draw.line(self.surface, (255, 255, 255), (self.long-14*self.k, self.larg/2-40*self.k), (self.long-27*self.k, self.larg/2-40*self.k), width=2*self.k)
        pygame.draw.line(self.surface, (255, 255, 255), (self.long-14*self.k, self.larg/2+40*self.k), (self.long-27*self.k, self.larg/2+40*self.k), width=2*self.k)
        pygame.draw.line(self.surface, (255, 255, 255), (self.long-38*self.k, self.larg/2-30*self.k), (self.long-38*self.k, self.larg/2+30*self.k), width=2*self.k)
        pygame.draw.arc(self.surface, (255, 255, 255), (self.long-39*self.k, self.larg/2-41*self.k, 25*self.k, 25*self.k), math.pi/2, math.pi, 2*self.k)
        pygame.draw.arc(self.surface, (255, 255, 255), (self.long-39*self.k, self.larg/2+16*self.k, 25*self.k, 25*self.k), math.pi, 3*math.pi/2, 2*self.k)

        pygame.draw.line(self.surface, (255, 255, 255), (14*self.k, self.larg/2-40*self.k), (27*self.k, self.larg/2-40*self.k), width=2*self.k)
        pygame.draw.line(self.surface, (255, 255, 255), (14*self.k, self.larg/2+40*self.k), (27*self.k, self.larg/2+40*self.k), width=2*self.k)
        pygame.draw.line(self.surface, (255, 255, 255), (38*self.k, self.larg/2-30*self.k), (38*self.k, self.larg/2+30*self.k), width=2*self.k)
        pygame.draw.arc(self.surface, (255, 255, 255), (14*self.k, self.larg/2-41*self.k, 25*self.k, 25*self.k), 0, math.pi/2, 2*self.k)
        pygame.draw.arc(self.surface, (255, 255, 255), (14*self.k, self.larg/2+16*self.k, 25*self.k, 25*self.k), 3*math.pi/2, 2*math.pi, 2*self.k)

        pygame.draw.rect(self.surface, (0, 0, 0), ((0, self.larg/2-32.5*self.k), (12*self.k, 65*self.k)))
        pygame.draw.rect(self.surface, (0, 0, 255), ((4.6*self.k, self.larg/2-30*self.k), (7.4*self.k, 60*self.k)))

        pygame.draw.rect(self.surface, (0, 0, 0), ((self.long-12*self.k, self.larg/2-32.5*self.k), (12*self.k, 65*self.k)))
        pygame.draw.rect(self.surface, (255, 255, 0), ((self.long-12*self.k, self.larg/2-30*self.k), (7.4*self.k, 60*self.k)))

        position_robot_affichage = self.font.render(str(self.robot), True, (255, 255, 255))
        self.surface.blit(position_robot_affichage, (20, 20))

    def physic_balle(self, dt):
        self.ball += self.velocity * dt
        pygame.draw.circle(self.surface, (255, 165, 0), self.ball, 2.1*self.k)
        self.velocity *= self.friction ** dt

    def physic_robot(self):
        pygame.draw.circle(self.surface, (255, 0, 0), self.robot, 17.5/2*self.k)

    def kick(self, forcex, forcey):
        self.velocity.xy = forcex, forcey

    def collision(self):
        r_ball, r_robot = 4.2/2*self.k, 17.5/2*self.k

        if self.ball.x < r_ball or self.ball.x > self.long-r_ball:
            self.ball.x = max(r_ball, min(self.ball.x, self.long-r_ball))
            self.velocity.x *= -0.7

        if self.ball.y < r_ball or self.ball.y > self.larg-r_ball:
            self.ball.y = max(r_ball, min(self.ball.y, self.larg-r_ball))
            self.velocity.y *= -0.7

        delta = self.ball - self.robot
        distance = delta.length()

        if 0 < distance < r_ball+r_robot:
            n = delta.normalize()
            self.ball = self.robot + n*(r_ball+r_robot)
            vn = (self.velocity-self.robot_vel).dot(n)

            if vn < 0:
                self.velocity -= 0.8*vn*n
        for wall in self.walls:
            self.collision_rect(wall)   # la fonction "point le plus proche" vue avant


    def collision_rect(self, rect):
        r = 4.2 * self.k

        # point du rectangle le plus proche du centre de la balle
        closest = pygame.Vector2(
            max(rect.left, min(self.ball.x, rect.right)),
            max(rect.top,  min(self.ball.y, rect.bottom)),
        )
        delta = self.ball - closest
        dist = delta.length()

        if dist >= r:
            return  # pas de collision

        if dist > 0:
            n = delta / dist
            self.ball += n * (r - dist)  # sort la balle du rectangle
        else:
            # centre de la balle dans le rectangle : on sort par la face la plus proche
            gaps = {
                (-1, 0): self.ball.x - rect.left,
                (1, 0):  rect.right - self.ball.x,
                (0, -1): self.ball.y - rect.top,
                (0, 1):  rect.bottom - self.ball.y,
            }
            direction = min(gaps, key=gaps.get)
            n = pygame.Vector2(direction)
            self.ball += n * (gaps[direction] + r)

        # rebond seulement si la balle va vers le rectangle
        vn = self.velocity.dot(n)
        if vn < 0:
            self.velocity -= 1.7 * vn * n  # 1.7 = 1 + élasticité 0.7
        

    def but(self):
        self.ball_rect = pygame.Rect(0, 0, 2*2.1*self.k, 2*2.1*self.k)
        self.ball_rect.center = self.ball

        if self.ball_rect.colliderect(pygame.Rect((4.6*self.k, self.larg/2-30*self.k), (7.4*self.k, 60*self.k))) or self.ball_rect.colliderect(pygame.Rect((self.long-12*self.k, self.larg/2-30*self.k), (7.4*self.k, 60*self.k))):
            print("But !")
            self.ball.update(self.long/2, self.larg/2)
            self.velocity.xy = 0, 0
            return True

        return False

    def deplacer_robot(self, dt):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)

        if keys[pygame.K_UP]:
            direction.y -= 1
        if keys[pygame.K_DOWN]:
            direction.y += 1
        if keys[pygame.K_LEFT]:
            direction.x -= 1
        if keys[pygame.K_RIGHT]:
            direction.x += 1

        if direction.length() > 0:
            direction = direction.normalize()

        self.robot += direction*self.robot_speed*dt

        rayon = 17.5/2*self.k
        self.robot.x = max(rayon, min(self.robot.x, self.long-rayon))
        self.robot.y = max(rayon, min(self.robot.y, self.larg-rayon))

        self.robot_vel = (self.robot-self.last_robot)/dt if dt > 0 else pygame.Vector2(0, 0)
        self.last_robot = self.robot.copy()


running = True
clock = pygame.time.Clock()

sim = Sim(243, 182, 5)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            sim.kick(0, 100)

    dt = clock.tick(60)/1000

    sim.draw()
    sim.deplacer_robot(dt)
    sim.physic_balle(dt)
    sim.physic_robot()
    sim.collision()
    sim.but()

    pygame.display.flip()

pygame.quit()