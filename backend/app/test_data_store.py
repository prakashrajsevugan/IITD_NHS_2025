"""
Test script for the in-memory data store.
This demonstrates how to use the data_store module.
"""
from . import data_store
import json

def test_data_store():
    """
    Test the in-memory data store functionality.
    """
    print("Testing in-memory data store...")
    
    # Get all containers
    containers = data_store.get_all_containers()
    print(f"Found {len(containers)} containers:")
    for container in containers:
        print(f"  - {container.id}: {container.zone} ({container.width}x{container.depth}x{container.height})")
    
    # Get all items
    items = data_store.get_all_items()
    print(f"\nFound {len(items)} items:")
    for item in items:
        container_info = f"in container {item.container_id}" if item.container_id else "not in any container"
        print(f"  - {item.id}: {item.name} ({item.width}x{item.depth}x{item.height}), {container_info}")
    
    # Create a new container
    new_container = data_store.create_container({
        "id": "C004",
        "zone": "Airlock",
        "width": 75.0,
        "depth": 75.0,
        "height": 75.0
    })
    print(f"\nCreated new container: {new_container.id} in zone {new_container.zone}")
    
    # Create a new item
    new_item = data_store.create_item({
        "id": "I004",
        "name": "Space Suit",
        "width": 50.0,
        "depth": 30.0,
        "height": 20.0,
        "mass": 25.0,
        "priority": 9
    })
    print(f"Created new item: {new_item.id} - {new_item.name}")
    
    # Place the item in the container
    success = data_store.place_item_in_container(new_item.id, new_container.id)
    if success:
        print(f"Successfully placed {new_item.id} in container {new_container.id}")
        
        # Check container's occupied volume
        container = data_store.get_container(new_container.id)
        print(f"Container {container.id} occupied volume: {container.occupied_volume}")
        
        # Remove the item from the container
        success = data_store.remove_item_from_container(new_item.id)
        if success:
            print(f"Successfully removed {new_item.id} from container {new_container.id}")
            container = data_store.get_container(new_container.id)
            print(f"Container {container.id} occupied volume after removal: {container.occupied_volume}")
    
    # Create a log entry
    log = data_store.create_log({
        "action_type": "TEST",
        "description": "Testing the data store",
        "user_id": "test_user",
        "item_id": new_item.id,
        "container_id": new_container.id
    })
    print(f"\nCreated log entry: {log.id} - {log.action_type}: {log.description}")
    
    # Get logs
    logs = data_store.get_logs()
    print(f"\nFound {len(logs)} logs:")
    for log in logs:
        print(f"  - {log.id}: {log.timestamp} - {log.action_type}: {log.description}")

if __name__ == "__main__":
    test_data_store()
