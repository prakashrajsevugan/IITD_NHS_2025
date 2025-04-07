from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any
from datetime import datetime
from .. import data_store

router = APIRouter()

@router.post("/retrieve")
async def retrieve_item(request: Dict[str, Any] = Body(...)):
    try:
        # Extract data from request
        item_id = request.get("itemId")
        user_id = request.get("userId")
        timestamp = request.get("timestamp")
        
        if not item_id:
            return {"success": False, "message": "Item ID is required"}
        
        # Check if item exists
        item = data_store.get_item(item_id)
        if not item:
            return {"success": False, "message": f"Item with ID {item_id} not found"}
        
        # Update usage count
        if not hasattr(item, 'usage_count'):
            item.usage_count = 0
        
        item.usage_count += 1
        
        # Check if item has reached usage limit
        if hasattr(item, 'usage_limit') and item.usage_limit and item.usage_count >= item.usage_limit:
            item.status = "Waste"
            
            # Log the usage limit reached
            data_store.create_log({
                "action_type": "USAGE_LIMIT_REACHED",
                "description": f"Item {item.id} reached usage limit of {item.usage_limit}",
                "item_id": item.id,
                "user_id": user_id,
                "timestamp": timestamp or datetime.now().isoformat()
            })
        
        # Update item in data store
        data_store.update_item(item)
        
        # Log the retrieval
        data_store.create_log({
            "action_type": "ITEM_RETRIEVED",
            "description": f"Item {item.id} retrieved by user {user_id}",
            "item_id": item.id,
            "user_id": user_id,
            "timestamp": timestamp or datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "message": f"Item {item.id} successfully retrieved"
        }
    
    except Exception as e:
        return {"success": False, "message": str(e)}
