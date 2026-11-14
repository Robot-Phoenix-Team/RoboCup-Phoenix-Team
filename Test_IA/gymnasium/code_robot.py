# code_robot.py
# Le robot se place derrière la balle, oriente son côté plat vers le but
# adverse, puis pousse la balle avec le plat. Quelle que soit sa position.
import math
import pygame
import __main__

speed = 800            # vitesse max (lue par sim.py)
rotation_speed = 6     # vitesse de rotation max en rad/s

# ---------------- Réglages ----------------
BUT_ADVERSE = "droite"        # "droite" = but jaune, "gauche" = but bleu
KP_ROT = 12.0                 # raideur de l'asservissement d'angle
ALIGN_TOL = 0.35              # rad : erreur d'angle max (~20°) pour foncer sur la balle
CONE = math.radians(30)       # demi-angle du cône "derrière la balle" où on peut foncer
ORBIT_STEP = 0.7              # rad : avance du point visé quand on contourne la balle
MAX_LEAD = 0.4                # s : anticipation max du mouvement de la balle


def _wrap(a):
    """Ramène un angle dans [-pi, pi]."""
    return (a + math.pi) % (2 * math.pi) - math.pi


def _goal(sim):
    """Centre de l'ouverture du but adverse."""
    x = sim.long - 8 * sim.k if BUT_ADVERSE == "droite" else 8 * sim.k
    return pygame.Vector2(x, sim.larg / 2)


def _shot_direction(sim, ball, goal, contact, r_rob):
    """Direction de tir (vecteur unitaire balle -> but).
    Si le robot ne peut pas se placer derrière la balle (balle collée à un mur),
    on tourne légèrement la direction de tir jusqu'à ce que ce soit possible."""
    to_goal = goal - ball
    base = to_goal.normalize() if to_goal.length() > 1e-6 else pygame.Vector2(1, 0)
    best, best_key = base, None
    for i in range(7):                      # 0°, ±15°, ... ±90°
        for sgn in (1, -1):
            if i == 0 and sgn == -1:
                continue
            u = base.rotate_rad(sgn * i * math.radians(15))
            p = ball - u * contact          # centre du robot au moment du contact
            if r_rob <= p.x <= sim.long - r_rob and r_rob <= p.y <= sim.larg - r_rob:
                key = (i, -u.y * to_goal.y)  # à écart égal, on préfère viser vers l'axe du but
                if best_key is None or key < best_key:
                    best, best_key = u, key
    return best


def _plan():
    """Retourne (direction de déplacement, gaz entre 0 et 1, erreur d'angle)."""
    sim = __main__.sim
    k = sim.k
    ball = pygame.Vector2(sim.ball)
    robot = pygame.Vector2(sim.robot)

    r_rob = 17.5 / 2 * k
    r_ball = 2.1 * k
    contact = sim.flat + r_ball + 2         # distance centre robot / centre balle au contact avec le plat
    ring = r_rob + r_ball + 7 * k           # rayon du cercle de contournement (ne touche jamais la balle)

    # Le plat est à l'arrière du robot (côté -e1) : pour qu'il regarde vers le but,
    # il faut angle = direction du tir + pi.
    u = _shot_direction(sim, ball, _goal(sim), contact, r_rob)
    target_angle = math.atan2(-u.y, -u.x)
    err = _wrap(target_angle - sim.angle)

    # Position du robot par rapport à la balle, comparée à "derrière la balle" (= -u)
    rel = robot - ball
    rho = rel.length()
    phi = math.atan2(rel.y, rel.x) if rho > 1e-6 else target_angle
    alpha = _wrap(phi - target_angle)       # 0 = pile derrière la balle

    if abs(alpha) < CONE:
        # Bien placé derrière la balle : on fonce dessus (avec anticipation)
        lead = min(rho / speed, MAX_LEAD)
        aim = ball + pygame.Vector2(sim.velocity) * lead
        direction = aim - robot
        # on attend d'être aligné avant le contact pour taper avec le plat
        throttle = 0.0 if (abs(err) > ALIGN_TOL and rho < ring + 20) else 1.0
    else:
        # Mal placé : on contourne la balle sur un cercle jusqu'à passer derrière
        phi_w = phi - math.copysign(ORBIT_STEP, alpha)
        way = ball + pygame.Vector2(math.cos(phi_w), math.sin(phi_w)) * ring
        direction = way - robot
        throttle = 1.0

    return direction, throttle, err


def get_velocity(keys):
    # sim.py normalise le vecteur s'il dépasse 1 puis le multiplie par `speed` :
    # on renvoie donc un vecteur de longueur <= 1.
    direction, throttle, _ = _plan()
    if throttle == 0.0 or direction.length() < 1e-6:
        return 0, 0
    direction.scale_to_length(throttle)
    return direction.x, direction.y


def get_rotation(keys):
    # vitesse angulaire (rad/s) : sim.angle += get_rotation() * dt
    _, _, err = _plan()
    return max(-rotation_speed, min(rotation_speed, KP_ROT * err))