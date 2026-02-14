"""Script to create a controller and generate a house using AI2THOR."""

from ai2thor.controller import Controller
import prior


def get_example_house():
    """Load an example house from ProcTHOR-10K dataset."""
    try:
        dataset = prior.load_dataset("procthor-10k")
        house = dataset["train"][0]
        return house
    except Exception as e:
        print(f"Error loading ProcTHOR-10K: {e}")
        return None


def create_controller():
    """Create and return an AI2THOR controller instance."""
    controller = Controller(
        use_cloudRendering=True,
        server_start_timeout=120
    )
    return controller


def create_house(controller, house=None):
    """
    Call the CreateHouse action on the controller.
    
    Args:
        controller: An instance of Controller
        house: House configuration dict (required). Should be a valid ProcTHOR house dict.
    
    Returns:
        The event/response from the action
    """
    if house is None:
        raise ValueError("house parameter is required and cannot be None")
    
    event = controller.step(action="CreateHouse", house=house)
    return event


def main():
    """Main execution function."""
    print("Creating AI2THOR controller...")
    controller = create_controller()
    
    print("Loading example house from ProcTHOR-10K...")
    house = get_example_house()
    
    if house is None:
        print("Failed to load house data.")
        return
    
    print("Calling CreateHouse action...")
    try:
        event = create_house(controller, house=house)
        
        print(f"Action successful: {event.metadata['lastActionSuccess']}")
        print(f"Action error: {event.metadata.get('errorMessage', 'None')}")
        
        if event.metadata['lastActionSuccess']:
            print("House created successfully!")
            
            # Optional: Initialize the scene
            print("\nCalling Initialize action...")
            evt_init = controller.step(action="Initialize", gridSize=0.25)
            print(f"Initialize successful: {evt_init.metadata['lastActionSuccess']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Keep the controller running if needed
    # controller.stop()


if __name__ == "__main__":
    main()
