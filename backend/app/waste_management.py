import pandas as pd
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from . import models, schemas, crud

# Constants
UNDOCKING_WEIGHT_LIMIT = 500  # kg

def identify_waste(db: Session, current_date: datetime = None) -> List[Dict[str, Any]]:
    """
    Identify items that should be marked as waste based on expiry date or usage limit.
    
    Args:
        db: Database session
        current_date: Current date for expiry check (defaults to now)
        
    Returns:
        List of waste items
    """
    if current_date is None:
        current_date = datetime.now()
    
    # Calculate threshold date (items expiring within 180 days are considered waste)
    threshold_date = current_date + timedelta(days=180)
    
    # Query items that are expired or have reached usage limit
    items = db.query(models.Item).filter(
        (
            (models.Item.expiry_date.isnot(None)) & 
            (models.Item.expiry_date <= threshold_date.isoformat())
        ) | 
        (
            (models.Item.usage_limit.isnot(None)) & 
            (models.Item.usage_limit <= 0)
        )
    ).all()
    
    # Update status to 'Waste'
    waste_items = []
    for item in items:
        if item.status != 'Waste':
            item.status = 'Waste'
            db.commit()
            
            # Log the action
            crud.log_action(
                db,
                schemas.LogCreate(
                    action_type="waste",
                    item_id=item.id,
                    astronaut_id="SYSTEM",
                    details={
                        "action": "identify",
                        "item_name": item.name,
                        "reason": "expired" if item.expiry_date and item.expiry_date <= current_date.isoformat() else "usage_limit"
                    }
                )
            )
        
        waste_items.append(item)
    
    return waste_items

def plan_waste_return(db: Session) -> Optional[Dict[str, Any]]:
    """
    Generate a plan for returning waste items, respecting the weight limit.
    
    Args:
        db: Database session
        
    Returns:
        A dictionary with the return plan and manifest, or None if no waste items
    """
    # Get all waste items
    waste_items = db.query(models.Item).filter(models.Item.status == 'Waste').all()
    
    if not waste_items:
        return None
    
    # Ensure undocking module exists
    undocking_module = db.query(models.Container).filter(models.Container.id == "UNDOCKING_MODULE").first()
    if not undocking_module:
        # Create undocking module if it doesn't exist
        undocking_module = models.Container(
            id="UNDOCKING_MODULE",
            zone="Undocking",
            width=200.0,
            depth=200.0,
            height=200.0,
            occupied_volume=0.0
        )
        db.add(undocking_module)
        db.commit()
    
    # Calculate total weight
    total_weight = sum(item.mass for item in waste_items)
    
    # If total weight exceeds limit, sort by priority and mass to select items
    selected_items = waste_items
    if total_weight > UNDOCKING_WEIGHT_LIMIT:
        # Convert to DataFrame for easier sorting and filtering
        items_df = pd.DataFrame([
            {
                "id": item.id,
                "name": item.name,
                "mass": item.mass,
                "priority": item.priority,
                "container_id": item.container_id
            }
            for item in waste_items
        ])
        
        # Sort by priority (low to high) and then by mass (high to low)
        items_df = items_df.sort_values(["priority", "mass"], ascending=[True, False])
        
        # Select items up to the weight limit
        cumulative_mass = 0
        selected_indices = []
        
        for idx, row in items_df.iterrows():
            if cumulative_mass + row["mass"] <= UNDOCKING_WEIGHT_LIMIT:
                cumulative_mass += row["mass"]
                selected_indices.append(idx)
        
        selected_items_df = items_df.iloc[selected_indices]
        
        # Get the original Item objects for the selected items
        selected_items = [
            item for item in waste_items 
            if item.id in selected_items_df["id"].values
        ]
    
    # Generate plan and manifest
    plan = []
    manifest_items = []
    
    for item in selected_items:
        # Add step to plan
        plan.append({
            "step": f"Move {item.id} ({item.name}) from {item.container_id or 'storage'} to UNDOCKING_MODULE",
            "mass_kg": item.mass,
            "item_id": item.id,
            "container_id": item.container_id
        })
        
        # Add item to manifest
        manifest_items.append({
            "item_id": item.id,
            "name": item.name,
            "mass_kg": item.mass
        })
    
    # Calculate total weight of selected items
    total_selected_weight = sum(item.mass for item in selected_items)
    
    # Create manifest
    manifest = {
        "items": manifest_items,
        "total_weight_kg": total_selected_weight
    }
    
    # Log the action
    crud.log_action(
        db,
        schemas.LogCreate(
            action_type="waste",
            astronaut_id="SYSTEM",
            details={
                "action": "plan",
                "items_count": len(selected_items),
                "total_weight": total_selected_weight
            }
        )
    )
    
    return {
        "plan": plan,
        "manifest": manifest
    }

def complete_undocking(db: Session) -> Dict[str, Any]:
    """
    Complete the undocking process by removing waste items and freeing up space.
    
    Args:
        db: Database session
        
    Returns:
        A dictionary with the result of the operation
    """
    # Get all waste items
    waste_items = db.query(models.Item).filter(models.Item.status == 'Waste').all()
    
    if not waste_items:
        return {
            "message": "No waste items to remove",
            "items_removed": 0
        }
    
    # Free up space and remove waste items
    for item in waste_items:
        # Calculate volume
        volume = item.width * item.depth * item.height
        
        # Update container's occupied volume if item is in a container
        if item.container_id:
            container = db.query(models.Container).filter(models.Container.id == item.container_id).first()
            if container:
                container.occupied_volume = max(0, container.occupied_volume - volume)
                db.commit()
        
        # Delete the item
        db.delete(item)
    
    # Reset undocking module
    undocking_module = db.query(models.Container).filter(models.Container.id == "UNDOCKING_MODULE").first()
    if undocking_module:
        undocking_module.occupied_volume = 0
        db.commit()
    
    # Log the action
    crud.log_action(
        db,
        schemas.LogCreate(
            action_type="waste",
            astronaut_id="SYSTEM",
            details={
                "action": "undock",
                "items_removed": len(waste_items)
            }
        )
    )
    
    db.commit()
    
    return {
        "message": f"Undocking completed successfully. {len(waste_items)} waste items removed.",
        "items_removed": len(waste_items)
    }
