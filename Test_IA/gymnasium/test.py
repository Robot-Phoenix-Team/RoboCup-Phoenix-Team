# Run `pip install "gymnasium[classic-control]"` for this example.
import gymnasium as gym
from stable_baselines3 import PPO
# Create our training environment - a cart with a pole that needs balancing
env = gym.make("CartPole-v1", render_mode="human")

import gymnasium as gym
from stable_baselines3 import PPO

model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=50_000)
model.save("ppo_cartpole")