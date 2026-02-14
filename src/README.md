# DreamAI

Simulation-first robotics platform that automatically improves how robots are trained by evolving environments, tasks, and rewards. Users describe high-level goals in plain language; the system generates scenarios, trains an agent, evaluates behavior, and analyzes failures with AI—closing the loop between training, evaluation, and failure understanding.

---

## Project structure

| Directory | Purpose |
|-----------|--------|
| **frontend/** | GUI (React/Tauri) |
| **backend/** | FastAPI, orchestrator, schemas, LLM, evaluation, VLM, storage |
| **envs/** | AI2-THOR and common environment utilities |
| **rl/** | Reinforcement learning (SB3, plugins, agent interface) |
| **tools/** | Recorder, replay, validators |
| **demos/** | Local run and demo scripts |

---

## Setup (ProcTHOR & AI2-THOR)

For the ProcTHOR demo and environment integration you need AI2-THOR, ProcTHOR, and the ProcTHOR-10K dataset. **Install ProcTHOR from the official repo as an editable package** so it works correctly with DreamAI (the PyPI package can be out of sync or miss fixes).

### 1. Clone and install ProcTHOR from source

```bash
# Clone the official ProcTHOR repo (e.g. alongside DreamAI or in a deps folder)
git clone https://github.com/allenai/procthor.git
cd procthor
pip install -e .
cd ..
```

### 2. Install DreamAI dependencies

From the **src** directory:

```bash
pip install -r requirements.txt
```

This installs `ai2thor`, `prior`, `gymnasium`, `pydantic`, and others. For global keyboard control in the demo, `pynput` is included; on macOS you may need to grant **Accessibility** permission to Terminal if keys do not work when the simulation window is focused.

### 3. Optional: virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e path/to/procthor
pip install -r requirements.txt
```

---

## Docker (ProcTHOR / AI2-THOR) — mainly for Windows

Docker + VNC lets you run the simulation in a container and view it in your browser. All Docker files live in **`docker/`** at the repo root.

From the **repo root** (parent of `src/`):

**Build:** `docker build -t src-thor -f docker/Dockerfile .`  
**Run:** `python docker/run_vnc.py` (optional: `python docker/run_vnc.py FloorPlan201`)

Then open **http://localhost:6080/vnc.html**. Full instructions, port overrides, and ARM (Apple Silicon) notes: see **[../docker/README.md](../docker/README.md)**.

---

## Running the ProcTHOR test

The script **`demos/run_proc_test.py`** is the single demo: it loads or generates a house, starts the AI2-THOR simulator, and lets you drive the agent with the keyboard (WASD, Q/E, X to quit).

### Where to run from

- **From the src directory (recommended):**
  ```bash
  cd src
  python demos/run_proc_test.py [options]
  ```
- **From the repo root (parent of src):**
  ```bash
  PYTHONPATH=. python src/demos/run_proc_test.py [options]
  ```

### How to get a house

| Mode | Command | Description |
|------|---------|-------------|
| **Dataset (default)** | `python demos/run_proc_test.py` | Loads ProcTHOR-10K train[0]. |
| **Dataset (choose house)** | `--split val --index 5` or `--random --seed 123` | Pick by split/index or random. |
| **Example schema** | `--use-example-schema` | Uses the canonical example house dict (10K train[0]) for schema-driven creation. |
| **Config (generate)** | `--config 2-bed-1-bath --seed 42` | Tries procedural generation; on failure (e.g. macOS) falls back to 10K. |
| **Config (fallback only)** | `--config 4-room --fallback-only` | Skips generation and loads from 10K. |

### Schema and inspecting the house dict

- **Print schema (for LLMs or editing):**  
  `python demos/run_proc_test.py --print-schema`
- **Dump example house as JSON (see exact format):**  
  `python demos/run_proc_test.py --print-example`  
  Shorter dump: `--print-example --print-example-max-objects 5`  
  Save to file: `--print-example --print-example-to example_house.json`

### Display and input

- `--no-fullscreen` — windowed mode (can reduce spinning cursor on macOS)
- `--width 1920 --height 1080` — window size in pixels
- `--terminal` — read keys from terminal only (must keep terminal focused; default is global keys via pynput)

### Notes

- **macOS:** Procedural generation (`--config` without `--fallback-only`) often fails (CreateHouse / resolution). Use dataset mode or `--fallback-only`; the script falls back automatically on error.
- **Spinning cursor** over the sim window on macOS is a known Unity quirk; try `--no-fullscreen`.

---

## Intent of the ProcTHOR test script

- **Validate setup:** Confirm ProcTHOR, AI2-THOR, and ProcTHOR-10K work in your environment.
- **Demonstrate scene sources:** Show the three ways to get a house (example schema, dataset, config/generation) that the rest of DreamAI can use.
- **Expose the house schema:** The house is a single dict (HouseDict) passed as `Controller(scene=house_dict)`. The script documents and lets you inspect this schema so you can drive scene creation from an LLM or from code (e.g. controlled random layouts from user input).
- **Support development:** Keyboard control and optional global keys let you move the agent while focusing the sim window; `--print-schema` and `--print-example` support tooling and documentation.

---

## Further reading

- **ARCHITECTURE.md** — Directory overview, ProcTHOR/AI2-THOR integration, backend specs (SceneSpec, TaskSpec, RewardSpec, FailureReport), and ThorEnv usage.
