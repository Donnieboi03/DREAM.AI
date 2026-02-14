"""Gymnasium wrappers for SB3 CnnPolicy compatibility."""

import gymnasium as gym
import numpy as np


class ChannelFirstWrapper(gym.ObservationWrapper):
    """Convert observation from HWC to CHW for SB3 CnnPolicy."""

    def __init__(self, env: gym.Env):
        super().__init__(env)
        if not isinstance(env.observation_space, gym.spaces.Box):
            raise ValueError("ChannelFirstWrapper expects Box observation space")
        shape = env.observation_space.shape
        if len(shape) != 3:
            raise ValueError("ChannelFirstWrapper expects 3D observation (H, W, C)")
        # (H, W, C) -> (C, H, W)
        self.observation_space = gym.spaces.Box(
            low=env.observation_space.low.min(),
            high=env.observation_space.high.max(),
            shape=(shape[2], shape[0], shape[1]),
            dtype=env.observation_space.dtype,
        )

    def observation(self, observation: np.ndarray) -> np.ndarray:
        return np.moveaxis(observation, -1, 0)
