import prior
from ai2thor.controller import Controller

def run_procthor_demo():
    # 1. Load the ProcTHOR-10K dataset 
    # (This may take a moment the first time as it downloads the metadata)
    print("Loading ProcTHOR dataset...")
    dataset = prior.load_dataset("procthor-10k")
    
    # 2. Grab a random house (the JSON dictionary) from the training set
    # Index 0 is just an example; you can pick any index up to 9,999
    house_data = dataset["train"][0] 
    
    # Print keys to see what's available
    print(f"House data keys: {list(house_data.keys())[:10]}")  # show first 10 keys
    house_id = house_data.get('id') or house_data.get('house_index') or '0'
    print(f"Initializing Controller with House: {house_id}")

    # 3. Launch the Simulator
    # We use width/height to keep it manageable on a laptop screen
    controller = Controller(
        agentMode="default",
        visibilityDistance=1.5,
        scene=house_data,  # This passes the JSON to the engine
        width=800,
        height=600,
    )

    # 4. Perform a simple action to prove it works
    event = controller.step(action="RotateRight")
    
    if event.metadata['lastActionSuccess']:
        print("Success! The house is loaded and the agent moved.")
    else:
        print("Action failed, but the scene is loaded.")

    print("Press Ctrl+C in the terminal to close.")
    # Keep the window open so you can look at it
    while True:
        pass

if __name__ == "__main__":
    run_procthor_demo()
