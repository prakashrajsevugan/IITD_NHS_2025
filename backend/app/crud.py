from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import numpy as np

from . import models, schemas

# Search and retrieval operations
def search_item(db: Session, request: schemas.SearchRequest):
    # Build query based on search criteria
    query = db.query(models.Item)
    
    if request.item_id:
        query = query.filter(models.Item.id == request.item_id)
    
    if request.name:
        # Improved search with partial matching
        query = query.filter(models.Item.name.ilike(f"%{request.name}%"))
    
    if request.zone:
        # Join with Container to filter by zone
        query = query.join(models.Container).filter(models.Container.zone == request.zone)
    
    if request.priority_min:
        query = query.filter(models.Item.priority >= request.priority_min)
    
    # Execute query
    items = query.all()
    
    # Enhanced scoring for search results
    scored_items = []
    for item in items:
        # Base score starts at 1.0
        score = 1.0
        
        # Prioritize by expiry date (if present)
        if item.expiry_date:
            system_date = db.query(models.SystemDate).first()
            current_date = system_date.current_date if system_date else datetime.utcnow()
            
            # Calculate days until expiry
            if item.expiry_date > current_date:
                days_until_expiry = (item.expiry_date - current_date).days
                # Items closer to expiry get higher priority (max boost for items expiring within 7 days)
                if days_until_expiry <= 7:
                    score += (1.0 - (days_until_expiry / 7.0)) * 0.5
        
        # Prioritize by item priority
        score += (item.priority / 100.0) * 0.3
        
        # Calculate retrieval difficulty
        if item.container_id:
            steps = calculate_retrieval_steps(db, item)
            # Items that are easier to retrieve get higher priority
            accessibility_score = 1.0 / (steps + 1)  # +1 to avoid division by zero
            score += accessibility_score * 0.2
            
            # Store retrieval steps for later use
            item.retrieval_steps = steps
        else:
            item.retrieval_steps = 0
        
        # Add to scored items list with score
        scored_items.append((item, score))
    
    # Sort by score (descending)
    scored_items.sort(key=lambda x: x[1], reverse=True)
    
    # Extract items and retrieval difficulty
    sorted_items = [item for item, _ in scored_items]
    retrieval_difficulty = {item.id: item.retrieval_steps for item, _ in scored_items}
    
    # Create result
    result = schemas.SearchResult(
        items=sorted_items,
        retrieval_difficulty=retrieval_difficulty
    )
    
    return result

def calculate_retrieval_steps(db: Session, item):
    """
    Enhanced algorithm to calculate the minimum number of items that need to be moved
    to access the target item, considering 3D spatial relationships.
    """
    # Get container and all items in it
    container = get_container(db, item.container_id)
    if not container:
        return 0
        
    container_items = db.query(models.Item).filter(models.Item.container_id == container.id).all()
    
    # Get item dimensions based on orientation
    item_width, item_depth, item_height = get_item_dimensions(item)
    
    # Define the target item's bounding box
    target_box = {
        'min_x': item.position_x,
        'max_x': item.position_x + item_width,
        'min_y': item.position_y,
        'max_y': item.position_y + item_depth,
        'min_z': item.position_z,
        'max_z': item.position_z + item_height
    }
    
    # Find all items that are blocking access to the target item
    # An item blocks access if:
    # 1. It's positioned in front of the target item (lower y value)
    # 2. It overlaps with the target item's projection onto the open face
    blocking_items = []
    
    for other_item in container_items:
        if other_item.id == item.id:
            continue
            
        # Get other item dimensions based on orientation
        other_width, other_depth, other_height = get_item_dimensions(other_item)
        
        # Define the other item's bounding box
        other_box = {
            'min_x': other_item.position_x,
            'max_x': other_item.position_x + other_width,
            'min_y': other_item.position_y,
            'max_y': other_item.position_y + other_depth,
            'min_z': other_item.position_z,
            'max_z': other_item.position_z + other_height
        }
        
        # Check if other item is in front of target item (assuming open face is at y=0)
        if other_box['max_y'] <= target_box['min_y']:
            # Check if there's overlap in x and z dimensions
            x_overlap = (other_box['min_x'] < target_box['max_x'] and 
                         other_box['max_x'] > target_box['min_x'])
            z_overlap = (other_box['min_z'] < target_box['max_z'] and 
                         other_box['max_z'] > target_box['min_z'])
            
            if x_overlap and z_overlap:
                # This item is blocking access
                blocking_items.append({
                    'item': other_item,
                    'distance': target_box['min_y'] - other_box['max_y']  # Distance between items
                })
    
    # Sort blocking items by distance from target (closest first)
    # This ensures we remove items in the correct order
    blocking_items.sort(key=lambda x: x['distance'])
    
    return len(blocking_items)

def get_item_dimensions(item):
    """Helper function to get item dimensions based on orientation."""
    if not item.orientation or item.orientation == "xyz":
        return item.width, item.depth, item.height
    elif item.orientation == "xzy":
        return item.width, item.height, item.depth
    elif item.orientation == "yxz":
        return item.depth, item.width, item.height
    elif item.orientation == "yzx":
        return item.depth, item.height, item.width
    elif item.orientation == "zxy":
        return item.height, item.width, item.depth
    elif item.orientation == "zyx":
        return item.height, item.depth, item.width
    else:
        return item.width, item.depth, item.height

def retrieve_item(db: Session, request: schemas.RetrievalRequest):
    """
    Enhanced retrieval function that generates optimal step-by-step retrieval instructions
    with detailed spatial planning.
    """
    # Get item
    item = get_item(db, request.item_id)
    if not item:
        raise ValueError(f"Item with ID {request.item_id} not found")
    
    if not item.container_id:
        raise ValueError(f"Item with ID {request.item_id} is not in any container")
    
    # Get container and all items in it
    container = get_container(db, item.container_id)
    container_items = db.query(models.Item).filter(models.Item.container_id == container.id).all()
    
    # Get item dimensions based on orientation
    item_width, item_depth, item_height = get_item_dimensions(item)
    
    # Define the target item's bounding box
    target_box = {
        'min_x': item.position_x,
        'max_x': item.position_x + item_width,
        'min_y': item.position_y,
        'max_y': item.position_y + item_depth,
        'min_z': item.position_z,
        'max_z': item.position_z + item_height
    }
    
    # Find all items that are blocking access to the target item
    blocking_items = []
    
    for other_item in container_items:
        if other_item.id == item.id:
            continue
            
        # Get other item dimensions based on orientation
        other_width, other_depth, other_height = get_item_dimensions(other_item)
        
        # Define the other item's bounding box
        other_box = {
            'min_x': other_item.position_x,
            'max_x': other_item.position_x + other_width,
            'min_y': other_item.position_y,
            'max_y': other_item.position_y + other_depth,
            'min_z': other_item.position_z,
            'max_z': other_item.position_z + other_height
        }
        
        # Check if other item is in front of target item (assuming open face is at y=0)
        if other_box['max_y'] <= target_box['min_y']:
            # Check if there's overlap in x and z dimensions
            x_overlap = (other_box['min_x'] < target_box['max_x'] and 
                         other_box['max_x'] > target_box['min_x'])
            z_overlap = (other_box['min_z'] < target_box['max_z'] and 
                         other_box['max_z'] > target_box['min_z'])
            
            if x_overlap and z_overlap:
                # This item is blocking access
                blocking_items.append({
                    'item': other_item,
                    'distance': target_box['min_y'] - other_box['max_y'],  # Distance between items
                    'volume': other_width * other_depth * other_height     # Volume of blocking item
                })
    
    # Sort blocking items by distance from target (closest first)
    # This ensures we remove items in the correct order
    blocking_items.sort(key=lambda x: x['distance'])
    
    # Calculate temporary positions for each item that needs to be moved
    # In a real implementation, this would use more sophisticated spatial planning
    temp_positions = {}
    temp_x, temp_z = 0, 0
    
    for block_info in blocking_items:
        block_item = block_info['item']
        block_width, block_depth, block_height = get_item_dimensions(block_item)
        
        # Find a temporary position outside the container
        # This is a simplified approach - in reality, we'd need to find actual valid positions
        temp_positions[block_item.id] = {
            "x": temp_x,
            "y": -block_depth - 10,  # Place outside the container
            "z": temp_z
        }
        
        # Update temp position for next item
        temp_x += block_width + 5
        if temp_x > container.width:
            temp_x = 0
            temp_z += block_height + 5
    
    # Create retrieval steps
    steps = []
    for i, block_info in enumerate(blocking_items):
        block_item = block_info['item']
        # Step to remove blocking item
        steps.append(schemas.RetrievalStep(
            step_number=i+1,
            action="remove",
            item_id=block_item.id,
            temporary_position=temp_positions[block_item.id]
        ))
    
    # Step to retrieve target item
    steps.append(schemas.RetrievalStep(
        step_number=len(blocking_items)+1,
        action="retrieve",
        item_id=item.id
    ))
    
    # Steps to place back blocking items in reverse order (last out, first in)
    for i, block_info in enumerate(reversed(blocking_items)):
        block_item = block_info['item']
        steps.append(schemas.RetrievalStep(
            step_number=len(blocking_items)+2+i,
            action="place_back",
            item_id=block_item.id,
            temporary_position={
                "x": block_item.position_x,
                "y": block_item.position_y,
                "z": block_item.position_z
            }
        ))
    
    # Update item usage count
    item.usage_count += 1
    if item.usage_limit and item.usage_count >= item.usage_limit:
        item.is_waste = True
    
    # Log retrieval
    log_retrieval = models.RetrievalLog(
        item_id=item.id,
        astronaut_id=request.astronaut_id,
        steps=len(blocking_items)
    )
    db.add(log_retrieval)
    
    # Log action
    log_action = models.ActionLog(
        action_type="retrieve",
        item_id=item.id,
        container_id=container.id,
        astronaut_id=request.astronaut_id,
        details=json.dumps({
            "action": "retrieved",
            "item_name": item.name,
            "container": container.id,
            "position": {
                "x": item.position_x,
                "y": item.position_y,
                "z": item.position_z
            },
            "steps_required": len(blocking_items),
            "blocking_items": [b['item'].id for b in blocking_items]
        })
    )
    db.add(log_action)
    
    db.commit()
    
    # Create result
    result = schemas.RetrievalResult(
        item_id=item.id,
        container_id=container.id,
        steps=steps,
        total_steps=len(blocking_items)
    )
    
    return result

# Item CRUD operations
def get_item(db: Session, item_id: str):
    return db.query(models.Item).filter(models.Item.id == item_id).first()

def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.Item(
        id=item.id,
        name=item.name,
        width=item.width,
        depth=item.depth,
        height=item.height,
        mass=item.mass,
        priority=item.priority,
        expiry_date=item.expiry_date,
        usage_limit=item.usage_limit,
        usage_count=0,
        preferred_zone=item.preferred_zone,
        is_waste=False
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# Container CRUD operations
def get_container(db: Session, container_id: str):
    return db.query(models.Container).filter(models.Container.id == container_id).first()

def get_containers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Container).offset(skip).limit(limit).all()

def create_container(db: Session, container: schemas.ContainerCreate):
    db_container = models.Container(
        id=container.id,
        zone=container.zone,
        width=container.width,
        depth=container.depth,
        height=container.height
    )
    db.add(db_container)
    db.commit()
    db.refresh(db_container)
    return db_container

# Placement recommendation operations
def recommend_placement(db: Session, request: schemas.PlacementRequest):
    item = get_item(db, request.item_id)
    if not item:
        raise ValueError(f"Item with ID {request.item_id} not found")
    
    # Get all containers or a specific container if preferred
    if request.preferred_container_id:
        containers = [get_container(db, request.preferred_container_id)]
        if not containers[0]:
            raise ValueError(f"Container with ID {request.preferred_container_id} not found")
    else:
        containers = get_containers(db)
    
    # Initialize placement options
    placement_options = []
    
    # For each container, find possible placements
    for container in containers:
        # Check if container zone matches item's preferred zone
        zone_match = item.preferred_zone == container.zone
        
        # Get all items in this container
        container_items = db.query(models.Item).filter(models.Item.container_id == container.id).all()
        
        # Try all possible orientations of the item
        item_dimensions = [(item.width, item.depth, item.height),
                          (item.width, item.height, item.depth),
                          (item.depth, item.width, item.height),
                          (item.depth, item.height, item.width),
                          (item.height, item.width, item.depth),
                          (item.height, item.depth, item.width)]
        
        orientation_names = ["xyz", "xzy", "yxz", "yzx", "zxy", "zyx"]
        
        for i, (width, depth, height) in enumerate(item_dimensions):
            # Check if item fits in container
            if width > container.width or depth > container.depth or height > container.height:
                continue
            
            # Find possible positions for the item
            positions = find_positions(container, container_items, width, depth, height)
            
            for pos_x, pos_y, pos_z in positions:
                # Calculate scores
                accessibility_score = calculate_accessibility_score(container, container_items, pos_x, pos_y, pos_z, width, depth, height)
                space_efficiency_score = calculate_space_efficiency_score(container, pos_x, pos_y, pos_z, width, depth, height)
                priority_score = item.priority / 100.0  # Normalize to 0-1
                zone_preference_score = 1.0 if zone_match else 0.5
                
                # Calculate overall score (weighted sum)
                overall_score = (0.4 * accessibility_score + 
                                0.2 * space_efficiency_score + 
                                0.3 * priority_score + 
                                0.1 * zone_preference_score)
                
                # Create placement option
                option = schemas.PlacementOption(
                    container_id=container.id,
                    position_x=pos_x,
                    position_y=pos_y,
                    position_z=pos_z,
                    orientation=orientation_names[i],
                    accessibility_score=accessibility_score,
                    space_efficiency_score=space_efficiency_score,
                    priority_score=priority_score,
                    zone_preference_score=zone_preference_score,
                    overall_score=overall_score
                )
                
                placement_options.append(option)
    
    # Sort options by overall score (descending)
    placement_options.sort(key=lambda x: x.overall_score, reverse=True)
    
    # Check if rearrangement is needed
    rearrangement_needed = len(placement_options) == 0
    rearrangement_plan = None
    
    if rearrangement_needed:
        # Generate rearrangement plan
        rearrangement_plan, new_option = generate_rearrangement_plan(db, item, containers)
        if new_option:
            placement_options.append(new_option)
    
    # Create recommendation
    recommendation = schemas.PlacementRecommendation(
        item_id=item.id,
        options=placement_options,
        recommended_option=placement_options[0] if placement_options else None,
        rearrangement_needed=rearrangement_needed,
        rearrangement_plan=rearrangement_plan
    )
    
    return recommendation

# Helper function to find possible positions for an item in a container
def find_positions(container, container_items, width, depth, height):
    # Simple implementation: check a grid of positions
    positions = []
    
    # Create a 3D grid representation of the container
    grid_resolution = 5  # cm
    grid_width = int(container.width // grid_resolution) + 1
    grid_depth = int(container.depth // grid_resolution) + 1
    grid_height = int(container.height // grid_resolution) + 1
    
    # Initialize grid (0 = empty, 1 = occupied)
    grid = np.zeros((grid_width, grid_depth, grid_height), dtype=int)
    
    # Mark occupied spaces
    for item in container_items:
        if item.orientation == "xyz":
            item_width, item_depth, item_height = item.width, item.depth, item.height
        elif item.orientation == "xzy":
            item_width, item_depth, item_height = item.width, item.height, item.depth
        elif item.orientation == "yxz":
            item_width, item_depth, item_height = item.depth, item.width, item.height
        elif item.orientation == "yzx":
            item_width, item_depth, item_height = item.depth, item.height, item.width
        elif item.orientation == "zxy":
            item_width, item_depth, item_height = item.height, item.width, item.depth
        elif item.orientation == "zyx":
            item_width, item_depth, item_height = item.height, item.depth, item.width
        
        # Convert item position to grid coordinates
        grid_x_start = int(item.position_x // grid_resolution)
        grid_y_start = int(item.position_y // grid_resolution)
        grid_z_start = int(item.position_z // grid_resolution)
        
        grid_x_end = min(grid_width, int((item.position_x + item_width) // grid_resolution) + 1)
        grid_y_end = min(grid_depth, int((item.position_y + item_depth) // grid_resolution) + 1)
        grid_z_end = min(grid_height, int((item.position_z + item_height) // grid_resolution) + 1)
        
        # Mark as occupied
        grid[grid_x_start:grid_x_end, grid_y_start:grid_y_end, grid_z_start:grid_z_end] = 1
    
    # Check each position in the grid
    for x in range(grid_width):
        for y in range(grid_depth):
            for z in range(grid_height):
                # Convert grid coordinates to actual coordinates
                pos_x = x * grid_resolution
                pos_y = y * grid_resolution
                pos_z = z * grid_resolution
                
                # Check if item fits within container bounds
                if (pos_x + width > container.width or
                    pos_y + depth > container.depth or
                    pos_z + height > container.height):
                    continue
                
                # Check if space is available
                grid_x_end = min(grid_width, int((pos_x + width) // grid_resolution) + 1)
                grid_y_end = min(grid_depth, int((pos_y + depth) // grid_resolution) + 1)
                grid_z_end = min(grid_height, int((pos_z + height) // grid_resolution) + 1)
                
                if np.sum(grid[x:grid_x_end, y:grid_y_end, z:grid_z_end]) == 0:
                    positions.append((pos_x, pos_y, pos_z))
    
    return positions

# Helper function to calculate accessibility score
def calculate_accessibility_score(container, container_items, pos_x, pos_y, pos_z, width, depth, height):
    # Simple implementation: higher score if closer to the open face
    # Assuming the open face is at y=0
    normalized_depth = 1.0 - (pos_y / container.depth)
    
    # Check if item is blocked by other items
    blocked_score = 1.0
    for item in container_items:
        # Check if item is in front of the new position
        if (item.position_y < pos_y and
            item.position_x < pos_x + width and
            item.position_x + item.width > pos_x and
            item.position_z < pos_z + height and
            item.position_z + item.height > pos_z):
            blocked_score *= 0.8  # Reduce score for each blocking item
    
    return normalized_depth * blocked_score

# Helper function to calculate space efficiency score
def calculate_space_efficiency_score(container, pos_x, pos_y, pos_z, width, depth, height):
    # Simple implementation: higher score if item is placed against walls or floor
    
    # Check if item is against walls or floor
    against_wall_count = 0
    if pos_x == 0 or pos_x + width == container.width:
        against_wall_count += 1
    if pos_y == 0 or pos_y + depth == container.depth:
        against_wall_count += 1
    if pos_z == 0 or pos_z + height == container.height:
        against_wall_count += 1
    
    # Normalize to 0-1
    return against_wall_count / 3.0

# Helper function to generate rearrangement plan
def generate_rearrangement_plan(db, item, containers):
    # Simple implementation: find a container with enough space after removing lower priority items
    
    for container in containers:
        # Get all items in this container
        container_items = db.query(models.Item).filter(models.Item.container_id == container.id).all()
        
        # Filter items with lower priority than the new item
        lower_priority_items = [i for i in container_items if i.priority < item.priority]
        
        # Sort by priority (ascending)
        lower_priority_items.sort(key=lambda x: x.priority)
        
        # Try removing items one by one until there's enough space
        removed_items = []
        for remove_item in lower_priority_items:
            removed_items.append(remove_item)
            
            # Check if there's enough space now
            remaining_items = [i for i in container_items if i not in removed_items]
            
            # Try all possible orientations of the item
            item_dimensions = [(item.width, item.depth, item.height),
                              (item.width, item.height, item.depth),
                              (item.depth, item.width, item.height),
                              (item.depth, item.height, item.width),
                              (item.height, item.width, item.depth),
                              (item.height, item.depth, item.width)]
            
            orientation_names = ["xyz", "xzy", "yxz", "yzx", "zxy", "zyx"]
            
            for i, (width, depth, height) in enumerate(item_dimensions):
                # Check if item fits in container
                if width > container.width or depth > container.depth or height > container.height:
                    continue
                
                # Find possible positions for the item
                positions = find_positions(container, remaining_items, width, depth, height)
                
                if positions:
                    # Found a valid position after rearrangement
                    pos_x, pos_y, pos_z = positions[0]
                    
                    # Create rearrangement plan
                    plan = []
                    for r_item in removed_items:
                        plan.append({
                            "action": "remove",
                            "item_id": r_item.id,
                            "item_name": r_item.name,
                            "from_container": container.id
                        })
                    
                    # Create placement option
                    option = schemas.PlacementOption(
                        container_id=container.id,
                        position_x=pos_x,
                        position_y=pos_y,
                        position_z=pos_z,
                        orientation=orientation_names[i],
                        accessibility_score=0.8,  # Estimated
                        space_efficiency_score=0.7,  # Estimated
                        priority_score=item.priority / 100.0,
                        zone_preference_score=1.0 if item.preferred_zone == container.zone else 0.5,
                        overall_score=0.7  # Estimated
                    )
                    
                    return plan, option
    
    # No rearrangement possible
    return None, None

def place_item(db: Session, request: schemas.PlacementRequest):
    """
    Enhanced placement function with better tracking and validation.
    Records item placement with detailed history and validates position conflicts.
    """
    # Get item
    item = get_item(db, request.item_id)
    if not item:
        raise ValueError(f"Item with ID {request.item_id} not found")
    
    # If a specific position is provided, validate and use it
    if hasattr(request, 'position') and request.position:
        # Validate the position
        container = get_container(db, request.position.container_id)
        if not container:
            return schemas.PlacementResult(
                success=False,
                item_id=item.id,
                message=f"Container with ID {request.position.container_id} not found"
            )
        
        # Check if item fits in container with the specified orientation
        item_width, item_depth, item_height = get_dimensions_by_orientation(
            item.width, item.depth, item.height, request.position.orientation
        )
        
        if (item_width > container.width or 
            item_depth > container.depth or 
            item_height > container.height):
            return schemas.PlacementResult(
                success=False,
                item_id=item.id,
                message="Item does not fit in container with the specified orientation"
            )
        
        # Check if position is valid (not conflicting with other items)
        container_items = db.query(models.Item).filter(
            models.Item.container_id == container.id,
            models.Item.id != item.id
        ).all()
        
        # Check for collision with other items
        if not is_position_valid(container_items, request.position.position_x, 
                               request.position.position_y, request.position.position_z, 
                               item_width, item_depth, item_height):
            return schemas.PlacementResult(
                success=False,
                item_id=item.id,
                message="Position conflicts with existing items"
            )
        
        # Update item with the specified position
        item.container_id = request.position.container_id
        item.position_x = request.position.position_x
        item.position_y = request.position.position_y
        item.position_z = request.position.position_z
        item.orientation = request.position.orientation
        
        # Create position object for result
        position = schemas.ItemPosition(
            container_id=request.position.container_id,
            position_x=request.position.position_x,
            position_y=request.position.position_y,
            position_z=request.position.position_z,
            orientation=request.position.orientation
        )
        
    else:
        # Get placement recommendation
        recommendation = recommend_placement(db, request)
        
        if not recommendation.recommended_option:
            return schemas.PlacementResult(
                success=False,
                item_id=item.id,
                message="No suitable placement found"
            )
        
        # Apply rearrangement if needed
        if recommendation.rearrangement_needed and recommendation.rearrangement_plan:
            # In a real implementation, this would involve more complex logic
            # to handle the actual rearrangement of items
            pass
        
        # Update item with new position
        option = recommendation.recommended_option
        item.container_id = option.container_id
        item.position_x = option.position_x
        item.position_y = option.position_y
        item.position_z = option.position_z
        item.orientation = option.orientation
        
        # Create position object for result
        position = schemas.ItemPosition(
            container_id=option.container_id,
            position_x=option.position_x,
            position_y=option.position_y,
            position_z=option.position_z,
            orientation=option.orientation
        )
    
    # Record previous position for history
    previous_position = None
    if hasattr(item, 'container_id') and item.container_id:
        previous_position = {
            "container_id": item.container_id,
            "position_x": item.position_x,
            "position_y": item.position_y,
            "position_z": item.position_z,
            "orientation": item.orientation
        }
    
    # Log action with detailed information
    log_action = models.ActionLog(
        action_type="place",
        item_id=item.id,
        container_id=position.container_id,
        astronaut_id=request.astronaut_id if hasattr(request, 'astronaut_id') else None,
        details=json.dumps({
            "action": "placed",
            "item_name": item.name,
            "container": position.container_id,
            "position": {
                "x": position.position_x,
                "y": position.position_y,
                "z": position.position_z,
                "orientation": position.orientation
            },
            "previous_position": previous_position,
            "timestamp": datetime.utcnow().isoformat()
        })
    )
    db.add(log_action)
    
    db.commit()
    
    # Create result
    result = schemas.PlacementResult(
        success=True,
        item_id=item.id,
        container_id=position.container_id,
        position=position,
        message="Item placed successfully"
    )
    
    return result

def get_dimensions_by_orientation(width, depth, height, orientation):
    """Helper function to get dimensions based on orientation."""
    if not orientation or orientation == "xyz":
        return width, depth, height
    elif orientation == "xzy":
        return width, height, depth
    elif orientation == "yxz":
        return depth, width, height
    elif orientation == "yzx":
        return depth, height, width
    elif orientation == "zxy":
        return height, width, depth
    elif orientation == "zyx":
        return height, depth, width
    else:
        return width, depth, height

def is_position_valid(container_items, pos_x, pos_y, pos_z, width, depth, height):
    """Check if a position is valid (no collision with other items)."""
    # Define the new item's bounding box
    new_box = {
        'min_x': pos_x,
        'max_x': pos_x + width,
        'min_y': pos_y,
        'max_y': pos_y + depth,
        'min_z': pos_z,
        'max_z': pos_z + height
    }
    
    # Check for collision with each existing item
    for item in container_items:
        # Get item dimensions based on orientation
        item_width, item_depth, item_height = get_item_dimensions(item)
        
        # Define the existing item's bounding box
        item_box = {
            'min_x': item.position_x,
            'max_x': item.position_x + item_width,
            'min_y': item.position_y,
            'max_y': item.position_y + item_depth,
            'min_z': item.position_z,
            'max_z': item.position_z + item_height
        }
        
        # Check for overlap in all three dimensions
        x_overlap = (new_box['min_x'] < item_box['max_x'] and 
                     new_box['max_x'] > item_box['min_x'])
        y_overlap = (new_box['min_y'] < item_box['max_y'] and 
                     new_box['max_y'] > item_box['min_y'])
        z_overlap = (new_box['min_z'] < item_box['max_z'] and 
                     new_box['max_z'] > item_box['min_z'])
        
        # If there's overlap in all dimensions, there's a collision
        if x_overlap and y_overlap and z_overlap:
            return False
    
    # No collision found
    return True

# Waste management operations
def identify_waste(db: Session):
    # Get current system date
    system_date = db.query(models.SystemDate).first()
    current_date = system_date.current_date if system_date else datetime.utcnow()
    
    # Find expired items
    expired_items = db.query(models.Item).filter(
        models.Item.expiry_date.isnot(None),
        models.Item.expiry_date <= current_date,
        models.Item.is_waste == False
    ).all()
    
    # Find depleted items
    depleted_items = db.query(models.Item).filter(
        models.Item.usage_limit.isnot(None),
        models.Item.usage_count >= models.Item.usage_limit,
        models.Item.is_waste == False
    ).all()
    
    # Mark items as waste
    for item in expired_items + depleted_items:
        item.is_waste = True
    
    db.commit()
    
    # Create result
    waste_items = []
    for item in expired_items:
        waste_items.append(schemas.WasteItem(
            item=item,
            reason="expired"
        ))
    
    for item in depleted_items:
        if item not in expired_items:  # Avoid duplicates
            waste_items.append(schemas.WasteItem(
                item=item,
                reason="usage_limit_reached"
            ))
    
    return waste_items

def plan_waste_return(db: Session, request: schemas.ReturnPlanRequest):
    # Get all waste items
    waste_items = db.query(models.Item).filter(models.Item.is_waste == True).all()
    
    # Sort by mass (descending) to prioritize heavier items
    waste_items.sort(key=lambda x: x.mass, reverse=True)
    
    # Select items for return within weight limit
    selected_items = []
    total_mass = 0.0
    
    for item in waste_items:
        if total_mass + item.mass <= request.max_weight:
            selected_items.append(item)
            total_mass += item.mass
    
    # Calculate space reclaimed per container
    space_reclaimed = {}
    for item in selected_items:
        if item.container_id:
            # Calculate volume of item
            if item.orientation == "xyz":
                volume = item.width * item.depth * item.height
            elif item.orientation == "xzy":
                volume = item.width * item.height * item.depth
            elif item.orientation == "yxz":
                volume = item.depth * item.width * item.height
            elif item.orientation == "yzx":
                volume = item.depth * item.height * item.width
            elif item.orientation == "zxy":
                volume = item.height * item.width * item.depth
            elif item.orientation == "zyx":
                volume = item.height * item.depth * item.width
            else:
                volume = item.width * item.depth * item.height
            
            if item.container_id in space_reclaimed:
                space_reclaimed[item.container_id] += volume
            else:
                space_reclaimed[item.container_id] = volume
    
    # Create return plan items
    return_plan_items = []
    for item in selected_items:
        return_plan_items.append(schemas.ReturnPlanItem(
            item_id=item.id,
            name=item.name,
            mass=item.mass,
            priority=item.priority,
            reason="expired" if item.expiry_date and item.expiry_date <= datetime.utcnow() else "usage_limit_reached"
        ))
    
    # Create result
    result = schemas.ReturnPlan(
        items=return_plan_items,
        total_mass=total_mass,
        remaining_capacity=request.max_weight - total_mass,
        space_reclaimed=space_reclaimed
    )
    
    return result

# Time simulation operations
def simulate_days(db: Session, days: int):
    # Get current system date
    system_date = db.query(models.SystemDate).first()
    if not system_date:
        system_date = models.SystemDate(current_date=datetime.utcnow())
        db.add(system_date)
    
    # Update system date
    current_date = system_date.current_date
    new_date = current_date + timedelta(days=days)
    system_date.current_date = new_date
    
    # Find newly expired items
    expired_items = db.query(models.Item).filter(
        models.Item.expiry_date.isnot(None),
        models.Item.expiry_date > current_date,
        models.Item.expiry_date <= new_date,
        models.Item.is_waste == False
    ).all()
    
    # Mark expired items as waste
    for item in expired_items:
        item.is_waste = True
    
    # No items are depleted during simulation (only during retrieval)
    depleted_items = []
    
    db.commit()
    
    # Create result
    result = schemas.SimulationResult(
        days_simulated=days,
        current_date=new_date,
        items_expired=expired_items,
        items_depleted=depleted_items
    )
    
    return result

# Logging operations
def get_logs(db: Session, skip: int = 0, limit: int = 100, filter_type: str = None, item_id: str = None, astronaut_id: str = None):
    """
    Enhanced log retrieval with filtering options.
    """
    query = db.query(models.ActionLog).order_by(models.ActionLog.timestamp.desc())
    
    # Apply filters if provided
    if filter_type:
        query = query.filter(models.ActionLog.action_type == filter_type)
    
    if item_id:
        query = query.filter(models.ActionLog.item_id == item_id)
    
    if astronaut_id:
        query = query.filter(models.ActionLog.astronaut_id == astronaut_id)
    
    # Execute query with pagination
    logs = query.offset(skip).limit(limit).all()
    
    return logs

# Import/Export operations
def import_items(db: Session, items: List[schemas.ItemCreate]):
    for item_data in items:
        # Check if item already exists
        existing_item = get_item(db, item_data.id)
        if existing_item:
            # Update existing item
            for key, value in item_data.dict().items():
                setattr(existing_item, key, value)
        else:
            # Create new item
            create_item(db, item_data)
    
    db.commit()
    return {"message": f"Imported {len(items)} items"}

def import_containers(db: Session, containers: List[schemas.ContainerCreate]):
    for container_data in containers:
        # Check if container already exists
        existing_container = get_container(db, container_data.id)
        if existing_container:
            # Update existing container
            for key, value in container_data.dict().items():
                setattr(existing_container, key, value)
        else:
            # Create new container
            create_container(db, container_data)
    
    db.commit()
    return {"message": f"Imported {len(containers)} containers"}

def export_items(db: Session):
    items = get_items(db)
    return items

def export_containers(db: Session):
    containers = get_containers(db)
    return containers
