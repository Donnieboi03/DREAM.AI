# DreamAI Architecture & Integration Guide

This document describes each directory in the project, how to integrate ProcTHOR and AI2-THOR to create and generate scenes, and the purpose of the backend specs.

---

## Directory Overview

| Directory | Purpose |
|-----------|---------|
| **`frontend/`** | GUI built with React and Tauri. Entry point for users to launch tasks, view runs, and configure the system. |
| **`backend/`** | Server-side logic: API, orchestration, schemas, LLM, evaluation, VLM, and storage. |
| **`backend/api/`** | FastAPI routes and WebSocket endpoints. Exposes the system to the frontend and external clients. |
| **`backend/orchestrator/`** | High-level flow: coordinates env, agent, planner, and evaluation in a single run or training loop. |
| **`backend/schemas/`** | Pydantic models (SceneSpec, TaskSpec, RewardSpec, FailureReport). LLM-filled hooks consumed by env, planner, and evaluation. |
| **`backend/llm/`** | LLM integration (e.g. Gemini), planner prompts, and structured output (e.g. via Instructor). |
| **`backend/evaluation/`** | Critic, reward adaptation, FailureReport generation, and iteration logic. |
| **`backend/vlm/`** | Vision-language / observer model for image-based critique or state description. |
| **`backend/storage/`** | Persistence for runs, checkpoints, logs, and replay data. |
| **`envs/`** | Simulation environments. Wrappers and adapters for AI2-THOR and ProcTHOR. |
| **`envs/ai2thor/`** | AI2-THOR controller wrapper (ThorEnv) and ProcTHOR scene-generation adapter. |
| **`envs/common/`** | Shared env utilities (e.g. action/obs constants, base mixins). |
| **`rl/`** | Reinforcement learning: agent interface, SB3 (PPO/SAC), plugins, and training entry points. |
| **`rl/sb3/`** | Stable-Baselines3 integration: VecEnv, PPO/SAC training loop, env workers. |
| **`rl/plugins/`** | Agent plugins (e.g. SB3 policy, scripted agent) implementing the agent interface. |
| **`tools/`** | Recorder (replay hooks), replay playback, and validators (guardrails). |
| **`tools/recorder/`** | Hooks to log transitions/trajectories during env steps for replay or analysis. |
| **`tools/replay/`** | Replay and analysis of recorded episodes. |
| **`tools/validators/`** | Input/output and safety validators used by the pipeline. |
| **`scripts/`** | One-off and demo scripts. **`run_proc_test.py`** is the single ProcTHOR demo: dataset mode (10K by split/index) or config mode (generate by room_spec_id with fallback to 10K). Use `--print-schema` to print the house customization schema (HouseDict: rooms, walls, doors, windows, objects, etc.) for LLM-driven or manual layout editing. |

---

## Setup and running the ProcTHOR demo

### Requirements

- **ProcTHOR:** Install from the **official repo as an editable package** so it works correctly with DreamAI (PyPI can be out of sync). From a clone of [allenai/procthor](https://github.com/allenai/procthor): `pip install -e .`
- **DreamAI deps:** `pip install -r requirements.txt` (ai2thor, prior, gymnasium, pydantic, pynput, etc.). See **README.md** for full setup.
- **Docker:** For containerized build and run (including **ARM/Apple Silicon** with `--platform=linux/amd64`), see **README.md** → “Docker (ProcTHOR / AI2-THOR)”.

### How to run the test

From the **dreamai** directory:

```bash
python scripts/run_proc_test.py [options]
```

From repo root: `PYTHONPATH=. python dreamai/scripts/run_proc_test.py [options]`.

| Option | Purpose |
|--------|---------|
| (none) | Dataset mode: load ProcTHOR-10K train[0]. |
| `--use-example-schema` | Create house from the built-in example house dict (schema-driven). |
| `--config 2-bed-1-bath` | Try procedural generation; fallback to 10K on failure. |
| `--split val --index 5` | Load 10K house by split and index. |
| `--random --seed 123` | Random house from split (reproducible with seed). |
| `--print-schema` | Print house customization schema (HouseDict types) and exit. |
| `--print-example` | Dump example house dict as JSON (optionally `--print-example-to FILE`, `--print-example-max-objects N`). |
| `--no-fullscreen`, `--width`, `--height` | Window size and mode. |
| `--terminal` | Read keys from terminal only (default: global keys via pynput). |

### Intent of the demo script

The script validates that ProcTHOR, AI2-THOR, and the 10K dataset work; demonstrates the three scene sources (example schema, dataset, config/generation) used elsewhere in DreamAI; and exposes the house dict schema so environments can be driven by an LLM or custom code (e.g. controlled random layouts). See **README.md** for full run instructions and intent.

---

## ProcTHOR & AI2-THOR Integration

### Roles

- **AI2-THOR** is the simulator: it runs the 3D scene and executes agent actions (move, rotate, interact).
- **ProcTHOR** provides procedural house generation and the ProcTHOR-10K dataset of pre-built house JSONs.

### Two Ways to Get a Scene

#### 1. Pre-generated houses (ProcTHOR-10K)

Use the **ProcTHOR-10K** dataset via the `prior` library. No live house generation; you load a house dict and pass it to the AI2-THOR Controller.

**Example (see `scripts/run_proc_test.py`):**

```python
import prior
from ai2thor.controller import Controller

# Load dataset (downloads metadata first time)
# Use revision=... for ai2thor < 5.0 to avoid prior/AI2-THOR version warning
dataset = prior.load_dataset("procthor-10k", revision="ab3cacd0fc17754d4c080a3fd50b18395fae8647")

# Get a house dict (train/val/test, index 0–9999 / 0–999)
house_data = dataset["train"][0]

# Start controller with that house
controller = Controller(
    agentMode="default",
    scene=house_data,  # Pass the JSON house directly
    width=800,
    height=600,
    snapToGrid=True,
    gridSize=0.25,
    rotateStepDegrees=90.0,
)
event = controller.step(action="MoveAhead")
```

- **Requires:** `pip install ai2thor prior`. Scripts use ProcTHOR-10K revision `ab3cacd0...` for compatibility when AI2-THOR is &lt; 5.0; omit `revision` for AI2-THOR 5.0+.
- **Works on:** macOS (including ARM) and Linux when the right builds exist. No `CreateHouse` call. Demo scripts use global keys (pynput) so you can focus the sim window; a spinning cursor over the Unity window on macOS is a known quirk (try `--no-fullscreen`).

#### 2. Live procedural generation (ProcTHOR HouseGenerator)

Use the **ProcTHOR** library to generate a new house at runtime and get an AI2-THOR controller with that scene already loaded.

**Example (see `envs/ai2thor/procthor_adapter.py`):**

```python
from dreamai.envs.ai2thor.procthor_adapter import create_procthor_scene
from dreamai.envs.ai2thor.thor_env import ThorEnv

# Optional: use a SceneSpec (e.g. from LLM) for seed
from dreamai.backend.schemas import SceneSpec
scene_spec = SceneSpec(seed=42, scene_type="procedural")

controller, house = create_procthor_scene(seed=42, scene_spec=scene_spec)
env = ThorEnv(controller=controller)
obs, info = env.reset()
obs, reward, term, trunc, info = env.step(0)  # 0 = MoveAhead
env.close()
```

- **Under the hood:** `create_procthor_scene` uses `procthor.generation.HouseGenerator` and `PROCTHOR10K_ROOM_SPEC_SAMPLER`, then returns the controller (with the procedural scene loaded) and the House object.
- **Config vs randomness:** `room_spec_id` (e.g. `"2-bed-1-bath"`) fixes which room types exist; layout and object placement are procedural and controlled by `seed`. Same config + same seed = same house. For finer control (e.g. floorplan scale, object counts), pass options via `create_procthor_scene(..., **house_generator_kwargs)` (ProcTHOR’s HouseGenerator accepts `sampling_vars` and related options).
- **Caveat:** On some setups (e.g. macOS ARM), the Unity build may not support `CreateHouse`; you get "Unable to CreateHouse!". In that case use **option 1** (ProcTHOR-10K) or a fixed iTHOR scene (e.g. `ThorEnv(scene_name="FloorPlan1")`). The demo script `run_proc_test.py` supports both options and `--width`/`--height`; run `python scripts/run_proc_test.py --print-schema` for the house dict schema used for customizations (rooms, objects, walls, doors, windows).

### Using ThorEnv (Gymnasium wrapper)

**`envs/ai2thor/thor_env.py`** wraps an AI2-THOR controller as a Gymnasium env:

- **From a scene name (iTHOR):** `ThorEnv(scene_name="FloorPlan1")`
- **From a ProcTHOR controller:** `ThorEnv(controller=controller)` after `create_procthor_scene(...)` or after loading a house from ProcTHOR-10K and starting a Controller with `scene=house_data`.

Actions are discrete (MoveAhead, MoveBack, RotateLeft, RotateRight, LookUp, LookDown, PickupObject, DropHandObject, ToggleObjectOn). Observation is RGB image; `info` includes `agent_position`, `agent_rotation`, and `last_action_success`.

### Summary

| Goal | Approach |
|------|----------|
| Use a pre-built procedural house | `prior.load_dataset("procthor-10k", revision="...")` → `dataset["train"][i]` → `Controller(scene=house_data)` (scripts use compat revision for ai2thor &lt; 5.0) |
| Generate a new procedural house at runtime | `create_procthor_scene(seed=..., scene_spec=...)` → `ThorEnv(controller=controller)` (may fail on macOS ARM) |
| Use a fixed iTHOR scene | `ThorEnv(scene_name="FloorPlan1")` or `Controller(scene="FloorPlan1")` |

---

## Backend Specs (LLM-Filled Hooks)

The specs in **`backend/schemas/`** define the **structure** of data that the LLM (or other components) produce. The rest of the pipeline (env, planner, evaluation) consumes these objects.

### SceneSpec

**File:** `backend/schemas/scene_spec.py`

**Purpose:** Describes the **scene** the agent will run in. Used to configure the environment and, when using procedural generation, options for ProcTHOR.

| Field | Use |
|-------|-----|
| `scene_id` | Unique identifier for the scene. |
| `scene_name` | e.g. `"FloorPlan28"` or `"procedural"`. |
| `scene_type` | e.g. `"kitchen"`, `"living_room"`, `"procedural"`. |
| `seed` | Random seed for procedural generation; passed to `create_procthor_scene(seed=...)` or `scene_spec_to_procthor_options(scene_spec)`. |
| `objectives` | Focus areas or target objects (for future use in generation or task setup). |
| `extra` | Provider-specific config. |

**Integration:** The orchestrator or env factory can build a scene from a SceneSpec: for iTHOR use `scene_name`; for ProcTHOR use `create_procthor_scene(scene_spec=scene_spec)` (or pass `scene_spec.seed`).

---

### TaskSpec

**File:** `backend/schemas/task_spec.py`

**Purpose:** Describes the **task** the agent should perform. Used by the planner and by the env (e.g. max steps, goal conditioning).

| Field | Use |
|-------|-----|
| `task_id` | Unique task identifier. |
| `description` | Natural language task description (required). |
| `goal` | Explicit goal statement. |
| `success_criteria` | List of conditions for success. |
| `max_steps` | Maximum environment steps; can set `env._max_steps` or episode length. |
| `subtasks` | Optional ordered subtasks. |
| `extra` | Provider-specific fields. |

**Integration:** The planner uses TaskSpec as the authoritative task description. The orchestrator can pass `max_steps` into the env and use `success_criteria` for evaluation.

---

### RewardSpec

**File:** `backend/schemas/reward_spec.py`

**Purpose:** Describes **how reward is shaped**. Used by the evaluation/reward pipeline and the critic.

| Field | Use |
|-------|-----|
| `reward_type` | e.g. `"sparse"`, `"dense"`, `"shaped"`. |
| `components` | Names of reward components. |
| `success_reward` | Reward on task success. |
| `failure_penalty` | Penalty on failure. |
| `custom_weights` | Weights per component. |
| `extra` | Provider-specific config. |

**Integration:** The evaluation module uses RewardSpec to configure reward computation and the critic. The reward pipeline can combine components using `custom_weights` and apply `success_reward` / `failure_penalty`.

---

### FailureReport

**File:** `backend/schemas/failure_report.py`

**Purpose:** Report of a **failure** for iteration and reward adaptation. Filled by the LLM or evaluation when an episode fails.

| Field | Use |
|-------|-----|
| `episode_id` | Episode or run identifier. |
| `failure_stage` | Where it failed (e.g. `"navigation"`, `"interaction"`). |
| `reason` | Human/LLM description of cause. |
| `suggested_fix` | Suggested change for the next iteration. |
| `extra` | Structured details. |

**Integration:** The evaluation pipeline produces or consumes FailureReports. The iteration logic can use `suggested_fix` and `failure_stage` to adjust tasks, rewards, or prompts in the next round.

---

## Quick Reference: Using the Specs

```python
from dreamai.backend.schemas import SceneSpec, TaskSpec, RewardSpec, FailureReport

# Example: LLM fills these (e.g. via Instructor); pipeline consumes them.
scene = SceneSpec(scene_type="kitchen", seed=42)
task = TaskSpec(description="Pick up the apple", max_steps=200)
reward = RewardSpec(reward_type="dense", success_reward=1.0)
failure = FailureReport(episode_id="ep1", failure_stage="navigation", reason="Agent got stuck")
```

For scene creation and generation, use **SceneSpec** with **ProcTHOR/AI2-THOR** as described in the integration section above.
