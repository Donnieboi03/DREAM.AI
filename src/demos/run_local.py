from ai2thor.controller import Controller

controller = Controller()

# Get all available iTHOR scenes
all_scenes = controller.ithor_scenes()

for scene in all_scenes:
    print(scene)
