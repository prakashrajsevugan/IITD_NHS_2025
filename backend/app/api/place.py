from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any
from datetime import datetime
from .. import data_store

router = APIRouter()

@router.post("/place")
async def place_item(request: Dict[str, Any] = Body(...)):
    try:
        # Extract data from request
        item_id = request.get("itemId")
        user_id = request.get("userId")
        timestamp = request.get("timestamp")
        container_id = request.get("containerId")
        position = request.get("position")
        
        if not item_id or not container_id:
            return {"success": False, "message": "Item ID and Container ID are required"}
        
        # Check if item exists
        item = data_store.get_item(item_id)
        if not item:
            return {"success": False, "message": f"Item with ID {item_id} not found"}
        
        # Check if container exists
        container = data_store.get_container(container_id)
        if not container:
            return {"success": False, "message": f"Container with ID {container_id} not found"}
        
        # Calculate volumes
        item_volume = item.width * item.depth * item.height
        container_volume = container.width * container.depth * container.height
        available_volume = container_volume - container.occupied_volume
        
        # Check if item fits in container
        if item_volume > available_volume:
            return {"success": False, "message": f"Item does not fit in container. Item volume: {item_volume}, Available volume: {available_volume}"}
        
        # Place item in container
        result = data_store.place_item(item_id, container_id)
        
        if result:
            # Store position information if provided
            if position:
                # In a real implementation, we would store the position information
                # For the in-memory implementation, we'll just log it
                pass
            
            # Log the placement
            data_store.create_log({
                "action_type": "PLACE_ITEM",
                "description": f"Item {item_id} placed in container {container_id}",
                "item_id": item_id,
                "container_id": container_id,
                "user_id": user_id,
                "timestamp": timestamp or datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "message": f"Item {item_id} successfully placed in container {container_id}"
            }
        else:
            return {"success": False, "message": "Failed to place item in container"}
    
    except Exception as e:
        return {"success": False, "message": str(e)}
