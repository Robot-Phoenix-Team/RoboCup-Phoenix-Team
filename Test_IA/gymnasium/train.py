"""Entraînement / lecture d'un agent PPO sur RobotSoccer-v0.

    python train.py train --steps 1000000          # entraîne et sauvegarde ppo_robot.zip
    python train.py play                           # regarde l'agent jouer (fenêtre pygame)
    python train.py eval --episodes 50             # taux de buts sur 50 épisodes
"""
import argparse

import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

import robot_env  # noqa: F401  (enregistre RobotSoccer-v0)

MODEL_PATH = "ppo_robot"


def evaluate(model, episodes: int, render: bool = False):
    mode = "wheels" if model.action_space.shape[0] == 4 else "body"  # déduit du modèle chargé
    env = gym.make("RobotSoccer-v0", render_mode="human" if render else None, action_mode=mode)
    goals = own_goals = timeouts = 0
    total_reward = 0.0
    for _ in range(episodes):
        obs, info = env.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            done = terminated or truncated
        if info["goal"] == 1:
            goals += 1
        elif info["goal"] == -1:
            own_goals += 1
        else:
            timeouts += 1
    env.close()
    print(f"{episodes} épisodes | buts : {goals} | contre son camp : {own_goals} | "
          f"sans but : {timeouts} | récompense moyenne : {total_reward / episodes:.2f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["train", "play", "eval"])
    parser.add_argument("--steps", type=int, default=1_000_000)
    parser.add_argument("--n-envs", type=int, default=8)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--model", default=MODEL_PATH)
    parser.add_argument("--action-mode", choices=["wheels", "body"], default="body",
                        help="wheels : 4 moteurs ; body : (avant, côté, rotation)")
    args = parser.parse_args()

    if args.mode == "train":
        vec_env = make_vec_env("RobotSoccer-v0", n_envs=args.n_envs, seed=args.seed,
                               env_kwargs={"action_mode": args.action_mode})
        model = PPO("MlpPolicy", vec_env, verbose=1, seed=args.seed, device="cpu",
                    n_steps=1024, batch_size=256, gamma=0.99, ent_coef=0.005)
        model.learn(total_timesteps=args.steps)
        model.save(args.model)
        evaluate(model, args.episodes)
    else:
        model = PPO.load(args.model, device="cpu")
        evaluate(model, args.episodes, render=(args.mode == "play"))


if __name__ == "__main__":
    main()
