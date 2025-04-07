import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from . import models, schemas, crud

def calculate_volume(item: Dict[str, Any]) -> float:
    """Calculate the volume of an item in cubic centimeters."""
    if isinstance(item, dict):
        return item["width_cm"] * item["depth_cm"] * item["height_cm"]
    else:
        return item.width * item.height * item.depth

def find_rearrangement(db: Session, new_items_df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Find a rearrangement plan for placing new items when space is insufficient.
    
    Args:
        db: Database session
        new_items_df: DataFrame containing new items to be placed
        
    Returns:
        A dictionary with rearrangement plan or None if no rearrangement is needed
    """
    # Get all containers
    containers = crud.get_all_containers(db)
    containers_dict = {
        container.id: {
            "zone": container.zone,
            "width": container.width,
            "depth": container.depth,
            "height": container.height,
            "occupied_volume": container.occupied_volume,
            "total_volume": container.width * container.depth * container.height
        } for container in containers
    }
    
    # Get all current items in containers
    current_items = crud.get_all_items(db)
    current_items_in_containers = [item for item in current_items if item.container_id]
    
    # Calculate total space needed for new items
    new_items_df["volume"] = new_items_df.apply(lambda item: 
        item["width_cm"] * item["depth_cm"] * item["height_cm"], axis=1)
    total_new_volume = new_items_df["volume"].sum()
    
    # Calculate available space across all containers
    total_available = sum(
        cont["total_volume"] - cont["occupied_volume"] 
        for cont in containers_dict.values()
    )
    
    # If there's enough space, no rearrangement needed
    if total_available >= total_new_volume:
        return None
    
    # Sort current items by priority (low to high) for relocation candidates
    current_items_with_volume = []
    for item in current_items_in_containers:
        item_dict = item.__dict__.copy()
        item_dict["volume"] = calculate_volume(item)
        current_items_with_volume.append(item_dict)
    
    # Sort by priority (low to high)
    relocation_candidates = sorted(
        current_items_with_volume, 
        key=lambda x: (x["priority"], -x["volume"])
    )
    
    # Find items to relocate
    volume_to_free = total_new_volume - total_available
    items_to_relocate = []
    freed_volume = 0
    
    for item in relocation_candidates:
        if freed_volume >= volume_to_free:
            break
        
        items_to_relocate.append(item)
        freed_volume += item["volume"]
        
        # Update container's occupied volume
        containers_dict[item["container_id"]]["occupied_volume"] -= item["volume"]
    
    # Generate step-by-step plan
    plan = []
    
    # Steps to remove items
    for item in items_to_relocate:
        plan.append({
            "step": f"Remove {item['id']} ({item['name']}) from {item['container_id']}",
            "volume_freed": item["volume"],
            "item_id": item["id"],
            "container_id": item["container_id"],
            "action": "remove"
        })
    
    # Attempt to place new items
    placed_items = []
    
    for _, new_item in new_items_df.iterrows():
        placed = False
        
        for cont_id, cont in containers_dict.items():
            # Check if item fits in container dimensions
            if (new_item["width_cm"] <= cont["width"] and 
                new_item["depth_cm"] <= cont["depth"] and 
                new_item["height_cm"] <= cont["height"] and 
                cont["occupied_volume"] + new_item["volume"] <= cont["total_volume"]):
                
                placed_items.append((new_item, cont_id))
                containers_dict[cont_id]["occupied_volume"] += new_item["volume"]
                
                plan.append({
                    "step": f"Place {new_item['item_id']} ({new_item['name']}) in {cont_id}",
                    "volume_added": new_item["volume"],
                    "item_id": new_item["item_id"],
                    "container_id": cont_id,
                    "action": "place"
                })
                
                placed = True
                break
        
        if not placed:
            # If we couldn't place an item even after rearrangement, return failure
            return {
                "success": False,
                "message": f"Could not place item {new_item['item_id']} even after rearrangement"
            }
    
    return {
        "success": True,
        "items_to_relocate": items_to_relocate,
        "plan": plan,
        "placed_items": placed_items
    }

def execute_rearrangement(db: Session, rearrangement_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a rearrangement plan by updating the database.
    
    Args:
        db: Database session
        rearrangement_plan: The rearrangement plan to execute
        
    Returns:
        A dictionary with the execution result
    """
    if not rearrangement_plan or not rearrangement_plan.get("success", False):
        return {"success": False, "message": "Invalid rearrangement plan"}
    
    # Execute each step in the plan
    for step in rearrangement_plan["plan"]:
        if step["action"] == "remove":
            # Update item to remove it from container
            item = crud.get_item(db, step["item_id"])
            if item:
                # Store the original container for logging
                original_container = item.container_id
                
                # Update the item
                item.container_id = None
                db.commit()
                
                # Log the action
                crud.log_action(
                    db,
                    schemas.LogCreate(
                        action_type="rearrange",
                        item_id=step["item_id"],
                        astronaut_id="SYSTEM",
                        details={
                            "action": "remove",
                            "item_name": item.name,
                            "from_container": original_container,
                            "volume": step["volume_freed"]
                        }
                    )
                )
                
                # Update container's occupied volume
                container = crud.get_container(db, original_container)
                if container:
                    container.occupied_volume -= step["volume_freed"]
                    db.commit()
        
        elif step["action"] == "place":
            # Get the item (might be a new item)
            item = crud.get_item(db, step["item_id"])
            
            if not item:
                # This is a new item, we need to create it
                # In a real implementation, you would extract all item details from the plan
                # For simplicity, we'll assume the item was already created
                continue
            
            # Update the item's container
            item.container_id = step["container_id"]
            db.commit()
            
            # Log the action
            crud.log_action(
                db,
                schemas.LogCreate(
                    action_type="rearrange",
                    item_id=step["item_id"],
                    astronaut_id="SYSTEM",
                    details={
                        "action": "place",
                        "item_name": item.name,
                        "to_container": step["container_id"],
                        "volume": step["volume_added"]
                    }
                )
            )
            
            # Update container's occupied volume
            container = crud.get_container(db, step["container_id"])
            if container:
                container.occupied_volume += step["volume_added"]
                db.commit()
    
    return {"success": True, "message": "Rearrangement executed successfully"}
