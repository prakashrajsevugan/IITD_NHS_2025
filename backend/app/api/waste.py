from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .. import data_store

router = APIRouter()

@router.get("/waste/identify")
def identify_waste_items():
    try:
        # Get all items
        all_items = data_store.get_all_items()
        
        # Identify waste items (already marked as waste)
        waste_items = []
        
        for item in all_items:
            if item.status == "Waste":
                # Get container information
                container = data_store.get_container(item.container_id) if item.container_id else None
                
                # Create position data (simplified for in-memory implementation)
                position = None
                if container:
                    position = {
                        "startCoordinates": {
                            "width": 0,
                            "depth": 0,
                            "height": 0
                        },
                        "endCoordinates": {
                            "width": item.width,
                            "depth": item.depth,
                            "height": item.height
                        }
                    }
                
                # Determine reason for waste
                reason = "Unknown"
                if hasattr(item, 'expiry_date') and item.expiry_date:
                    expiry_date = datetime.fromisoformat(item.expiry_date)
                    if datetime.now() >= expiry_date:
                        reason = "Expired"
                
                if hasattr(item, 'usage_count') and hasattr(item, 'usage_limit'):
                    if item.usage_limit and item.usage_count >= item.usage_limit:
                        reason = "Out of Uses"
                
                waste_items.append({
                    "itemId": item.id,
                    "name": item.name,
                    "reason": reason,
                    "containerId": item.container_id if item.container_id else None,
                    "position": position
                })
        
        # Identify potential waste items (expired or usage limit reached)
        current_date = datetime.now()
        potential_waste = []
        
        for item in all_items:
            if item.status == "Waste":
                continue  # Skip items already marked as waste
            
            # Check expiry date
            if hasattr(item, 'expiry_date') and item.expiry_date:
                expiry_date = datetime.fromisoformat(item.expiry_date)
                if current_date >= expiry_date:
                    # Get container information
                    container = data_store.get_container(item.container_id) if item.container_id else None
                    
                    # Create position data (simplified for in-memory implementation)
                    position = None
                    if container:
                        position = {
                            "startCoordinates": {
                                "width": 0,
                                "depth": 0,
                                "height": 0
                            },
                            "endCoordinates": {
                                "width": item.width,
                                "depth": item.depth,
                                "height": item.height
                            }
                        }
                    
                    potential_waste.append({
                        "itemId": item.id,
                        "name": item.name,
                        "reason": "Expired",
                        "containerId": item.container_id if item.container_id else None,
                        "position": position
                    })
                    continue
            
            # Check usage limit
            if hasattr(item, 'usage_count') and hasattr(item, 'usage_limit'):
                if item.usage_limit and item.usage_count >= item.usage_limit:
                    # Get container information
                    container = data_store.get_container(item.container_id) if item.container_id else None
                    
                    # Create position data (simplified for in-memory implementation)
                    position = None
                    if container:
                        position = {
                            "startCoordinates": {
                                "width": 0,
                                "depth": 0,
                                "height": 0
                            },
                            "endCoordinates": {
                                "width": item.width,
                                "depth": item.depth,
                                "height": item.height
                            }
                        }
                    
                    potential_waste.append({
                        "itemId": item.id,
                        "name": item.name,
                        "reason": "Out of Uses",
                        "containerId": item.container_id if item.container_id else None,
                        "position": position
                    })
        
        # Log the identification
        data_store.create_log({
            "action_type": "IDENTIFY_WASTE",
            "description": f"Identified {len(waste_items)} waste items and {len(potential_waste)} potential waste items"
        })
        
        # Combine waste and potential waste items
        all_waste_items = waste_items + potential_waste
        
        return {
            "success": True,
            "wasteItems": all_waste_items
        }
    
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/waste/return-plan")
def generate_waste_return_plan(request: Dict[str, Any] = Body(...)):
    try:
        # Get request data
        undocking_container_id = request.get("undockingContainerId")
        undocking_date = request.get("undockingDate")
        max_weight = request.get("maxWeight", 0)
        
        if not undocking_container_id:
            return {"success": False, "message": "Undocking container ID is required"}
        
        if max_weight <= 0:
            return {"success": False, "message": "Maximum weight must be greater than 0"}
        
        # Get all waste items
        all_items = data_store.get_all_items()
        waste_items = [item for item in all_items if item.status == "Waste"]
        
        # Sort waste items by priority (higher priority first)
        sorted_waste = sorted(waste_items, key=lambda x: x.priority if hasattr(x, 'priority') else 0, reverse=True)
        
        # Generate return plan respecting weight limit
        return_plan = []
        return_items = []
        remaining_weight = max_weight
        step = 1
        
        for item in sorted_waste:
            if item.mass <= remaining_weight:
                # Add to return plan
                return_plan.append({
                    "step": step,
                    "itemId": item.id,
                    "itemName": item.name,
                    "fromContainer": item.container_id if item.container_id else None,
                    "toContainer": undocking_container_id
                })
                
                # Add to return items
                return_items.append({
                    "itemId": item.id,
                    "name": item.name,
                    "reason": "Waste"
                })
                
                remaining_weight -= item.mass
                step += 1
        
        # Generate retrieval steps
        retrieval_steps = []
        step = 1
        
        for item in return_items:
            # Add removal step
            retrieval_steps.append({
                "step": step,
                "action": "remove",
                "itemId": item["itemId"],
                "itemName": item["name"]
            })
            step += 1
            
            # Add retrieve step
            retrieval_steps.append({
                "step": step,
                "action": "retrieve",
                "itemId": item["itemId"],
                "itemName": item["name"]
            })
            step += 1
        
        # Calculate total volume and weight
        total_volume = sum(item.width * item.depth * item.height for item in waste_items if item.id in [i["itemId"] for i in return_items])
        total_weight = max_weight - remaining_weight
        
        # Create return manifest
        return_manifest = {
            "undockingContainerId": undocking_container_id,
            "undockingDate": undocking_date,
            "returnItems": return_items,
            "totalVolume": total_volume,
            "totalWeight": total_weight
        }
        
        # Log the plan generation
        data_store.create_log({
            "action_type": "WASTE_RETURN_PLAN",
            "description": f"Generated waste return plan with {len(return_items)} items, total weight: {total_weight} kg"
        })
        
        return {
            "success": True,
            "returnPlan": return_plan,
            "retrievalSteps": retrieval_steps,
            "returnManifest": return_manifest
        }
    
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/waste/complete-undocking")
def complete_undocking(request: Dict[str, Any] = Body(...)):
    try:
        # Get request data
        undocking_container_id = request.get("undockingContainerId")
        timestamp = request.get("timestamp")
        
        if not undocking_container_id:
            return {"success": False, "message": "Undocking container ID is required"}
        
        # Get all waste items
        all_items = data_store.get_all_items()
        waste_items = [item for item in all_items if item.status == "Waste"]
        
        # Remove waste items from data store
        removed_items = []
        
        for item in waste_items:
            # Remove item from data store
            data_store.remove_item(item.id)
            removed_items.append(item.id)
        
        # Log the undocking
        data_store.create_log({
            "action_type": "UNDOCKING_COMPLETE",
            "description": f"Removed {len(removed_items)} waste items during undocking",
            "timestamp": timestamp or datetime.now().isoformat(),
            "container_id": undocking_container_id
        })
        
        return {
            "success": True,
            "itemsRemoved": len(removed_items)
        }
    
    except Exception as e:
        return {"success": False, "message": str(e)}
