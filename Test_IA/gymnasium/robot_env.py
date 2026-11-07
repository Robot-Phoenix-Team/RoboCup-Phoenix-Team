"""Environnement Gymnasium : robot omnidirectionnel (4 roues mecanum) qui doit marquer.

Port Python fidèle de la physique du simulateur JavaScript (Robot Simulator) :
mêmes constantes, même cinématique mecanum, même rebond de balle, même collision
robot/balle et même détection de but. Le pas de temps par défaut est 1/30 s,
soit le dt maximal utilisé par la boucle du simulateur (0.033 s).

Espace d'action  : Box(-1, 1, (4,)) -> vitesse des 4 roues en % / 100
                   (équivalent de setmotor_speed1..4 : 1=avant-gauche,
                   2=avant-droit, 3=arrière-gauche, 4=arrière-droit).
Espace d'observation : Box(16,) voir _get_obs().
Terminaison      : but dans la cage de droite (+), but dans la cage de gauche (-).
Troncature       : max_steps pas sans but.
"""
from __future__ import annotations

import math

import gymnasium as gym
import numpy as np
from gymnasium import spaces

# ─── Constantes (identiques au simulateur JS) ──────────────────────────────
FIELD_W, FIELD_H = 2.43, 1.83
BALL_RESTITUTION = 0.6
BALL_FRICTION = 0.7
WHEEL_RADIUS = 0.03
MAX_WHEEL_OMEGA = 40.0
MAX_WHEEL_ACCEL = 120.0
ROBOT_RADIUS = 0.09
ROBOT_HALF_LENGTH = 0.09
ROBOT_HALF_WIDTH = 0.09
BALL_RADIUS = 0.04
GOAL_WIDTH = 0.6
GOAL_DEPTH = 0.15

TARGET_GOAL = np.array([FIELD_W, FIELD_H / 2])  # cage de droite = cage à attaquer
MAX_BALL_SPEED = 2.0  # sert uniquement à normaliser l'observation


class RobotSoccerEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

    # Pondération de la récompense
    GOAL_REWARD = 10.0
    OWN_GOAL_PENALTY = -10.0
    STEP_PENALTY = -0.01
    SHAPING_ROBOT_BALL = 1.0  # récompense le rapprochement robot -> balle
    SHAPING_BALL_GOAL = 3.0   # récompense le rapprochement balle -> cage cible

    PIXELS_PER_METER = 300

    def __init__(self, render_mode=None, max_steps: int = 600,
                 randomize: bool = True, dt: float = 1 / 30,
                 action_mode: str = "wheels"):
        """action_mode :
        - "wheels" : 4 valeurs = vitesse des 4 roues (comme setmotor_speed1..4).
        - "body"   : 3 valeurs = (avant, côté, rotation) dans le repère robot, convertis en
                     vitesses de roues par la cinématique inverse. Apprentissage plus facile.
        """
        super().__init__()
        if render_mode is not None and render_mode not in self.metadata["render_modes"]:
            raise ValueError(f"render_mode invalide : {render_mode}")
        if action_mode not in ("wheels", "body"):
            raise ValueError(f"action_mode invalide : {action_mode}")
        self.render_mode = render_mode
        self.max_steps = max_steps
        self.randomize = randomize
        self.dt = dt
        self.action_mode = action_mode

        n_actions = 4 if action_mode == "wheels" else 3
        self.action_space = spaces.Box(-1.0, 1.0, shape=(n_actions,), dtype=np.float32)
        self.observation_space = spaces.Box(-np.inf, np.inf, shape=(16,), dtype=np.float32)

        self._window = None
        self._clock = None
        self._surface = None

    # ─── Gymnasium API ────────────────────────────────────────────────────
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)  # initialise self.np_random

        rng = self.np_random
        self.wheels = np.zeros(4)
        self.wheel_targets = np.zeros(4)
        self.steps = 0

        if self.randomize:
            m = ROBOT_RADIUS
            self.robot_pos = rng.uniform([m, m], [FIELD_W - m, FIELD_H - m])
            self.heading = float(rng.uniform(-math.pi, math.pi))
            # balle hors des cages et pas sur le robot
            while True:
                self.ball_pos = rng.uniform([GOAL_DEPTH, 0.1], [FIELD_W - GOAL_DEPTH, FIELD_H - 0.1])
                if np.linalg.norm(self.ball_pos - self.robot_pos) > ROBOT_RADIUS + BALL_RADIUS + 0.05:
                    break
        else:  # configuration initiale du simulateur
            self.robot_pos = np.array([FIELD_W * 0.5, FIELD_H * 0.5])
            self.heading = 0.0
            self.ball_pos = np.array([FIELD_W * 0.7, FIELD_H * 0.5])
        self.ball_vel = np.zeros(2)

        if self.render_mode == "human":
            self.render()
        return self._get_obs(), self._get_info(0)

    def step(self, action):
        action = np.clip(np.asarray(action, dtype=np.float64), -1.0, 1.0)
        if self.action_mode == "wheels":
            self.wheel_targets = action * MAX_WHEEL_OMEGA  # = setmotor_speed (% / 100 * omega max)
        else:
            self.wheel_targets = self._body_to_wheels(action)

        d_rb0, d_bg0 = self._distances()
        goal = self._physics(self.dt)
        d_rb, d_bg = self._distances()

        reward = (self.STEP_PENALTY
                  + self.SHAPING_ROBOT_BALL * (d_rb0 - d_rb)
                  + self.SHAPING_BALL_GOAL * (d_bg0 - d_bg))
        if goal == 1:
            reward += self.GOAL_REWARD
        elif goal == -1:
            reward += self.OWN_GOAL_PENALTY

        self.steps += 1
        terminated = goal != 0
        truncated = (not terminated) and self.steps >= self.max_steps

        if self.render_mode == "human":
            self.render()
        return self._get_obs(), float(reward), terminated, truncated, self._get_info(goal)

    @staticmethod
    def _body_to_wheels(action):
        """(avant, côté, rotation) normalisés -> vitesses angulaires des roues (rad/s).
        Inverse exacte de la cinématique mecanum de _physics ; la combinaison non
        actionnable des roues est fixée à 0, puis on respecte la limite des moteurs."""
        L = ROBOT_HALF_LENGTH + ROBOT_HALF_WIDTH
        vx = action[0] * WHEEL_RADIUS * MAX_WHEEL_OMEGA      # 1.2 m/s
        vy = action[1] * WHEEL_RADIUS * MAX_WHEEL_OMEGA
        omega = action[2] * WHEEL_RADIUS * MAX_WHEEL_OMEGA / L  # ~6.7 rad/s
        a, b, c = 4 * vx / WHEEL_RADIUS, 4 * vy / WHEEL_RADIUS, 4 * L * omega / WHEEL_RADIUS
        wheels = np.array([a - b - c, a + b + c, a + b - c, a - b + c]) / 4
        return np.clip(wheels, -MAX_WHEEL_OMEGA, MAX_WHEEL_OMEGA)

    # ─── Physique (port de stepPhysics du simulateur JS) ──────────────────
    def _physics(self, dt: float) -> int:
        """Avance d'un pas. Renvoie +1 (but à droite), -1 (but à gauche) ou 0."""
        # Rampe d'accélération des roues
        max_delta = MAX_WHEEL_ACCEL * dt
        self.wheels += np.clip(self.wheel_targets - self.wheels, -max_delta, max_delta)

        # Cinématique mecanum
        fl, fr, rl, rr = self.wheels
        R = WHEEL_RADIUS
        L = ROBOT_HALF_LENGTH + ROBOT_HALF_WIDTH
        vx = R * (fl + fr + rl + rr) / 4
        vy = R * (-fl + fr + rl - rr) / 4
        omega = R * (-fl + fr - rl + rr) / (4 * L)

        # Repère robot -> monde
        c, s = math.cos(self.heading), math.sin(self.heading)
        vxw = vx * c - vy * s
        vyw = vx * s + vy * c

        self.robot_pos += np.array([vxw, vyw]) * dt
        self.heading += omega * dt
        self.heading = math.atan2(math.sin(self.heading), math.cos(self.heading))
        self.robot_pos[0] = np.clip(self.robot_pos[0], ROBOT_RADIUS, FIELD_W - ROBOT_RADIUS)
        self.robot_pos[1] = np.clip(self.robot_pos[1], ROBOT_RADIUS, FIELD_H - ROBOT_RADIUS)

        # Balle : déplacement, frottement, rebonds sur les bords
        r = BALL_RADIUS
        self.ball_pos += self.ball_vel * dt
        self.ball_vel *= max(0.0, 1 - BALL_FRICTION * dt)
        bp, bv = self.ball_pos, self.ball_vel
        if bp[0] < r:
            bp[0] = r
            bv[0] = abs(bv[0]) * BALL_RESTITUTION
        if bp[0] > FIELD_W - r:
            bp[0] = FIELD_W - r
            bv[0] = -abs(bv[0]) * BALL_RESTITUTION
        if bp[1] < r:
            bp[1] = r
            bv[1] = abs(bv[1]) * BALL_RESTITUTION
        if bp[1] > FIELD_H - r:
            bp[1] = FIELD_H - r
            bv[1] = -abs(bv[1]) * BALL_RESTITUTION

        # Détection des buts : balle contre le fond, dans l'ouverture de la cage
        goal_top = FIELD_H / 2 - GOAL_WIDTH / 2
        goal_bottom = FIELD_H / 2 + GOAL_WIDTH / 2
        if goal_top <= bp[1] <= goal_bottom:
            if bp[0] >= FIELD_W - r:
                return 1
            if bp[0] <= r:
                return -1

        # Collision robot <-> balle
        d = bp - self.robot_pos
        dist = float(np.hypot(d[0], d[1]))
        min_d = BALL_RADIUS + ROBOT_RADIUS
        if 0.0001 < dist < min_d:
            n = d / dist
            self.ball_pos[:] = self.robot_pos + n * min_d
            self.ball_vel[:] = np.array([vxw, vyw]) + n * 0.4
        return 0

    # ─── Observation / info ───────────────────────────────────────────────
    def _distances(self):
        d_rb = float(np.linalg.norm(self.ball_pos - self.robot_pos))
        d_bg = float(np.linalg.norm(TARGET_GOAL - self.ball_pos))
        return d_rb, d_bg

    def _to_body(self, v):
        c, s = math.cos(self.heading), math.sin(self.heading)
        return np.array([v[0] * c + v[1] * s, -v[0] * s + v[1] * c])

    def _get_obs(self):
        c, s = math.cos(self.heading), math.sin(self.heading)
        obs = np.concatenate([
            [2 * self.robot_pos[0] / FIELD_W - 1, 2 * self.robot_pos[1] / FIELD_H - 1, c, s],
            [2 * self.ball_pos[0] / FIELD_W - 1, 2 * self.ball_pos[1] / FIELD_H - 1],
            self.ball_vel / MAX_BALL_SPEED,
            self._to_body(self.ball_pos - self.robot_pos) / FIELD_W,   # balle, repère robot
            self._to_body(TARGET_GOAL - self.robot_pos) / FIELD_W,     # cage cible, repère robot
            self.wheels / MAX_WHEEL_OMEGA,
        ])
        return obs.astype(np.float32)

    def _get_info(self, goal: int):
        d_rb, d_bg = self._distances()
        return {"goal": goal, "distance_robot_ball": d_rb, "distance_ball_goal": d_bg}

    # ─── Rendu ────────────────────────────────────────────────────────────
    def _draw(self, surface):
        import pygame

        S = self.PIXELS_PER_METER
        W, H = FIELD_W, FIELD_H

        def p(x, y):
            return int(x * S), int(y * S)

        white = (200, 210, 205)
        surface.fill((13, 26, 18))
        pygame.draw.rect(surface, white, (0, 0, int(W * S), int(H * S)), 2)
        pygame.draw.line(surface, white, p(W / 2, 0), p(W / 2, H), 2)
        pygame.draw.circle(surface, white, p(W / 2, H / 2), int(0.25 * S), 2)
        pygame.draw.circle(surface, white, p(W / 2, H / 2), 3)

        top = int((H / 2 - GOAL_WIDTH / 2) * S)
        gw, gd = int(GOAL_WIDTH * S), int(GOAL_DEPTH * S)
        pygame.draw.rect(surface, (255, 110, 110), (0, top, gd, gw), 2)                 # cage adverse (but contre son camp)
        pygame.draw.rect(surface, (0, 194, 168), (int(W * S) - gd, top, gd, gw), 3)     # cage cible

        cx, cy = p(*self.robot_pos)
        r = int(ROBOT_RADIUS * S)
        pygame.draw.circle(surface, (20, 30, 45), (cx, cy), r)
        pygame.draw.circle(surface, (0, 194, 168), (cx, cy), r, 3)
        c, s = math.cos(self.heading), math.sin(self.heading)
        pygame.draw.line(surface, (255, 255, 255), (cx, cy), (cx + 0.9 * r * c, cy + 0.9 * r * s), 3)
        for ang in (math.pi / 4, -math.pi / 4, 3 * math.pi / 4, -3 * math.pi / 4):
            a = self.heading + ang
            pygame.draw.circle(surface, (58, 77, 100),
                               (cx + 0.85 * r * math.cos(a), cy + 0.85 * r * math.sin(a)), max(3, r // 6))

        pygame.draw.circle(surface, (240, 140, 20), p(*self.ball_pos), int(BALL_RADIUS * S))

    def render(self):
        if self.render_mode is None:
            return None
        import pygame

        size = (int(FIELD_W * self.PIXELS_PER_METER), int(FIELD_H * self.PIXELS_PER_METER))
        if self.render_mode == "human":
            if self._window is None:
                pygame.init()
                pygame.display.init()
                self._window = pygame.display.set_mode(size)
                pygame.display.set_caption("RobotSoccer")
                self._clock = pygame.time.Clock()
            pygame.event.pump()
            self._draw(self._window)
            pygame.display.flip()
            self._clock.tick(self.metadata["render_fps"])
            return None

        # rgb_array
        if self._surface is None:
            self._surface = pygame.Surface(size)
        self._draw(self._surface)
        return np.transpose(np.array(pygame.surfarray.pixels3d(self._surface)), (1, 0, 2))

    def close(self):
        if self._window is not None:
            import pygame
            pygame.display.quit()
            pygame.quit()
            self._window = None


if "RobotSoccer-v0" not in gym.registry:
    gym.register(id="RobotSoccer-v0", entry_point="robot_env:RobotSoccerEnv")
