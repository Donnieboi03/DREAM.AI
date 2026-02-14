"""Predefined policy modes and network sizes for SB3 PPO training."""

POLICY_MODES = ("default", "fast", "sample_efficient", "exploration")
NETWORK_SIZES = ("small", "medium", "large")


def get_policy_config(mode: str) -> dict:
    """Return PPO training kwargs for the given mode. Falls back to default if unknown."""
    presets = {
        "default": {
            "learning_rate": 3e-4,
            "n_steps": 2048,
            "batch_size": 64,
            "n_epochs": 10,
            "ent_coef": 0.01,  # Encourage exploration; movement actions have sparse reward
        },
        "fast": {
            "learning_rate": 5e-4,
            "n_steps": 1024,
            "batch_size": 32,
            "n_epochs": 5,
            "ent_coef": 0.01,
        },
        "sample_efficient": {
            "learning_rate": 1e-4,
            "n_steps": 4096,
            "batch_size": 128,
            "n_epochs": 15,
            "ent_coef": 0.01,
        },
        "exploration": {
            "learning_rate": 3e-4,
            "n_steps": 2048,
            "batch_size": 64,
            "n_epochs": 10,
            "ent_coef": 0.05,  # Stronger entropy for sparse-reward tasks
        },
    }
    return presets.get(mode, presets["default"]).copy()


def get_network_config(size: str) -> dict:
    """Return policy_kwargs (net_arch) for the given network size. Falls back to medium if unknown."""
    presets = {
        "small": dict(net_arch=dict(pi=[64, 64], vf=[64, 64])),
        "medium": dict(net_arch=dict(pi=[256, 256], vf=[256, 256])),
        "large": dict(net_arch=dict(pi=[512, 512], vf=[512, 512])),
    }
    return presets.get(size, presets["medium"]).copy()
