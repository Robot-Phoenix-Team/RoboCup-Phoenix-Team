# code_robot.py
# Le robot se place derriere la balle, oriente son cote plat vers le but adverse,
# puis pousse la balle avec le plat. Il ne sort jamais des lignes blanches et
# n'entre jamais dans une surface de reparation.
import math
import pygame
import __main__

speed = 800            # vitesse max (lue par sim.py)
rotation_speed = 20    # vitesse de rotation max en rad/s

# ---------------- Reglages ----------------
BUT_ADVERSE = "droite"        # "droite" = but jaune, "gauche" = but bleu
KP_ROT = 20.0                 # raideur de l'asservissement d'angle
ALIGN_TOL = 0.08              # rad : erreur d'angle max avant de toucher la balle
CONE = math.radians(30)       # demi-angle du cone "derriere la balle" ou on peut foncer
ORBIT_STEP = 0.7              # rad : avance du point vise quand on contourne la balle
MAX_LEAD = 0.4                # s : anticipation max du mouvement de la balle
LAT_TOL = 24                  # px : decalage lateral tolere entre le centre du robot et la balle (le plat est large)
TIR_PRUDENT = False           # False = toujours a fond (le plus rapide) ; True = dose la puissance pour ne jamais
                              # laisser la balle s'arreter dans une surface de reparation (un peu plus lent)
END_SPEED = 250               # px/s : (prudent) vitesse voulue de la balle en arrivant dans le but
STAGE = 330                   # px : (prudent) distance au but ou on laisse la balle si elle est trop loin pour un tir direct
MAX_PUSH = 400                # px : (prudent) distance max parcourue par la balle lors d'un rapprochement
NUDGE = 100                   # px : distance parcourue par la balle lors d'une poussee de repositionnement (cas rares)
DT = 1 / 60                   # s : duree d'une frame
EFF = 1.2                     # rendement du choc plat/balle (1.4 de face, moins en biais)


_charging = False             # memoire du mode (evite d'osciller entre foncer et contourner)


def _wrap(a):
    """Ramene un angle dans [-pi, pi]."""
    return (a + math.pi) % (2 * math.pi) - math.pi


def _goal(sim):
    """Centre de l'ouverture du but adverse."""
    x = sim.long - 8 * sim.k if BUT_ADVERSE == "droite" else 8 * sim.k
    return pygame.Vector2(x, sim.larg / 2)


def _free(sim, p):
    """True si le centre du robot peut etre en p (dans les lignes, hors surfaces de reparation)."""
    k = sim.k
    r = 17.5 / 2 * k
    cx, cy = sim.long / 2, sim.larg / 2
    if abs(p.x - cx) > 107.5 * k - r or abs(p.y - cy) > 77 * k - r:
        return False
    for x0, x1 in ((14 * k, 38 * k), (sim.long - 38 * k, sim.long - 14 * k)):
        if x0 - r < p.x < x1 + r and abs(p.y - cy) < 30 * k + r:
            return False
    return True


def _project(sim, p):
    """Point libre le plus proche de p (pour ne jamais viser un point interdit)."""
    k = sim.k
    r = 17.5 / 2 * k
    cx, cy = sim.long / 2, sim.larg / 2
    lx, ly = 107.5 * k - r, 77 * k - r
    q = pygame.Vector2(max(cx - lx, min(p.x, cx + lx)), max(cy - ly, min(p.y, cy + ly)))
    for x0, x1 in ((14 * k, 38 * k), (sim.long - 38 * k, sim.long - 14 * k)):
        if x0 - r < q.x < x1 + r and abs(q.y - cy) < 30 * k + r:
            m = 3                           # petite marge pour sortir franchement de la zone
            opts = ((q.x - (x0 - r), pygame.Vector2(x0 - r - m, q.y)),
                    ((x1 + r) - q.x, pygame.Vector2(x1 + r + m, q.y)),
                    (q.y - (cy - 30 * k - r), pygame.Vector2(q.x, cy - 30 * k - r - m)),
                    ((cy + 30 * k + r) - q.y, pygame.Vector2(q.x, cy + 30 * k + r + m)))
            q = min((o for o in opts if _free(sim, o[1])), key=lambda o: o[0], default=opts[0])[1]
    return q


def _limit(sim, robot, v):
    """Empeche de sortir des lignes ou d'entrer dans une surface (anticipe une frame)."""
    if not _free(sim, robot):                      # deja dedans (pousse par l'autre robot) : retour vers le centre
        back = pygame.Vector2(sim.long / 2, sim.larg / 2) - robot
        return back.normalize() if back.length() > 1e-6 else v
    d = v * (speed / 60 * 1.3)
    if _free(sim, robot + d):
        return v
    n = v.length()
    if _free(sim, robot + pygame.Vector2(d.x, 0)):      # on glisse le long de l'obstacle, sans ralentir
        return pygame.Vector2(math.copysign(n, v.x) if abs(v.x) > 0.25 * n else v.x, 0)
    if _free(sim, robot + pygame.Vector2(0, d.y)):
        return pygame.Vector2(0, math.copysign(n, v.y) if abs(v.y) > 0.25 * n else v.y)
    return pygame.Vector2(0, 0)


def _shot_direction(sim, ball, goal, reach):
    """Direction de poussee (vecteur unitaire) et ecart par rapport a la direction du but (0 = tir direct).
    Si le robot ne peut pas se placer derriere la balle (mur, surface de reparation),
    on tourne la direction par pas de 15 degres jusqu'a ce que ce soit possible."""
    to_goal = goal - ball
    base = to_goal.normalize() if to_goal.length() > 1e-6 else pygame.Vector2(1, 0)
    best, best_key = (base, 0), None
    for i in range(13):
        for sgn in (1, -1):
            if i == 0 and sgn == -1:
                continue
            u = base.rotate_rad(sgn * i * math.radians(15))
            perp = pygame.Vector2(-u.y, u.x)
            for t in (0, 12, -12, LAT_TOL, -LAT_TOL):   # le plat est plus large que la balle
                if _free(sim, ball - u * reach + perp * t):
                    key = (i, -u.y * to_goal.y)
                    if best_key is None or key < best_key:
                        best, best_key = (u, i), key
                    break
    return best


def _orbit_side(sim, ball, phi, alpha, ring):
    """Sens de contournement (+1/-1) : le plus court dont l'arc reste dans la zone libre."""
    short = math.copysign(1, alpha)
    for s, total in ((short, abs(alpha)), (-short, 2 * math.pi - abs(alpha))):
        n = int(total / 0.2) + 1
        if all(_free(sim, ball + pygame.Vector2(math.cos(phi - s * total * i / n),
                                                 math.sin(phi - s * total * i / n)) * ring)
               for i in range(1, n + 1)):
            return s
    return short


def _contact_speed(sim, ball, goal, dev):
    """Vitesse (px/s) du robot au contact. Pleine vitesse sauf poussee de repositionnement ou mode prudent."""
    f = sim.friction
    d = (goal - ball).length()
    if dev:                                           # balle collee a un mur / une surface : petite poussee
        vb = f * NUDGE
    elif not TIR_PRUDENT:
        return speed
    elif d <= (EFF * speed - END_SPEED) / f:          # tir direct : la balle arrive dans le but
        vb = END_SPEED + f * d
    else:                                             # trop loin : on rapproche sans entrer dans la surface
        vb = f * min(d - STAGE, MAX_PUSH)
    return max(120, min(speed, vb / EFF))


def _plan():
    """Retourne (direction de deplacement, gaz entre 0 et 1, erreur d'angle)."""
    sim = __main__.sim
    k = sim.k
    ball = pygame.Vector2(sim.ball)
    robot = pygame.Vector2(sim.robot)

    r_rob = 17.5 / 2 * k
    r_ball = 2.1 * k
    ring = r_rob + r_ball + 7 * k           # rayon du cercle de contournement (ne touche jamais la balle)
    goal = _goal(sim)

    # Le plat est a l'arriere du robot (cote -e1) : pour qu'il regarde vers la direction
    # de poussee u, il faut angle = direction de u + pi.
    u, dev = _shot_direction(sim, ball, goal, sim.flat + 0.5 * r_ball)   # le plat touche la balle des ~35 px
    target_angle = math.atan2(-u.y, -u.x)
    err = _wrap(target_angle - sim.angle)

    # Position du robot par rapport a la balle, comparee a "derriere la balle" (= -u)
    rel = robot - ball
    rho = rel.length()
    phi = math.atan2(rel.y, rel.x) if rho > 1e-6 else target_angle
    alpha = _wrap(phi - target_angle)       # 0 = pile derriere la balle

    global _charging
    _charging = abs(alpha) < (CONE * 1.5 if _charging else CONE)
    if _charging:
        # Bien place derriere la balle : on fonce dessus (avec anticipation)
        lead = min(rho / speed, MAX_LEAD)
        aim = ball + pygame.Vector2(sim.velocity) * lead
        direction = aim - robot
        throttle = 1.0
        vc = _contact_speed(sim, ball, goal, dev)
        if vc < speed:                      # seule la derniere frame avant le contact est a la vitesse voulue
            r = rho - 46
            if r <= speed * DT:
                throttle = (r - 0.5 * vc * DT) / DT / speed if r > vc * DT else vc / speed
        e = abs(err)
        if e > ALIGN_TOL:
            # temps qu'il faut encore pour finir de tourner (rotation plafonnee, puis exponentielle)
            lim = rotation_speed / KP_ROT
            t_rot = max(0.0, e - lim) / rotation_speed + math.log(min(e, lim) / ALIGN_TOL) / KP_ROT
            # on ralentit juste ce qu'il faut pour arriver au contact quand l'angle est bon : pas d'arret
            throttle = min(throttle, max(0.0, rho - 40) / (t_rot + 0.02) / speed)
    else:
        # Mal place : on contourne la balle sur un cercle jusqu'a passer derriere
        s = _orbit_side(sim, ball, phi, alpha, ring)
        phi_w = phi - s * ORBIT_STEP
        way = _project(sim, ball + pygame.Vector2(math.cos(phi_w), math.sin(phi_w)) * ring)
        direction = way - robot
        throttle = 1.0

    return direction, throttle, err


def get_velocity(keys):
    # sim.py normalise le vecteur s'il depasse 1 puis le multiplie par `speed` :
    # on renvoie donc un vecteur de longueur <= 1.
    direction, throttle, _ = _plan()
    if throttle == 0.0 or direction.length() < 1e-6:
        v = pygame.Vector2(0, 0)
    else:
        v = direction.normalize() * throttle
    v = _limit(__main__.sim, pygame.Vector2(__main__.sim.robot), v)
    return v.x, v.y


def get_rotation(keys):
    # vitesse angulaire (rad/s) : sim.angle += get_rotation() * dt
    _, _, err = _plan()
    return max(-rotation_speed, min(rotation_speed, KP_ROT * err))