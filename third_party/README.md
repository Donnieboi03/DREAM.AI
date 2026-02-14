# Third-Party Dependencies

## rl_thor

[rl_thor](https://github.com/JulianPaquerot/rl_thor) (MIT) provides GraphTask-based reward computation for RL training. DREAM.AI uses it for task-specific rewards (e.g. place apple on plate, pick up mug).

- **Location**: `third_party/rl_thor`
- **Install**: `pip install -e third_party/rl_thor`
- **Python**: Requires 3.12+

Docker images install rl_thor automatically during build.
