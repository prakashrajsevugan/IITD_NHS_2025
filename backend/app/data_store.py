"""
In-memory data store for the Space Station Cargo Management System.
This replaces the SQLite database with Python dictionaries and lists.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any

# In-memory data stores
containers = {}
items = {}
logs = []

# Counter for log IDs
log_counter = 0

class Container:
    def __init__(self, id: str, zone: str, width: float, depth: float, height: float, mass: float = 0.0):
        self.id = id
        self.zone = zone
        self.width = width
        self.depth = depth
        self.height = height
        self.mass = mass
        self.occupied_volume = 0.0
        self.items = []  # List of item IDs in this container
    
    def to_dict(self):
        return {
            "id": self.id,
            "zone": self.zone,
            "width": self.width,
            "depth": self.depth,
            "height": self.height,
            "mass": self.mass,
            "occupied_volume": self.occupied_volume,
            "items": self.items
        }

class Item:
    def __init__(self, id: str, name: str, width: float, depth: float, height: float, 
                 mass: float, priority: int, expiry_date: Optional[str] = None, 
                 usage_limit: Optional[int] = None, preferred_zone: Optional[str] = None):
        self.id = id
        self.name = name
        self.width = width
        self.depth = depth
        self.height = height
        self.mass = mass
        self.priority = priority
        self.expiry_date = expiry_date
        self.usage_limit = usage_limit
        self.preferred_zone = preferred_zone
        self.container_id = None
        self.status = "Active"
        self.usage_count = 0
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "width": self.width,
            "depth": self.depth,
            "height": self.height,
            "mass": self.mass,
            "priority": self.priority,
            "expiry_date": self.expiry_date,
            "usage_limit": self.usage_limit,
            "usage_count": getattr(self, 'usage_count', 0),
            "preferred_zone": self.preferred_zone,
            "container_id": self.container_id,
            "status": self.status
        }

class Log:
    def __init__(self, action_type: str, description: str, user_id: Optional[str] = None, 
                 item_id: Optional[str] = None, container_id: Optional[str] = None):
        global log_counter
        log_counter += 1
        self.id = log_counter
        self.timestamp = datetime.now()
        self.action_type = action_type
        self.description = description
        self.user_id = user_id
        self.item_id = item_id
        self.container_id = container_id
    
    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "action_type": self.action_type,
            "description": self.description,
            "user_id": self.user_id,
            "item_id": self.item_id,
            "container_id": self.container_id
        }

# CRUD operations for containers
def create_container(container_data: Dict[str, Any]) -> Container:
    container = Container(
        id=container_data["id"],
        zone=container_data["zone"],
        width=container_data["width"],
        depth=container_data["depth"],
        height=container_data["height"],
        mass=container_data.get("mass", 0.0)
    )
    containers[container.id] = container
    return container

def get_container(container_id: str) -> Optional[Container]:
    return containers.get(container_id)

def get_all_containers(skip: int = 0, limit: int = 100) -> List[Container]:
    return list(containers.values())[skip:skip+limit]

def update_container(container_id: str, updates: Dict[str, Any]) -> Optional[Container]:
    container = containers.get(container_id)
    if container:
        for key, value in updates.items():
            if hasattr(container, key):
                setattr(container, key, value)
        return container
    return None

def delete_container(container_id: str) -> bool:
    if container_id in containers:
        del containers[container_id]
        return True
    return False

# CRUD operations for items
def create_item(item_data: Dict[str, Any]) -> Item:
    item = Item(
        id=item_data["id"],
        name=item_data["name"],
        width=item_data["width"],
        depth=item_data["depth"],
        height=item_data["height"],
        mass=item_data["mass"],
        priority=item_data["priority"],
        expiry_date=item_data.get("expiry_date"),
        usage_limit=item_data.get("usage_limit"),
        preferred_zone=item_data.get("preferred_zone")
    )
    items[item.id] = item
    return item

def get_item(item_id: str) -> Optional[Item]:
    return items.get(item_id)

def get_all_items(skip: int = 0, limit: int = 100) -> List[Item]:
    return list(items.values())[skip:skip+limit]

def update_item(item_id: str, updates: Dict[str, Any]) -> Optional[Item]:
    item = items.get(item_id)
    if item:
        for key, value in updates.items():
            if hasattr(item, key):
                setattr(item, key, value)
        return item
    return None

def delete_item(item_id: str) -> bool:
    if item_id in items:
        del items[item_id]
        return True
    return False

# CRUD operations for logs
def create_log(log_data: Dict[str, Any]) -> Log:
    log = Log(
        action_type=log_data["action_type"],
        description=log_data["description"],
        user_id=log_data.get("user_id"),
        item_id=log_data.get("item_id"),
        container_id=log_data.get("container_id")
    )
    logs.append(log)
    return log

def get_logs(
    action_type: Optional[str] = None,
    user_id: Optional[str] = None,
    item_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    limit: int = 100
) -> List[Log]:
    filtered_logs = logs
    
    if action_type:
        filtered_logs = [log for log in filtered_logs if log.action_type == action_type]
    
    if user_id:
        filtered_logs = [log for log in filtered_logs if log.user_id == user_id]
    
    if item_id:
        filtered_logs = [log for log in filtered_logs if log.item_id == item_id]
    
    if start_date:
        start_datetime = datetime.fromisoformat(start_date)
        filtered_logs = [log for log in filtered_logs if log.timestamp >= start_datetime]
    
    if end_date:
        end_datetime = datetime.fromisoformat(end_date)
        filtered_logs = [log for log in filtered_logs if log.timestamp <= end_datetime]
    
    # Sort by timestamp descending (newest first)
    filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
    
    # Pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    return filtered_logs[start_idx:end_idx]

# Helper function to place item in container
def place_item_in_container(item_id: str, container_id: str) -> bool:
    item = items.get(item_id)
    container = containers.get(container_id)
    
    if not item or not container:
        return False
    
    # Calculate item volume
    item_volume = item.width * item.depth * item.height
    
    # Calculate container volume
    container_volume = container.width * container.depth * container.height
    
    # Check if there's enough space
    if container.occupied_volume + item_volume > container_volume:
        return False
    
    # Update item and container
    item.container_id = container_id
    container.occupied_volume += item_volume
    container.items.append(item_id)
    
    return True

# Alias for place_item_in_container to maintain compatibility with existing code
def place_item(item_id: str, container_id: str) -> bool:
    """
    Alias for place_item_in_container function to maintain compatibility with existing code.
    Places an item in a container.
    
    Args:
        item_id: ID of the item to place
        container_id: ID of the container to place the item in
        
    Returns:
        bool: True if the item was successfully placed, False otherwise
    """
    return place_item_in_container(item_id, container_id)

# Helper function to remove item from container
def remove_item_from_container(item_id: str) -> bool:
    item = items.get(item_id)
    
    if not item or not item.container_id:
        return False
    
    container = containers.get(item.container_id)
    
    if not container:
        return False
    
    # Calculate item volume
    item_volume = item.width * item.depth * item.height
    
    # Update container
    container.occupied_volume -= item_volume
    if item_id in container.items:
        container.items.remove(item_id)
    
    # Update item
    item.container_id = None
    
    return True

# Initialize with some sample data
def initialize_sample_data():
    # Create sample containers
    create_container({
        "id": "C001",
        "zone": "Storage",
        "width": 100.0,
        "depth": 100.0,
        "height": 100.0
    })
    
    create_container({
        "id": "C002",
        "zone": "Lab",
        "width": 50.0,
        "depth": 50.0,
        "height": 50.0
    })
    
    create_container({
        "id": "C003",
        "zone": "Undocking",
        "width": 200.0,
        "depth": 200.0,
        "height": 200.0
    })
    
    # Create sample items
    create_item({
        "id": "I001",
        "name": "Food Package",
        "width": 10.0,
        "depth": 10.0,
        "height": 10.0,
        "mass": 5.0,
        "priority": 5,
        "expiry_date": "2025-12-31"
    })
    
    create_item({
        "id": "I002",
        "name": "Medical Kit",
        "width": 20.0,
        "depth": 15.0,
        "height": 10.0,
        "mass": 3.0,
        "priority": 10
    })
    
    create_item({
        "id": "I003",
        "name": "Science Equipment",
        "width": 30.0,
        "depth": 30.0,
        "height": 20.0,
        "mass": 15.0,
        "priority": 7,
        "usage_limit": 10
    })
    
    # Place items in containers
    place_item_in_container("I001", "C001")
    place_item_in_container("I002", "C002")
    
    # Create sample logs
    create_log({
        "action_type": "INIT",
        "description": "System initialized with sample data"
    })

# Initialize with sample data from samples folder
def initialize_with_samples(containers_limit=0, items_limit=200):
    """
    Initialize the data store with sample data from the samples folder.
    
    Args:
        containers_limit: Maximum number of containers to import (0 for all)
        items_limit: Maximum number of items to import
    
    Returns:
        Tuple of (containers_count, items_count)
    """
    try:
        import os
        import pandas as pd
        
        # Sample file paths
        samples_dir = r"c:\Users\Admin\Downloads\samples-20250407T034157Z-001\samples"
        containers_file = os.path.join(samples_dir, "containers.csv")
        items_file = os.path.join(samples_dir, "input_items.csv")
        
        # Check if files exist
        if not os.path.exists(containers_file) or not os.path.exists(items_file):
            print(f"Sample files not found in {samples_dir}")
            # Fall back to basic sample data
            initialize_sample_data()
            return 0, 0
        
        # Import containers
        containers_count = 0
        try:
            # Read the CSV file
            df = pd.read_csv(containers_file)
            
            # Limit if needed
            if containers_limit > 0:
                df = df.head(containers_limit)
            
            # Process containers
            for _, row in df.iterrows():
                # Create container data dictionary
                container_data = {
                    "id": row["container_id"],
                    "zone": row["zone"],
                    "width": float(row["width_cm"]),
                    "depth": float(row["depth_cm"]),
                    "height": float(row["height_cm"])
                }
                
                # Create container in data store
                create_container(container_data)
                containers_count += 1
        except Exception as e:
            print(f"Error importing containers: {str(e)}")
            # Fall back to basic sample data
            initialize_sample_data()
            return 0, 0
        
        # Import items
        items_count = 0
        try:
            # Read the CSV file
            df = pd.read_csv(items_file)
            
            # Limit the number of items if needed
            if items_limit > 0:
                df = df.head(items_limit)
            
            # Process items
            for _, row in df.iterrows():
                # Create item data dictionary
                item_data = {
                    "id": row["item_id"],
                    "name": row["name"],
                    "width": float(row["width_cm"]),
                    "depth": float(row["depth_cm"]),
                    "height": float(row["height_cm"]),
                    "mass": float(row["mass_kg"]),
                    "priority": int(row["priority"])
                }
                
                # Add optional fields if present
                if "expiry_date" in row and row["expiry_date"] != "N/A":
                    item_data["expiry_date"] = row["expiry_date"]
                
                if "usage_limit" in row and not pd.isna(row["usage_limit"]):
                    item_data["usage_limit"] = int(row["usage_limit"])
                
                # Create item in data store
                create_item(item_data)
                items_count += 1
        except Exception as e:
            print(f"Error importing items: {str(e)}")
            # If items import fails but containers succeeded, keep the containers
            if containers_count == 0:
                # Fall back to basic sample data
                initialize_sample_data()
            return containers_count, 0
        
        # Log the import
        create_log({
            "action_type": "IMPORT_SAMPLES",
            "description": f"Imported {containers_count} containers and {items_count} items from sample files"
        })
        
        return containers_count, items_count
    
    except Exception as e:
        print(f"Error initializing with samples: {str(e)}")
        # Fall back to basic sample data
        initialize_sample_data()
        return 0, 0

# Try to initialize with samples first, fall back to basic sample data if that fails
try:
    containers_count, items_count = initialize_with_samples()
    if containers_count == 0 and items_count == 0:
        # If sample initialization failed, use basic sample data
        initialize_sample_data()
    else:
        print(f"Initialized with {containers_count} containers and {items_count} items from sample files")
except Exception as e:
    print(f"Error during initialization: {str(e)}")
    # Fall back to basic sample data
    initialize_sample_data()
