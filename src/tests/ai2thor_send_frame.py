import base64
import io
import json
from ai2thor.controller import Controller
from PIL import Image

controller = Controller(scene="FloorPlan10")
event = controller.step(action="RotateRight")

agent = event.metadata["agent"]
meta = {
    "position": agent["position"],
    "rotation": agent["rotation"],
    "scene": event.metadata.get("sceneName", "FloorPlan10"),
}

# Encode frame as PNG -> base64
buf = io.BytesIO()
Image.fromarray(event.frame).save(buf, format="PNG")
b64 = base64.b64encode(buf.getvalue()).decode("ascii")

print("DREAMAI_META " + json.dumps(meta))
print("DREAMAI_FRAME_B64_BEGIN")
print(b64)
print("DREAMAI_FRAME_B64_END")

controller.stop()